#!/bin/bash

# Output CSV file
output_file="../data/oss-agent-makers-catalogue.csv"

# Write CSV header
echo "repo_name,language,format" > "$output_file"

# Find all metadata.json files in oss-agent-makers subdirectories
find .. -name "metadata.json" -type f -not -path "*/scripts/*" -not -path "*/data/*" -not -path "*/logs/*" -not -path "*/extraction/*" | while read -r metadata_file; do
    # Extract repo_name and eval_output from metadata.json
    repo_name=$(jq -r '.repo_name // empty' "$metadata_file" 2>/dev/null)
    eval_output=$(jq -r '.eval_output // empty' "$metadata_file" 2>/dev/null)
    
    # Skip if required fields are missing
    if [ -z "$repo_name" ] || [ -z "$eval_output" ]; then
        continue
    fi
    
    # Parse language and format from eval_output
    # eval_output format is typically: "Format type, Language"
    format=$(echo "$eval_output" | cut -d',' -f1 | xargs)
    language=$(echo "$eval_output" | cut -d',' -f2 | xargs)
    
    # Write to CSV
    echo "\"$repo_name\",\"$language\",\"$format\"" >> "$output_file"
done

echo "Catalogue written to $output_file"