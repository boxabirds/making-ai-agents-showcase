package main

import (
	"encoding/json"
	"fmt"
	"log"
	"regexp"
	"strings"
)

// ReActAgent implements the ReAct (Reasoning and Acting) pattern
type ReActAgent struct {
	llmClient    LLMClient
	systemPrompt string
	maxIters     int
	verbose      bool
}

// NewReActAgent creates a new ReAct agent
func NewReActAgent(llmClient LLMClient, systemPrompt string, maxIters int, verbose bool) *ReActAgent {
	return &ReActAgent{
		llmClient:    llmClient,
		systemPrompt: systemPrompt,
		maxIters:     maxIters,
		verbose:      verbose,
	}
}

// ToolCall represents a tool invocation
type ToolCall struct {
	Name string                 `json:"name"`
	Args map[string]interface{} `json:"args"`
}

// Run executes the ReAct loop for the given prompt
func (a *ReActAgent) Run(userPrompt string) (string, error) {
	// Build the initial prompt with available tools
	toolDescriptions := a.getToolDescriptions()
	
	conversationHistory := fmt.Sprintf(`You have access to the following tools:

%s

Use the following format:

Thought: reason about what you need to do next
Action: the action to take, should be one of the tool names
Action Input: the input to the action as a JSON object
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now have enough information to provide a final answer
Final Answer: the final answer to the original input question

Begin!

User Request: %s

Thought:`, toolDescriptions, userPrompt)
	
	// ReAct loop
	for i := 0; i < a.maxIters; i++ {
		if a.verbose {
			log.Printf("Iteration %d/%d", i+1, a.maxIters)
		}
		
		// Get LLM response
		response, err := a.llmClient.Complete(conversationHistory, a.systemPrompt, 0.0)
		if err != nil {
			return "", fmt.Errorf("LLM error in iteration %d: %w", i+1, err)
		}
		
		if a.verbose {
			log.Printf("LLM Response:\n%s", response)
		}
		
		// Check if we have a final answer
		if strings.Contains(response, "Final Answer:") {
			// Extract final answer
			parts := strings.Split(response, "Final Answer:")
			if len(parts) >= 2 {
				finalAnswer := strings.TrimSpace(parts[1])
				// Remove any trailing markers
				if idx := strings.Index(finalAnswer, "\nThought:"); idx > 0 {
					finalAnswer = finalAnswer[:idx]
				}
				return finalAnswer, nil
			}
		}
		
		// Parse action and action input
		action, actionInput, err := a.parseAction(response)
		if err != nil {
			// If we can't parse an action, add the response and continue
			conversationHistory += response + "\n"
			continue
		}
		
		if a.verbose {
			log.Printf("Action: %s", action)
			log.Printf("Action Input: %v", actionInput)
		}
		
		// Execute the tool
		observation, err := a.executeTool(action, actionInput)
		if err != nil {
			observation = fmt.Sprintf("Error: %v", err)
		}
		
		if a.verbose {
			log.Printf("Observation: %s", observation)
		}
		
		// Add to conversation history
		conversationHistory += response
		if !strings.HasSuffix(response, "\n") {
			conversationHistory += "\n"
		}
		conversationHistory += fmt.Sprintf("Observation: %s\n", observation)
		conversationHistory += "Thought: "
	}
	
	return "", fmt.Errorf("reached maximum iterations (%d) without finding a final answer", a.maxIters)
}

// getToolDescriptions returns formatted descriptions of available tools
func (a *ReActAgent) getToolDescriptions() string {
	var descriptions []string
	
	descriptions = append(descriptions, `1. find_all_matching_files: Find files matching a pattern while respecting .gitignore
   Arguments:
   - directory (string, required): Directory to search in
   - pattern (string, optional): File pattern to match (glob format), default: "*"
   - respect_gitignore (bool, optional): Whether to respect .gitignore patterns, default: true
   - include_hidden (bool, optional): Whether to include hidden files, default: false
   - include_subdirs (bool, optional): Whether to include subdirectories, default: true`)
	
	descriptions = append(descriptions, `2. read_file: Read the contents of a file
   Arguments:
   - file_path (string, required): Path to the file to read`)
	
	return strings.Join(descriptions, "\n\n")
}

// parseAction extracts action and action input from the response
func (a *ReActAgent) parseAction(response string) (string, map[string]interface{}, error) {
	// Look for Action: and Action Input:
	actionRegex := regexp.MustCompile(`Action:\s*(.+?)(?:\n|$)`)
	inputRegex := regexp.MustCompile(`Action Input:\s*(.+?)(?:\n|$)`)
	
	actionMatch := actionRegex.FindStringSubmatch(response)
	if len(actionMatch) < 2 {
		return "", nil, fmt.Errorf("no action found in response")
	}
	
	inputMatch := inputRegex.FindStringSubmatch(response)
	if len(inputMatch) < 2 {
		return "", nil, fmt.Errorf("no action input found in response")
	}
	
	action := strings.TrimSpace(actionMatch[1])
	inputStr := strings.TrimSpace(inputMatch[1])
	
	// Parse JSON input
	var actionInput map[string]interface{}
	if err := json.Unmarshal([]byte(inputStr), &actionInput); err != nil {
		// Try to handle simple cases where it might not be proper JSON
		// For example: {"file_path": "/path/to/file"}
		return "", nil, fmt.Errorf("error parsing action input as JSON: %w", err)
	}
	
	return action, actionInput, nil
}

// executeTool executes a tool and returns the observation
func (a *ReActAgent) executeTool(toolName string, args map[string]interface{}) (string, error) {
	result, err := ExecuteTool(toolName, args)
	if err != nil {
		return "", err
	}
	return result, nil
}