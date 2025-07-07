#ifndef AGENT_H
#define AGENT_H

#include "platform.h"
#include "http.h"
#include "cJSON.h"

#define MAX_STEPS 50
#define MAX_MEMORY_SIZE 100

extern const char* REACT_SYSTEM_PROMPT;

// Message structure for conversation history
typedef struct {
    char* role;
    char* content;
} Message;

// Agent structure
typedef struct {
    HttpClient* client;
    char* model_id;
    Message* memory;
    size_t memory_count;
    size_t memory_capacity;
    FILE* log_file;
} TechWriterAgent;

// Response types
typedef enum {
    RESPONSE_ACTION,
    RESPONSE_FINAL,
    RESPONSE_UNKNOWN
} ResponseType;

typedef struct {
    ResponseType type;
    char* action;
    char* action_input;
    char* final_answer;
} ParsedResponse;

// Agent functions
TechWriterAgent* agent_create(const char* model_name, const char* base_url);
void agent_destroy(TechWriterAgent* agent);
char* agent_run(TechWriterAgent* agent, const char* prompt, const char* directory);

// Internal functions
void agent_add_message(TechWriterAgent* agent, const char* role, const char* content);
char* agent_call_llm(TechWriterAgent* agent);
ParsedResponse* agent_parse_response(const char* response);
void parsed_response_destroy(ParsedResponse* parsed);
char* agent_execute_tool(TechWriterAgent* agent, const char* tool_name, const char* action_input);

// Utility functions
char* extract_repo_info(const char* repo_url, char** owner, char** repo_name);
char* clone_or_update_repo(const char* repo_url, const char* cache_dir);
void save_results(const char* content, const char* repo_name, const char* model, 
                  const char* output_dir, const char* extension, const char* file_name);
void create_metadata(const char* output_file, const char* model, 
                     const char* repo_url, const char* repo_name);

#endif // AGENT_H