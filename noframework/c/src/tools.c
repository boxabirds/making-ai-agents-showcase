#include "tools.h"
#include <string.h>
#include <ctype.h>

#ifdef PLATFORM_WINDOWS
#include <windows.h>
#else
#include <dirent.h>
#include <fnmatch.h>
#endif

// File list management
FileList* file_list_create(void) {
    FileList* list = safe_calloc(1, sizeof(FileList));
    list->capacity = 16;
    list->files = safe_calloc(list->capacity, sizeof(char*));
    return list;
}

void file_list_destroy(FileList* list) {
    if (!list) return;
    for (size_t i = 0; i < list->count; i++) {
        free(list->files[i]);
    }
    free(list->files);
    free(list);
}

void file_list_add(FileList* list, const char* file) {
    if (list->count >= list->capacity) {
        list->capacity *= 2;
        list->files = safe_realloc(list->files, list->capacity * sizeof(char*));
    }
    list->files[list->count++] = safe_strdup(file);
}

// Pattern matching
bool match_pattern(const char* filename, const char* pattern) {
    if (strcmp(pattern, "*") == 0 || strcmp(pattern, "*.*") == 0) {
        return true;
    }
    
    if (string_starts_with(pattern, "*.")) {
        const char* ext = pattern + 1;
        return string_ends_with(filename, ext);
    }
    
#ifdef PLATFORM_WINDOWS
    // Simple pattern matching for Windows
    return strcmp(filename, pattern) == 0;
#else
    // Use fnmatch on POSIX systems
    return fnmatch(pattern, filename, 0) == 0;
#endif
}

// Gitignore handling
GitIgnore* gitignore_load(const char* directory) {
    char gitignore_path[1024];
    snprintf(gitignore_path, sizeof(gitignore_path), "%s/.gitignore", directory);
    
    if (!platform_file_exists(gitignore_path)) {
        return NULL;
    }
    
    FILE* file = fopen(gitignore_path, "r");
    if (!file) return NULL;
    
    GitIgnore* ignore = safe_calloc(1, sizeof(GitIgnore));
    ignore->capacity = 16;
    ignore->patterns = safe_calloc(ignore->capacity, sizeof(char*));
    
    char line[256];
    while (fgets(line, sizeof(line), file)) {
        char* trimmed = string_trim(line);
        if (strlen(trimmed) > 0 && trimmed[0] != '#') {
            if (ignore->count >= ignore->capacity) {
                ignore->capacity *= 2;
                ignore->patterns = safe_realloc(ignore->patterns, ignore->capacity * sizeof(char*));
            }
            ignore->patterns[ignore->count++] = safe_strdup(trimmed);
        }
    }
    
    fclose(file);
    return ignore;
}

void gitignore_destroy(GitIgnore* ignore) {
    if (!ignore) return;
    for (size_t i = 0; i < ignore->count; i++) {
        free(ignore->patterns[i]);
    }
    free(ignore->patterns);
    free(ignore);
}

bool gitignore_should_ignore(GitIgnore* ignore, const char* path) {
    if (!ignore) return false;
    
    for (size_t i = 0; i < ignore->count; i++) {
        const char* pattern = ignore->patterns[i];
        
        // Simple pattern matching
        if (strstr(path, pattern) != NULL) {
            return true;
        }
        
        // Check if path ends with pattern
        if (string_ends_with(path, pattern)) {
            return true;
        }
        
        // Check if any component matches
        char* path_copy = safe_strdup(path);
        char* token = strtok(path_copy, "/\\");
        while (token) {
            if (strcmp(token, pattern) == 0) {
                free(path_copy);
                return true;
            }
            token = strtok(NULL, "/\\");
        }
        free(path_copy);
    }
    
    return false;
}

