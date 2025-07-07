#include "platform.h"
#include "agent.h"
#include <getopt.h>
#include <ctype.h>

void print_usage(const char* program_name) {
    fprintf(stderr, "Usage: %s [directory] [options]\n\n", program_name);
    fprintf(stderr, "Analyse a codebase using an LLM agent.\n\n");
    fprintf(stderr, "Positional arguments:\n");
    fprintf(stderr, "  directory             Directory containing the codebase to analyse\n\n");
    fprintf(stderr, "Options:\n");
    fprintf(stderr, "  --repo REPO           GitHub repository URL to clone (e.g. https://github.com/owner/repo)\n");
    fprintf(stderr, "  --prompt FILE         Path to a file containing the analysis prompt (required)\n");
    fprintf(stderr, "  --cache-dir DIR       Directory to cache cloned repositories (default: ~/.cache/github)\n");
    fprintf(stderr, "  --output-dir DIR      Directory to save results to (default: output)\n");
    fprintf(stderr, "  --extension EXT       File extension for output files (default: .md)\n");
    fprintf(stderr, "  --file-name FILE      Specific file name for output (overrides --extension)\n");
    fprintf(stderr, "  --model MODEL         Model to use (format: vendor/model, default: openai/gpt-4o-mini)\n");
    fprintf(stderr, "  --base-url URL        Base URL for the API (automatically set based on model if not provided)\n");
    fprintf(stderr, "  -h, --help            Show this help message and exit\n\n");
    fprintf(stderr, "Dependencies:\n");
    fprintf(stderr, "  This program requires environment variables:\n");
    fprintf(stderr, "  - OPENAI_API_KEY for OpenAI models\n");
    fprintf(stderr, "  - GEMINI_API_KEY for Google models\n");
}

int main(int argc, char* argv[]) {
    // Default values
    char* directory = NULL;
    char* repo_url = NULL;
    char* prompt_file = NULL;
    char* cache_dir = "~/.cache/github";
    char* output_dir = "output";
    char* extension = ".md";
    char* file_name = NULL;
    char* model = "openai/gpt-4o-mini";
    char* base_url = NULL;
    
    // Parse command line arguments
    static struct option long_options[] = {
        {"repo", required_argument, 0, 0},
        {"prompt", required_argument, 0, 0},
        {"cache-dir", required_argument, 0, 0},
        {"output-dir", required_argument, 0, 0},
        {"extension", required_argument, 0, 0},
        {"file-name", required_argument, 0, 0},
        {"model", required_argument, 0, 0},
        {"base-url", required_argument, 0, 0},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };
    
    int option_index = 0;
    int c;
    
    while ((c = getopt_long(argc, argv, "h", long_options, &option_index)) != -1) {
        switch (c) {
            case 0:
                // Long option
                if (strcmp(long_options[option_index].name, "repo") == 0) {
                    repo_url = optarg;
                } else if (strcmp(long_options[option_index].name, "prompt") == 0) {
                    prompt_file = optarg;
                } else if (strcmp(long_options[option_index].name, "cache-dir") == 0) {
                    cache_dir = optarg;
                } else if (strcmp(long_options[option_index].name, "output-dir") == 0) {
                    output_dir = optarg;
                } else if (strcmp(long_options[option_index].name, "extension") == 0) {
                    extension = optarg;
                } else if (strcmp(long_options[option_index].name, "file-name") == 0) {
                    file_name = optarg;
                } else if (strcmp(long_options[option_index].name, "model") == 0) {
                    model = optarg;
                } else if (strcmp(long_options[option_index].name, "base-url") == 0) {
                    base_url = optarg;
                }
                break;
            case 'h':
                print_usage(argv[0]);
                return 0;
            case '?':
                return 1;
        }
    }
    
    // Get positional directory argument
    if (optind < argc) {
        directory = argv[optind];
    }
    
    // Validate arguments
    if (!prompt_file) {
        fprintf(stderr, "Error: --prompt is required\n");
        return 1;
    }
    
    // Read prompt file
    FILE* prompt_fp = fopen(prompt_file, "r");
    if (!prompt_fp) {
        fprintf(stderr, "Error: Cannot open prompt file: %s\n", prompt_file);
        return 1;
    }
    
    fseek(prompt_fp, 0, SEEK_END);
    long prompt_size = ftell(prompt_fp);
    fseek(prompt_fp, 0, SEEK_SET);
    
    char* prompt = safe_malloc(prompt_size + 1);
    fread(prompt, 1, prompt_size, prompt_fp);
    prompt[prompt_size] = '\0';
    fclose(prompt_fp);
    
    // Handle repository or directory
    char* repo_name = NULL;
    char* analysis_dir = NULL;
    char* cloned_dir = NULL;
    
    if (repo_url) {
        cloned_dir = clone_or_update_repo(repo_url, cache_dir);
        if (!cloned_dir) {
            fprintf(stderr, "Error: Failed to clone/update repository\n");
            free(prompt);
            return 1;
        }
        analysis_dir = cloned_dir;
        
        // Extract repo name
        char* owner = NULL;
        extract_repo_info(repo_url, &owner, &repo_name);
        free(owner);
    } else {
        if (!directory) {
            directory = ".";
        }
        analysis_dir = platform_normalize_path(directory);
        
        // Get base name for repo_name
        char* last_sep = strrchr(analysis_dir, PATH_SEPARATOR_CHAR);
        repo_name = safe_strdup(last_sep ? last_sep + 1 : analysis_dir);
    }
    
    // Create agent and run analysis
    TechWriterAgent* agent = agent_create(model, base_url);
    if (!agent) {
        fprintf(stderr, "Error: Failed to create agent\n");
        free(prompt);
        free(cloned_dir);
        free(repo_name);
        if (!repo_url) free(analysis_dir);
        return 1;
    }
    
    char* analysis_result = agent_run(agent, prompt, analysis_dir);
    
    // Save results
    save_results(analysis_result, repo_name, model, output_dir, extension, file_name);
    
    // Create metadata
    char output_path[1024];
    if (file_name) {
        snprintf(output_path, sizeof(output_path), "%s%c%s", output_dir, PATH_SEPARATOR_CHAR, file_name);
    } else {
        // Same logic as save_results for consistency
        char* model_copy = safe_strdup(model);
        char* slash = strchr(model_copy, '/');
        if (slash) {
            *slash = '\0';
            const char* vendor = model_copy;
            const char* model_id = slash + 1;
            
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
    
    create_metadata(output_path, model, repo_url ? repo_url : "", repo_name);
    
    // Cleanup
    agent_destroy(agent);
    free(analysis_result);
    free(prompt);
    free(cloned_dir);
    free(repo_name);
    if (!repo_url && analysis_dir != directory) free(analysis_dir);
    
    return 0;
}