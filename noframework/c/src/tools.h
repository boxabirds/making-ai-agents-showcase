#ifndef TOOLS_H
#define TOOLS_H

#include "platform.h"
#include "cJSON.h"

// File information structure
typedef struct {
    char** files;
    size_t count;
    size_t capacity;
} FileList;

// Tool functions matching the agent's requirements
char* find_all_matching_files(const char* directory, const char* pattern);
char* read_file(const char* file_path);

// File list management
FileList* file_list_create(void);
void file_list_destroy(FileList* list);
void file_list_add(FileList* list, const char* file);

// Pattern matching
bool match_pattern(const char* filename, const char* pattern);

// Gitignore handling
typedef struct {
    char** patterns;
    size_t count;
    size_t capacity;
} GitIgnore;

GitIgnore* gitignore_load(const char* directory);
void gitignore_destroy(GitIgnore* ignore);
bool gitignore_should_ignore(GitIgnore* ignore, const char* path);

// Directory traversal
void traverse_directory(const char* directory, const char* pattern, FileList* results, GitIgnore* gitignore, const char* base_dir);

#endif // TOOLS_H