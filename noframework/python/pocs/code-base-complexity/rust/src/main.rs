//! Codebase Complexity Analyzer
//!
//! Analyzes code complexity using tree-sitter AST parsing with .gitignore support.
//! Produces language-agnostic metrics for scaling documentation effort.

use anyhow::Result;
use clap::Parser;
use ignore::WalkBuilder;
use rayon::prelude::*;
use serde::Serialize;
use std::{
    collections::HashMap,
    env,
    fs,
    path::{Path, PathBuf},
    process::Command,
    time::Instant,
};
use tree_sitter::{Language, Node, Parser as TsParser};

// Complexity thresholds for bucket classification
const COMPLEXITY_THRESHOLD_SIMPLE: f64 = 20.0;
const COMPLEXITY_THRESHOLD_MEDIUM: f64 = 50.0;

// Top functions limit
const TOP_FUNCTIONS_LIMIT: usize = 10;

// ============================================================================
// Language Support
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum SupportedLanguage {
    Python,
    JavaScript,
    TypeScript,
    Go,
    Rust,
    Java,
}

impl SupportedLanguage {
    fn from_extension(ext: &str) -> Option<Self> {
        match ext {
            "py" => Some(Self::Python),
            "js" | "mjs" | "cjs" | "jsx" => Some(Self::JavaScript),
            "ts" | "tsx" => Some(Self::TypeScript),
            "go" => Some(Self::Go),
            "rs" => Some(Self::Rust),
            "java" => Some(Self::Java),
            _ => None,
        }
    }

    fn name(&self) -> &'static str {
        match self {
            Self::Python => "python",
            Self::JavaScript => "javascript",
            Self::TypeScript => "typescript",
            Self::Go => "go",
            Self::Rust => "rust",
            Self::Java => "java",
        }
    }

    fn tree_sitter_language(&self) -> Language {
        match self {
            Self::Python => tree_sitter_python::language(),
            Self::JavaScript => tree_sitter_javascript::language(),
            Self::TypeScript => tree_sitter_typescript::language_typescript(),
            Self::Go => tree_sitter_go::language(),
            Self::Rust => tree_sitter_rust::language(),
            Self::Java => tree_sitter_java::language(),
        }
    }

    fn function_node_types(&self) -> &'static [&'static str] {
        match self {
            Self::Python => &["function_definition"],
            Self::JavaScript => &[
                "function_declaration",
                "method_definition",
                "arrow_function",
                "function_expression",
            ],
            Self::TypeScript => &[
                "function_declaration",
                "method_definition",
                "arrow_function",
                "function_expression",
            ],
            Self::Go => &["function_declaration", "method_declaration"],
            Self::Rust => &["function_item"],
            Self::Java => &["method_declaration", "constructor_declaration"],
        }
    }

    fn decision_point_types(&self) -> &'static [&'static str] {
        match self {
            Self::Python => &[
                "if_statement",
                "elif_clause",
                "for_statement",
                "while_statement",
                "match_statement",
                "except_clause",
                "conditional_expression",
            ],
            Self::JavaScript => &[
                "if_statement",
                "for_statement",
                "for_in_statement",
                "while_statement",
                "do_statement",
                "switch_case",
                "catch_clause",
                "ternary_expression",
            ],
            Self::TypeScript => &[
                "if_statement",
                "for_statement",
                "for_in_statement",
                "while_statement",
                "do_statement",
                "switch_case",
                "catch_clause",
                "ternary_expression",
            ],
            Self::Go => &[
                "if_statement",
                "for_statement",
                "expression_case",
                "type_case",
            ],
            Self::Rust => &[
                "if_expression",
                "if_let_expression",
                "for_expression",
                "while_expression",
                "loop_expression",
                "match_arm",
            ],
            Self::Java => &[
                "if_statement",
                "for_statement",
                "while_statement",
                "do_statement",
                "enhanced_for_statement",
                "switch_label",
                "catch_clause",
                "ternary_expression",
            ],
        }
    }

    fn nesting_node_types(&self) -> &'static [&'static str] {
        match self {
            Self::Python => &[
                "if_statement",
                "elif_clause",
                "for_statement",
                "while_statement",
                "match_statement",
                "except_clause",
            ],
            Self::JavaScript | Self::TypeScript => &[
                "if_statement",
                "for_statement",
                "for_in_statement",
                "while_statement",
                "do_statement",
                "switch_case",
                "catch_clause",
            ],
            Self::Go => &[
                "if_statement",
                "for_statement",
                "expression_case",
                "type_case",
            ],
            Self::Rust => &[
                "if_expression",
                "if_let_expression",
                "for_expression",
                "while_expression",
                "loop_expression",
                "match_arm",
            ],
            Self::Java => &[
                "if_statement",
                "for_statement",
                "while_statement",
                "do_statement",
                "enhanced_for_statement",
                "switch_label",
                "catch_clause",
            ],
        }
    }

    fn boolean_operators(&self) -> &'static [&'static str] {
        match self {
            Self::Python => &["and", "or"],
            _ => &["&&", "||"],
        }
    }
}

