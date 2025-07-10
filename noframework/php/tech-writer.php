#!/usr/bin/env php
<?php
require_once __DIR__ . '/vendor/autoload.php';

use GuzzleHttp\Client;
use Monolog\Logger;
use Monolog\Handler\StreamHandler;
use Symfony\Component\Finder\Finder;

// Constants
const MAX_STEPS = 50;
const TEMPERATURE = 0;
const TEXT_MIME_TYPES = ['application/json', 'application/xml', 'application/javascript'];
const REACT_SYSTEM_PROMPT = 'You are a technical documentation assistant that analyses codebases and generates comprehensive documentation.

When given a directory path and a specific analysis request, you will:
1. Explore the codebase structure to understand its organization
2. Read relevant files to comprehend the implementation details
3. Generate detailed technical documentation based on your analysis

You have access to tools that help you explore and understand codebases:
- find_all_matching_files: Find files matching patterns in directories
- read_file: Read the contents of specific files

Important guidelines:
- Always start by exploring the directory structure to understand the codebase layout
- Read files strategically based on the documentation needs
- Pay attention to configuration files, main entry points, and key modules
- Generate clear, well-structured documentation that would help developers understand the codebase

Use the following format:

Thought: I need to [describe what you need to do next]
Action: [tool_name]
Action Input: {"param1": "value1", "param2": "value2"}
Observation: [tool output will be provided here]
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now have enough information to generate the documentation
Final Answer: [Your complete technical documentation]

Begin your analysis now.';

class TechWriterAgent {
    private $logger;
    private $client;
    private $modelId;
    private $memory = [];
    private $finalAnswer = null;
    private $baseUrl;
    private $apiKey;

    public function __construct($modelName, $baseUrl = null) {
        // Set up logging
        $logDir = __DIR__ . '/logs';
        if (!is_dir($logDir)) {
            mkdir($logDir, 0755, true);
        }
        $this->logger = new Logger('tech-writer');
        $this->logger->pushHandler(new StreamHandler($logDir . '/tech-writer-' . date('Ymd-His') . '.log', Logger::DEBUG));
        
        // Parse model name
        $parts = explode('/', $modelName, 2);
        if (count($parts) !== 2) {
            throw new Exception("Invalid model name format");
        }
        
        $vendor = $parts[0];
        $this->modelId = $parts[1];
        
        // Set up API client based on vendor
        switch ($vendor) {
            case 'google':
                $this->apiKey = getenv('GEMINI_API_KEY');
                if (!$this->apiKey) {
                    throw new Exception("GEMINI_API_KEY environment variable is not set");
                }
                $this->baseUrl = $baseUrl ?: 'https://generativelanguage.googleapis.com/v1beta/openai/';
                break;
            
            case 'openai':
                $this->apiKey = getenv('OPENAI_API_KEY');
                if (!$this->apiKey) {
                    throw new Exception("OPENAI_API_KEY environment variable is not set");
                }
                $this->baseUrl = $baseUrl ?: 'https://api.openai.com/v1/';
                break;
            
            default:
                throw new Exception("Unknown model vendor: $vendor");
        }
        
        $this->client = new Client([
            'base_uri' => $this->baseUrl,
            'headers' => [
                'Authorization' => 'Bearer ' . $this->apiKey,
                'Content-Type' => 'application/json'
            ]
        ]);
    }

