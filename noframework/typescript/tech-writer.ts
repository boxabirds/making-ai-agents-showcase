#!/usr/bin/env bun
import OpenAI from 'openai';
import * as fs from 'fs';
import * as path from 'path';
import minimist from 'minimist';
import { execSync } from 'child_process';
import { glob } from 'glob';

// Constants
const MAX_STEPS = 50;
const CACHE_DIR = path.join(process.env.HOME || '', '.cache/github');

// Environment variables
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

// ANSI color codes
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const BLUE = '\x1b[34m';
const NC = '\x1b[0m'; // No Color

// System prompt
const REACT_SYSTEM_PROMPT = `You are a technical documentation assistant that analyses codebases and generates comprehensive documentation.

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

Begin your analysis now.`;

// Logging
class Logger {
  private logFile: string;
  private logDir: string;

  constructor() {
    this.logDir = path.join(process.cwd(), 'logs');
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    this.logFile = path.join(this.logDir, `tech-writer-${timestamp}.log`);
  }

  private log(level: string, message: string) {
    const timestamp = new Date().toISOString();
    const logEntry = `${timestamp} - ${level} - ${message}\n`;
    fs.appendFileSync(this.logFile, logEntry);
    console.error(`${timestamp} - ${level} - ${message}`);
  }

  info(message: string) {
    this.log('INFO', message);
  }

  error(message: string) {
    this.log('ERROR', message);
  }

  debug(message: string) {
    this.log('DEBUG', message);
  }
}

const logger = new Logger();

