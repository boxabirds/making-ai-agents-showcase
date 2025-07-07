#include "agent.h"
#include "tools.h"
#include <time.h>
#include <ctype.h>

const char* REACT_SYSTEM_PROMPT = 
"You are a technical documentation assistant that analyses codebases and generates comprehensive documentation.\n"
"\n"
"When given a directory path and a specific analysis request, you will:\n"
"1. Explore the codebase structure to understand its organization\n"
"2. Read relevant files to comprehend the implementation details\n"
"3. Generate detailed technical documentation based on your analysis\n"
"\n"
"You have access to tools that help you explore and understand codebases:\n"
"- find_all_matching_files: Find files matching patterns in directories\n"
"- read_file: Read the contents of specific files\n"
"\n"
"Important guidelines:\n"
"- Always start by exploring the directory structure to understand the codebase layout\n"
"- Read files strategically based on the documentation needs\n"
"- Pay attention to configuration files, main entry points, and key modules\n"
"- Generate clear, well-structured documentation that would help developers understand the codebase\n"
"\n"
"Use the following format:\n"
"\n"
"Thought: I need to [describe what you need to do next]\n"
"Action: [tool_name]\n"
"Action Input: {\"param1\": \"value1\", \"param2\": \"value2\"}\n"
"Observation: [tool output will be provided here]\n"
"... (repeat Thought/Action/Action Input/Observation as needed)\n"
"Thought: I now have enough information to generate the documentation\n"
"Final Answer: [Your complete technical documentation]\n"
"\n"
"Begin your analysis now.";

TechWriterAgent* agent_create(const char* model_name, const char* base_url) {
    // Parse model name (vendor/model)
    char* slash = strchr(model_name, '/');
    if (!slash) {
        log_message(LOG_ERROR, "Invalid model name format: %s", model_name);
        return NULL;
    }
    
    char vendor[64];
    size_t vendor_len = slash - model_name;
    if (vendor_len >= sizeof(vendor)) {
        log_message(LOG_ERROR, "Vendor name too long");
        return NULL;
    }
    strncpy(vendor, model_name, vendor_len);
    vendor[vendor_len] = '\0';
    
    const char* model_id = slash + 1;
    
    // Set up API configuration
    char* api_key = NULL;
    const char* api_base_url = base_url;
    
    if (strcmp(vendor, "google") == 0) {
        api_key = getenv("GEMINI_API_KEY");
        if (!api_key) {
            log_message(LOG_ERROR, "GEMINI_API_KEY environment variable not set");
            return NULL;
        }
        if (!api_base_url) {
            api_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/";
        }
    } else if (strcmp(vendor, "openai") == 0) {
        api_key = getenv("OPENAI_API_KEY");
        if (!api_key) {
            log_message(LOG_ERROR, "OPENAI_API_KEY environment variable not set");
            return NULL;
        }
        if (!api_base_url) {
            api_base_url = "https://api.openai.com/v1/";
        }
    } else {
        log_message(LOG_ERROR, "Unknown model vendor: %s", vendor);
        return NULL;
    }
    
    // Create agent
    TechWriterAgent* agent = safe_calloc(1, sizeof(TechWriterAgent));
    agent->model_id = safe_strdup(model_id);
    agent->client = http_client_create(api_base_url, api_key);
    if (!agent->client) {
        free(agent->model_id);
        free(agent);
        return NULL;
    }
    
    // Initialize memory
    agent->memory_capacity = 10;
    agent->memory = safe_calloc(agent->memory_capacity, sizeof(Message));
    
    // Create log directory and file
    platform_make_directory("logs");
    char log_filename[256];
    time_t now = time(NULL);
    snprintf(log_filename, sizeof(log_filename), "logs/tech-writer-%ld.log", (long)now);
    agent->log_file = fopen(log_filename, "w");
    
    log_message(LOG_INFO, "Starting ReAct agent with model: %s", model_id);
    
    return agent;
}

void agent_destroy(TechWriterAgent* agent) {
    if (!agent) return;
    
    http_client_destroy(agent->client);
    free(agent->model_id);
    
    for (size_t i = 0; i < agent->memory_count; i++) {
        free(agent->memory[i].role);
        free(agent->memory[i].content);
    }
    free(agent->memory);
    
    if (agent->log_file) {
        fclose(agent->log_file);
    }
    
    free(agent);
}

void agent_add_message(TechWriterAgent* agent, const char* role, const char* content) {
    if (agent->memory_count >= agent->memory_capacity) {
        agent->memory_capacity *= 2;
        agent->memory = safe_realloc(agent->memory, agent->memory_capacity * sizeof(Message));
    }
    
    agent->memory[agent->memory_count].role = safe_strdup(role);
    agent->memory[agent->memory_count].content = safe_strdup(content);
    agent->memory_count++;
}