// ============================================================================
// Metrics Data Structures
// ============================================================================

#[derive(Debug, Clone, Serialize)]
struct FunctionMetrics {
    file: String,
    name: String,
    line: usize,
    end_line: usize,
    cyclomatic_complexity: usize,
    cognitive_complexity: usize,
    max_nesting_depth: usize,
    lines_of_code: usize,
    parameter_count: usize,
}

#[derive(Debug, Clone, Serialize)]
struct FileMetrics {
    path: String,
    language: String,
    lines_of_code: usize,
    function_count: usize,
    class_count: usize,
    avg_complexity: f64,
    max_complexity: usize,
    parse_success: bool,
    functions: Vec<FunctionMetrics>,
}

#[derive(Debug, Serialize)]
struct RepoSummary {
    total_files: usize,
    total_functions: usize,
    languages: HashMap<String, usize>,
    complexity_score: f64,
    complexity_bucket: String,
    description: String,
    parse_success_rate: f64,
}

#[derive(Debug, Serialize)]
struct Distribution {
    low: usize,
    medium: usize,
    high: usize,
}

#[derive(Debug, Serialize)]
struct TopFunction {
    file: String,
    name: String,
    line: usize,
    cyclomatic_complexity: usize,
    cognitive_complexity: usize,
}

#[derive(Debug, Serialize)]
struct RepoMetrics {
    repository: String,
    scan_time_ms: u64,
    summary: RepoSummary,
    distribution: Distribution,
    top_complex_functions: Vec<TopFunction>,
    #[serde(skip_serializing_if = "Option::is_none")]
    files: Option<Vec<FileMetrics>>,
}

// ============================================================================
// CLI
// ============================================================================

#[derive(Parser, Debug)]
#[command(
    author,
    version,
    about = "Analyze codebase complexity using tree-sitter AST parsing"
)]
struct Args {
    /// Local path to repository
    #[arg(long)]
    path: Option<String>,

    /// GitHub repository URL (e.g., https://github.com/axios/axios)
    #[arg(long)]
    repo: Option<String>,

    /// Directory for caching cloned repos
    #[arg(long, default_value = "~/.cache/github")]
    cache_dir: String,

    /// Output file (default: stdout)
    #[arg(short, long)]
    output: Option<String>,

    /// Include per-file metrics in output (verbose)
    #[arg(long)]
    include_files: bool,
}

// ============================================================================
// Repository Handling
// ============================================================================

