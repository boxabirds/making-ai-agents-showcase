use anyhow::{Context, Result};
use async_openai::{
    config::OpenAIConfig,
    types::{
        ChatCompletionRequestMessage, ChatCompletionRequestSystemMessageArgs,
        ChatCompletionRequestUserMessageArgs, ChatCompletionRequestAssistantMessageArgs,
        CreateChatCompletionRequestArgs,
    },
    Client,
};
use chrono::Local;
use clap::Parser;
use ignore::WalkBuilder;
use serde::{Deserialize, Serialize};
use std::{
    env,
    fs,
    io::Write,
    path::{Path, PathBuf},
    process::Command,
};

const MAX_STEPS: usize = 15;
const REACT_SYSTEM_PROMPT: &str = r#"You are a technical documentation assistant that analyses codebases and generates comprehensive documentation.

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

Begin your analysis now."#;

#[derive(Parser, Debug)]
#[command(author, version, about = "Analyse a codebase using an LLM agent", long_about = None)]
struct Args {
    /// Directory containing the codebase to analyse
    directory: Option<String>,

    /// GitHub repository URL to clone (e.g. https://github.com/owner/repo)
    #[arg(long)]
    repo: Option<String>,

    /// Path to a file containing the analysis prompt
    #[arg(long, required = true)]
    prompt: String,

    /// Directory to cache cloned repositories
    #[arg(long, default_value = "~/.cache/github")]
    cache_dir: String,

    /// Directory to save results to
    #[arg(long, default_value = "output")]
    output_dir: String,

    /// File extension for output files
    #[arg(long, default_value = ".md")]
    extension: String,

    /// Specific file name for output (overrides --extension)
    #[arg(long)]
    file_name: Option<String>,

    /// Model to use (format: vendor/model)
    #[arg(long, default_value = "openai/gpt-4o-mini")]
    model: String,

    /// Base URL for the API (automatically set based on model if not provided)
    #[arg(long)]
    base_url: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ToolInput {
    directory: Option<String>,
    pattern: Option<String>,
    file_path: Option<String>,
}

#[derive(Debug, Serialize)]
struct FileReadResult {
    #[serde(skip_serializing_if = "Option::is_none")]
    file: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

#[derive(Debug, Serialize)]
struct Metadata {
    model: String,
    github_url: String,
    repo_name: String,
    timestamp: String,
}

struct Logger {
    log_file: PathBuf,
}

impl Logger {
    fn new() -> Result<Self> {
        let log_dir = Path::new("logs");
        fs::create_dir_all(log_dir)?;
        
        let timestamp = Local::now().format("%Y%m%d-%H%M%S");
        let log_file = log_dir.join(format!("tech-writer-{}.log", timestamp));
        
        Ok(Self { log_file })
    }

    fn log(&self, level: &str, message: &str) -> Result<()> {
        let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S");
        let log_entry = format!("{} - {} - {}\n", timestamp, level, message);
        
        let mut file = fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.log_file)?;
        file.write_all(log_entry.as_bytes())?;
        
        eprintln!("{}", log_entry.trim_end());
        Ok(())
    }

    fn info(&self, message: &str) -> Result<()> {
        self.log("INFO", message)
    }

    fn error(&self, message: &str) -> Result<()> {
        self.log("ERROR", message)
    }

