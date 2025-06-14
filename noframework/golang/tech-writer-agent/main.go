package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Command line arguments structure
type Args struct {
	Directory  string
	Repo       string
	PromptFile string
	Model      string
	BaseURL    string
	CacheDir   string
	OutputDir  string
	Extension  string
	FileName   string
	EvalPrompt string
}

func main() {
	// Configure logging
	log.SetFlags(log.LstdFlags | log.Lshortfile)

	// Parse command line arguments
	args, err := getCommandLineArgs()
	if err != nil {
		log.Fatalf("Error parsing arguments: %v", err)
	}

	// Configure code base source
	repoURL, directoryPath, err := configureCodeBaseSource(args.Repo, args.Directory, args.CacheDir)
	if err != nil {
		log.Fatalf("Error configuring code base source: %v", err)
	}

	// Analyze the codebase
	analysisResult, repoName, _, err := analyzeCodebase(directoryPath, args.PromptFile, args.Model, args.BaseURL, repoURL)
	if err != nil {
		log.Fatalf("Error analyzing codebase: %v", err)
	}

	// Save results
	outputFile, err := saveResults(analysisResult, args.Model, repoName, args.OutputDir, args.Extension, args.FileName)
	if err != nil {
		log.Fatalf("Error saving results: %v", err)
	}
	log.Printf("Analysis complete. Results saved to: %s", outputFile)

	// Create metadata
	if err := createMetadata(outputFile, args.Model, repoURL, repoName, analysisResult, args.EvalPrompt); err != nil {
		log.Fatalf("Error creating metadata: %v", err)
	}
}

func getCommandLineArgs() (*Args, error) {
	args := &Args{}

	// Custom argument parsing to handle mixed positional and flag arguments
	// This is needed because Go's flag package stops at the first non-flag argument
	var positionalArgs []string
	var flagArgs []string
	
	// Separate positional arguments from flags
	for i := 1; i < len(os.Args); i++ {
		arg := os.Args[i]
		if strings.HasPrefix(arg, "-") {
			// This is a flag, add it and its value (if any)
			flagArgs = append(flagArgs, arg)
			// Check if this flag has a value
			if i+1 < len(os.Args) && !strings.HasPrefix(os.Args[i+1], "-") {
				i++
				flagArgs = append(flagArgs, os.Args[i])
			}
		} else {
			positionalArgs = append(positionalArgs, arg)
		}
	}
	
	// Set os.Args to only contain program name and flags for flag.Parse()
	os.Args = append([]string{os.Args[0]}, flagArgs...)

	// Define flags
	flag.StringVar(&args.Repo, "repo", "", "GitHub repository URL to clone (e.g. https://github.com/owner/repo)")
	flag.StringVar(&args.PromptFile, "prompt", "", "Path to a file containing the analysis prompt (required)")
	flag.StringVar(&args.Model, "model", "openai/gpt-4o-mini", "Model to use for analysis (format: vendor/model)")
	flag.StringVar(&args.BaseURL, "base-url", "", "Base URL for the API (automatically set based on model if not provided)")
	flag.StringVar(&args.CacheDir, "cache-dir", "~/.cache/github", "Directory to cache cloned repositories")
	flag.StringVar(&args.OutputDir, "output-dir", "output", "Directory to save results to")
	flag.StringVar(&args.Extension, "extension", ".md", "File extension for output files")
	flag.StringVar(&args.FileName, "file-name", "", "Specific file name for output (overrides --extension)")
	flag.StringVar(&args.EvalPrompt, "eval-prompt", "", "Path to file containing prompt to evaluate the tech writer results")

	flag.Parse()

	// Handle positional arguments
	if len(positionalArgs) > 0 {
		args.Directory = positionalArgs[0]
	}

	// Debug: print parsed arguments
	// log.Printf("Parsed args: Directory=%q, Repo=%q, PromptFile=%q", args.Directory, args.Repo, args.PromptFile)

	// Validate required arguments
	if args.PromptFile == "" {
		return nil, fmt.Errorf("-prompt is required")
	}

	if args.Directory == "" && args.Repo == "" {
		return nil, fmt.Errorf("either directory or -repo is required")
	}

	// Check API keys
	if os.Getenv("OPENAI_API_KEY") == "" && os.Getenv("GEMINI_API_KEY") == "" {
		return nil, fmt.Errorf("neither OPENAI_API_KEY nor GEMINI_API_KEY environment variables are set")
	}

	return args, nil
}

