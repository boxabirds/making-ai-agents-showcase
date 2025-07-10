#!/usr/bin/env python3
import subprocess
import os

repo_path = "/Users/julian/.cache/github/axios/axios"

# Get git tracked files
result = subprocess.run(["git", "-C", repo_path, "ls-files"], 
                       capture_output=True, text=True)
git_files = set(result.stdout.strip().split('\n')) if result.returncode == 0 else set()

print(f"Git tracks {len(git_files)} files")

# Run Zig implementation to get its file list
# We'll need to parse the output
print("\nRunning Zig implementation...")
zig_cmd = [
    "./zig-out/bin/tech-writer",
    "--repo", "https://github.com/axios/axios",
    "--prompt", "../../eval/eval.prompt.txt", 
    "--output-dir", "./output",
    "--file-name", "test-zig-debug.md",
    "--model", "openai/gpt-4o-mini"
]

cwd = "/Users/julian/expts/awesome-agent-showcase/noframework/zig"
result = subprocess.run(zig_cmd, cwd=cwd, capture_output=True, text=True, timeout=30)

# Extract file count from output
import re
match = re.search(r"Found (\d+) matching files", result.stdout + result.stderr)
if match:
    zig_count = int(match.group(1))
    print(f"Zig found {zig_count} files")
else:
    print("Could not find file count in Zig output")
    print("Output:", result.stdout[:500])
    print("Error:", result.stderr[:500])

# Check what patterns might be missing files
print("\nAnalyzing missing files...")
print("\nChecking hidden files in git:")
hidden_files = [f for f in git_files if f.startswith('.') or '/' in f and f.split('/')[-1].startswith('.')]
print(f"Hidden files in git: {len(hidden_files)}")
for f in sorted(hidden_files)[:10]:
    print(f"  {f}")

print("\nChecking files without extensions:")
no_ext = [f for f in git_files if '.' not in os.path.basename(f)]
print(f"Files without extensions: {len(no_ext)}")
for f in sorted(no_ext)[:10]:
    print(f"  {f}")