fn clone_or_update_repo(repo_url: &str, cache_dir: &str) -> Result<PathBuf> {
    let repo_name = repo_url
        .trim_end_matches('/')
        .split('/')
        .last()
        .unwrap_or("repo")
        .trim_end_matches(".git");

    let owner = repo_url.split('/').nth(3).unwrap_or("unknown");

    let cache_dir = cache_dir.replace("~", &env::var("HOME").unwrap_or_default());
    let cache_path = PathBuf::from(cache_dir).join(owner).join(repo_name);

    if let Some(parent) = cache_path.parent() {
        fs::create_dir_all(parent)?;
    }

    if cache_path.join(".git").exists() {
        eprintln!("Updating existing repository: {}", cache_path.display());
        Command::new("git")
            .args(["pull", "--quiet"])
            .current_dir(&cache_path)
            .status()?;
    } else {
        eprintln!("Cloning repository: {}", repo_url);
        Command::new("git")
            .args(["clone", "--quiet", repo_url, cache_path.to_str().unwrap()])
            .status()?;
    }

    Ok(cache_path)
}

// ============================================================================
// File Discovery
// ============================================================================

fn discover_files(repo_root: &Path) -> Vec<PathBuf> {
    let mut files = Vec::new();

    let walker = WalkBuilder::new(repo_root)
        .hidden(false)
        .git_ignore(true)
        .git_global(false)
        .git_exclude(false)
        .filter_entry(|e| {
            let name = e.file_name().to_string_lossy();
            // Skip common non-source directories
            name != ".git" && name != "node_modules" && name != "__pycache__" && name != "vendor"
        })
        .build();

    for entry in walker.flatten() {
        let path = entry.path();

        if !path.is_file() {
            continue;
        }

        // Check extension
        let ext = match path.extension().and_then(|e| e.to_str()) {
            Some(e) => e,
            None => continue,
        };

        if SupportedLanguage::from_extension(ext).is_none() {
            continue;
        }

        // Skip binary files (simple heuristic)
        if let Ok(content) = fs::read(path) {
            if content.len() > 1024 && content[..1024].contains(&0) {
                continue;
            }
            if content.contains(&0) {
                continue;
            }
        } else {
            continue;
        }

        files.push(path.to_path_buf());
    }

    files
}

// ============================================================================
// AST Analysis
// ============================================================================

fn get_node_text<'a>(node: &Node, source: &'a [u8]) -> &'a str {
    std::str::from_utf8(&source[node.byte_range()]).unwrap_or("")
}

fn is_decision_point(node_type: &str, lang: SupportedLanguage) -> bool {
    lang.decision_point_types().contains(&node_type)
}

fn is_nesting_node(node_type: &str, lang: SupportedLanguage) -> bool {
    lang.nesting_node_types().contains(&node_type)
}

fn is_function_node(node_type: &str, lang: SupportedLanguage) -> bool {
    lang.function_node_types().contains(&node_type)
}

fn count_boolean_operators(node: Node, source: &[u8], lang: SupportedLanguage) -> usize {
    let operators = lang.boolean_operators();
    let mut count = 0;

    let mut cursor = node.walk();
    let mut stack = vec![node];

    while let Some(current) = stack.pop() {
        let node_type = current.kind();

        if node_type == "binary_expression" || node_type == "boolean_operator" {
            // Check operator child
            cursor.reset(current);
            if cursor.goto_first_child() {
                loop {
                    let child = cursor.node();
                    let child_text = get_node_text(&child, source);
                    if operators.contains(&child_text) {
                        count += 1;
                    }
                    if !cursor.goto_next_sibling() {
                        break;
                    }
                }
            }
        }

        // Add children to stack
        for i in 0..current.child_count() {
            if let Some(child) = current.child(i) {
                stack.push(child);
            }
        }
    }

    count
}

fn calculate_cyclomatic_complexity(func_node: Node, source: &[u8], lang: SupportedLanguage) -> usize {
    let mut complexity = 1;
    let mut stack = vec![func_node];

    while let Some(node) = stack.pop() {
        if is_decision_point(node.kind(), lang) {
            complexity += 1;
        }

        // Count boolean operators
        if node.kind() == "binary_expression" || node.kind() == "boolean_operator" {
            let operators = lang.boolean_operators();
            for i in 0..node.child_count() {
                if let Some(child) = node.child(i) {
                    let text = get_node_text(&child, source);
                    if operators.contains(&text) {
                        complexity += 1;
                    }
                }
            }
        }

        for i in 0..node.child_count() {
            if let Some(child) = node.child(i) {
                stack.push(child);
            }
        }
    }

    complexity
}