    public function run($prompt, $directory) {
        $this->logger->info("Starting ReAct agent with model: {$this->modelId}");
        
        // Initialize conversation
        $this->memory = [
            ['role' => 'system', 'content' => REACT_SYSTEM_PROMPT],
            ['role' => 'user', 'content' => "Base directory for analysis: $directory\n\n$prompt"]
        ];
        
        // ReAct loop
        for ($step = 0; $step < MAX_STEPS; $step++) {
            $this->logger->info("Step " . ($step + 1) . "/" . MAX_STEPS);
            
            try {
                // Get LLM response
                $response = $this->callLLM();
                $this->logger->debug("LLM Response: $response");
                
                // Add assistant response to memory
                $this->memory[] = ['role' => 'assistant', 'content' => $response];
                
                // Parse response
                $parsed = $this->parseResponse($response);
                
                if ($parsed['type'] === 'final') {
                    $this->finalAnswer = $parsed['answer'];
                    $this->logger->info("Final answer received");
                    break;
                } elseif ($parsed['type'] === 'action') {
                    // Execute tool
                    $observation = $this->executeTool($parsed['action'], $parsed['input']);
                    
                    // Add observation to memory
                    $this->memory[] = ['role' => 'user', 'content' => "Observation: $observation"];
                    
                    $this->logger->debug("Tool result: " . strlen($observation) . " chars");
                }
            } catch (Exception $e) {
                $this->logger->error("Error in step " . ($step + 1) . ": " . $e->getMessage());
                throw $e;
            }
        }
        
        if ($this->finalAnswer === null) {
            throw new Exception("Failed to complete analysis within " . MAX_STEPS . " steps");
        }
        
        return $this->finalAnswer;
    }

    private function callLLM() {
        $response = $this->client->post('chat/completions', [
            'json' => [
                'model' => $this->modelId,
                'messages' => $this->memory,
                'temperature' => TEMPERATURE
            ]
        ]);
        
        $data = json_decode($response->getBody(), true);
        return $data['choices'][0]['message']['content'] ?? '';
    }

    private function parseResponse($response) {
        // Check for Final Answer
        if (strpos($response, 'Final Answer:') !== false) {
            $pos = strpos($response, 'Final Answer:');
            $finalAnswer = trim(substr($response, $pos + 13));
            return ['type' => 'final', 'answer' => $finalAnswer];
        }
        
        // Extract Action and Action Input
        $lines = explode("\n", $response);
        $action = null;
        $collectingInput = false;
        $inputLines = [];
        
        foreach ($lines as $line) {
            if (strpos($line, 'Action:') === 0) {
                $action = trim(substr($line, 7));
            } elseif (strpos($line, 'Action Input:') === 0) {
                $collectingInput = true;
                $rest = trim(substr($line, 13));
                if (!empty($rest)) {
                    $inputLines[] = $rest;
                }
            } elseif ($collectingInput) {
                // Stop collecting if we hit another section marker
                if (strpos($line, 'Thought:') === 0 || 
                    strpos($line, 'Action:') === 0 || 
                    strpos($line, 'Observation:') === 0 || 
                    strpos($line, 'Final Answer:') === 0) {
                    break;
                }
                $inputLines[] = $line;
            }
        }
        
        if ($action && !empty($inputLines)) {
            $input = trim(implode("\n", $inputLines));
            return ['type' => 'action', 'action' => $action, 'input' => $input];
        }
        
        return ['type' => 'unknown'];
    }

    private function executeTool($toolName, $actionInput) {
        $this->logger->debug("Executing tool: $toolName with input: $actionInput");
        
        $input = json_decode($actionInput, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            return json_encode(['error' => 'Error parsing input: ' . json_last_error_msg()]);
        }
        
        switch ($toolName) {
            case 'find_all_matching_files':
                $directory = $input['directory'] ?? '';
                $pattern = $input['pattern'] ?? '*';
                return json_encode($this->findAllMatchingFiles($directory, $pattern));
                
            case 'read_file':
                $filePath = $input['file_path'] ?? '';
                return json_encode($this->readFile($filePath));
                
            default:
                return json_encode(['error' => "Unknown tool: $toolName"]);
        }
    }

