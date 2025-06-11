#!/usr/bin/env python3
"""
DSPy Customer Service Agent Demo
Based on: https://dspy.ai/tutorials/customer_service_agent/
"""

import dspy
from typing import List, Optional
import json

# Configure the language model
lm = dspy.LM('openai/gpt-4o-mini')
dspy.configure(lm=lm)

# 1. Define the Task Signature
class ServiceRequest(dspy.Signature):
    """Answer questions about a software library using provided documentation."""
    
    # Input fields
    question: str = dspy.InputField(desc="User's question about the software")
    documentation: str = dspy.InputField(desc="Relevant documentation context")
    
    # Output field
    answer: str = dspy.OutputField(desc="Helpful and accurate response")

# 2. Build a simple RAG pipeline
class CustomerServiceBot(dspy.Module):
    def __init__(self):
        # Initialize the Chain of Thought module with our signature
        self.generate_answer = dspy.ChainOfThought(ServiceRequest)
    
    def forward(self, question: str, documentation: str = "") -> str:
        """Process a customer service request."""
        # If no documentation provided, use a placeholder
        if not documentation:
            documentation = "No specific documentation available."
        
        # Generate answer using the configured module
        result = self.generate_answer(
            question=question,
            documentation=documentation
        )
        
        return result.answer

# 3. Test the agent
def main():
    # Initialize the customer service bot
    bot = CustomerServiceBot()
    
    # Example documentation context
    sample_docs = """
    DSPy is a framework for algorithmically optimizing LM prompts and weights.
    
    Key features:
    - Signatures: Define input/output behavior declaratively
    - Modules: Composable units that use LMs
    - Optimizers: Algorithms to tune prompts automatically
    - Teleprompt: Automatic prompt engineering
    
    Installation: pip install dspy
    
    Basic usage:
    1. Define a signature (input/output spec)
    2. Use modules like ChainOfThought, ReAct, etc.
    3. Compile with optimizers to improve performance
    """
    
    # Test questions
    test_questions = [
        "How do I install DSPy?",
        "What are the main components of DSPy?",
        "Can you explain what signatures are?",
        "How does DSPy differ from other prompt engineering tools?"
    ]
    
    print("DSPy Customer Service Bot Demo")
    print("=" * 50)
    
    for question in test_questions:
        print(f"\nQ: {question}")
        answer = bot(question=question, documentation=sample_docs)
        print(f"A: {answer}")
        print("-" * 50)
    
    # Interactive mode
    print("\nEntering interactive mode (type 'quit' to exit)")
    while True:
        user_question = input("\nYour question: ")
        if user_question.lower() in ['quit', 'exit', 'q']:
            break
        
        answer = bot(question=user_question, documentation=sample_docs)
        print(f"\nAnswer: {answer}")

if __name__ == "__main__":
    main()