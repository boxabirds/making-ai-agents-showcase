-module(json_simple).
-export([encode/1, decode/1]).

%% Simple JSON encoder
encode(Term) when is_map(Term) ->
    Items = maps:fold(fun(K, V, Acc) ->
        [io_lib:format("~p:~s", [encode_key(K), encode(V)]) | Acc]
    end, [], Term),
    ["{", string:join(lists:reverse(Items), ","), "}"];

encode(Term) when is_list(Term) ->
    case io_lib:printable_list(Term) of
        true -> io_lib:format("~p", [Term]); % String
        false -> % Array
            Items = [encode(Item) || Item <- Term],
            ["[", string:join(Items, ","), "]"]
    end;

encode(Term) when is_binary(Term) ->
    io_lib:format("~p", [binary_to_list(Term)]);

encode(Term) when is_atom(Term) ->
    io_lib:format("~p", [atom_to_list(Term)]);

encode(Term) when is_integer(Term) ->
    integer_to_list(Term);

encode(Term) when is_float(Term) ->
    float_to_list(Term).

encode_key(K) when is_binary(K) -> io_lib:format("~p", [binary_to_list(K)]);
encode_key(K) when is_atom(K) -> io_lib:format("~p", [atom_to_list(K)]);
encode_key(K) -> io_lib:format("~p", [K]).

%% Simple JSON decoder - just parse the OpenAI response structure we need
decode(JsonString) when is_list(JsonString) ->
    decode(list_to_binary(JsonString));

decode(JsonBinary) when is_binary(JsonBinary) ->
    %% Very simple decoder for OpenAI responses
    try
        %% Extract choices array
        case re:run(JsonBinary, <<"\"choices\":\\s*\\[([^\\]]+)\\]">>, [{capture, [1], binary}]) of
            {match, [ChoicesJson]} ->
                %% Extract content from first choice
                case re:run(ChoicesJson, <<"\"content\":\\s*\"([^\"]+)\"">>, [{capture, [1], binary}, ungreedy]) of
                    {match, [Content]} ->
                        #{<<"choices">> => [#{<<"message">> => #{<<"content">> => Content}}]};
                    nomatch ->
                        %% Try to handle escaped quotes in content
                        case re:run(ChoicesJson, <<"\"content\":\\s*\"((?:[^\"\\\\]|\\\\.)*)\"">>, [{capture, [1], binary}]) of
                            {match, [Content]} ->
                                %% Unescape the content
                                UnescapedContent = unescape_json_string(Content),
                                #{<<"choices">> => [#{<<"message">> => #{<<"content">> => UnescapedContent}}]};
                            nomatch ->
                                #{<<"choices">> => []}
                        end
                end;
            nomatch ->
                #{<<"choices">> => []}
        end
    catch
        _:_ -> #{<<"choices">> => []}
    end.

%% Helper to unescape JSON strings
unescape_json_string(Bin) ->
    binary:replace(binary:replace(Bin, <<"\\n">>, <<"\n">>, [global]), 
                   <<"\\\"">>, <<"\"">>, [global]).