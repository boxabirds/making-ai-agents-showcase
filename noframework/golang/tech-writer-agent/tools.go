package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"strings"
	
	gitignore "github.com/denormal/go-gitignore"
)

// Tool represents a callable tool function
type Tool struct {
	Name        string
	Description string
	Function    func(args map[string]interface{}) (interface{}, error)
}

// ToolResult represents the result of a tool call
type ToolResult struct {
	Success bool        `json:"success"`
	Result  interface{} `json:"result,omitempty"`
	Error   string      `json:"error,omitempty"`
}

// FileSearchResult represents the result of finding files
type FileSearchResult struct {
	Files []string `json:"files"`
	Count int      `json:"count"`
}

// FileReadResult represents the result of reading a file
type FileReadResult struct {
	File    string `json:"file"`
	Content string `json:"content"`
}

// Available tools
var Tools = map[string]Tool{
	"find_all_matching_files": {
		Name:        "find_all_matching_files",
		Description: "Find files matching a pattern while respecting .gitignore",
		Function:    findAllMatchingFiles,
	},
	"read_file": {
		Name:        "read_file",
		Description: "Read the contents of a file",
		Function:    readFile,
	},
}

// findAllMatchingFiles finds files matching a pattern
func findAllMatchingFiles(args map[string]interface{}) (interface{}, error) {
	// Extract arguments with defaults
	directory, ok := args["directory"].(string)
	if !ok {
		return nil, fmt.Errorf("directory parameter is required")
	}
	
	pattern, ok := args["pattern"].(string)
	if !ok {
		pattern = "*"
	}
	
	respectGitignore := true
	if val, ok := args["respect_gitignore"].(bool); ok {
		respectGitignore = val
	}
	
	includeHidden := false
	if val, ok := args["include_hidden"].(bool); ok {
		includeHidden = val
	}
	
	includeSubdirs := true
	if val, ok := args["include_subdirs"].(bool); ok {
		includeSubdirs = val
	}
	
	log.Printf("Tool invoked: find_all_matching_files(directory='%s', pattern='%s', respect_gitignore=%v, include_hidden=%v, include_subdirs=%v)",
		directory, pattern, respectGitignore, includeHidden, includeSubdirs)
	
	// Resolve directory path
	absDir, err := filepath.Abs(directory)
	if err != nil {
		return nil, fmt.Errorf("error resolving directory path: %w", err)
	}
	
	// Check if directory exists
	if _, err := os.Stat(absDir); os.IsNotExist(err) {
		log.Printf("Directory not found: %s", directory)
		return FileSearchResult{Files: []string{}, Count: 0}, nil
	}
	
	// Get gitignore matcher if needed
	var matcher gitignore.GitIgnore
	if respectGitignore {
		matcher = loadGitignoreMatcher(absDir)
	}
	
	var matchingFiles []string
	
	// Walk the directory tree
	err = filepath.Walk(absDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip files we can't access
		}
		
		// Skip directories
		if info.IsDir() {
			// Always skip .git directory
			if filepath.Base(path) == ".git" {
				return filepath.SkipDir
			}
			// Skip subdirectories if not included
			if !includeSubdirs && path != absDir {
				return filepath.SkipDir
			}
			return nil
		}
		
		// Get relative path for pattern matching
		relPath, err := filepath.Rel(absDir, path)
		if err != nil {
			return nil
		}
		
		// Skip hidden files if not included
		if !includeHidden && strings.HasPrefix(filepath.Base(path), ".") {
			// Check if any parent directory is hidden
			parts := strings.Split(relPath, string(filepath.Separator))
			hasHiddenParent := false
			for i := 0; i < len(parts)-1; i++ { // Exclude the filename itself
				if strings.HasPrefix(parts[i], ".") {
					hasHiddenParent = true
					break
				}
			}
			// Only skip if it's in a hidden directory
			if hasHiddenParent {
				return nil
			}
			// Hidden files in non-hidden directories (like .gitignore) should be included
		}
		
		// Skip gitignored files
		if respectGitignore && shouldIgnore(relPath, matcher) {
			return nil
		}
		
		// Check if file matches pattern
		matched, err := filepath.Match(pattern, filepath.Base(path))
		if err != nil {
			return nil
		}
		
		if matched {
			matchingFiles = append(matchingFiles, path)
		}
		
		return nil
	})
	
	if err != nil {
		return nil, fmt.Errorf("error walking directory: %w", err)
	}
	
	log.Printf("Found %d matching files", len(matchingFiles))
	
	return FileSearchResult{
		Files: matchingFiles,
		Count: len(matchingFiles),
	}, nil
}

