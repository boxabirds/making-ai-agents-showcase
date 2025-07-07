package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// Constants for system prompts
const (
	MAX_ITERATIONS = 50
	
	ROLE_AND_TASK = `You are an expert tech writer that helps teams understand codebases with accurate and concise supporting analysis and documentation. 
Your task is to analyse the local filesystem to understand the structure and functionality of a codebase.`

	GENERAL_ANALYSIS_GUIDELINES = `Follow these guidelines:
- Use the available tools to explore the filesystem, read files, and gather information.
- Make no assumptions about file types or formats - analyse each file based on its content and extension.
- Focus on providing a comprehensive, accurate, and well-structured analysis.
- Include code snippets and examples where relevant.
- Organize your response with clear headings and sections.
- Cite specific files and line numbers to support your observations.`

	INPUT_PROCESSING_GUIDELINES = `Important guidelines:
- The user's analysis prompt will be provided in the initial message, prefixed with the base directory of the codebase (e.g., "Base directory: /path/to/codebase").
- Analyse the codebase based on the instructions in the prompt, using the base directory as the root for all relative paths.
- Make no assumptions about file types or formats - analyse each file based on its content and extension.
- Adapt your analysis approach based on the codebase and the prompt's requirements.
- Be thorough but focus on the most important aspects as specified in the prompt.
- Provide clear, structured summaries of your findings in your final response.
- Handle errors gracefully and report them clearly if they occur but don't let them halt the rest of the analysis.`

	CODE_ANALYSIS_STRATEGIES = `When analysing code:
- Start by exploring the directory structure to understand the project organisation.
- Identify key files like README, configuration files, or main entry points.
- Ignore temporary files and directories like node_modules, .git, etc.
- Analyse relationships between components (e.g., imports, function calls).
- Look for patterns in the code organisation (e.g., line counts, TODOs).
- Summarise your findings to help someone understand the codebase quickly, tailored to the prompt.`

	REACT_PLANNING_STRATEGY = `You should follow the ReAct pattern:
1. Thought: Reason about what you need to do next
2. Action: Use one of the available tools
3. Observation: Review the results of the tool
4. Repeat until you have enough information to provide a final answer`

	QUALITY_REQUIREMENTS = `When you've completed your analysis, provide a final answer in the form of a comprehensive Markdown document 
that provides a mutually exclusive and collectively exhaustive (MECE) analysis of the codebase using the user prompt.

Your analysis should be thorough, accurate, and helpful for someone trying to understand this codebase.`
)

// GetTechWriterSystemPrompt returns the complete system prompt
func GetTechWriterSystemPrompt() string {
	return fmt.Sprintf("%s\n\n%s\n\n%s\n\n%s\n\n%s",
		ROLE_AND_TASK,
		GENERAL_ANALYSIS_GUIDELINES,
		INPUT_PROCESSING_GUIDELINES,
		CODE_ANALYSIS_STRATEGIES,
		QUALITY_REQUIREMENTS)
}

// GetReActSystemPrompt returns the ReAct-specific system prompt
func GetReActSystemPrompt() string {
	return fmt.Sprintf("%s\n\n%s", GetTechWriterSystemPrompt(), REACT_PLANNING_STRATEGY)
}

// readPromptFile reads a prompt from an external file
func readPromptFile(filePath string) (string, error) {
	content, err := os.ReadFile(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return "", fmt.Errorf("prompt file not found: %s", filePath)
		}
		return "", fmt.Errorf("error reading prompt file: %w", err)
	}
	return strings.TrimSpace(string(content)), nil
}

// sanitizeFilename sanitizes a string to be safe for use in filenames
func sanitizeFilename(name string) string {
	// Characters that are problematic in filenames across different OS
	unsafeChars := `/\:*?"<>|`
	for _, char := range unsafeChars {
		name = strings.ReplaceAll(name, string(char), "-")
	}
	return name
}

