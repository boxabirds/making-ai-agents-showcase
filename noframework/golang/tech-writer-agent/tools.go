package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"strings"
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
	
	// Get gitignore patterns if needed
	var gitignorePatterns []string
	if respectGitignore {
		gitignorePatterns = getGitignorePatterns(absDir)
	}
	
	var matchingFiles []string
	
	// Walk the directory tree
	err = filepath.Walk(absDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip files we can't access
		}
		
		// Skip directories
		if info.IsDir() {
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
			return nil
		}
		
		// Skip gitignored files
		if respectGitignore && isGitignored(relPath, gitignorePatterns) {
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

// getGitignorePatterns reads .gitignore patterns from a directory
func getGitignorePatterns(directory string) []string {
	var patterns []string
	
	gitignorePath := filepath.Join(directory, ".gitignore")
	file, err := os.Open(gitignorePath)
	if err != nil {
		return patterns
	}
	defer file.Close()
	
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		// Skip empty lines and comments
		if line != "" && !strings.HasPrefix(line, "#") {
			patterns = append(patterns, line)
		}
	}
	
	log.Printf("Loaded %d patterns from .gitignore", len(patterns))
	return patterns
}

// isGitignored checks if a file path matches any gitignore pattern
func isGitignored(path string, patterns []string) bool {
	// Convert to forward slashes for consistent matching
	path = filepath.ToSlash(path)
	
	for _, pattern := range patterns {
		// Simple pattern matching (not full gitignore spec)
		// Handle directory patterns
		if strings.HasSuffix(pattern, "/") {
			if strings.HasPrefix(path, pattern) || strings.Contains(path, "/"+pattern) {
				return true
			}
		} else {
			// Handle file patterns
			matched, _ := filepath.Match(pattern, filepath.Base(path))
			if matched {
				return true
			}
			// Also check if the pattern matches any part of the path
			if strings.Contains(path, pattern) {
				return true
			}
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