func configureCodeBaseSource(repoArg, directoryArg, cacheDir string) (repoURL, directoryPath string, err error) {
	if repoArg != "" {
		// Validate GitHub URL
		if !validateGitHubURL(repoArg) {
			return "", "", fmt.Errorf("invalid GitHub repository URL format")
		}
		// Clone repository
		repoURL = repoArg
		directoryPath, err = cloneRepo(repoArg, cacheDir)
		if err != nil {
			return "", "", fmt.Errorf("failed to clone repository: %w", err)
		}
	} else {
		directoryPath = directoryArg
		// Validate directory exists
		if _, err := os.Stat(directoryPath); os.IsNotExist(err) {
			return "", "", fmt.Errorf("directory not found: %s", directoryPath)
		}
	}
	return repoURL, directoryPath, nil
}

func analyzeCodebase(directoryPath, promptFilePath, modelName, baseURL, repoURL string) (string, string, string, error) {
	// Read the prompt file
	prompt, err := readPromptFile(promptFilePath)
	if err != nil {
		return "", "", "", err
	}
	
	// Prepare the full prompt with base directory
	fullPrompt := fmt.Sprintf("Base directory: %s\n\n%s", directoryPath, prompt)
	
	// Create LLM client
	llmClient, err := NewLLMClient(modelName, baseURL)
	if err != nil {
		return "", "", "", err
	}
	
	// Create ReAct agent
	systemPrompt := GetReActSystemPrompt()
	// Enable verbose mode for debugging
	verbose := os.Getenv("VERBOSE") == "true"
	agent := NewReActAgent(llmClient, systemPrompt, MAX_ITERATIONS, verbose)
	
	// Run the analysis
	log.Printf("Starting analysis of %s", directoryPath)
	analysisResult, err := agent.Run(fullPrompt)
	if err != nil {
		return "", "", "", fmt.Errorf("analysis failed: %w", err)
	}
	
	// Extract repo name
	repoName := filepath.Base(directoryPath)
	if repoURL != "" {
		parts := strings.Split(repoURL, "/")
		if len(parts) > 0 {
			repoName = strings.TrimSuffix(parts[len(parts)-1], ".git")
		}
	}
	
	return analysisResult, repoName, repoURL, nil
}

func saveResults(analysisResult, modelName, repoName, outputDir, extension, fileName string) (string, error) {
	// Create output directory if it doesn't exist
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return "", fmt.Errorf("error creating output directory: %w", err)
	}
	
	var outputPath string
	
	if fileName != "" {
		// Use the specific file name provided
		outputPath = filepath.Join(outputDir, fileName)
	} else {
		// Use the existing logic with timestamp
		if extension == "" {
			extension = ".md"
		}
		
		// Ensure extension starts with a dot
		if !strings.HasPrefix(extension, ".") {
			extension = "." + extension
		}
		
		// Generate timestamp for filename
		timestamp := time.Now().Format("20060102-150405")
		
		// Sanitize model name for use in filename
		safeModelName := sanitizeFilename(modelName)
		
		// Include repository name in filename if available
		var outputFilename string
		if repoName != "" {
			outputFilename = fmt.Sprintf("%s-%s-%s%s", timestamp, repoName, safeModelName, extension)
		} else {
			outputFilename = fmt.Sprintf("%s-%s%s", timestamp, safeModelName, extension)
		}
		
		outputPath = filepath.Join(outputDir, outputFilename)
	}
	
	// Save results to file
	if err := os.WriteFile(outputPath, []byte(analysisResult), 0644); err != nil {
		return "", fmt.Errorf("failed to save results: %w", err)
	}
	
	return outputPath, nil
}