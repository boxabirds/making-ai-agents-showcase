package main

import (
    "fmt"
    "log"
    "os"
    "path/filepath"
    "strings"
    gitignore "github.com/denormal/go-gitignore"
)

func main() {
    directory := "/Users/julian/.cache/github/axios/axios"
    
    // Load gitignore
    matcher, err := gitignore.NewFromFile(filepath.Join(directory, ".gitignore"))
    if err != nil {
        matcher = nil
    }
    
    count := 0
    hiddenInRoot := 0
    
    filepath.Walk(directory, func(path string, info os.FileInfo, err error) error {
        if err != nil {
            return nil
        }
        
        if info.IsDir() {
            if filepath.Base(path) == ".git" {
                return filepath.SkipDir
            }
            return nil
        }
        
        relPath, _ := filepath.Rel(directory, path)
        
        // Check if hidden file in root
        if strings.HasPrefix(filepath.Base(path), ".") {
            parts := strings.Split(relPath, string(filepath.Separator))
            if len(parts) == 1 {
                hiddenInRoot++
                fmt.Printf("Hidden in root: %s\n", relPath)
            }
        }
        
        // Check gitignore
        if matcher != nil && matcher.Ignore(relPath) {
            return nil
        }
        
        count++
        return nil
    })
    
    fmt.Printf("\nTotal files (excluding .git and gitignored): %d\n", count)
    fmt.Printf("Hidden files in root: %d\n", hiddenInRoot)
}