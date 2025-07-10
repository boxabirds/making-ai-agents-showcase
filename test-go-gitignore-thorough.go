package main

import (
    "fmt"
    "os"
    "path/filepath"
    gitignore "github.com/denormal/go-gitignore"
)

func main() {
    homeDir := os.Getenv("HOME")
    if homeDir == "" {
        homeDir = "."
    }
    
    repoPath := filepath.Join(homeDir, ".cache/github/axios/axios")
    gitignorePath := filepath.Join(repoPath, ".gitignore")
    
    // Load gitignore two ways
    fmt.Println("Testing go-gitignore library:")
    fmt.Println("Repository:", repoPath)
    fmt.Println()
    
    // Method 1: NewFromFile
    matcher1, err := gitignore.NewFromFile(gitignorePath)
    if err != nil {
        fmt.Printf("Error loading .gitignore: %v\n", err)
        return
    }
    
    // Method 2: NewRepository
    matcher2, err := gitignore.NewRepository(repoPath)
    if err != nil {
        fmt.Printf("Error creating repository matcher: %v\n", err)
        // Continue with just matcher1
        matcher2 = matcher1
    }
    
    // Test files
    testFiles := []string{
        ".DS_Store",
        "bin/.DS_Store",
        "lib/.DS_Store",
        "test/.DS_Store",
        ".github/.DS_Store",
        "node_modules/test.js",
        "coverage/index.html",
        ".gitignore",
        ".npmignore",
        "src/axios.js",
        ".git/config",
    }
    
    fmt.Println("Testing patterns with NewFromFile:")
    for _, file := range testFiles {
        ignored := matcher1.Ignore(file)
        match := matcher1.Match(file)
        fmt.Printf("  %-30s Ignore: %-5v Match: %v\n", file, ignored, match)
    }
    
    if matcher2 != matcher1 {
        fmt.Println("\nTesting patterns with NewRepository:")
        for _, file := range testFiles {
            ignored := matcher2.Ignore(file)
            match := matcher2.Match(file)
            fmt.Printf("  %-30s Ignore: %-5v Match: %v\n", file, ignored, match)
        }
    }
    
    // Test absolute vs relative paths
    fmt.Println("\nTesting with absolute paths:")
    for _, file := range testFiles[:3] {
        absPath := filepath.Join(repoPath, file)
        ignored := matcher1.Ignore(absPath)
        match := matcher1.Match(absPath)
        fmt.Printf("  %-30s Ignore: %-5v Match: %v\n", file, ignored, match)
    }
}