// Utility functions
function sanitizeFilename(name: string): string {
  return name.replace(/[/\\:*?"<>|]/g, '-');
}

function jsonEscape(text: string): string {
  return JSON.stringify(text);
}

// Tool: find_all_matching_files
function findAllMatchingFiles(
  directory: string,
  pattern: string = '*',
  respectGitignore: boolean = true,
  includeHidden: boolean = false,
  includeSubdirs: boolean = true
): string[] {
  logger.info(`Tool invoked: find_all_matching_files(directory='${directory}', pattern='${pattern}', respect_gitignore=${respectGitignore}, include_hidden=${includeHidden}, include_subdirs=${includeSubdirs})`);

  if (!fs.existsSync(directory)) {
    logger.error(`Directory not found: ${directory}`);
    return [];
  }

  const absoluteDir = path.resolve(directory);
  const results: string[] = [];

  try {
    // Read .gitignore patterns if needed
    let gitignorePatterns: string[] = ['.git/**'];  // Always ignore .git directory
    if (respectGitignore) {
      const gitignorePath = path.join(absoluteDir, '.gitignore');
      if (fs.existsSync(gitignorePath)) {
        const rawPatterns = fs.readFileSync(gitignorePath, 'utf-8')
          .split('\n')
          .filter(line => line.trim() && !line.startsWith('#'))
          .map(line => line.trim());
        
        // Convert gitignore patterns to glob patterns
        for (const pattern of rawPatterns) {
          if (pattern.startsWith('!')) continue; // Skip negations for now
          
          if (pattern.endsWith('/')) {
            // Directory pattern
            gitignorePatterns.push(pattern + '**');
            gitignorePatterns.push('**/' + pattern + '**');
          } else if (!pattern.includes('/')) {
            // Simple filename/pattern - should match in any directory
            gitignorePatterns.push(pattern);
            gitignorePatterns.push('**/' + pattern);
          } else if (pattern.startsWith('/')) {
            // Root-relative pattern
            gitignorePatterns.push(pattern.substring(1));
          } else {
            // Other patterns
            gitignorePatterns.push(pattern);
            gitignorePatterns.push('**/' + pattern);
          }
        }
      }
    }

    // Use glob to find files
    const globPattern = includeSubdirs 
      ? (pattern === '*' ? '**/*' : `**/${pattern}`)
      : pattern;
    const options = {
      cwd: absoluteDir,
      dot: true,  // Always include hidden files, let gitignore handle exclusions
      ignore: respectGitignore ? gitignorePatterns : undefined,
      nodir: true
    };

    const files = glob.sync(globPattern, options);
    
    for (const file of files) {
      const fullPath = path.join(absoluteDir, file);
      results.push(fullPath);
    }

    logger.info(`Found ${results.length} matching files`);
    return results;
  } catch (error) {
    logger.error(`Error finding files: ${error}`);
    return [];
  }
}

// Tool: read_file
function readFile(filePath: string): { file?: string; content?: string; error?: string } {
  logger.info(`Tool invoked: read_file(file_path='${filePath}')`);

  if (!fs.existsSync(filePath)) {
    return { error: `File not found: ${filePath}` };
  }

  try {
    // Check if file is binary
    const buffer = fs.readFileSync(filePath);
    const isBinary = buffer.includes(0);
    
    if (isBinary) {
      logger.debug(`File detected as binary: ${filePath}`);
      return { error: `Cannot read binary file: ${filePath}` };
    }

    const content = buffer.toString('utf-8');
    const charCount = content.length;
    logger.info(`Successfully read file: ${filePath} (${charCount} chars)`);

    return { file: filePath, content };
  } catch (error) {
    return { error: `Failed to read file: ${filePath}` };
  }
}

// Execute tool based on parsed action
function executeTool(toolName: string, actionInput: string): string {
  logger.debug(`Executing tool: ${toolName} with input: ${actionInput}`);

  try {
    const input = JSON.parse(actionInput);
    
    switch (toolName) {
      case 'find_all_matching_files': {
        const directory = input.directory || '';
        const pattern = input.pattern || '*';
        const files = findAllMatchingFiles(directory, pattern);
        return JSON.stringify(files);
      }
      case 'read_file': {
        const filePath = input.file_path || '';
        const result = readFile(filePath);
        return JSON.stringify(result);
      }
      default:
        return JSON.stringify({ error: `Unknown tool: ${toolName}` });
    }
  } catch (error) {
    return JSON.stringify({ error: `Error executing tool: ${error}` });
  }
}

// Parse LLM response
function parseResponse(response: string): { type: 'final' | 'action' | 'unknown'; action?: string; input?: string; finalAnswer?: string } {
  // Check for Final Answer
  if (response.includes('Final Answer:')) {
    const match = response.match(/Final Answer:\s*([\s\S]*)/);
    if (match) {
      return { type: 'final', finalAnswer: match[1].trim() };
    }
  }

  // Extract Action and Action Input
  const actionMatch = response.match(/^Action:\s*(.+)$/m);
  const inputMatch = response.match(/^Action Input:\s*([\s\S]*?)(?=^(?:Thought:|Action:|Observation:|Final Answer:)|\s*$)/m);

  if (actionMatch && inputMatch) {
    return {
      type: 'action',
      action: actionMatch[1].trim(),
      input: inputMatch[1].trim()
    };
  }

  return { type: 'unknown' };
}

// Main ReAct agent
class TechWriterAgent {
  private client: OpenAI;
  private modelId: string;
  private memory: OpenAI.ChatCompletionMessageParam[] = [];
  private finalAnswer: string | null = null;

  constructor(modelName: string, baseUrl?: string) {
    const [vendor, modelId] = modelName.split('/', 2);
    this.modelId = modelId;

    // Initialize OpenAI client based on vendor
    if (vendor === 'google') {
      if (!GEMINI_API_KEY) {
        throw new Error('GEMINI_API_KEY environment variable is not set');
      }
      this.client = new OpenAI({
        apiKey: GEMINI_API_KEY,
        baseURL: baseUrl || 'https://generativelanguage.googleapis.com/v1beta/openai/'
      });
    } else if (vendor === 'openai') {
      if (!OPENAI_API_KEY) {
        throw new Error('OPENAI_API_KEY environment variable is not set');
      }
      this.client = new OpenAI({
        apiKey: OPENAI_API_KEY,
        baseURL: baseUrl
      });
    } else {
      throw new Error(`Unknown model vendor: ${vendor}`);
    }
  }

  async run(prompt: string, directory: string): Promise<string> {
    logger.info(`Starting ReAct agent with model: ${this.modelId}`);

    // Initialize conversation
    this.memory = [
      { role: 'system', content: REACT_SYSTEM_PROMPT },
      { role: 'user', content: `Base directory for analysis: ${directory}\n\n${prompt}` }
    ];

    // ReAct loop
    for (let step = 0; step < MAX_STEPS; step++) {
      logger.info(`Step ${step + 1}/${MAX_STEPS}`);

      try {
        // Get LLM response
        const completion = await this.client.chat.completions.create({
          model: this.modelId,
          messages: this.memory,
          temperature: 0
        });

        const response = completion.choices[0].message.content || '';
        logger.debug(`LLM Response: ${response}`);

        // Add assistant response to memory
        this.memory.push({ role: 'assistant', content: response });

        // Parse response
        const parsed = parseResponse(response);

        if (parsed.type === 'final' && parsed.finalAnswer) {
          this.finalAnswer = parsed.finalAnswer;
          logger.info('Final answer received');
          break;
        } else if (parsed.type === 'action' && parsed.action && parsed.input) {
          // Execute tool
          const observation = executeTool(parsed.action, parsed.input);
          
          // Add observation to memory
          this.memory.push({ role: 'user', content: `Observation: ${observation}` });
          
          logger.debug(`Tool result: ${observation.length} chars`);
        }
      } catch (error) {
        logger.error(`Error in step ${step + 1}: ${error}`);
        throw error;
      }
    }

    if (!this.finalAnswer) {
      throw new Error(`Failed to complete analysis within ${MAX_STEPS} steps`);
    }

    return this.finalAnswer;
  }
}

// Save results
function saveResults(
  content: string,
  repoName: string,
  model: string,
  outputDir: string,
  extension: string,
  fileName?: string
): string {
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5).replace('T', '-');
  const [vendor, modelId] = model.split('/', 2);
  const safeModel = sanitizeFilename(modelId);

  const outputFile = fileName
    ? path.join(outputDir, fileName)
    : path.join(outputDir, `${timestamp}-${repoName}-${vendor}-${safeModel}${extension}`);

  fs.writeFileSync(outputFile, content);
  logger.info(`Results saved to: ${outputFile}`);
  return outputFile;
}

// Create metadata
function createMetadata(
  outputFile: string,
  model: string,
  repoUrl: string,
  repoName: string
): void {
  const metadataFile = outputFile.replace(path.extname(outputFile), '.metadata.json');
  const metadata = {
    model,
    github_url: repoUrl,
    repo_name: repoName,
    timestamp: new Date().toISOString()
  };

  fs.writeFileSync(metadataFile, JSON.stringify(metadata, null, 2));
  logger.info(`Metadata saved to: ${metadataFile}`);
}

// Clone or update repository
function cloneOrUpdateRepo(repoUrl: string): string {
  const repoName = path.basename(repoUrl, '.git');
  const owner = path.basename(path.dirname(repoUrl));
  const cachePath = path.join(CACHE_DIR, owner, repoName);

  if (!fs.existsSync(path.dirname(cachePath))) {
    fs.mkdirSync(path.dirname(cachePath), { recursive: true });
  }

  if (fs.existsSync(path.join(cachePath, '.git'))) {
    logger.info(`Updating existing repository: ${cachePath}`);
    execSync('git pull --quiet', { cwd: cachePath });
  } else {
    logger.info(`Cloning repository: ${repoUrl}`);
    execSync(`git clone --quiet "${repoUrl}" "${cachePath}"`);
  }

  return cachePath;
}

// Main function
async function main() {
  const args = minimist(process.argv.slice(2), {
    string: ['repo', 'cache-dir', 'output-dir', 'extension', 'file-name', 'model', 'base-url', 'prompt'],
    alias: {
      h: 'help'
    },
    default: {
      'cache-dir': CACHE_DIR,
      'output-dir': 'output',
      'extension': '.md',
      'model': 'openai/gpt-4o-mini'
    }
  });

  if (args.help) {
    console.log(`Usage: ${process.argv[1]} [directory] [options]

Analyse a codebase using an LLM agent.

Positional arguments:
  directory             Directory containing the codebase to analyse

Options:
  --repo REPO           GitHub repository URL to clone (e.g. https://github.com/owner/repo)
  --prompt FILE         Path to a file containing the analysis prompt (required)
  --cache-dir DIR       Directory to cache cloned repositories (default: ~/.cache/github)
  --output-dir DIR      Directory to save results to (default: output)
  --extension EXT       File extension for output files (default: .md)
  --file-name FILE      Specific file name for output (overrides --extension)
  --model MODEL         Model to use (format: vendor/model, default: openai/gpt-4o-mini)
  --base-url URL        Base URL for the API (automatically set based on model if not provided)
  -h, --help            Show this help message and exit

Dependencies:
  This script requires environment variables:
  - OPENAI_API_KEY for OpenAI models
  - GEMINI_API_KEY for Google models`);
    process.exit(0);
  }

  // Validate arguments
  if (!args.prompt) {
    console.error('Error: --prompt is required');
    process.exit(1);
  }

  if (!fs.existsSync(args.prompt)) {
    console.error(`Error: Prompt file not found: ${args.prompt}`);
    process.exit(1);
  }

  // Read prompt
  const prompt = fs.readFileSync(args.prompt, 'utf-8');

  // Handle repository or directory
  let directory: string;
  let repoUrl = '';
  let repoName: string;

  if (args.repo) {
    directory = cloneOrUpdateRepo(args.repo);
    repoUrl = args.repo;
    repoName = path.basename(args.repo, '.git');
  } else {
    directory = args._[0] || '.';
    if (!fs.existsSync(directory)) {
      console.error(`Error: Directory not found: ${directory}`);
      process.exit(1);
    }
    directory = path.resolve(directory);
    repoName = path.basename(directory);
  }

  try {
    // Run the agent
    const agent = new TechWriterAgent(args.model, args['base-url']);
    const analysisResult = await agent.run(prompt, directory);

    // Save results
    const outputFile = saveResults(
      analysisResult,
      repoName,
      args.model,
      args['output-dir'],
      args.extension,
      args['file-name']
    );

    // Create metadata
    createMetadata(outputFile, args.model, repoUrl, repoName);
  } catch (error) {
    logger.error(`Analysis failed: ${error}`);
    process.exit(1);
  }
}

// Run main function
if (import.meta.main) {
  main().catch(error => {
    console.error(`Error: ${error}`);
    process.exit(1);
  });
}