#!/bin/bash

# Output CSV file
output_file="oss-agent-makers-versions.csv"

# Write CSV header
echo "repo_name,version" > "$output_file"

# Process each directory in oss-agent-makers
for dir in oss-agent-makers/*/; do
    # Skip if not a directory
    [ -d "$dir" ] || continue
    
    # Get the repo name (directory name)
    repo_name=$(basename "$dir")
    
    # Check if .venv exists in the directory
    if [ -d "$dir/.venv" ]; then
        # Look for version in multiple ways
        version=""
        
        # Method 1: Check dist-info directories in site-packages
        # Try various naming patterns
        patterns=("${repo_name}" "${repo_name//-/_}" "${repo_name//_/-}")
        
        # Add special cases
        case "$repo_name" in
            "autogen") patterns+=("pyautogen") ;;
            "camel") patterns+=("camel_ai" "camel-ai") ;;
            "water") patterns+=("water_ai" "water-ai") ;;
        esac
        
        for pattern in "${patterns[@]}"; do
            dist_info=$(find "$dir/.venv/lib/python"*/site-packages -maxdepth 1 -name "${pattern}-*.dist-info" 2>/dev/null | head -1)
            if [ -n "$dist_info" ] && [ -f "$dist_info/METADATA" ]; then
                version=$(grep "^Version:" "$dist_info/METADATA" | cut -d' ' -f2 | head -1)
                break
            fi
        done
        
        # Method 2: If not found, try pip list
        if [ -z "$version" ]; then
            version=$(cd "$dir" && {
                source .venv/bin/activate 2>/dev/null
                
                # Try different variations of the package name
                for name in "$repo_name" "${repo_name//-/_}" "${repo_name//_/-}"; do
                    result=$(pip list 2>/dev/null | grep -i "^${name} " | awk '{print $2}' | head -1)
                    [ -n "$result" ] && echo "$result" && break
                done
            })
        fi
        
        # Method 3: Check if installed in editable mode
        if [ -z "$version" ]; then
            # Check for .egg-info or .dist-info in the main directory
            egg_info=$(find "$dir" -maxdepth 2 -name "*.egg-info" -o -name "*.dist-info" 2>/dev/null | head -1)
            if [ -n "$egg_info" ] && [ -f "$egg_info/PKG-INFO" ]; then
                version=$(grep "^Version:" "$egg_info/PKG-INFO" | cut -d' ' -f2 | head -1)
                [ -n "$version" ] && version="${version} (editable)"
            fi
        fi
        
        # If version found, add to CSV
        if [ -n "$version" ]; then
            echo "\"$repo_name\",\"$version\"" >> "$output_file"
        else
            echo "\"$repo_name\",\"not found\"" >> "$output_file"
        fi
    else
        echo "\"$repo_name\",\"no .venv\"" >> "$output_file"
    fi
done

echo "Version catalogue written to $output_file"