fn calculate_cognitive_complexity(func_node: Node, lang: SupportedLanguage) -> usize {
    fn visit(node: Node, nesting_level: usize, lang: SupportedLanguage) -> usize {
        let mut complexity = 0;

        if is_decision_point(node.kind(), lang) {
            complexity += 1 + nesting_level;
        }

        let child_nesting = if is_nesting_node(node.kind(), lang) {
            nesting_level + 1
        } else {
            nesting_level
        };

        for i in 0..node.child_count() {
            if let Some(child) = node.child(i) {
                complexity += visit(child, child_nesting, lang);
            }
        }

        complexity
    }

    visit(func_node, 0, lang)
}

fn calculate_max_nesting_depth(func_node: Node, lang: SupportedLanguage) -> usize {
    fn visit(node: Node, current_depth: usize, lang: SupportedLanguage) -> usize {
        let depth = if is_nesting_node(node.kind(), lang) {
            current_depth + 1
        } else {
            current_depth
        };

        let mut max_depth = depth;
        for i in 0..node.child_count() {
            if let Some(child) = node.child(i) {
                max_depth = max_depth.max(visit(child, depth, lang));
            }
        }

        max_depth
    }

    visit(func_node, 0, lang)
}

fn get_function_name(func_node: Node, source: &[u8]) -> String {
    // Try common field names
    for field in ["name", "declarator"] {
        if let Some(child) = func_node.child_by_field_name(field) {
            if child.kind() == "function_declarator" {
                if let Some(name) = child.child_by_field_name("declarator") {
                    return get_node_text(&name, source).to_string();
                }
            }
            return get_node_text(&child, source).to_string();
        }
    }

    // Fallback: find identifier child
    for i in 0..func_node.child_count() {
        if let Some(child) = func_node.child(i) {
            if child.kind() == "identifier" {
                return get_node_text(&child, source).to_string();
            }
        }
    }

    "<anonymous>".to_string()
}

fn get_parameter_count(func_node: Node) -> usize {
    let params = func_node.child_by_field_name("parameters");
    if params.is_none() {
        return 0;
    }

    let params = params.unwrap();
    let param_types = [
        "identifier",
        "typed_parameter",
        "parameter",
        "formal_parameter",
        "required_parameter",
        "object_pattern",
        "array_pattern",
    ];

    let mut count = 0;
    for i in 0..params.child_count() {
        if let Some(child) = params.child(i) {
            if param_types.contains(&child.kind()) {
                count += 1;
            }
        }
    }

    count
}

// ============================================================================
// File Analysis
// ============================================================================

