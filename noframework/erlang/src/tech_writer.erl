-module(tech_writer).
-export([main/1]).

-define(MAX_STEPS, 15).
-define(CACHE_DIR, "~/.cache/github").
-define(OUTPUT_DIR, "output").

%% Main entry point
main(Args) ->
    %% Start required applications
    application:ensure_all_started(inets),
    application:ensure_all_started(ssl),
    application:ensure_all_started(jsx),
    application:ensure_all_started(hackney),
    
    try
        ParsedArgs = parse_args(Args),
        run(ParsedArgs)
    catch
        error:{badarg, Msg} ->
            io:format("Error: ~s~n", [Msg]),
            print_usage(),
            halt(1);
        Class:Error:Stacktrace ->
            io:format("Error ~p: ~p~n", [Class, Error]),
            io:format("Stacktrace: ~p~n", [Stacktrace]),
            halt(1)
    end.

%% Run the tech writer
run(#{repo := Repo, prompt := PromptFile, output_dir := OutputDir, 
      file_name := FileName, model := Model}) ->
    
    %% Set up logging
    {Date, Time} = calendar:local_time(),
    LogFileName = io_lib:format("tech-writer-~4..0B~2..0B~2..0B-~2..0B~2..0B~2..0B.log",
                               [element(1, Date), element(2, Date), element(3, Date),
                                element(1, Time), element(2, Time), element(3, Time)]),
    LogDir = filename:join(filename:dirname(?FILE), "logs"),
    filelib:ensure_dir(filename:join(LogDir, "dummy")),
    LogFile = filename:join(LogDir, LogFileName),
    
    log_info("Starting Tech Writer Agent", LogFile),
    log_info(io_lib:format("Model: ~s", [Model]), LogFile),
    
    %% Read prompt
    {ok, PromptContent} = file:read_file(PromptFile),
    Prompt = string:trim(binary_to_list(PromptContent)),
    
    %% Clone or update repository
    RepoPath = clone_or_update_repo(Repo, LogFile),
    log_info(io_lib:format("Repository path: ~s", [RepoPath]), LogFile),
    
    %% Run ReAct agent
    log_info("Starting ReAct agent", LogFile),
    Result = react_loop(RepoPath, Prompt, Model, 1, ?MAX_STEPS, [], LogFile),
    
    %% Save results
    filelib:ensure_dir(filename:join(OutputDir, "dummy")),
    OutputFile = filename:join(OutputDir, FileName),
    ok = file:write_file(OutputFile, Result),
    log_info(io_lib:format("Results saved to: ~s", [OutputFile]), LogFile),
    
    %% Save metadata
    Metadata = create_metadata(Repo, PromptFile, Model, Result),
    MetadataFile = filename:rootname(OutputFile) ++ ".metadata.json",
    ok = file:write_file(MetadataFile, Metadata),
    log_info(io_lib:format("Metadata saved to: ~s", [MetadataFile]), LogFile),
    
    halt(0).

%% Parse command line arguments
parse_args(Args) ->
    %% Convert all arguments to strings if they're binaries
    StringArgs = [case Arg of
        Bin when is_binary(Bin) -> binary_to_list(Bin);
        Str -> Str
    end || Arg <- Args],
    parse_args(StringArgs, #{model => "openai/gpt-4o-mini", 
                       output_dir => ?OUTPUT_DIR}).

parse_args([], Acc) ->
    %% Validate required args
    case maps:is_key(repo, Acc) andalso maps:is_key(prompt, Acc) of
        true -> 
            %% Set default file name if not provided
            case maps:is_key(file_name, Acc) of
                true -> Acc;
                false ->
                    {Date, Time} = calendar:local_time(),
                    DefaultName = io_lib:format("tech-writer-~4..0B~2..0B~2..0B-~2..0B~2..0B~2..0B.md",
                                              [element(1, Date), element(2, Date), element(3, Date),
                                               element(1, Time), element(2, Time), element(3, Time)]),
                    maps:put(file_name, DefaultName, Acc)
            end;
        false -> 
            error({badarg, "Missing required arguments: --repo and --prompt"})
    end;

