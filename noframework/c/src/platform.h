#ifndef PLATFORM_H
#define PLATFORM_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <time.h>

#ifdef _WIN32
    #define PLATFORM_WINDOWS
    #include <windows.h>
    #include <direct.h>
    #include <io.h>
    #define PATH_SEPARATOR "\\"
    #define PATH_SEPARATOR_CHAR '\\'
    #define mkdir(path, mode) _mkdir(path)
    #define popen _popen
    #define pclose _pclose
    #define strdup _strdup
    #define access _access
    #define F_OK 0
    #define snprintf _snprintf
#else
    #define PLATFORM_POSIX
    #include <unistd.h>
    #include <dirent.h>
    #include <sys/stat.h>
    #include <sys/types.h>
    #include <sys/wait.h>
    #include <errno.h>
    #define PATH_SEPARATOR "/"
    #define PATH_SEPARATOR_CHAR '/'
#endif

// Platform-independent functions
char* platform_get_home_dir(void);
int platform_make_directory(const char* path);
int platform_file_exists(const char* path);
int platform_is_directory(const char* path);
char* platform_normalize_path(const char* path);
int platform_execute_command(const char* command, char* output, size_t output_size);

// String utilities
char* string_duplicate(const char* str);
char* string_trim(char* str);
int string_starts_with(const char* str, const char* prefix);
int string_ends_with(const char* str, const char* suffix);
char* string_replace_char(char* str, char old_char, char new_char);

// Safe string functions
#ifdef PLATFORM_WINDOWS
size_t strlcpy(char* dst, const char* src, size_t size);
size_t strlcat(char* dst, const char* src, size_t size);
#endif

// Memory allocation with error checking
void* safe_malloc(size_t size);
void* safe_calloc(size_t nmemb, size_t size);
void* safe_realloc(void* ptr, size_t size);
char* safe_strdup(const char* str);

// Logging
typedef enum {
    LOG_DEBUG,
    LOG_INFO,
    LOG_WARNING,
    LOG_ERROR
} LogLevel;

void log_message(LogLevel level, const char* format, ...);
void log_to_file(const char* filename, const char* format, ...);

#endif // PLATFORM_H