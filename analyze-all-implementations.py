#!/usr/bin/env python3
import subprocess
import json
import os
import sys
from pathlib import Path

repo_path = "/Users/julian/.cache/github/axios/axios"

def get_git_files():
    """Get the ground truth - files tracked by git"""
    result = subprocess.run(["git", "-C", repo_path, "ls-files"], 
                           capture_output=True, text=True)
    if result.returncode == 0:
        return set(result.stdout.strip().split('\n'))
    return set()

def run_python_impl():
    """Run Python implementation and get file list"""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'noframework/python'))
    from common.tools import find_all_matching_files
    
    files = find_all_matching_files(
        directory=repo_path,
        pattern="*",
        respect_gitignore=True,
        include_hidden=False,
        include_subdirs=True,
        return_paths_as="str"
    )
    
    # Convert to relative paths
    rel_files = set()
    for f in files:
        try:
            rel_path = os.path.relpath(f, repo_path)
            rel_files.add(rel_path)
        except:
            pass
    return rel_files

def run_go_impl():
    """Run Go implementation and extract file list from logs"""
    print("Running Go implementation...")
    cmd = [
        "go", "run", ".",
        "--repo", "https://github.com/axios/axios",
        "--prompt", "../../../eval/eval.prompt.txt",
        "--output-dir", "./output",
        "--file-name", "test-analyze.md",
        "--model", "openai/gpt-4o-mini"
    ]
    
    # Run the command and capture the file list from the tool output
    cwd = "/Users/julian/expts/awesome-agent-showcase/noframework/golang/tech-writer-agent"
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
    
    # Parse the output to extract files
    files = set()
    # The Go implementation logs the actual file paths in the JSON response
    # We need to run a simpler test that just calls the tool directly
    
    # Instead, let's create a small Go program to call the function directly
    test_go = '''package main
import (
    "encoding/json"
    "fmt"
    "log"
)

func main() {
    result, err := findAllMatchingFiles(map[string]interface{}{
        "directory": "/Users/julian/.cache/github/axios/axios",
        "pattern": "*",
        "respect_gitignore": true,
        "include_hidden": false,
        "include_subdirs": true,
    })
    if err != nil {
        log.Fatal(err)
    }
    
    if searchResult, ok := result.(FileSearchResult); ok {
        data, _ := json.Marshal(searchResult.Files)
        fmt.Println(string(data))
    }
}'''
    
    # Save and run the test
    test_file = "/Users/julian/expts/awesome-agent-showcase/noframework/golang/tech-writer-agent/test_files.go"
    with open(test_file, 'w') as f:
        f.write(test_go)
    
    result = subprocess.run(["go", "run", "test_files.go", "tools.go"], 
                          cwd=cwd, capture_output=True, text=True)
    os.remove(test_file)
    
    if result.returncode == 0 and result.stdout:
        file_list = json.loads(result.stdout)
        for f in file_list:
            rel_path = os.path.relpath(f, repo_path)
            files.add(rel_path)
    
    return files

def analyze_differences(impl_name, impl_files, git_files):
    """Analyze differences between implementation and git"""
    missing = git_files - impl_files
    extra = impl_files - git_files
    
    print(f"\n{'='*60}")
    print(f"{impl_name} Implementation Analysis")
    print(f"{'='*60}")
    print(f"Git tracked files: {len(git_files)}")
    print(f"{impl_name} found: {len(impl_files)}")
    print(f"Missing files: {len(missing)}")
    print(f"Extra files: {len(extra)}")
    
    if missing:
        print(f"\nMissing files (in git but not found by {impl_name}):")
        for f in sorted(missing)[:10]:  # Show first 10
            print(f"  - {f}")
            # Check file properties
            full_path = os.path.join(repo_path, f)
            if os.path.exists(full_path):
                stat = os.stat(full_path)
                basename = os.path.basename(f)
                dirname = os.path.dirname(f)
                print(f"    Exists: Yes, Hidden: {basename.startswith('.')}, Dir: {dirname}")
        if len(missing) > 10:
            print(f"  ... and {len(missing)-10} more")
    
    if extra:
        print(f"\nExtra files (found by {impl_name} but not in git):")
        for f in sorted(extra)[:10]:  # Show first 10
            print(f"  + {f}")
            # Check if it's untracked
            result = subprocess.run(["git", "-C", repo_path, "status", "--porcelain", f], 
                                  capture_output=True, text=True)
            if result.stdout.strip().startswith("??"):
                print(f"    Status: Untracked file")
        if len(extra) > 10:
            print(f"  ... and {len(extra)-10} more")
    
    # Analyze patterns
    if missing:
        print("\nPattern analysis of missing files:")
        patterns = {}
        for f in missing:
            ext = os.path.splitext(f)[1]
            if ext:
                patterns[ext] = patterns.get(ext, 0) + 1
        for ext, count in sorted(patterns.items(), key=lambda x: -x[1])[:5]:
            print(f"  {ext}: {count} files")

def main():
    # Get ground truth
    git_files = get_git_files()
    print(f"Git tracks {len(git_files)} files in the repository")
    
    # Test Python implementation
    try:
        python_files = run_python_impl()
        analyze_differences("Python", python_files, git_files)
    except Exception as e:
        print(f"Error running Python implementation: {e}")
    
    # Test Go implementation
    try:
        go_files = run_go_impl()
        if go_files:
            analyze_differences("Go", go_files, git_files)
    except Exception as e:
        print(f"Error running Go implementation: {e}")
    
    # For other implementations, we'd need to create similar test harnesses
    # or parse their output logs

if __name__ == "__main__":
    main()