parse_args(["--repo", Repo | Rest], Acc) ->
    parse_args(Rest, maps:put(repo, Repo, Acc));
parse_args(["--prompt", Prompt | Rest], Acc) ->
    parse_args(Rest, maps:put(prompt, Prompt, Acc));
parse_args(["--output-dir", Dir | Rest], Acc) ->
    parse_args(Rest, maps:put(output_dir, Dir, Acc));
parse_args(["--file-name", Name | Rest], Acc) ->
    parse_args(Rest, maps:put(file_name, Name, Acc));
parse_args(["--model", Model | Rest], Acc) ->
    parse_args(Rest, maps:put(model, Model, Acc));
parse_args([Unknown | _], _) ->
    error({badarg, io_lib:format("Unknown argument: ~s", [Unknown])}).

%% Print usage information
print_usage() ->
    io:format("Usage: tech-writer.sh [OPTIONS]~n~n"),
    io:format("Required options:~n"),
    io:format("  --repo URL          GitHub repository URL~n"),
    io:format("  --prompt FILE       Path to prompt file~n~n"),
    io:format("Optional options:~n"),
    io:format("  --output-dir DIR    Output directory (default: output)~n"),
    io:format("  --file-name NAME    Output file name~n"),
    io:format("  --model MODEL       LLM model to use (default: openai/gpt-4o-mini)~n").

%% Clone or update repository
clone_or_update_repo(RepoUrl, LogFile) ->
    %% Extract repo name from URL
    RepoName = filename:basename(filename:dirname(RepoUrl)) ++ "/" ++ 
               filename:basename(RepoUrl, ".git"),
    CacheDir = filename:join(os:getenv("HOME"), ".cache/github"),
    RepoPath = filename:join(CacheDir, RepoName),
    
    filelib:ensure_dir(filename:join(CacheDir, "dummy")),
    
    case filelib:is_dir(filename:join(RepoPath, ".git")) of
        true ->
            log_info(io_lib:format("Updating existing repository: ~s", [RepoPath]), LogFile),
            os:cmd(io_lib:format("cd ~s && git pull --quiet", [RepoPath]));
        false ->
            log_info(io_lib:format("Cloning repository: ~s", [RepoUrl]), LogFile),
            os:cmd(io_lib:format("git clone --quiet ~s ~s", [RepoUrl, RepoPath]))
    end,
    
    RepoPath.

%% ReAct agent loop
react_loop(_RepoPath, _Prompt, _Model, Step, MaxSteps, Memory, _LogFile) when Step > MaxSteps ->
    %% Extract final answer from memory
    extract_final_answer(Memory);

react_loop(RepoPath, Prompt, Model, Step, MaxSteps, Memory, LogFile) ->
    log_info(io_lib:format("Step ~B/~B", [Step, MaxSteps]), LogFile),
    
    %% Prepare prompt for LLM
    SystemPrompt = get_system_prompt(),
    UserPrompt = build_user_prompt(RepoPath, Prompt, Memory),
    
    %% Call LLM
    Response = call_llm(Model, SystemPrompt, UserPrompt, LogFile),
    
    %% Parse response
    case parse_llm_response(Response) of
        {final_answer, Answer} ->
            log_info("Final answer received", LogFile),
            Answer;
        {action, Action, ActionInput} ->
            %% Execute action
            Observation = execute_action(Action, ActionInput, RepoPath, LogFile),
            
            %% Add to memory
            NewMemory = Memory ++ [{thought, extract_thought(Response)},
                                  {action, Action},
                                  {action_input, ActionInput},
                                  {observation, Observation}],
            
            %% Continue loop
            react_loop(RepoPath, Prompt, Model, Step + 1, MaxSteps, NewMemory, LogFile);
        error ->
            log_info("No valid action found in response", LogFile),
            react_loop(RepoPath, Prompt, Model, Step + 1, MaxSteps, Memory, LogFile)
    end.