    private function findAllMatchingFiles($directory, $pattern) {
        $this->logger->info("Tool invoked: find_all_matching_files(directory='$directory', pattern='$pattern')");
        
        if (!is_dir($directory)) {
            $this->logger->error("Directory not found: $directory");
            return [];
        }
        
        $finder = new Finder();
        $finder->files()->in($directory);
        
        // Include dot files (hidden files) - let gitignore handle exclusions
        $finder->ignoreDotFiles(false);
        
        // Always exclude .git directory
        $finder->exclude('.git');
        
        // Handle pattern
        if ($pattern === '*' || $pattern === '*.*') {
            // Match all files
        } elseif (strpos($pattern, '*.') === 0) {
            // Extension pattern
            $ext = substr($pattern, 2);
            $finder->name("*.$ext");
        } else {
            // Exact name
            $finder->name($pattern);
        }
        
        // Respect .gitignore
        if (file_exists($directory . '/.gitignore')) {
            $gitignore = file_get_contents($directory . '/.gitignore');
            $patterns = array_filter(explode("\n", $gitignore), function($line) {
                return !empty($line) && $line[0] !== '#';
            });
            foreach ($patterns as $ignorePattern) {
                $finder->notPath($ignorePattern);
            }
        }
        
        $files = [];
        foreach ($finder as $file) {
            $files[] = $file->getRealPath();
        }
        
        $this->logger->info("Found " . count($files) . " matching files");
        return $files;
    }

    private function readFile($filePath) {
        $this->logger->info("Tool invoked: read_file(file_path='$filePath')");
        
        if (!file_exists($filePath)) {
            return ['error' => "File not found: $filePath"];
        }
        
        // Check if binary
        $finfo = finfo_open(FILEINFO_MIME_TYPE);
        $mimeType = finfo_file($finfo, $filePath);
        finfo_close($finfo);
        
        if (strpos($mimeType, 'text/') !== 0 && !in_array($mimeType, TEXT_MIME_TYPES)) {
            $this->logger->debug("File detected as binary: $filePath");
            return ['error' => "Cannot read binary file: $filePath"];
        }
        
        $content = file_get_contents($filePath);
        if ($content === false) {
            return ['error' => "Failed to read file: $filePath"];
        }
        
        $charCount = strlen($content);
        $this->logger->info("Successfully read file: $filePath ($charCount chars)");
        
        return [
            'file' => $filePath,
            'content' => $content
        ];
    }
}

// Helper functions
function sanitizeFilename($name) {
    return str_replace(['/', '\\', ':', '*', '?', '"', '<', '>', '|'], '-', $name);
}

function saveResults($content, $repoName, $model, $outputDir, $extension, $fileName = null) {
    global $logger;
    
    if (!is_dir($outputDir)) {
        mkdir($outputDir, 0755, true);
    }
    
    if ($fileName) {
        $outputPath = $outputDir . '/' . $fileName;
    } else {
        $timestamp = date('Ymd-His');
        $parts = explode('/', $model, 2);
        $vendor = $parts[0];
        $modelId = sanitizeFilename($parts[1]);
        
        $outputPath = $outputDir . "/$timestamp-$repoName-$vendor-$modelId$extension";
    }
    
    file_put_contents($outputPath, $content);
    $logger->info("Results saved to: $outputPath");
    
    return $outputPath;
}

function createMetadata($outputFile, $model, $repoUrl, $repoName) {
    global $logger;
    
    $metadataFile = preg_replace('/\.[^.]+$/', '.metadata.json', $outputFile);
    
    $metadata = [
        'model' => $model,
        'github_url' => $repoUrl,
        'repo_name' => $repoName,
        'timestamp' => date('c')
    ];
    
    file_put_contents($metadataFile, json_encode($metadata, JSON_PRETTY_PRINT));
    $logger->info("Metadata saved to: $metadataFile");
}

function cloneOrUpdateRepo($repoUrl, $cacheDir) {
    global $logger;
    
    $parts = explode('/', rtrim($repoUrl, '/'));
    $repoName = str_replace('.git', '', end($parts));
    $owner = $parts[count($parts) - 2];
    
    $cacheDir = str_replace('~', $_SERVER['HOME'], $cacheDir);
    $cachePath = "$cacheDir/$owner/$repoName";
    
    if (!is_dir(dirname($cachePath))) {
        mkdir(dirname($cachePath), 0755, true);
    }
    
    if (is_dir("$cachePath/.git")) {
        $logger->info("Updating existing repository: $cachePath");
        exec("cd '$cachePath' && git pull --quiet");
    } else {
        $logger->info("Cloning repository: $repoUrl");
        exec("git clone --quiet '$repoUrl' '$cachePath'");
    }
    
    return $cachePath;
}