fn analyze_file(file_path: &Path, repo_root: &Path) -> Option<FileMetrics> {
    let ext = file_path.extension()?.to_str()?;
    let lang = SupportedLanguage::from_extension(ext)?;

    let content = fs::read(file_path).ok()?;
    let source = String::from_utf8_lossy(&content);
    let lines_of_code = source.lines().count();

    let rel_path = file_path
        .strip_prefix(repo_root)
        .ok()?
        .to_string_lossy()
        .to_string();

    // Parse with tree-sitter
    let mut parser = TsParser::new();
    parser.set_language(&lang.tree_sitter_language()).ok()?;

    let tree = match parser.parse(&content, None) {
        Some(t) => t,
        None => {
            return Some(FileMetrics {
                path: rel_path,
                language: lang.name().to_string(),
                lines_of_code,
                function_count: 0,
                class_count: 0,
                avg_complexity: 0.0,
                max_complexity: 0,
                parse_success: false,
                functions: Vec::new(),
            });
        }
    };

    let mut functions = Vec::new();
    let mut class_count = 0;

    fn visit_node(
        node: Node,
        source: &[u8],
        lang: SupportedLanguage,
        rel_path: &str,
        functions: &mut Vec<FunctionMetrics>,
        class_count: &mut usize,
    ) {
        let kind = node.kind();

        if kind == "class_definition" || kind == "class_declaration" {
            *class_count += 1;
        }

        if is_function_node(kind, lang) {
            let name = get_function_name(node, source);
            let start_line = node.start_position().row + 1;
            let end_line = node.end_position().row + 1;
            let cyclomatic = calculate_cyclomatic_complexity(node, source, lang);
            let cognitive = calculate_cognitive_complexity(node, lang);
            let max_nesting = calculate_max_nesting_depth(node, lang);
            let param_count = get_parameter_count(node);

            functions.push(FunctionMetrics {
                file: rel_path.to_string(),
                name,
                line: start_line,
                end_line,
                cyclomatic_complexity: cyclomatic,
                cognitive_complexity: cognitive,
                max_nesting_depth: max_nesting,
                lines_of_code: end_line - start_line + 1,
                parameter_count: param_count,
            });
        }

        for i in 0..node.child_count() {
            if let Some(child) = node.child(i) {
                visit_node(child, source, lang, rel_path, functions, class_count);
            }
        }
    }

    visit_node(
        tree.root_node(),
        &content,
        lang,
        &rel_path,
        &mut functions,
        &mut class_count,
    );

    let avg_complexity = if !functions.is_empty() {
        functions.iter().map(|f| f.cyclomatic_complexity).sum::<usize>() as f64
            / functions.len() as f64
    } else {
        0.0
    };

    let max_complexity = functions
        .iter()
        .map(|f| f.cyclomatic_complexity)
        .max()
        .unwrap_or(0);

    Some(FileMetrics {
        path: rel_path,
        language: lang.name().to_string(),
        lines_of_code,
        function_count: functions.len(),
        class_count,
        avg_complexity: (avg_complexity * 100.0).round() / 100.0,
        max_complexity,
        parse_success: true,
        functions,
    })
}

// ============================================================================
// Repository Analysis
// ============================================================================

fn get_complexity_bucket(score: f64) -> (&'static str, &'static str) {
    if score < COMPLEXITY_THRESHOLD_SIMPLE {
        ("simple", "Small, focused codebase")
    } else if score < COMPLEXITY_THRESHOLD_MEDIUM {
        ("medium", "Moderate complexity codebase")
    } else {
        ("complex", "Large, complex codebase")
    }
}

fn analyze_repository(repo_path: &Path, repo_name: &str) -> Result<RepoMetrics> {
    let start = Instant::now();

    eprintln!("Discovering files in {}...", repo_path.display());
    let files = discover_files(repo_path);
    eprintln!("Found {} source files", files.len());

    // Parallel file analysis
    let file_metrics: Vec<FileMetrics> = files
        .par_iter()
        .enumerate()
        .filter_map(|(i, path)| {
            if (i + 1) % 50 == 0 {
                eprintln!("Processing file {}/{}...", i + 1, files.len());
            }
            analyze_file(path, repo_path)
        })
        .collect();

    // Aggregate metrics
    let all_functions: Vec<&FunctionMetrics> = file_metrics
        .iter()
        .flat_map(|fm| &fm.functions)
        .collect();

    let total_functions = all_functions.len();
    let total_files = file_metrics.len();

    // Language breakdown
    let mut languages: HashMap<String, usize> = HashMap::new();
    for fm in &file_metrics {
        *languages.entry(fm.language.clone()).or_insert(0) += 1;
    }

    // Complexity distribution
    let low = all_functions
        .iter()
        .filter(|f| f.cyclomatic_complexity <= 5)
        .count();
    let medium = all_functions
        .iter()
        .filter(|f| f.cyclomatic_complexity > 5 && f.cyclomatic_complexity <= 15)
        .count();
    let high = all_functions
        .iter()
        .filter(|f| f.cyclomatic_complexity > 15)
        .count();

    // Complexity score
    let complexity_score = if !all_functions.is_empty() {
        let avg_complexity = all_functions
            .iter()
            .map(|f| f.cyclomatic_complexity)
            .sum::<usize>() as f64
            / all_functions.len() as f64;
        let language_diversity = languages.len() as f64;
        let size_factor = (total_functions as f64 / 100.0).min(1.0);
        avg_complexity * (1.0 + 0.1 * language_diversity) * (1.0 + size_factor)
    } else {
        0.0
    };

    let (bucket, description) = get_complexity_bucket(complexity_score);

    // Top complex functions
    let mut sorted_functions: Vec<_> = all_functions.iter().collect();
    sorted_functions.sort_by(|a, b| b.cyclomatic_complexity.cmp(&a.cyclomatic_complexity));

    let top_complex: Vec<TopFunction> = sorted_functions
        .iter()
        .take(TOP_FUNCTIONS_LIMIT)
        .map(|f| TopFunction {
            file: f.file.clone(),
            name: f.name.clone(),
            line: f.line,
            cyclomatic_complexity: f.cyclomatic_complexity,
            cognitive_complexity: f.cognitive_complexity,
        })
        .collect();

    let parse_success_count = file_metrics.iter().filter(|fm| fm.parse_success).count();
    let parse_success_rate = if total_files > 0 {
        (parse_success_count as f64 / total_files as f64 * 1000.0).round() / 10.0
    } else {
        0.0
    };

    let scan_time_ms = start.elapsed().as_millis() as u64;

    Ok(RepoMetrics {
        repository: repo_name.to_string(),
        scan_time_ms,
        summary: RepoSummary {
            total_files,
            total_functions,
            languages,
            complexity_score: (complexity_score * 100.0).round() / 100.0,
            complexity_bucket: bucket.to_string(),
            description: description.to_string(),
            parse_success_rate,
        },
        distribution: Distribution { low, medium, high },
        top_complex_functions: top_complex,
        files: None,
    })
}

