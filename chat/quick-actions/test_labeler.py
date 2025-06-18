#!/usr/bin/env python3
"""Test the trained label generator on new headings."""

import os
import dspy
from train_labeler import LabelGenerator

# Configure DSPy
lm = dspy.LM(
    model=os.environ.get("MODEL", "openai/gpt-4o-mini"),
    temperature=0.7,
)
dspy.configure(lm=lm)

def main():
    # Load the optimized model
    model = LabelGenerator()
    model.load('output/optimized_label_generator.json')
    
    # Test headings without labels
    test_headings = [
        "Introduction to Machine Learning",
        "How to Configure Your Development Environment",
        "Understanding the Core Architecture",
        "Frequently Asked Questions",
        "API Authentication and Security",
        "Building Your First Application",
        "Advanced Configuration Options",
        "Debugging Common Issues",
        "Performance Optimization Techniques",
        "Deployment Best Practices"
    ]
    
    print("Testing label generation on new headings:\n")
    
    for heading in test_headings:
        pred = model(heading=heading)
        print(f"Heading: '{heading}'")
        print(f"Generated Label: '{pred.label}'")
        print()
    
    # Show the prompt using inspect_history
    print("\n--- Prompt Structure ---")
    print("To see the exact prompt used, DSPy provides inspect_history:")
    print()
    dspy.inspect_history(n=1)

if __name__ == "__main__":
    main()