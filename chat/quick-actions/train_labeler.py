#!/usr/bin/env python3
"""Train a DSPy model to generate short labels from headings."""

import os
import json
import dspy
from pathlib import Path

# Configure DSPy with OpenAI
lm = dspy.LM(
    model=os.environ.get("MODEL", "openai/gpt-4o-mini"),
    temperature=0.7,
)
dspy.configure(lm=lm)

class GenerateLabel(dspy.Signature):
    """Generate a short, concise label (1-3 words) for a section heading that will be used as a quick action button."""
    
    heading: str = dspy.InputField(desc="The full section heading text")
    label: str = dspy.OutputField(desc="A short 1-3 word label suitable for a navigation button")

class LabelGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(GenerateLabel)
    
    def forward(self, heading):
        return self.generate(heading=heading)

def load_training_data():
    """Load the training data extracted from report.md."""
    data_path = Path(__file__).parent / 'output/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Convert to DSPy examples
    examples = []
    for item in data:
        example = dspy.Example(
            heading=item['full_heading'],
            label=item['short_label']
        ).with_inputs('heading')
        examples.append(example)
    
    return examples

def evaluate_exact_match(example, prediction, trace=None):
    """Simple evaluation metric."""
    return prediction.label.strip().lower() == example.label.strip().lower()

def main():
    # Load training data
    print("Loading training data...")
    examples = load_training_data()
    print(f"Loaded {len(examples)} examples")
    
    # Split into train/test
    train_examples = examples[:int(len(examples) * 0.8)]
    test_examples = examples[int(len(examples) * 0.8):]
    
    print(f"Training set: {len(train_examples)} examples")
    print(f"Test set: {len(test_examples)} examples")
    
    # Create model
    model = LabelGenerator()
    
    # Test before optimization
    print("\n--- Before optimization ---")
    for ex in test_examples[:3]:
        pred = model(heading=ex.heading)
        print(f"Input: '{ex.heading}'")
        print(f"Expected: '{ex.label}'")
        print(f"Predicted: '{pred.label}'")
        print()
    
    # Optimize with BootstrapFewShot
    print("Optimizing model...")
    optimizer = dspy.BootstrapFewShot(
        metric=evaluate_exact_match,
        max_bootstrapped_demos=4,
        max_labeled_demos=4,
    )
    
    optimized_model = optimizer.compile(model, trainset=train_examples)
    
    # Test after optimization
    print("\n--- After optimization ---")
    correct = 0
    for ex in test_examples:
        pred = optimized_model(heading=ex.heading)
        if pred.label.strip().lower() == ex.label.strip().lower():
            correct += 1
        if test_examples.index(ex) < 3:  # Show first 3
            print(f"Input: '{ex.heading}'")
            print(f"Expected: '{ex.label}'")
            print(f"Predicted: '{pred.label}'")
            print()
    
    print(f"Accuracy: {correct}/{len(test_examples)} = {correct/len(test_examples)*100:.1f}%")
    
    # Save the optimized model
    optimized_model.save('output/optimized_label_generator.json')
    print("\nModel saved to: output/optimized_label_generator.json")
    
    # Inspect the optimized prompt using the correct method
    print("\n--- Optimized Prompt ---")
    
    # According to DSPy docs, use lm.history directly
    print(f"Total LM calls: {len(lm.history)}")
    
    # Access the last call
    if lm.history:
        last_call = lm.history[-1]
        print(f"\nLast call keys: {list(last_call.keys())}")
        
        # Save the full last call
        with open('output/lm_history_full.json', 'w') as f:
            import json
            json.dump(last_call, f, indent=2, default=str)
        print("\nFull lm.history[-1] saved to: output/lm_history_full.json")
        
        # Now use inspect_history to get a formatted view
        print("\n--- Formatted history using lm.inspect_history(n=1) ---")
        lm.inspect_history(n=1)  # This prints the formatted history
    
    # Save the optimized prompt structure
    try:
        prompt_info = {
            "signature": str(optimized_model.generate.signature),
            "demos": optimized_model.generate.demos if hasattr(optimized_model.generate, 'demos') else None
        }
        with open('output/optimized_prompt_structure.json', 'w') as f:
            import json
            json.dump(prompt_info, f, indent=2, default=str)
        print("\nOptimized prompt structure saved to: output/optimized_prompt_structure.json")
    except Exception as e:
        print(f"Error saving prompt structure: {e}")

if __name__ == "__main__":
    main()