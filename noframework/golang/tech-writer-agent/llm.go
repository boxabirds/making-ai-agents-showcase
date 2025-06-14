package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// LLMClient interface for different LLM providers
type LLMClient interface {
	Complete(prompt string, systemPrompt string, temperature float32) (string, error)
}

// OpenAIClient implements LLMClient for OpenAI API
type OpenAIClient struct {
	apiKey  string
	model   string
	baseURL string
}

// GeminiClient implements LLMClient for Google Gemini API
type GeminiClient struct {
	apiKey  string
	model   string
	baseURL string
}

// NewLLMClient creates an appropriate LLM client based on the model name
func NewLLMClient(modelName string, baseURL string) (LLMClient, error) {
	// Parse vendor/model format
	parts := strings.Split(modelName, "/")
	if len(parts) != 2 {
		return nil, fmt.Errorf("invalid model format. Expected vendor/model (e.g., openai/gpt-4o-mini)")
	}
	
	vendor := parts[0]
	model := parts[1]
	
	switch vendor {
	case "openai":
		apiKey := os.Getenv("OPENAI_API_KEY")
		if apiKey == "" {
			return nil, fmt.Errorf("OPENAI_API_KEY environment variable not set")
		}
		if baseURL == "" {
			baseURL = "https://api.openai.com/v1"
		}
		return &OpenAIClient{
			apiKey:  apiKey,
			model:   model,
			baseURL: baseURL,
		}, nil
		
	case "google":
		apiKey := os.Getenv("GEMINI_API_KEY")
		if apiKey == "" {
			return nil, fmt.Errorf("GEMINI_API_KEY environment variable not set")
		}
		if baseURL == "" {
			baseURL = "https://generativelanguage.googleapis.com/v1beta/openai"
		}
		return &GeminiClient{
			apiKey:  apiKey,
			model:   model,
			baseURL: baseURL,
		}, nil
		
	default:
		return nil, fmt.Errorf("unsupported vendor: %s", vendor)
	}
}

// OpenAI API structures
type OpenAIRequest struct {
	Model       string                 `json:"model"`
	Messages    []OpenAIMessage        `json:"messages"`
	Temperature float32                `json:"temperature"`
}

type OpenAIMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type OpenAIResponse struct {
	Choices []struct {
		Message OpenAIMessage `json:"message"`
	} `json:"choices"`
	Error *struct {
		Message string `json:"message"`
		Type    string `json:"type"`
	} `json:"error,omitempty"`
}

// Complete implements the LLMClient interface for OpenAI
func (c *OpenAIClient) Complete(prompt string, systemPrompt string, temperature float32) (string, error) {
	messages := []OpenAIMessage{
		{Role: "system", Content: systemPrompt},
		{Role: "user", Content: prompt},
	}
	
	reqBody := OpenAIRequest{
		Model:       c.model,
		Messages:    messages,
		Temperature: temperature,
	}
	
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("error marshaling request: %w", err)
	}
	
	req, err := http.NewRequest("POST", c.baseURL+"/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("error creating request: %w", err)
	}
	
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	
	client := &http.Client{Timeout: 300 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("error making request: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("error reading response: %w", err)
	}
	
	var openAIResp OpenAIResponse
	if err := json.Unmarshal(body, &openAIResp); err != nil {
		return "", fmt.Errorf("error parsing response: %w", err)
	}
	
	if openAIResp.Error != nil {
		return "", fmt.Errorf("API error: %s", openAIResp.Error.Message)
	}
	
	if len(openAIResp.Choices) == 0 {
		return "", fmt.Errorf("no response choices returned")
	}
	
	return openAIResp.Choices[0].Message.Content, nil
}

// Complete implements the LLMClient interface for Gemini
func (c *GeminiClient) Complete(prompt string, systemPrompt string, temperature float32) (string, error) {
	// Gemini uses the same OpenAI-compatible API through the compatibility endpoint
	messages := []OpenAIMessage{
		{Role: "system", Content: systemPrompt},
		{Role: "user", Content: prompt},
	}
	
	reqBody := OpenAIRequest{
		Model:       c.model,
		Messages:    messages,
		Temperature: temperature,
	}
	
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("error marshaling request: %w", err)
	}
	
	req, err := http.NewRequest("POST", c.baseURL+"/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("error creating request: %w", err)
	}
	
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	
	client := &http.Client{Timeout: 300 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("error making request: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("error reading response: %w", err)
	}
	
	var openAIResp OpenAIResponse
	if err := json.Unmarshal(body, &openAIResp); err != nil {
		return "", fmt.Errorf("error parsing response: %w", err)
	}
	
	if openAIResp.Error != nil {
		return "", fmt.Errorf("API error: %s", openAIResp.Error.Message)
	}
	
	if len(openAIResp.Choices) == 0 {
		return "", fmt.Errorf("no response choices returned")
	}
	
	return openAIResp.Choices[0].Message.Content, nil
}