%% Get system prompt
get_system_prompt() ->
    "You are a technical documentation assistant that analyses codebases and generates comprehensive documentation.

When given a directory path and a specific analysis request, you will:
1. Explore the codebase structure to understand its organization
2. Read relevant files to comprehend the implementation details
3. Generate detailed technical documentation based on your analysis

You have access to tools that help you explore and understand codebases:
- find_all_matching_files: Find files matching patterns in directories
- read_file: Read the contents of specific files

Important guidelines:
- Always start by exploring the directory structure to understand the codebase layout
- Read files strategically based on the documentation needs
- Pay attention to configuration files, main entry points, and key modules
- Generate clear, well-structured documentation that would help developers understand the codebase

Use the following format:

Thought: I need to [describe what you need to do next]
Action: [tool_name]
Action Input: {\"param\": \"value\"}
Observation: [tool output will be provided here]

... (repeat Thought/Action/Observation as needed)

Thought: I have gathered enough information to provide the final answer
Final Answer: [Your comprehensive documentation/analysis]".

%% Build user prompt
build_user_prompt(RepoPath, Prompt, Memory) ->
    MemoryStr = format_memory(Memory),
    io_lib:format("Analyze the codebase at: ~s~n~nRequest: ~s~n~n~s", 
                  [RepoPath, Prompt, MemoryStr]).

%% Format memory for prompt
format_memory([]) -> "";
format_memory(Memory) ->
    format_memory(Memory, []).

format_memory([], Acc) ->
    lists:reverse(Acc);
format_memory([{thought, T} | Rest], Acc) ->
    format_memory(Rest, [io_lib:format("Thought: ~s~n", [T]) | Acc]);
format_memory([{action, A} | Rest], Acc) ->
    format_memory(Rest, [io_lib:format("Action: ~s~n", [A]) | Acc]);
format_memory([{action_input, I} | Rest], Acc) ->
    format_memory(Rest, [io_lib:format("Action Input: ~s~n", [I]) | Acc]);
format_memory([{observation, O} | Rest], Acc) ->
    format_memory(Rest, [io_lib:format("Observation: ~s~n", [O]) | Acc]).

%% Call LLM
call_llm(Model, SystemPrompt, UserPrompt, LogFile) ->
    %% Get API key and base URL
    {ApiKey, BaseUrl} = get_api_config(Model),
    
    %% Prepare request
    Messages = [#{role => system, content => SystemPrompt},
                #{role => user, content => UserPrompt}],
    
    Body = jsx:encode(#{
        <<"model">> => list_to_binary(get_model_name(Model)),
        <<"messages">> => [#{<<"role">> => atom_to_binary(Role, utf8), 
                           <<"content">> => list_to_binary(Content)} 
                         || #{role := Role, content := Content} <- Messages],
        <<"temperature">> => 0,
        <<"max_tokens">> => 2000
    }),
    
    Headers = [{"Authorization", "Bearer " ++ ApiKey},
               {"Content-Type", "application/json"}],
    
    %% Make request
    case httpc:request(post, {BaseUrl ++ "/chat/completions", Headers, "application/json", Body}, 
                      [{timeout, 30000}], []) of
        {ok, {{_, 200, _}, _, ResponseBody}} ->
            Decoded = jsx:decode(list_to_binary(ResponseBody), [return_maps]),
            Choices = maps:get(<<"choices">>, Decoded, []),
            case Choices of
                [] -> error({llm_error, "No choices in response"});
                [Choice | _] ->
                    Message = maps:get(<<"message">>, Choice),
                    Content = maps:get(<<"content">>, Message),
                    ContentStr = binary_to_list(Content),
                    log_debug(io_lib:format("LLM Response: ~s", [ContentStr]), LogFile),
                    ContentStr
            end;
        {ok, {{_, StatusCode, _}, _, ResponseBody}} ->
            error({llm_error, io_lib:format("HTTP ~B: ~s", [StatusCode, ResponseBody])});
        {error, Reason} ->
            error({llm_error, Reason})
    end.

%% Get API configuration
get_api_config(Model) ->
    case string:split(Model, "/") of
        ["openai" | _] ->
            ApiKey = os:getenv("OPENAI_API_KEY"),
            case ApiKey of
                false -> error({missing_api_key, "OPENAI_API_KEY not set"});
                _ -> {ApiKey, "https://api.openai.com/v1"}
            end;
        ["gemini" | _] ->
            ApiKey = os:getenv("GEMINI_API_KEY"),
            case ApiKey of
                false -> error({missing_api_key, "GEMINI_API_KEY not set"});
                _ -> {ApiKey, "https://generativelanguage.googleapis.com/v1beta"}
            end;
        _ ->
            error({unsupported_model, Model})
    end.

%% Get model name from model string
get_model_name(Model) ->
    case string:split(Model, "/") of
        [_, Name] -> Name;
        _ -> Model
    end.

%% Parse LLM response
parse_llm_response(Response) ->
    %% Check for final answer
    case re:run(Response, "Final Answer:\\s*(.+)", [{capture, all_but_first, list}, dotall]) of
        {match, [Answer]} ->
            {final_answer, string:trim(Answer)};
        nomatch ->
            %% Check for action
            case re:run(Response, "Action:\\s*(\\w+)\\s*Action Input:\\s*(.+?)(?=Observation:|Thought:|$)", 
                       [{capture, all_but_first, list}, dotall]) of
                {match, [Action, Input]} ->
                    {action, string:trim(Action), string:trim(Input)};
                nomatch ->
                    error
            end
    end.

%% Extract thought from response
extract_thought(Response) ->
    case re:run(Response, "Thought:\\s*(.+?)(?=Action:|Final Answer:|$)", 
               [{capture, all_but_first, list}, dotall]) of
        {match, [Thought]} -> string:trim(Thought);
        nomatch -> ""
    end.

%% Execute action
execute_action("find_all_matching_files", Input, RepoPath, LogFile) ->
    %% Parse JSON input
    try
        Decoded = jsx:decode(list_to_binary(Input), [return_maps]),
        Directory = maps:get(<<"directory">>, Decoded, RepoPath),
        Pattern = maps:get(<<"pattern">>, Decoded, <<"*">>),
        
        log_info(io_lib:format("Tool invoked: find_all_matching_files(directory='~s', pattern='~s')", 
                               [Directory, Pattern]), LogFile),
        
        %% Find files
        Files = find_files(binary_to_list(Directory), binary_to_list(Pattern)),
        FileCount = length(Files),
        log_info(io_lib:format("Found ~p matching files", [FileCount]), LogFile),
        string:join(Files, "\n")
    catch
        _:_ ->
            "Error: Invalid action input"
    end;

execute_action("read_file", Input, _RepoPath, _LogFile) ->
    %% Parse JSON input
    try
        Decoded = jsx:decode(list_to_binary(Input), [return_maps]),
        FilePath = binary_to_list(maps:get(<<"file_path">>, Decoded)),
        
        %% Read file
        case file:read_file(FilePath) of
            {ok, Content} ->
                %% Limit size
                ContentStr = binary_to_list(Content),
                case length(ContentStr) > 10000 of
                    true -> string:sub_string(ContentStr, 1, 10000) ++ "\n[truncated]";
                    false -> ContentStr
                end;
            {error, Reason} ->
                io_lib:format("Error reading file: ~p", [Reason])
        end
    catch
        _:_ ->
            "Error: Invalid action input"
    end;

execute_action(Action, _Input, _RepoPath, _LogFile) ->
    io_lib:format("Error: Unknown action '~s'", [Action]).

%% Find files matching pattern
find_files(Directory, Pattern) ->
    case file:list_dir(Directory) of
        {ok, Files} ->
            find_files_recursive(Directory, Pattern, Files, []);
        {error, _} ->
            []
    end.

find_files_recursive(_Dir, _Pattern, [], Acc) ->
    lists:reverse(Acc);
find_files_recursive(Dir, Pattern, [File | Rest], Acc) ->
    FullPath = filename:join(Dir, File),
    case filelib:is_dir(FullPath) of
        true ->
            %% Skip .git and other hidden directories
            case hd(File) of
                $. -> find_files_recursive(Dir, Pattern, Rest, Acc);
                _ ->
                    case file:list_dir(FullPath) of
                        {ok, SubFiles} ->
                            SubResults = find_files_recursive(FullPath, Pattern, SubFiles, []),
                            find_files_recursive(Dir, Pattern, Rest, SubResults ++ Acc);
                        {error, _} ->
                            find_files_recursive(Dir, Pattern, Rest, Acc)
                    end
            end;
        false ->
            %% Check if file matches pattern
            case filelib:is_file(FullPath) andalso match_pattern(File, Pattern) of
                true -> find_files_recursive(Dir, Pattern, Rest, [FullPath | Acc]);
                false -> find_files_recursive(Dir, Pattern, Rest, Acc)
            end
    end.

%% Simple pattern matching
match_pattern(_File, "*") -> true;
match_pattern(File, Pattern) ->
    filelib:is_file(File) andalso 
    re:run(File, wildcard_to_regex(Pattern), [{capture, none}]) =/= nomatch.

%% Convert wildcard pattern to regex
wildcard_to_regex(Pattern) ->
    Escaped = re:replace(Pattern, "[.^$+?{}\\[\\]\\\\|()`]", "\\\\&", [global, {return, list}]),
    WithStar = re:replace(Escaped, "\\*", ".*", [global, {return, list}]),
    WithQuestion = re:replace(WithStar, "\\?", ".", [global, {return, list}]),
    "^" ++ WithQuestion ++ "$".

%% Extract final answer from memory
extract_final_answer([]) -> "No analysis generated";
extract_final_answer(Memory) ->
    extract_final_answer(lists:reverse(Memory), none).

extract_final_answer([], none) -> "No analysis generated";
extract_final_answer([], Answer) -> Answer;
extract_final_answer([{observation, Obs} | Rest], _) ->
    extract_final_answer(Rest, Obs);
extract_final_answer([_ | Rest], Answer) ->
    extract_final_answer(Rest, Answer).

%% Create metadata
create_metadata(Repo, PromptFile, Model, Result) ->
    {Date, Time} = calendar:local_time(),
    Timestamp = io_lib:format("~4..0B-~2..0B-~2..0BT~2..0B:~2..0B:~2..0B",
                             [element(1, Date), element(2, Date), element(3, Date),
                              element(1, Time), element(2, Time), element(3, Time)]),
    
    Metadata = #{
        repository => list_to_binary(Repo),
        prompt_file => list_to_binary(PromptFile),
        model => list_to_binary(Model),
        timestamp => list_to_binary(Timestamp),
        word_count => length(string:tokens(Result, " \n\t")),
        char_count => length(Result)
    },
    
    jsx:encode(Metadata, [{indent, 2}]).

%% Logging functions
log_info(Msg, LogFile) ->
    log("INFO", Msg, LogFile).

log_debug(Msg, LogFile) ->
    log("DEBUG", Msg, LogFile).

log(Level, Msg, LogFile) ->
    {Date, Time} = calendar:local_time(),
    Timestamp = io_lib:format("~4..0B-~2..0B-~2..0B ~2..0B:~2..0B:~2..0B",
                             [element(1, Date), element(2, Date), element(3, Date),
                              element(1, Time), element(2, Time), element(3, Time)]),
    LogMsg = io_lib:format("~s - ~s - ~s~n", [Timestamp, Level, Msg]),
    io:format("~s", [LogMsg]),
    file:write_file(LogFile, LogMsg, [append]).