char* agent_call_llm(TechWriterAgent* agent) {
    // Build request JSON
    cJSON* request = cJSON_CreateObject();
    cJSON_AddStringToObject(request, "model", agent->model_id);
    
    cJSON* messages = cJSON_CreateArray();
    for (size_t i = 0; i < agent->memory_count; i++) {
        cJSON* msg = cJSON_CreateObject();
        cJSON_AddStringToObject(msg, "role", agent->memory[i].role);
        cJSON_AddStringToObject(msg, "content", agent->memory[i].content);
        cJSON_AddItemToArray(messages, msg);
    }
    cJSON_AddItemToObject(request, "messages", messages);
    cJSON_AddNumberToObject(request, "temperature", 0);
    
    char* request_str = cJSON_PrintUnformatted(request);
    cJSON_Delete(request);
    
    // Make HTTP request
    HttpResponse* response = http_post_json(agent->client, "chat/completions", request_str);
    free(request_str);
    
    if (!response) {
        return NULL;
    }
    
    // Parse response
    cJSON* json = cJSON_Parse(response->data);
    if (!json) {
        log_message(LOG_ERROR, "Failed to parse LLM response");
        http_response_destroy(response);
        return NULL;
    }
    
    cJSON* choices = cJSON_GetObjectItem(json, "choices");
    if (!choices || !cJSON_IsArray(choices) || cJSON_GetArraySize(choices) == 0) {
        log_message(LOG_ERROR, "No choices in LLM response");
        cJSON_Delete(json);
        http_response_destroy(response);
        return NULL;
    }
    
    cJSON* choice = cJSON_GetArrayItem(choices, 0);
    cJSON* message = cJSON_GetObjectItem(choice, "message");
    cJSON* content = cJSON_GetObjectItem(message, "content");
    
    char* result = NULL;
    if (content && cJSON_IsString(content)) {
        result = safe_strdup(content->valuestring);
    }
    
    cJSON_Delete(json);
    http_response_destroy(response);
    
    return result;
}

ParsedResponse* agent_parse_response(const char* response) {
    ParsedResponse* parsed = safe_calloc(1, sizeof(ParsedResponse));
    
    // Check for Final Answer
    const char* final_answer_marker = "Final Answer:";
    char* final_pos = strstr(response, final_answer_marker);
    if (final_pos) {
        parsed->type = RESPONSE_FINAL;
        final_pos += strlen(final_answer_marker);
        while (*final_pos && isspace(*final_pos)) final_pos++;
        parsed->final_answer = safe_strdup(final_pos);
        return parsed;
    }
    
    // Look for Action and Action Input
    const char* action_marker = "Action:";
    const char* input_marker = "Action Input:";
    
    char* action_pos = strstr(response, action_marker);
    char* input_pos = strstr(response, input_marker);
    
    if (action_pos && input_pos && input_pos > action_pos) {
        parsed->type = RESPONSE_ACTION;
        
        // Extract action
        action_pos += strlen(action_marker);
        while (*action_pos && isspace(*action_pos)) action_pos++;
        
        char* action_end = strstr(action_pos, "\n");
        if (action_end) {
            size_t action_len = action_end - action_pos;
            parsed->action = safe_malloc(action_len + 1);
            strncpy(parsed->action, action_pos, action_len);
            parsed->action[action_len] = '\0';
            parsed->action = string_trim(parsed->action);
        }
        
        // Extract action input
        input_pos += strlen(input_marker);
        while (*input_pos && isspace(*input_pos)) input_pos++;
        
        // Find the end of the JSON input (look for next section or end)
        char* input_end = strstr(input_pos, "\nThought:");
        if (!input_end) input_end = strstr(input_pos, "\nAction:");
        if (!input_end) input_end = strstr(input_pos, "\nObservation:");
        if (!input_end) input_end = strstr(input_pos, "\nFinal Answer:");
        if (!input_end) input_end = (char*)response + strlen(response);
        
        size_t input_len = input_end - input_pos;
        parsed->action_input = safe_malloc(input_len + 1);
        strncpy(parsed->action_input, input_pos, input_len);
        parsed->action_input[input_len] = '\0';
        parsed->action_input = string_trim(parsed->action_input);
    } else {
        parsed->type = RESPONSE_UNKNOWN;
    }
    
    return parsed;
}

void parsed_response_destroy(ParsedResponse* parsed) {
    if (!parsed) return;
    free(parsed->action);
    free(parsed->action_input);
    free(parsed->final_answer);
    free(parsed);
}

