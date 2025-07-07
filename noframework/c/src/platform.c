#include "platform.h"
#include <stdarg.h>
#include <ctype.h>

char* platform_get_home_dir(void) {
#ifdef PLATFORM_WINDOWS
    char* home = getenv("USERPROFILE");
    if (!home) {
        home = getenv("HOMEDRIVE");
        if (home) {
            char* path = getenv("HOMEPATH");
            if (path) {
                static char full_path[MAX_PATH];
                snprintf(full_path, sizeof(full_path), "%s%s", home, path);
                return full_path;
            }
        }
    }
    return home;
#else
    return getenv("HOME");
#endif
}

int platform_make_directory(const char* path) {
#ifdef PLATFORM_WINDOWS
    return mkdir(path) == 0 ? 0 : -1;
#else
    return mkdir(path, 0755) == 0 ? 0 : -1;
#endif
}

int platform_file_exists(const char* path) {
    return access(path, F_OK) == 0;
}

int platform_is_directory(const char* path) {
#ifdef PLATFORM_WINDOWS
    DWORD attrs = GetFileAttributesA(path);
    return (attrs != INVALID_FILE_ATTRIBUTES && (attrs & FILE_ATTRIBUTE_DIRECTORY));
#else
    struct stat st;
    return (stat(path, &st) == 0 && S_ISDIR(st.st_mode));
#endif
}

char* platform_normalize_path(const char* path) {
    if (!path) return NULL;
    
    char* normalized = safe_strdup(path);
    
    // Expand home directory
    if (path[0] == '~' && (path[1] == '/' || path[1] == '\\' || path[1] == '\0')) {
        char* home = platform_get_home_dir();
        if (home) {
            size_t home_len = strlen(home);
            size_t path_len = strlen(path + 1);
            char* new_path = safe_malloc(home_len + path_len + 1);
            strcpy(new_path, home);
            strcat(new_path, path + 1);
            free(normalized);
            normalized = new_path;
        }
    }
    
    // Convert path separators
#ifdef PLATFORM_WINDOWS
    string_replace_char(normalized, '/', '\\');
#else
    string_replace_char(normalized, '\\', '/');
#endif
    
    return normalized;
}

int platform_execute_command(const char* command, char* output, size_t output_size) {
    FILE* pipe = popen(command, "r");
    if (!pipe) return -1;
    
    size_t total_read = 0;
    if (output && output_size > 0) {
        char buffer[256];
        while (fgets(buffer, sizeof(buffer), pipe) != NULL) {
            size_t len = strlen(buffer);
            if (total_read + len < output_size - 1) {
                strcpy(output + total_read, buffer);
                total_read += len;
            }
        }
        output[total_read] = '\0';
    }
    
    int status = pclose(pipe);
#ifdef PLATFORM_WINDOWS
    return status;
#else
    return WEXITSTATUS(status);
#endif
}

// String utilities
char* string_duplicate(const char* str) {
    if (!str) return NULL;
    return safe_strdup(str);
}

char* string_trim(char* str) {
    if (!str) return NULL;
    
    // Trim leading whitespace
    while (isspace((unsigned char)*str)) str++;
    
    if (*str == 0) return str;
    
    // Trim trailing whitespace
    char* end = str + strlen(str) - 1;
    while (end > str && isspace((unsigned char)*end)) end--;
    
    end[1] = '\0';
    return str;
}

int string_starts_with(const char* str, const char* prefix) {
    if (!str || !prefix) return 0;
    return strncmp(str, prefix, strlen(prefix)) == 0;
}

int string_ends_with(const char* str, const char* suffix) {
    if (!str || !suffix) return 0;
    size_t str_len = strlen(str);
    size_t suffix_len = strlen(suffix);
    if (suffix_len > str_len) return 0;
    return strcmp(str + str_len - suffix_len, suffix) == 0;
}

char* string_replace_char(char* str, char old_char, char new_char) {
    if (!str) return NULL;
    for (char* p = str; *p; p++) {
        if (*p == old_char) *p = new_char;
    }
    return str;
}

// Safe string functions
#ifdef PLATFORM_WINDOWS
size_t strlcpy(char* dst, const char* src, size_t size) {
    size_t src_len = strlen(src);
    if (size > 0) {
        size_t copy_len = (src_len >= size) ? size - 1 : src_len;
        memcpy(dst, src, copy_len);
        dst[copy_len] = '\0';
    }
    return src_len;
}

size_t strlcat(char* dst, const char* src, size_t size) {
    size_t dst_len = strlen(dst);
    if (dst_len >= size) return size + strlen(src);
    size_t remaining = size - dst_len - 1;
    size_t src_len = strlen(src);
    size_t copy_len = (src_len > remaining) ? remaining : src_len;
    memcpy(dst + dst_len, src, copy_len);
    dst[dst_len + copy_len] = '\0';
    return dst_len + src_len;
}
#endif

// Memory allocation with error checking
void* safe_malloc(size_t size) {
    void* ptr = malloc(size);
    if (!ptr && size > 0) {
        fprintf(stderr, "Error: Failed to allocate %zu bytes\n", size);
        exit(1);
    }
    return ptr;
}

void* safe_calloc(size_t nmemb, size_t size) {
    void* ptr = calloc(nmemb, size);
    if (!ptr && nmemb > 0 && size > 0) {
        fprintf(stderr, "Error: Failed to allocate %zu x %zu bytes\n", nmemb, size);
        exit(1);
    }
    return ptr;
}

void* safe_realloc(void* ptr, size_t size) {
    void* new_ptr = realloc(ptr, size);
    if (!new_ptr && size > 0) {
        fprintf(stderr, "Error: Failed to reallocate %zu bytes\n", size);
        exit(1);
    }
    return new_ptr;
}

char* safe_strdup(const char* str) {
    if (!str) return NULL;
    char* dup = strdup(str);
    if (!dup) {
        fprintf(stderr, "Error: Failed to duplicate string\n");
        exit(1);
    }
    return dup;
}

// Logging
void log_message(LogLevel level, const char* format, ...) {
    const char* level_str[] = {"DEBUG", "INFO", "WARNING", "ERROR"};
    
    time_t now;
    time(&now);
    struct tm* tm_info = localtime(&now);
    char time_str[26];
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_info);
    
    fprintf(stderr, "[%s] [%s] ", time_str, level_str[level]);
    
    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
    
    fprintf(stderr, "\n");
}

void log_to_file(const char* filename, const char* format, ...) {
    FILE* file = fopen(filename, "a");
    if (!file) return;
    
    time_t now;
    time(&now);
    struct tm* tm_info = localtime(&now);
    char time_str[26];
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_info);
    
    fprintf(file, "[%s] ", time_str);
    
    va_list args;
    va_start(args, format);
    vfprintf(file, format, args);
    va_end(args);
    
    fprintf(file, "\n");
    fclose(file);
}