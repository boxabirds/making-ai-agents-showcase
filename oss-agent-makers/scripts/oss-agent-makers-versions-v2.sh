#!/bin/bash

# Output CSV file
output_file="../data/oss-agent-makers-versions.csv"

# Write CSV header
echo "repo_name,version,package_name" > "$output_file"

# Function to extract package names from install.sh
extract_package_names() {
    local install_file="$1"
    local packages=()
    
    if [ -f "$install_file" ]; then
        # Extract from pip install commands
        grep -E "(pip install|uv add|uv pip install)" "$install_file" | while read -r line; do
            # Remove comments and extract package names
            pkg_line=$(echo "$line" | sed 's/#.*//' | sed 's/.*\(pip install\|uv add\|uv pip install\)//')
            # Handle quotes and extract package names (without version specifiers)
            echo "$pkg_line" | tr ' ' '\n' | grep -v '^-' | sed 's/["\047]//' | sed 's/\[.*//' | sed 's/[<>=!].*//' | grep -v '^$'
        done | sort -u
    fi
}

# Process each directory in oss-agent-makers
for dir in ../*/; do
    # Skip if not a directory
    [ -d "$dir" ] || continue
    
    # Get the repo name (directory name)
    repo_name=$(basename "$dir")
    
    # Skip special directories
    if [[ "$repo_name" == "scripts" || "$repo_name" == "data" || "$repo_name" == "logs" || "$repo_name" == "extraction" ]]; then
        continue
    fi
    
    # Extract package names from install.sh
    packages=($(extract_package_names "$dir/install.sh"))
    
    # Check if .venv exists in the directory
    if [ -d "$dir/.venv" ]; then
        found_version=""
        found_package=""
        
        # Try to find installed packages from the list
        for pkg in "${packages[@]}"; do
            # Check dist-info directories
            dist_info=$(find "$dir/.venv/lib/python"*/site-packages -maxdepth 1 -name "${pkg}-*.dist-info" -o -name "${pkg//-/_}-*.dist-info" 2>/dev/null | head -1)
            if [ -n "$dist_info" ] && [ -f "$dist_info/METADATA" ]; then
                version=$(grep "^Version:" "$dist_info/METADATA" | cut -d' ' -f2 | head -1)
                if [ -n "$version" ]; then
                    found_version="$version"
                    found_package="$pkg"
                    break
                fi
            fi
        done
        
        # If not found via install.sh packages, fall back to directory-based search
        if [ -z "$found_version" ]; then
            # Find any dist-info that might match the repo name
            for pattern in "${repo_name}" "${repo_name//-/_}" "${repo_name//_/-}"; do
                dist_info=$(find "$dir/.venv/lib/python"*/site-packages -maxdepth 1 -name "*${pattern}*.dist-info" 2>/dev/null | head -1)
                if [ -n "$dist_info" ] && [ -f "$dist_info/METADATA" ]; then
                    version=$(grep "^Version:" "$dist_info/METADATA" | cut -d' ' -f2 | head -1)
                    pkg_name=$(grep "^Name:" "$dist_info/METADATA" | cut -d' ' -f2 | head -1)
                    if [ -n "$version" ]; then
                        found_version="$version"
                        found_package="$pkg_name"
                        break
                    fi
                fi
            done
        fi
        
        # Output result
        if [ -n "$found_version" ]; then
            echo "\"$repo_name\",\"$found_version\",\"$found_package\"" >> "$output_file"
        else
            echo "\"$repo_name\",\"not found\",\"\"" >> "$output_file"
        fi
    else
        echo "\"$repo_name\",\"no .venv\",\"\"" >> "$output_file"
    fi
done

echo "Version catalogue written to $output_file"