char* agent_execute_tool(TechWriterAgent* agent, const char* tool_name, const char* action_input) {
    log_message(LOG_DEBUG, "Executing tool: %s with input: %s", tool_name, action_input);
    
    // Parse JSON input
    cJSON* input = cJSON_Parse(action_input);
    if (!input) {
        return safe_strdup("{\"error\": \"Failed to parse input JSON\"}");
    }
    
    char* result = NULL;
    
    if (strcmp(tool_name, "find_all_matching_files") == 0) {
        cJSON* directory = cJSON_GetObjectItem(input, "directory");
        cJSON* pattern = cJSON_GetObjectItem(input, "pattern");
        
        const char* dir_str = (directory && cJSON_IsString(directory)) ? directory->valuestring : "";
        const char* pat_str = (pattern && cJSON_IsString(pattern)) ? pattern->valuestring : "*";
        
        result = find_all_matching_files(dir_str, pat_str);
    } else if (strcmp(tool_name, "read_file") == 0) {
        cJSON* file_path = cJSON_GetObjectItem(input, "file_path");
        
        if (file_path && cJSON_IsString(file_path)) {
            result = read_file_content(file_path->valuestring);
        } else {
            result = safe_strdup("{\"error\": \"file_path parameter required\"}");
        }
    } else {
        char error[256];
        snprintf(error, sizeof(error), "{\"error\": \"Unknown tool: %s\"}", tool_name);
        result = safe_strdup(error);
    }
    
    cJSON_Delete(input);
    
    if (agent->log_file) {
        fprintf(agent->log_file, "Tool result: %zu chars\n", strlen(result));
    }
    
    return result;
}

char* agent_run(TechWriterAgent* agent, const char* prompt, const char* directory) {
    log_message(LOG_INFO, "Starting ReAct agent with model: %s", agent->model_id);
    
    // Initialize conversation
    agent_add_message(agent, "system", REACT_SYSTEM_PROMPT);
    
    char user_prompt[2048];
    snprintf(user_prompt, sizeof(user_prompt), 
             "Base directory for analysis: %s\n\n%s", directory, prompt);
    agent_add_message(agent, "user", user_prompt);
    
    char* final_answer = NULL;
    
    // ReAct loop
    for (int step = 0; step < MAX_STEPS; step++) {
        log_message(LOG_INFO, "Step %d/%d", step + 1, MAX_STEPS);
        
        // Get LLM response
        char* response = agent_call_llm(agent);
        if (!response) {
            log_message(LOG_ERROR, "Failed to get LLM response");
            break;
        }
        
        log_message(LOG_DEBUG, "LLM Response: %s", response);
        
        // Add assistant response to memory
        agent_add_message(agent, "assistant", response);
        
        // Parse response
        ParsedResponse* parsed = agent_parse_response(response);
        
        if (parsed->type == RESPONSE_FINAL) {
            final_answer = safe_strdup(parsed->final_answer);
            log_message(LOG_INFO, "Final answer received");
            parsed_response_destroy(parsed);
            free(response);
            break;
        } else if (parsed->type == RESPONSE_ACTION) {
            // Execute tool
            char* observation = agent_execute_tool(agent, parsed->action, parsed->action_input);
            
            // Add observation to memory
            char obs_message[strlen(observation) + 20];
            snprintf(obs_message, sizeof(obs_message), "Observation: %s", observation);
            agent_add_message(agent, "user", obs_message);
            
            free(observation);
        }
        
        parsed_response_destroy(parsed);
        free(response);
    }
    
    if (!final_answer) {
        log_message(LOG_ERROR, "Failed to complete analysis within %d steps", MAX_STEPS);
        final_answer = safe_strdup("Failed to complete analysis");
    }
    
    return final_answer;
}

// Utility functions
char* extract_repo_info(const char* repo_url, char** owner, char** repo_name) {
    // Extract repo name from URL (e.g., https://github.com/owner/repo.git)
    char* url_copy = safe_strdup(repo_url);
    
    // Remove .git suffix if present
    char* git_suffix = strstr(url_copy, ".git");
    if (git_suffix) *git_suffix = '\0';
    
    // Find the last two path components
    char* last_slash = strrchr(url_copy, '/');
    if (!last_slash) {
        free(url_copy);
        return NULL;
    }
    
    *repo_name = safe_strdup(last_slash + 1);
    *last_slash = '\0';
    
    char* second_last_slash = strrchr(url_copy, '/');
    if (second_last_slash) {
        *owner = safe_strdup(second_last_slash + 1);
    }
    
    free(url_copy);
    return *repo_name;
}