// Parse command line arguments
$options = getopt('h', [
    'repo:',
    'prompt:',
    'cache-dir:',
    'output-dir:',
    'extension:',
    'file-name:',
    'model:',
    'base-url:',
    'help'
]);

// Show help
if (isset($options['h']) || isset($options['help'])) {
    echo "Usage: $argv[0] [directory] [options]\n\n";
    echo "Analyse a codebase using an LLM agent.\n\n";
    echo "Positional arguments:\n";
    echo "  directory             Directory containing the codebase to analyse\n\n";
    echo "Options:\n";
    echo "  --repo REPO           GitHub repository URL to clone (e.g. https://github.com/owner/repo)\n";
    echo "  --prompt FILE         Path to a file containing the analysis prompt (required)\n";
    echo "  --cache-dir DIR       Directory to cache cloned repositories (default: ~/.cache/github)\n";
    echo "  --output-dir DIR      Directory to save results to (default: output)\n";
    echo "  --extension EXT       File extension for output files (default: .md)\n";
    echo "  --file-name FILE      Specific file name for output (overrides --extension)\n";
    echo "  --model MODEL         Model to use (format: vendor/model, default: openai/gpt-4o-mini)\n";
    echo "  --base-url URL        Base URL for the API (automatically set based on model if not provided)\n";
    echo "  -h, --help            Show this help message and exit\n\n";
    echo "Dependencies:\n";
    echo "  This script requires environment variables:\n";
    echo "  - OPENAI_API_KEY for OpenAI models\n";
    echo "  - GEMINI_API_KEY for Google models\n";
    exit(0);
}

// Get positional directory argument
$positionalArgs = array_filter($argv, function($arg) {
    return $arg[0] !== '-';
});
array_shift($positionalArgs); // Remove script name
$directory = array_shift($positionalArgs);

// Set defaults
$promptFile = $options['prompt'] ?? null;
$cacheDir = $options['cache-dir'] ?? '~/.cache/github';
$outputDir = $options['output-dir'] ?? 'output';
$extension = $options['extension'] ?? '.md';
$fileName = $options['file-name'] ?? null;
$model = $options['model'] ?? 'openai/gpt-4o-mini';
$baseUrl = $options['base-url'] ?? null;

// Validate arguments
if (!$promptFile) {
    echo "Error: --prompt is required\n";
    exit(1);
}

if (!file_exists($promptFile)) {
    echo "Error: Prompt file not found: $promptFile\n";
    exit(1);
}

// Read prompt
$prompt = file_get_contents($promptFile);

// Set up logging
$logger = new Logger('tech-writer');
$logDir = __DIR__ . '/logs';
if (!is_dir($logDir)) {
    mkdir($logDir, 0755, true);
}
$logger->pushHandler(new StreamHandler($logDir . '/tech-writer-' . date('Ymd-His') . '.log', Logger::DEBUG));
$logger->pushHandler(new StreamHandler('php://stderr', Logger::INFO));

try {
    // Handle repository or directory
    if (isset($options['repo'])) {
        $repoUrl = $options['repo'];
        $directory = cloneOrUpdateRepo($repoUrl, $cacheDir);
        $repoName = basename($repoUrl, '.git');
    } else {
        if (!$directory) {
            $directory = '.';
        }
        if (!is_dir($directory)) {
            echo "Error: Directory not found: $directory\n";
            exit(1);
        }
        $directory = realpath($directory);
        $repoName = basename($directory);
        $repoUrl = '';
    }
    
    // Run the agent
    $agent = new TechWriterAgent($model, $baseUrl);
    $analysisResult = $agent->run($prompt, $directory);
    
    // Save results
    $outputFile = saveResults($analysisResult, $repoName, $model, $outputDir, $extension, $fileName);
    
    // Create metadata
    createMetadata($outputFile, $model, $repoUrl, $repoName);
    
} catch (Exception $e) {
    $logger->error("Analysis failed: " . $e->getMessage());
    exit(1);
}