// validateGitHubURL validates GitHub URL or owner/repo format
func validateGitHubURL(url string) bool {
	// Standard GitHub URL pattern
	if strings.HasPrefix(url, "https://github.com/") {
		parts := strings.Split(strings.TrimPrefix(url, "https://github.com/"), "/")
		return len(parts) >= 2 && parts[0] != "" && parts[1] != ""
	}
	
	// owner/repo format
	if !strings.HasPrefix(url, "http") && strings.Count(url, "/") == 1 {
		parts := strings.Split(url, "/")
		return len(parts) == 2 && parts[0] != "" && parts[1] != ""
	}
	
	return false
}

// getRepoNameFromURL extracts owner/repo from GitHub URL
func getRepoNameFromURL(url string) string {
	url = strings.TrimSuffix(strings.TrimSuffix(url, "/"), ".git")
	
	if strings.HasPrefix(url, "https://github.com/") {
		return strings.TrimPrefix(url, "https://github.com/")
	}
	
	// Already in owner/repo format
	return url
}

// cloneRepo clones a repository to the cache directory
func cloneRepo(repoURL, cacheDir string) (string, error) {
	repoName := getRepoNameFromURL(repoURL)
	
	// Expand tilde in cache directory
	if strings.HasPrefix(cacheDir, "~") {
		homeDir, err := os.UserHomeDir()
		if err != nil {
			return "", fmt.Errorf("error getting home directory: %w", err)
		}
		cacheDir = filepath.Join(homeDir, cacheDir[1:])
	}
	
	repoPath := filepath.Join(cacheDir, repoName)
	
	// Check if already cloned
	if _, err := os.Stat(repoPath); err == nil {
		return repoPath, nil
	}
	
	// Create parent directory
	if err := os.MkdirAll(filepath.Dir(repoPath), 0755); err != nil {
		return "", fmt.Errorf("error creating cache directory: %w", err)
	}
	
	// Clone the repository
	cmd := exec.Command("git", "clone", "--depth", "1", repoURL, repoPath)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("failed to clone repository: %s\n%s", err, string(output))
	}
	
	return repoPath, nil
}

// Metadata represents the metadata for a tech writer output
type Metadata struct {
	Model     string `json:"model"`
	GitHubURL string `json:"github_url"`
	RepoName  string `json:"repo_name"`
	Timestamp string `json:"timestamp"`
	EvalOutput string `json:"eval_output,omitempty"`
	EvalError  string `json:"eval_error,omitempty"`
}

// createMetadata creates a metadata JSON file for the tech writer output
func createMetadata(outputFile, modelName, repoURL, repoName, techWriterResult, evalPromptFile string) error {
	metadata := Metadata{
		Model:     modelName,
		GitHubURL: repoURL,
		RepoName:  repoName,
		Timestamp: time.Now().Format(time.RFC3339),
	}
	
	// Run evaluation if prompt provided
	if evalPromptFile != "" {
		evalPrompt, err := readPromptFile(evalPromptFile)
		if err != nil {
			metadata.EvalError = err.Error()
		} else {
			// Prepare the full prompt with the tech writer result
			fullPrompt := fmt.Sprintf("%s\n\n%s", evalPrompt, techWriterResult)
			
			// Create LLM client for evaluation
			llmClient, err := NewLLMClient(modelName, "")
			if err != nil {
				metadata.EvalError = err.Error()
			} else {
				// Call the API for evaluation
				evalResult, err := llmClient.Complete(fullPrompt, "", 0)
				if err != nil {
					metadata.EvalError = err.Error()
				} else {
					metadata.EvalOutput = evalResult
				}
			}
		}
	}
	
	// Create metadata filename
	dir := filepath.Dir(outputFile)
	base := strings.TrimSuffix(filepath.Base(outputFile), filepath.Ext(outputFile))
	metadataFile := filepath.Join(dir, base+".metadata.json")
	
	// Save the metadata
	jsonData, err := json.MarshalIndent(metadata, "", "  ")
	if err != nil {
		return fmt.Errorf("error marshaling metadata: %w", err)
	}
	
	if err := os.WriteFile(metadataFile, jsonData, 0644); err != nil {
		return fmt.Errorf("error writing metadata file: %w", err)
	}
	
	log.Printf("Metadata saved to: %s", metadataFile)
	return nil
}