char* clone_or_update_repo(const char* repo_url, const char* cache_dir) {
    char* owner = NULL;
    char* repo_name = NULL;
    
    if (!extract_repo_info(repo_url, &owner, &repo_name)) {
        return NULL;
    }
    
    // Expand cache directory
    char* expanded_cache = platform_normalize_path(cache_dir);
    
    // Create cache path
    char cache_path[1024];
    snprintf(cache_path, sizeof(cache_path), "%s%c%s%c%s", 
             expanded_cache, PATH_SEPARATOR_CHAR, owner, PATH_SEPARATOR_CHAR, repo_name);
    
    // Create directories
    char owner_path[1024];
    snprintf(owner_path, sizeof(owner_path), "%s%c%s", expanded_cache, PATH_SEPARATOR_CHAR, owner);
    platform_make_directory(expanded_cache);
    platform_make_directory(owner_path);
    
    // Check if already cloned
    char git_path[1024];
    snprintf(git_path, sizeof(git_path), "%s%c.git", cache_path, PATH_SEPARATOR_CHAR);
    
    char command[2048];
    if (platform_is_directory(git_path)) {
        log_message(LOG_INFO, "Updating existing repository: %s", cache_path);
        snprintf(command, sizeof(command), "cd \"%s\" && git pull --quiet", cache_path);
    } else {
        log_message(LOG_INFO, "Cloning repository: %s", repo_url);
        snprintf(command, sizeof(command), "git clone --quiet \"%s\" \"%s\"", repo_url, cache_path);
    }
    
    int result = platform_execute_command(command, NULL, 0);
    
    free(owner);
    free(repo_name);
    free(expanded_cache);
    
    if (result != 0) {
        log_message(LOG_ERROR, "Git command failed with exit code: %d", result);
        return NULL;
    }
    
    return safe_strdup(cache_path);
}

void save_results(const char* content, const char* repo_name, const char* model, 
                  const char* output_dir, const char* extension, const char* file_name) {
    platform_make_directory(output_dir);
    
    char output_path[1024];
    if (file_name) {
        snprintf(output_path, sizeof(output_path), "%s%c%s", output_dir, PATH_SEPARATOR_CHAR, file_name);
    } else {
        // Parse model vendor/id
        char* model_copy = safe_strdup(model);
        char* slash = strchr(model_copy, '/');
        if (slash) {
            *slash = '\0';
            const char* vendor = model_copy;
            const char* model_id = slash + 1;
            
            // Sanitize model ID
            char sanitized_model[256];
            size_t j = 0;
            for (size_t i = 0; model_id[i] && j < sizeof(sanitized_model) - 1; i++) {
                if (isalnum(model_id[i]) || model_id[i] == '-' || model_id[i] == '_') {
                    sanitized_model[j++] = model_id[i];
                } else {
                    sanitized_model[j++] = '-';
                }
            }
            sanitized_model[j] = '\0';
            
            time_t now = time(NULL);
            snprintf(output_path, sizeof(output_path), "%s%c%ld-%s-%s-%s%s",
                     output_dir, PATH_SEPARATOR_CHAR, (long)now, repo_name, vendor, sanitized_model, extension);
        }
        free(model_copy);
    }
    
    FILE* file = fopen(output_path, "w");
    if (file) {
        fputs(content, file);
        fclose(file);
        log_message(LOG_INFO, "Results saved to: %s", output_path);
    }
}

void create_metadata(const char* output_file, const char* model, 
                     const char* repo_url, const char* repo_name) {
    // Replace extension with .metadata.json
    char metadata_path[1024];
    strcpy(metadata_path, output_file);
    
    char* last_dot = strrchr(metadata_path, '.');
    if (last_dot) {
        strcpy(last_dot, ".metadata.json");
    } else {
        strcat(metadata_path, ".metadata.json");
    }
    
    // Create metadata JSON
    cJSON* metadata = cJSON_CreateObject();
    cJSON_AddStringToObject(metadata, "model", model);
    cJSON_AddStringToObject(metadata, "github_url", repo_url);
    cJSON_AddStringToObject(metadata, "repo_name", repo_name);
    
    time_t now = time(NULL);
    char timestamp[64];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%dT%H:%M:%S", localtime(&now));
    cJSON_AddStringToObject(metadata, "timestamp", timestamp);
    
    char* json_str = cJSON_Print(metadata);
    
    FILE* file = fopen(metadata_path, "w");
    if (file) {
        fputs(json_str, file);
        fclose(file);
        log_message(LOG_INFO, "Metadata saved to: %s", metadata_path);
    }
    
    cJSON_free(json_str);
    cJSON_Delete(metadata);
}