    fn debug(&self, message: &str) -> Result<()> {
        self.log("DEBUG", message)
    }
}

fn sanitize_filename(name: &str) -> String {
    name.chars()
        .map(|c| match c {
            '/' | '\\' | ':' | '*' | '?' | '"' | '<' | '>' | '|' => '-',
            _ => c,
        })
        .collect()
}

fn find_all_matching_files(
    directory: &str,
    pattern: &str,
    logger: &Logger,
) -> Result<Vec<String>> {
    logger.info(&format!(
        "Tool invoked: find_all_matching_files(directory='{}', pattern='{}')",
        directory, pattern
    ))?;

    let dir_path = Path::new(directory);
    if !dir_path.exists() {
        logger.error(&format!("Directory not found: {}", directory))?;
        return Ok(vec![]);
    }

    let mut files = Vec::new();
    let walker = WalkBuilder::new(dir_path)
        .hidden(false)
        .git_ignore(true)
        .build();

    for entry in walker {
        let entry = entry?;
        let path = entry.path();
        
        if path.is_file() {
            let file_name = path.file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("");
            
            // Simple glob matching
            let matches = if pattern == "*" || pattern == "*.*" {
                true
            } else if pattern.starts_with("*.") {
                let ext = &pattern[2..];
                file_name.ends_with(&format!(".{}", ext))
            } else {
                file_name == pattern
            };
            
            if matches {
                files.push(path.to_string_lossy().to_string());
            }
        }
    }

    logger.info(&format!("Found {} matching files", files.len()))?;
    Ok(files)
}

fn read_file(file_path: &str, logger: &Logger) -> Result<FileReadResult> {
    logger.info(&format!("Tool invoked: read_file(file_path='{}')", file_path))?;

    let path = Path::new(file_path);
    if !path.exists() {
        return Ok(FileReadResult {
            file: None,
            content: None,
            error: Some(format!("File not found: {}", file_path)),
        });
    }

    match fs::read(path) {
        Ok(bytes) => {
            // Check if binary
            if bytes.contains(&0) {
                logger.debug(&format!("File detected as binary: {}", file_path))?;
                return Ok(FileReadResult {
                    file: None,
                    content: None,
                    error: Some(format!("Cannot read binary file: {}", file_path)),
                });
            }

            match String::from_utf8(bytes) {
                Ok(content) => {
                    let char_count = content.len();
                    logger.info(&format!(
                        "Successfully read file: {} ({} chars)",
                        file_path, char_count
                    ))?;
                    Ok(FileReadResult {
                        file: Some(file_path.to_string()),
                        content: Some(content),
                        error: None,
                    })
                }
                Err(_) => Ok(FileReadResult {
                    file: None,
                    content: None,
                    error: Some(format!("Cannot decode file as UTF-8: {}", file_path)),
                }),
            }
        }
        Err(e) => Ok(FileReadResult {
            file: None,
            content: None,
            error: Some(format!("Failed to read file: {}", e)),
        }),
    }
}

fn execute_tool(tool_name: &str, action_input: &str, logger: &Logger) -> Result<String> {
    logger.debug(&format!(
        "Executing tool: {} with input: {}",
        tool_name, action_input
    ))?;

    let input: ToolInput = match serde_json::from_str(action_input) {
        Ok(input) => input,
        Err(e) => return Ok(serde_json::to_string(&serde_json::json!({
            "error": format!("Error parsing input: {}", e)
        }))?),
    };

    match tool_name {
        "find_all_matching_files" => {
            let directory = input.directory.unwrap_or_default();
            let pattern = input.pattern.unwrap_or_else(|| "*".to_string());
            let files = find_all_matching_files(&directory, &pattern, logger)?;
            Ok(serde_json::to_string(&files)?)
        }
        "read_file" => {
            let file_path = input.file_path.unwrap_or_default();
            let result = read_file(&file_path, logger)?;
            Ok(serde_json::to_string(&result)?)
        }
        _ => Ok(serde_json::to_string(&serde_json::json!({
            "error": format!("Unknown tool: {}", tool_name)
        }))?),
    }
}

#[derive(Debug)]
enum ParsedResponse {
    Final(String),
    Action { action: String, input: String },
    Unknown,
}

fn parse_response(response: &str) -> ParsedResponse {
    // Check for Final Answer
    if response.contains("Final Answer:") {
        if let Some(pos) = response.find("Final Answer:") {
            let final_answer = response[pos + 13..].trim().to_string();
            return ParsedResponse::Final(final_answer);
        }
    }

    // Extract Action and Action Input
    let lines: Vec<&str> = response.lines().collect();
    let mut action: Option<String> = None;
    let mut collecting_input = false;
    let mut input_lines = Vec::new();
    
    for line in lines.iter() {
        if line.starts_with("Action:") {
            action = Some(line[7..].trim().to_string());
        } else if line.starts_with("Action Input:") {
            collecting_input = true;
            // Start collecting from the rest of this line if there's content
            let rest = line[13..].trim();
            if !rest.is_empty() {
                input_lines.push(rest);
            }
        } else if collecting_input {
            // Stop collecting if we hit another section marker
            if line.starts_with("Thought:") || 
               line.starts_with("Action:") || 
               line.starts_with("Observation:") || 
               line.starts_with("Final Answer:") {
                break;
            }
            input_lines.push(line);
        }
    }
    
    if let Some(action) = action {
        if !input_lines.is_empty() {
            let input = input_lines.join("\n").trim().to_string();
            return ParsedResponse::Action { action, input };
        }
    }

    ParsedResponse::Unknown
}

struct TechWriterAgent {
    client: Client<OpenAIConfig>,
    model_id: String,
    logger: Logger,
}

impl TechWriterAgent {
    fn new(model_name: &str, base_url: Option<String>) -> Result<Self> {
        let parts: Vec<&str> = model_name.split('/').collect();
        if parts.len() != 2 {
            return Err(anyhow::anyhow!("Invalid model name format"));
        }
        
        let vendor = parts[0];
        let model_id = parts[1].to_string();
        
        let config = match vendor {
            "google" => {
                let api_key = env::var("GEMINI_API_KEY")
                    .context("GEMINI_API_KEY environment variable is not set")?;
                let base_url = base_url.unwrap_or_else(|| 
                    "https://generativelanguage.googleapis.com/v1beta/openai/".to_string()
                );
                OpenAIConfig::new()
                    .with_api_key(api_key)
                    .with_api_base(base_url)
            }
            "openai" => {
                let api_key = env::var("OPENAI_API_KEY")
                    .context("OPENAI_API_KEY environment variable is not set")?;
                let mut config = OpenAIConfig::new().with_api_key(api_key);
                if let Some(url) = base_url {
                    config = config.with_api_base(url);
                }
                config
            }
            _ => return Err(anyhow::anyhow!("Unknown model vendor: {}", vendor)),
        };
        
        let client = Client::with_config(config);
        let logger = Logger::new()?;
        
        Ok(Self {
            client,
            model_id,
            logger,
        })
    }

