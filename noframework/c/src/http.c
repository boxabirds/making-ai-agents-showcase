#include "http.h"
#include <string.h>

static size_t write_callback(void* contents, size_t size, size_t nmemb, void* userp) {
    size_t real_size = size * nmemb;
    HttpResponse* response = (HttpResponse*)userp;
    
    // Resize buffer if needed
    while (response->size + real_size >= response->capacity) {
        response->capacity *= 2;
        response->data = safe_realloc(response->data, response->capacity);
    }
    
    memcpy(&(response->data[response->size]), contents, real_size);
    response->size += real_size;
    response->data[response->size] = 0;
    
    return real_size;
}

HttpClient* http_client_create(const char* base_url, const char* api_key) {
    HttpClient* client = safe_calloc(1, sizeof(HttpClient));
    
    // Initialize CURL
    curl_global_init(CURL_GLOBAL_DEFAULT);
    client->curl = curl_easy_init();
    if (!client->curl) {
        free(client);
        return NULL;
    }
    
    client->base_url = safe_strdup(base_url);
    client->api_key = safe_strdup(api_key);
    
    // Set up headers
    client->headers = NULL;
    client->headers = curl_slist_append(client->headers, "Content-Type: application/json");
    client->headers = curl_slist_append(client->headers, "Accept: application/json");
    
    char auth_header[256];
    snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", api_key);
    client->headers = curl_slist_append(client->headers, auth_header);
    
    return client;
}

void http_client_destroy(HttpClient* client) {
    if (!client) return;
    
    if (client->curl) {
        curl_easy_cleanup(client->curl);
    }
    
    if (client->headers) {
        curl_slist_free_all(client->headers);
    }
    
    free(client->base_url);
    free(client->api_key);
    free(client);
    
    curl_global_cleanup();
}

HttpResponse* http_post_json(HttpClient* client, const char* endpoint, const char* json_payload) {
    if (!client || !client->curl || !endpoint || !json_payload) return NULL;
    
    HttpResponse* response = safe_calloc(1, sizeof(HttpResponse));
    response->capacity = 4096;
    response->data = safe_malloc(response->capacity);
    response->size = 0;
    
    // Build full URL
    char url[1024];
    snprintf(url, sizeof(url), "%s%s", client->base_url, endpoint);
    
    // Set CURL options
    curl_easy_setopt(client->curl, CURLOPT_URL, url);
    curl_easy_setopt(client->curl, CURLOPT_HTTPHEADER, client->headers);
    curl_easy_setopt(client->curl, CURLOPT_POSTFIELDS, json_payload);
    curl_easy_setopt(client->curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(client->curl, CURLOPT_WRITEDATA, response);
    curl_easy_setopt(client->curl, CURLOPT_TIMEOUT, 120L);
    curl_easy_setopt(client->curl, CURLOPT_SSL_VERIFYPEER, 1L);
    curl_easy_setopt(client->curl, CURLOPT_SSL_VERIFYHOST, 2L);
    
    // Perform request
    CURLcode res = curl_easy_perform(client->curl);
    
    if (res != CURLE_OK) {
        log_message(LOG_ERROR, "CURL error: %s", curl_easy_strerror(res));
        http_response_destroy(response);
        return NULL;
    }
    
    // Check HTTP response code
    long http_code = 0;
    curl_easy_getinfo(client->curl, CURLINFO_RESPONSE_CODE, &http_code);
    
    if (http_code != 200) {
        log_message(LOG_ERROR, "HTTP error: %ld", http_code);
        log_message(LOG_ERROR, "Response: %s", response->data);
        // Don't destroy response here - let caller handle it
    }
    
    return response;
}

void http_response_destroy(HttpResponse* response) {
    if (!response) return;
    free(response->data);
    free(response);
}

char* http_url_encode(HttpClient* client, const char* str) {
    if (!client || !client->curl || !str) return NULL;
    return curl_easy_escape(client->curl, str, 0);
}