// ============================================================================
// Main
// ============================================================================

fn main() -> Result<()> {
    let args = Args::parse();

    if args.path.is_none() && args.repo.is_none() {
        anyhow::bail!("Either --path or --repo is required");
    }

    // Resolve repository path
    let (repo_path, repo_name) = if let Some(ref repo_url) = args.repo {
        let path = clone_or_update_repo(repo_url, &args.cache_dir)?;
        let name = repo_url
            .trim_end_matches('/')
            .split('/')
            .last()
            .unwrap_or("repo")
            .trim_end_matches(".git")
            .to_string();
        (path, name)
    } else {
        let path = PathBuf::from(args.path.as_ref().unwrap());
        if !path.exists() {
            anyhow::bail!("Path not found: {}", path.display());
        }
        let name = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown")
            .to_string();
        (path.canonicalize()?, name)
    };

    eprintln!("Analyzing {}...", repo_name);
    let mut metrics = analyze_repository(&repo_path, &repo_name)?;

    if args.include_files {
        // Re-analyze to include files
        let files = discover_files(&repo_path);
        let file_metrics: Vec<FileMetrics> = files
            .par_iter()
            .filter_map(|path| analyze_file(path, &repo_path))
            .collect();
        metrics.files = Some(file_metrics);
    }

    // Output JSON
    let json_output = serde_json::to_string_pretty(&metrics)?;

    if let Some(output_path) = args.output {
        fs::write(&output_path, &json_output)?;
        eprintln!("Results written to {}", output_path);
    } else {
        println!("{}", json_output);
    }

    // Summary to stderr
    eprintln!("\n=== Summary ===");
    eprintln!("Repository: {}", metrics.repository);
    eprintln!("Scan time: {}ms", metrics.scan_time_ms);
    eprintln!("Total files: {}", metrics.summary.total_files);
    eprintln!("Total functions: {}", metrics.summary.total_functions);
    eprintln!("Languages: {:?}", metrics.summary.languages);
    eprintln!(
        "Complexity score: {} ({})",
        metrics.summary.complexity_score, metrics.summary.complexity_bucket
    );
    eprintln!(
        "Distribution: Low={}, Medium={}, High={}",
        metrics.distribution.low, metrics.distribution.medium, metrics.distribution.high
    );

    Ok(())
}
