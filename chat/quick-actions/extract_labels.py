#!/usr/bin/env python3
"""Extract training data from report.md headings."""

import re
import json
from pathlib import Path

def extract_headings_with_labels(markdown_path):
    """Extract H1 and H2 headings with their parenthetical labels."""
    with open(markdown_path, 'r') as f:
        content = f.read()
    
    # Pattern to match headings with optional parenthetical labels
    pattern = r'^(#{1,2})\s+(.+?)(?:\s*\(([^)]+)\))?\s*$'
    
    training_data = []
    
    for line in content.split('\n'):
        match = re.match(pattern, line)
        if match:
            level = len(match.group(1))  # 1 for H1, 2 for H2
            full_text = match.group(2).strip()
            label = match.group(3) if match.group(3) else None
            
            if label:  # Only include headings that have labels
                training_data.append({
                    'level': level,
                    'full_heading': full_text,
                    'short_label': label,
                    'original_line': line.strip()
                })
    
    return training_data

def main():
    # Path to report-with-quick-actions.md
    report_path = Path(__file__).parent / 'sources/report-with-quick-actions.md'
    
    # Extract training data
    data = extract_headings_with_labels(report_path)
    
    # Save as JSON for training
    output_path = Path(__file__).parent / 'output/training_data.json'
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Print summary
    print(f"Extracted {len(data)} labeled headings:")
    print(f"- H1 headings: {sum(1 for d in data if d['level'] == 1)}")
    print(f"- H2 headings: {sum(1 for d in data if d['level'] == 2)}")
    print(f"\nSaved to: {output_path}")
    
    # Show some examples
    print("\nExamples:")
    for item in data[:5]:
        print(f"  '{item['full_heading']}' -> '{item['short_label']}'")

if __name__ == "__main__":
    main()