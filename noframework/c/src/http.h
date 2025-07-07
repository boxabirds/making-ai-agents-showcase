#ifndef HTTP_H
#define HTTP_H

#include "platform.h"
#include <curl/curl.h>

typedef struct {
    char* data;
    size_t size;
    size_t capacity;
} HttpResponse;

typedef struct {
    CURL* curl;
    struct curl_slist* headers;
    char* base_url;
    char* api_key;
} HttpClient;

// HTTP client functions
HttpClient* http_client_create(const char* base_url, const char* api_key);
void http_client_destroy(HttpClient* client);

// HTTP request functions
HttpResponse* http_post_json(HttpClient* client, const char* endpoint, const char* json_payload);
void http_response_destroy(HttpResponse* response);

// Utility functions
char* http_url_encode(HttpClient* client, const char* str);

#endif // HTTP_H