// readFile reads the contents of a file
func readFile(args map[string]interface{}) (interface{}, error) {
	filePath, ok := args["file_path"].(string)
	if !ok {
		return nil, fmt.Errorf("file_path parameter is required")
	}
	
	log.Printf("Tool invoked: read_file(file_path='%s')", filePath)
	
	// Check if file exists
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		return map[string]string{"error": fmt.Sprintf("File not found: %s", filePath)}, nil
	}
	
	// Check if it's a binary file
	if isBinary(filePath) {
		log.Printf("File detected as binary: %s", filePath)
		return map[string]string{"error": fmt.Sprintf("Cannot read binary file: %s", filePath)}, nil
	}
	
	// Read the file
	content, err := os.ReadFile(filePath)
	if err != nil {
		if os.IsPermission(err) {
			return map[string]string{"error": fmt.Sprintf("Permission denied when reading file: %s", filePath)}, nil
		}
		return map[string]string{"error": fmt.Sprintf("Error reading file: %s", err)}, nil
	}
	
	fileContent := string(content)
	log.Printf("Successfully read file: %s (%d chars)", filePath, len(fileContent))
	
	return FileReadResult{
		File:    filePath,
		Content: fileContent,
	}, nil
}

// loadGitignoreMatcher creates a gitignore matcher from .gitignore file
func loadGitignoreMatcher(directory string) gitignore.GitIgnore {
	gitignorePath := filepath.Join(directory, ".gitignore")
	
	// Try to load from file
	matcher, err := gitignore.NewFromFile(gitignorePath)
	if err != nil {
		// If no .gitignore file, create empty matcher
		// For now, we'll return nil and handle it in the caller
		log.Printf("No .gitignore found: %v", err)
		return nil
	} else {
		log.Printf("Loaded gitignore patterns from %s", gitignorePath)
	}
	
	return matcher
}

// shouldIgnore checks if a file should be ignored based on gitignore patterns
// This function works around several issues in the go-gitignore library:
// 1. The library doesn't handle directory patterns correctly (e.g., "node_modules/")
// 2. The library's Match() method can cause nil pointer panics
// 3. The library doesn't work well when not in the repository directory
func shouldIgnore(relPath string, matcher gitignore.GitIgnore) bool {
	if matcher == nil {
		return false
	}
	
	// First try the matcher's Ignore method
	if matcher.Ignore(relPath) {
		return true
	}
	
	// The go-gitignore library has issues with directory patterns.
	// Check if the file is in a directory that should be ignored.
	parts := strings.Split(relPath, string(filepath.Separator))
	for i := 1; i <= len(parts); i++ {
		dirPath := strings.Join(parts[:i], string(filepath.Separator))
		// Check both with and without trailing slash
		if matcher.Ignore(dirPath) || matcher.Ignore(dirPath + "/") {
			return true
		}
	}
	
	return false
}



// isBinary checks if a file is binary by reading the first few bytes
func isBinary(filePath string) bool {
	file, err := os.Open(filePath)
	if err != nil {
		return true // Assume binary if we can't open
	}
	defer file.Close()
	
	// Read first 512 bytes
	buffer := make([]byte, 512)
	n, err := file.Read(buffer)
	if err != nil && err != io.EOF {
		return true
	}
	
	// Check for null bytes (common in binary files)
	for i := 0; i < n; i++ {
		if buffer[i] == 0 {
			return true
		}
	}
	
	// Check if it's mostly printable ASCII
	printable := 0
	for i := 0; i < n; i++ {
		if buffer[i] >= 32 && buffer[i] <= 126 || buffer[i] == '\n' || buffer[i] == '\r' || buffer[i] == '\t' {
			printable++
		}
	}
	
	// If less than 80% printable, consider it binary
	return float64(printable)/float64(n) < 0.8
}

// ExecuteTool executes a tool by name with the given arguments
func ExecuteTool(toolName string, args map[string]interface{}) (string, error) {
	tool, exists := Tools[toolName]
	if !exists {
		return "", fmt.Errorf("unknown tool: %s", toolName)
	}
	
	result, err := tool.Function(args)
	if err != nil {
		return "", err
	}
	
	// Convert result to JSON string
	jsonBytes, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return "", fmt.Errorf("error marshaling result: %w", err)
	}
	
	return string(jsonBytes), nil
}