// Directory traversal
void traverse_directory(const char* directory, const char* pattern, FileList* results, GitIgnore* gitignore, const char* base_dir) {
#ifdef PLATFORM_WINDOWS
    WIN32_FIND_DATAA find_data;
    char search_path[MAX_PATH];
    snprintf(search_path, sizeof(search_path), "%s\\*", directory);
    
    HANDLE handle = FindFirstFileA(search_path, &find_data);
    if (handle == INVALID_HANDLE_VALUE) return;
    
    do {
        if (strcmp(find_data.cFileName, ".") == 0 || strcmp(find_data.cFileName, "..") == 0) {
            continue;
        }
        
        char full_path[MAX_PATH];
        snprintf(full_path, sizeof(full_path), "%s\\%s", directory, find_data.cFileName);
        
        // Calculate relative path from base directory
        const char* rel_path = full_path;
        if (base_dir && string_starts_with(full_path, base_dir)) {
            rel_path = full_path + strlen(base_dir);
            while (*rel_path == '\\' || *rel_path == '/') rel_path++;
        }
        
        if (gitignore && gitignore_should_ignore(gitignore, rel_path)) {
            continue;
        }
        
        if (find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
            traverse_directory(full_path, pattern, results, gitignore, base_dir);
        } else {
            if (match_pattern(find_data.cFileName, pattern)) {
                file_list_add(results, full_path);
            }
        }
    } while (FindNextFileA(handle, &find_data));
    
    FindClose(handle);
#else
    DIR* dir = opendir(directory);
    if (!dir) return;
    
    struct dirent* entry;
    while ((entry = readdir(dir)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }
        
        char full_path[1024];
        snprintf(full_path, sizeof(full_path), "%s/%s", directory, entry->d_name);
        
        // Calculate relative path from base directory
        const char* rel_path = full_path;
        if (base_dir && string_starts_with(full_path, base_dir)) {
            rel_path = full_path + strlen(base_dir);
            while (*rel_path == '/' || *rel_path == '\\') rel_path++;
        }
        
        if (gitignore && gitignore_should_ignore(gitignore, rel_path)) {
            continue;
        }
        
        struct stat st;
        if (stat(full_path, &st) == 0) {
            if (S_ISDIR(st.st_mode)) {
                traverse_directory(full_path, pattern, results, gitignore, base_dir);
            } else if (S_ISREG(st.st_mode)) {
                if (match_pattern(entry->d_name, pattern)) {
                    file_list_add(results, full_path);
                }
            }
        }
    }
    
    closedir(dir);
#endif
}

// Tool functions
char* find_all_matching_files(const char* directory, const char* pattern) {
    log_message(LOG_INFO, "Tool invoked: find_all_matching_files(directory='%s', pattern='%s')", directory, pattern);
    
    if (!platform_is_directory(directory)) {
        log_message(LOG_ERROR, "Directory not found: %s", directory);
        return safe_strdup("[]");
    }
    
    FileList* results = file_list_create();
    GitIgnore* gitignore = gitignore_load(directory);
    
    traverse_directory(directory, pattern, results, gitignore, directory);
    
    // Convert to JSON array
    cJSON* json_array = cJSON_CreateArray();
    for (size_t i = 0; i < results->count; i++) {
        cJSON_AddItemToArray(json_array, cJSON_CreateString(results->files[i]));
    }
    
    char* json_string = cJSON_PrintUnformatted(json_array);
    cJSON_Delete(json_array);
    
    log_message(LOG_INFO, "Found %zu matching files", results->count);
    
    file_list_destroy(results);
    gitignore_destroy(gitignore);
    
    return json_string;
}

char* read_file(const char* file_path) {
    log_message(LOG_INFO, "Tool invoked: read_file(file_path='%s')", file_path);
    
    FILE* file = fopen(file_path, "rb");
    if (!file) {
        cJSON* error = cJSON_CreateObject();
        cJSON_AddStringToObject(error, "error", "File not found");
        char* result = cJSON_PrintUnformatted(error);
        cJSON_Delete(error);
        return result;
    }
    
    // Get file size
    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    fseek(file, 0, SEEK_SET);
    
    // Check if file is too large
    if (file_size > 10 * 1024 * 1024) {
        fclose(file);
        cJSON* error = cJSON_CreateObject();
        cJSON_AddStringToObject(error, "error", "File too large");
        char* result = cJSON_PrintUnformatted(error);
        cJSON_Delete(error);
        return result;
    }
    
    // Read file content
    char* content = safe_malloc(file_size + 1);
    size_t read_size = fread(content, 1, file_size, file);
    content[read_size] = '\0';
    fclose(file);
    
    // Check if binary (contains null bytes)
    for (size_t i = 0; i < read_size; i++) {
        if (content[i] == '\0') {
            free(content);
            log_message(LOG_DEBUG, "File detected as binary: %s", file_path);
            cJSON* error = cJSON_CreateObject();
            cJSON_AddStringToObject(error, "error", "Cannot read binary file");
            char* result = cJSON_PrintUnformatted(error);
            cJSON_Delete(error);
            return result;
        }
    }
    
    log_message(LOG_INFO, "Successfully read file: %s (%ld chars)", file_path, file_size);
    
    // Create JSON response
    cJSON* response = cJSON_CreateObject();
    cJSON_AddStringToObject(response, "file", file_path);
    cJSON_AddStringToObject(response, "content", content);
    
    char* json_string = cJSON_PrintUnformatted(response);
    cJSON_Delete(response);
    free(content);
    
    return json_string;
}