    async fn run(&self, prompt: &str, directory: &str) -> Result<String> {
        self.logger.info(&format!("Starting ReAct agent with model: {}", self.model_id))?;
        
        let mut messages = vec![
            ChatCompletionRequestMessage::System(
                ChatCompletionRequestSystemMessageArgs::default()
                    .content(REACT_SYSTEM_PROMPT)
                    .build()?
            ),
            ChatCompletionRequestMessage::User(
                ChatCompletionRequestUserMessageArgs::default()
                    .content(format!("Base directory for analysis: {}\n\n{}", directory, prompt))
                    .build()?
            ),
        ];
        
        for step in 0..MAX_STEPS {
            self.logger.info(&format!("Step {}/{}", step + 1, MAX_STEPS))?;
            
            // Get LLM response
            let request = CreateChatCompletionRequestArgs::default()
                .model(&self.model_id)
                .messages(messages.clone())
                .temperature(0.0)
                .build()?;
            
            let response = self.client.chat()
                .create(request)
                .await?;
            
            let content = response.choices[0].message.content.clone()
                .unwrap_or_default();
            
            self.logger.debug(&format!("LLM Response: {}", content))?;
            
            // Add assistant response to messages
            messages.push(ChatCompletionRequestMessage::Assistant(
                ChatCompletionRequestAssistantMessageArgs::default()
                    .content(content.clone())
                    .build()?
            ));
            
            // Parse response
            match parse_response(&content) {
                ParsedResponse::Final(answer) => {
                    self.logger.info("Final answer received")?;
                    return Ok(answer);
                }
                ParsedResponse::Action { action, input } => {
                    // Execute tool
                    let observation = execute_tool(&action, &input, &self.logger)?;
                    
                    // Add observation to messages
                    messages.push(ChatCompletionRequestMessage::User(
                        ChatCompletionRequestUserMessageArgs::default()
                            .content(format!("Observation: {}", observation))
                            .build()?
                    ));
                    
                    self.logger.debug(&format!("Tool result: {} chars", observation.len()))?;
                }
                ParsedResponse::Unknown => {
                    self.logger.debug("No valid action found in response")?;
                }
            }
        }
        
        Err(anyhow::anyhow!(
            "Failed to complete analysis within {} steps",
            MAX_STEPS
        ))
    }
}

fn save_results(
    content: &str,
    repo_name: &str,
    model: &str,
    output_dir: &str,
    extension: &str,
    file_name: Option<String>,
    logger: &Logger,
) -> Result<PathBuf> {
    fs::create_dir_all(output_dir)?;
    
    let output_path = if let Some(name) = file_name {
        PathBuf::from(output_dir).join(name)
    } else {
        let timestamp = Local::now().format("%Y%m%d-%H%M%S");
        let parts: Vec<&str> = model.split('/').collect();
        let vendor = parts[0];
        let model_id = sanitize_filename(parts[1]);
        
        PathBuf::from(output_dir).join(format!(
            "{}-{}-{}-{}{}",
            timestamp, repo_name, vendor, model_id, extension
        ))
    };
    
    fs::write(&output_path, content)?;
    logger.info(&format!("Results saved to: {}", output_path.display()))?;
    
    Ok(output_path)
}

fn create_metadata(
    output_file: &Path,
    model: &str,
    repo_url: &str,
    repo_name: &str,
    logger: &Logger,
) -> Result<()> {
    let metadata_file = output_file.with_extension("metadata.json");
    
    let metadata = Metadata {
        model: model.to_string(),
        github_url: repo_url.to_string(),
        repo_name: repo_name.to_string(),
        timestamp: Local::now().to_rfc3339(),
    };
    
    let json = serde_json::to_string_pretty(&metadata)?;
    fs::write(&metadata_file, json)?;
    
    logger.info(&format!("Metadata saved to: {}", metadata_file.display()))?;
    Ok(())
}

fn clone_or_update_repo(repo_url: &str, cache_dir: &str, logger: &Logger) -> Result<PathBuf> {
    let repo_name = repo_url.split('/').last()
        .unwrap_or("repo")
        .trim_end_matches(".git");
    let owner = repo_url.split('/').nth(3).unwrap_or("unknown");
    
    let cache_dir = cache_dir.replace("~", &env::var("HOME").unwrap_or_default());
    let cache_path = PathBuf::from(cache_dir).join(owner).join(repo_name);
    
    fs::create_dir_all(cache_path.parent().unwrap())?;
    
    if cache_path.join(".git").exists() {
        logger.info(&format!("Updating existing repository: {}", cache_path.display()))?;
        Command::new("git")
            .args(&["pull", "--quiet"])
            .current_dir(&cache_path)
            .status()?;
    } else {
        logger.info(&format!("Cloning repository: {}", repo_url))?;
        Command::new("git")
            .args(&["clone", "--quiet", repo_url, cache_path.to_str().unwrap()])
            .status()?;
    }
    
    Ok(cache_path)
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    
    // Read prompt
    let prompt = fs::read_to_string(&args.prompt)
        .context("Failed to read prompt file")?;
    
    // Handle repository or directory
    let (directory, repo_url, repo_name) = if let Some(repo) = args.repo {
        let logger = Logger::new()?;
        let dir = clone_or_update_repo(&repo, &args.cache_dir, &logger)?;
        let name = repo.split('/').last()
            .unwrap_or("repo")
            .trim_end_matches(".git");
        (dir, repo.clone(), name.to_string())
    } else {
        let dir = args.directory.unwrap_or_else(|| ".".to_string());
        let path = PathBuf::from(&dir);
        if !path.exists() {
            return Err(anyhow::anyhow!("Directory not found: {}", dir));
        }
        let abs_path = path.canonicalize()?;
        let name = abs_path.file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown")
            .to_string();
        (abs_path, String::new(), name)
    };
    
    // Run the agent
    let agent = TechWriterAgent::new(&args.model, args.base_url)?;
    let analysis_result = agent.run(&prompt, directory.to_str().unwrap()).await?;
    
    // Save results
    let output_file = save_results(
        &analysis_result,
        &repo_name,
        &args.model,
        &args.output_dir,
        &args.extension,
        args.file_name,
        &agent.logger,
    )?;
    
    // Create metadata
    create_metadata(&output_file, &args.model, &repo_url, &repo_name, &agent.logger)?;
    
    Ok(())
}
