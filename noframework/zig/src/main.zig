const std = @import("std");
const http = std.http;
const json = std.json;
const fs = std.fs;
const process = std.process;
const mem = std.mem;
const fmt = std.fmt;
const GitIgnore = @import("gitignore.zig").GitIgnore;

const MAX_STEPS = 50;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
const TEMPERATURE: f32 = 0;
const REACT_SYSTEM_PROMPT =
    \\You are a technical documentation assistant that analyses codebases and generates comprehensive documentation.
    \\
    \\When given a directory path and a specific analysis request, you will:
    \\1. Explore the codebase structure to understand its organization
    \\2. Read relevant files to comprehend the implementation details
    \\3. Generate detailed technical documentation based on your analysis
    \\
    \\You have access to tools that help you explore and understand codebases:
    \\- find_all_matching_files: Find files matching patterns in directories
    \\- read_file: Read the contents of specific files
    \\
    \\Important guidelines:
    \\- Always start by exploring the directory structure to understand the codebase layout
    \\- Read files strategically based on the documentation needs
    \\- Pay attention to configuration files, main entry points, and key modules
    \\- Generate clear, well-structured documentation that would help developers understand the codebase
    \\
    \\Use the following format:
    \\
    \\Thought: I need to [describe what you need to do next]
    \\Action: [tool_name]
    \\Action Input: {"param1": "value1", "param2": "value2"}
    \\Observation: [tool output will be provided here]
    \\... (repeat Thought/Action/Action Input/Observation as needed)
    \\Thought: I now have enough information to generate the documentation
    \\Final Answer: [Your complete technical documentation]
    \\
    \\Begin your analysis now.
;

const Message = struct {
    role: []const u8,
    content: []const u8,
};

const ChatRequest = struct {
    model: []const u8,
    messages: []Message,
    temperature: f32 = TEMPERATURE,
};

const Choice = struct {
    message: struct {
        content: []const u8,
    },
};

const ChatResponse = struct {
    choices: []Choice,
};

const ParsedResponse = struct {
    response_type: enum { action, final_answer, unknown },
    action: ?[]const u8 = null,
    action_input: ?[]const u8 = null,
    final_answer: ?[]const u8 = null,
};

const TechWriterAgent = struct {
    allocator: mem.Allocator,
    model_id: []const u8,
    api_key: []const u8,
    base_url: []const u8,
    memory: std.ArrayList(Message),
    log_file: ?fs.File,

    pub fn init(allocator: mem.Allocator, model_name: []const u8, base_url_opt: ?[]const u8) !TechWriterAgent {
        var iter = mem.split(u8, model_name, "/");
        const vendor = iter.next() orelse return error.InvalidModelName;
        const model_id = iter.next() orelse return error.InvalidModelName;

        var api_key: []const u8 = undefined;
        var base_url: []const u8 = undefined;

        if (mem.eql(u8, vendor, "google")) {
            api_key = std.process.getEnvVarOwned(allocator, "GEMINI_API_KEY") catch return error.MissingGeminiApiKey;
            base_url = base_url_opt orelse "https://generativelanguage.googleapis.com/v1beta/openai/";
        } else if (mem.eql(u8, vendor, "openai")) {
            api_key = std.process.getEnvVarOwned(allocator, "OPENAI_API_KEY") catch return error.MissingOpenAIApiKey;
            base_url = base_url_opt orelse "https://api.openai.com/v1/";
        } else {
            return error.UnknownVendor;
        }

        // Create logs directory
        fs.cwd().makeDir("logs") catch |err| switch (err) {
            error.PathAlreadyExists => {},
            else => return err,
        };

        const timestamp = std.time.timestamp();
        const log_filename = try fmt.allocPrint(allocator, "logs/tech-writer-{d}.log", .{timestamp});
        defer allocator.free(log_filename);

        const log_file = try fs.cwd().createFile(log_filename, .{});

        return TechWriterAgent{
            .allocator = allocator,
            .model_id = try allocator.dupe(u8, model_id),
            .api_key = api_key,
            .base_url = try allocator.dupe(u8, base_url),
            .memory = std.ArrayList(Message).init(allocator),
            .log_file = log_file,
        };
    }

    pub fn deinit(self: *TechWriterAgent) void {
        self.allocator.free(self.model_id);
        self.allocator.free(self.api_key);
        self.allocator.free(self.base_url);
        for (self.memory.items) |msg| {
            self.allocator.free(msg.role);
            self.allocator.free(msg.content);
        }
        self.memory.deinit();
        if (self.log_file) |f| f.close();
    }

    fn log(self: *TechWriterAgent, comptime format: []const u8, args: anytype) void {
        const stderr = std.io.getStdErr().writer();
        stderr.print(format ++ "\n", args) catch {};
        
        if (self.log_file) |f| {
            const writer = f.writer();
            writer.print(format ++ "\n", args) catch {};
        }
    }

    pub fn run(self: *TechWriterAgent, prompt: []const u8, directory: []const u8) ![]u8 {
        self.log("Starting ReAct agent with model: {s}", .{self.model_id});

        // Initialize conversation
        try self.memory.append(.{
            .role = try self.allocator.dupe(u8, "system"),
            .content = try self.allocator.dupe(u8, REACT_SYSTEM_PROMPT),
        });

        const user_prompt = try fmt.allocPrint(self.allocator, "Base directory for analysis: {s}\n\n{s}", .{ directory, prompt });
        defer self.allocator.free(user_prompt);

        try self.memory.append(.{
            .role = try self.allocator.dupe(u8, "user"),
            .content = try self.allocator.dupe(u8, user_prompt),
        });

        var final_answer: ?[]u8 = null;

        // ReAct loop
        var step: usize = 0;
        while (step < MAX_STEPS) : (step += 1) {
            self.log("Step {d}/{d}", .{ step + 1, MAX_STEPS });

            // Get LLM response
            const response = try self.callLLM();
            defer self.allocator.free(response);

            self.log("LLM Response: {s}", .{response});

            // Add assistant response to memory
            try self.memory.append(.{
                .role = try self.allocator.dupe(u8, "assistant"),
                .content = try self.allocator.dupe(u8, response),
            });

            // Parse response
            const parsed = try self.parseResponse(response);
            defer {
                if (parsed.action) |a| self.allocator.free(a);
                if (parsed.action_input) |a| self.allocator.free(a);
                if (parsed.final_answer) |a| self.allocator.free(a);
            }

            switch (parsed.response_type) {
                .final_answer => {
                    if (parsed.final_answer) |answer| {
                        final_answer = try self.allocator.dupe(u8, answer);
                        self.log("Final answer received", .{});
                        break;
                    }
                },
                .action => {
                    if (parsed.action) |action| {
                        if (parsed.action_input) |input| {
                            // Execute tool
                            const observation = try self.executeTool(action, input);
                            defer self.allocator.free(observation);

                            const obs_msg = try fmt.allocPrint(self.allocator, "Observation: {s}", .{observation});
                            defer self.allocator.free(obs_msg);

                            try self.memory.append(.{
                                .role = try self.allocator.dupe(u8, "user"),
                                .content = try self.allocator.dupe(u8, obs_msg),
                            });

                            self.log("Tool result: {d} chars", .{observation.len});
                        }
                    }
                },
                .unknown => {
                    self.log("Unknown response format", .{});
                },
            }
        }

        if (final_answer == null) {
            return error.NoFinalAnswer;
        }

        return final_answer.?;
    }

    fn callLLM(self: *TechWriterAgent) ![]u8 {
        const request_body = try json.stringifyAlloc(self.allocator, ChatRequest{
            .model = self.model_id,
            .messages = self.memory.items,
            .temperature = TEMPERATURE,
        }, .{});
        defer self.allocator.free(request_body);

        const url = try fmt.allocPrint(self.allocator, "{s}chat/completions", .{self.base_url});
        defer self.allocator.free(url);

        const uri = try std.Uri.parse(url);
        
        var client = http.Client{ .allocator = self.allocator };
        defer client.deinit();

        const auth_header = try fmt.allocPrint(self.allocator, "Bearer {s}", .{self.api_key});
        defer self.allocator.free(auth_header);

        var server_header_buffer: [16 * 1024]u8 = undefined;
        const headers = [_]http.Header{
            .{ .name = "Authorization", .value = auth_header },
            .{ .name = "Content-Type", .value = "application/json" },
            .{ .name = "Accept", .value = "application/json" },
        };

        var req = try client.open(.POST, uri, .{
            .server_header_buffer = &server_header_buffer,
            .extra_headers = &headers,
        });
        defer req.deinit();

        req.transfer_encoding = .{ .content_length = request_body.len };
        try req.send();
        try req.writeAll(request_body);
        try req.finish();
        try req.wait();

        if (req.response.status != .ok) {
            self.log("HTTP request failed with status: {}", .{req.response.status});
            return error.HttpRequestFailed;
        }

        const body = try req.reader().readAllAlloc(self.allocator, MAX_FILE_SIZE);
        defer self.allocator.free(body);

        const parsed = try json.parseFromSlice(ChatResponse, self.allocator, body, .{ .ignore_unknown_fields = true });
        defer parsed.deinit();

        if (parsed.value.choices.len == 0) {
            return error.NoChoicesInResponse;
        }

        return self.allocator.dupe(u8, parsed.value.choices[0].message.content);
    }

    fn parseResponse(self: *TechWriterAgent, response: []const u8) !ParsedResponse {
        // Check for Final Answer
        if (mem.indexOf(u8, response, "Final Answer:")) |pos| {
            var answer_start = pos + 13;
            while (answer_start < response.len and std.ascii.isWhitespace(response[answer_start])) : (answer_start += 1) {}
            const final_answer = mem.trim(u8, response[answer_start..], " \t\n\r");
            return ParsedResponse{
                .response_type = .final_answer,
                .final_answer = try self.allocator.dupe(u8, final_answer),
            };
        }

        // Extract Action and Action Input
        var lines = mem.split(u8, response, "\n");
        var action: ?[]const u8 = null;
        var collecting_input = false;
        var input_lines = std.ArrayList([]const u8).init(self.allocator);
        defer input_lines.deinit();

        while (lines.next()) |line| {
            if (mem.startsWith(u8, line, "Action:")) {
                var action_start: usize = 7;
                while (action_start < line.len and std.ascii.isWhitespace(line[action_start])) : (action_start += 1) {}
                action = mem.trim(u8, line[action_start..], " \t\n\r");
            } else if (mem.startsWith(u8, line, "Action Input:")) {
                collecting_input = true;
                const input_start = 13;
                if (input_start < line.len) {
                    const rest = mem.trim(u8, line[input_start..], " \t\n\r");
                    if (rest.len > 0) {
                        try input_lines.append(rest);
                    }
                }
            } else if (collecting_input) {
                // Stop collecting if we hit another section marker
                if (mem.startsWith(u8, line, "Thought:") or
                    mem.startsWith(u8, line, "Action:") or
                    mem.startsWith(u8, line, "Observation:") or
                    mem.startsWith(u8, line, "Final Answer:"))
                {
                    break;
                }
                try input_lines.append(line);
            }
        }

        if (action != null and input_lines.items.len > 0) {
            const input = try mem.join(self.allocator, "\n", input_lines.items);
            return ParsedResponse{
                .response_type = .action,
                .action = try self.allocator.dupe(u8, action.?),
                .action_input = input,
            };
        }

        return ParsedResponse{ .response_type = .unknown };
    }

    fn executeTool(self: *TechWriterAgent, tool_name: []const u8, action_input: []const u8) ![]u8 {
        self.log("Executing tool: {s} with input: {s}", .{ tool_name, action_input });

        const parsed = try json.parseFromSlice(std.json.Value, self.allocator, action_input, .{});
        defer parsed.deinit();

        if (mem.eql(u8, tool_name, "find_all_matching_files")) {
            const directory = if (parsed.value.object.get("directory")) |d| d.string else "";
            const pattern = if (parsed.value.object.get("pattern")) |p| p.string else "*";
            return self.findAllMatchingFiles(directory, pattern);
        } else if (mem.eql(u8, tool_name, "read_file")) {
            const file_path = if (parsed.value.object.get("file_path")) |f| f.string else "";
            return self.readFile(file_path);
        } else {
            return try fmt.allocPrint(self.allocator, "{{\"error\": \"Unknown tool: {s}\"}}", .{tool_name});
        }
    }

    fn findAllMatchingFiles(self: *TechWriterAgent, directory: []const u8, pattern: []const u8) ![]u8 {
        self.log("Tool invoked: find_all_matching_files(directory='{s}', pattern='{s}')", .{ directory, pattern });

        var files = std.ArrayList([]const u8).init(self.allocator);
        defer {
            for (files.items) |file| {
                self.allocator.free(file);
            }
            files.deinit();
        }

        const dir = fs.cwd().openDir(directory, .{ .iterate = true }) catch {
            self.log("Directory not found: {s}", .{directory});
            return self.allocator.dupe(u8, "[]");
        };
        var walker = try dir.walk(self.allocator);
        defer walker.deinit();

        // Load gitignore patterns
        const gitignore_path = try fmt.allocPrint(self.allocator, "{s}/.gitignore", .{directory});
        defer self.allocator.free(gitignore_path);
        
        var gitignore = try GitIgnore.loadFromFile(self.allocator, gitignore_path);
        defer gitignore.deinit();

        while (try walker.next()) |entry| {
            if (entry.kind != .file) continue;

            // Check if file should be ignored
            if (gitignore.shouldIgnore(entry.path, false)) continue;

            // Check pattern match
            var matches = false;
            if (mem.eql(u8, pattern, "*")) {
                matches = true;
            } else if (mem.eql(u8, pattern, "*.*")) {
                // Match files with a dot in the name
                if (mem.indexOf(u8, entry.basename, ".") != null) {
                    matches = true;
                }
            } else if (mem.startsWith(u8, pattern, "*.")) {
                const ext = pattern[1..];
                if (mem.endsWith(u8, entry.path, ext)) {
                    matches = true;
                }
            } else {
                if (mem.eql(u8, entry.basename, pattern)) {
                    matches = true;
                }
            }

            if (matches) {
                const full_path = try fmt.allocPrint(self.allocator, "{s}/{s}", .{ directory, entry.path });
                try files.append(full_path);
            }
        }

        self.log("Found {d} matching files", .{files.items.len});

        // Build JSON array
        var result = std.ArrayList(u8).init(self.allocator);
        try result.append('[');
        for (files.items, 0..) |file, i| {
            if (i > 0) try result.appendSlice(", ");
            try result.append('"');
            try result.appendSlice(file);
            try result.append('"');
        }
        try result.append(']');

        return result.toOwnedSlice();
    }

    fn readFile(self: *TechWriterAgent, file_path: []const u8) ![]u8 {
        self.log("Tool invoked: read_file(file_path='{s}')", .{file_path});

        const file = fs.cwd().openFile(file_path, .{}) catch {
            return try fmt.allocPrint(self.allocator, "{{\"error\": \"File not found: {s}\"}}", .{file_path});
        };
        defer file.close();

        const stat = try file.stat();
        if (stat.size > MAX_FILE_SIZE) {
            return try fmt.allocPrint(self.allocator, "{{\"error\": \"File too large: {s}\"}}", .{file_path});
        }

        const content = try file.readToEndAlloc(self.allocator, @intCast(stat.size));
        defer self.allocator.free(content);

        // Check if binary by looking for null bytes
        if (mem.indexOf(u8, content, "\x00") != null) {
            self.log("File detected as binary: {s}", .{file_path});
            return try fmt.allocPrint(self.allocator, "{{\"error\": \"Cannot read binary file: {s}\"}}", .{file_path});
        }

        self.log("Successfully read file: {s} ({d} chars)", .{ file_path, content.len });

        // Escape content for JSON
        var escaped = std.ArrayList(u8).init(self.allocator);
        const writer = escaped.writer();
        try json.stringify(.{
            .file = file_path,
            .content = content,
        }, .{}, writer);

        return escaped.toOwnedSlice();
    }
};

fn cloneOrUpdateRepo(allocator: mem.Allocator, repo_url: []const u8, cache_dir: []const u8) ![]u8 {
    const stderr = std.io.getStdErr().writer();

    // Extract repo name from URL
    var parts = mem.split(u8, repo_url, "/");
    var repo_name: []const u8 = "";
    while (parts.next()) |part| {
        repo_name = part;
    }
    if (mem.endsWith(u8, repo_name, ".git")) {
        repo_name = repo_name[0 .. repo_name.len - 4];
    }

    // Extract owner
    parts = mem.split(u8, repo_url, "/");
    var owner: []const u8 = "";
    var prev: []const u8 = "";
    while (parts.next()) |part| {
        if (mem.eql(u8, part, repo_name) or mem.eql(u8, part, try fmt.allocPrint(allocator, "{s}.git", .{repo_name}))) {
            owner = prev;
            break;
        }
        prev = part;
    }

    // Expand home directory
    var expanded_cache_dir: []const u8 = cache_dir;
    var allocated_cache_dir = false;
    if (mem.startsWith(u8, cache_dir, "~/")) {
        const home = std.process.getEnvVarOwned(allocator, "HOME") catch return error.NoHomeDirectory;
        defer allocator.free(home);
        expanded_cache_dir = try fmt.allocPrint(allocator, "{s}{s}", .{ home, cache_dir[1..] });
        allocated_cache_dir = true;
    }
    defer {
        if (allocated_cache_dir) {
            allocator.free(expanded_cache_dir);
        }
    }

    const cache_path = try fmt.allocPrint(allocator, "{s}/{s}/{s}", .{ expanded_cache_dir, owner, repo_name });
    defer allocator.free(cache_path);

    // Create cache directory
    const owner_path = try fmt.allocPrint(allocator, "{s}/{s}", .{ expanded_cache_dir, owner });
    defer allocator.free(owner_path);
    try fs.cwd().makePath(owner_path);

    // Check if already cloned
    const git_path = try fmt.allocPrint(allocator, "{s}/.git", .{cache_path});
    defer allocator.free(git_path);

    if (fs.cwd().openDir(git_path, .{})) |d| {
        var dir = d;
        dir.close();
        try stderr.print("Updating existing repository: {s}\n", .{cache_path});

        var child = std.ChildProcess.init(&[_][]const u8{ "git", "-C", cache_path, "pull", "--quiet" }, allocator);
        child.stdout_behavior = .Ignore;
        child.stderr_behavior = .Ignore;
        try child.spawn();
        const term = try child.wait();
        if (term.Exited != 0) {
            return error.GitPullFailed;
        }
    } else |_| {
        try stderr.print("Cloning repository: {s}\n", .{repo_url});

        var clone_child = std.ChildProcess.init(&[_][]const u8{ "git", "clone", "--quiet", repo_url, cache_path }, allocator);
        clone_child.stdout_behavior = .Ignore;
        clone_child.stderr_behavior = .Ignore;
        try clone_child.spawn();
        const clone_term = try clone_child.wait();
        if (clone_term.Exited != 0) {
            return error.GitCloneFailed;
        }
    }

    return allocator.dupe(u8, cache_path);
}

fn saveResults(allocator: mem.Allocator, content: []const u8, repo_name: []const u8, model: []const u8, output_dir: []const u8, extension: []const u8, file_name: ?[]const u8) ![]u8 {
    const stderr = std.io.getStdErr().writer();

    try fs.cwd().makePath(output_dir);

    var output_path: []u8 = undefined;
    if (file_name) |name| {
        output_path = try fmt.allocPrint(allocator, "{s}/{s}", .{ output_dir, name });
    } else {
        const timestamp = std.time.timestamp();
        var model_parts = mem.split(u8, model, "/");
        const vendor = model_parts.next() orelse "unknown";
        const model_id = model_parts.next() orelse "unknown";

        // Sanitize model ID
        var sanitized_model = std.ArrayList(u8).init(allocator);
        defer sanitized_model.deinit();
        for (model_id) |c| {
            if (std.ascii.isAlphanumeric(c) or c == '-' or c == '_') {
                try sanitized_model.append(c);
            } else {
                try sanitized_model.append('-');
            }
        }

        output_path = try fmt.allocPrint(allocator, "{s}/{d}-{s}-{s}-{s}{s}", .{ output_dir, timestamp, repo_name, vendor, sanitized_model.items, extension });
    }

    const file = try fs.cwd().createFile(output_path, .{});
    defer file.close();
    try file.writeAll(content);

    try stderr.print("Results saved to: {s}\n", .{output_path});
    return output_path;
}

fn createMetadata(allocator: mem.Allocator, output_file: []const u8, model: []const u8, repo_url: []const u8, repo_name: []const u8) !void {
    const stderr = std.io.getStdErr().writer();

    // Replace extension with .metadata.json
    var metadata_path = std.ArrayList(u8).init(allocator);
    defer metadata_path.deinit();

    const last_dot = mem.lastIndexOf(u8, output_file, ".");
    if (last_dot) |pos| {
        try metadata_path.appendSlice(output_file[0..pos]);
    } else {
        try metadata_path.appendSlice(output_file);
    }
    try metadata_path.appendSlice(".metadata.json");

    const timestamp = std.time.timestamp();
    const metadata = .{
        .model = model,
        .github_url = repo_url,
        .repo_name = repo_name,
        .timestamp = timestamp,
    };

    const file = try fs.cwd().createFile(metadata_path.items, .{});
    defer file.close();

    try json.stringify(metadata, .{ .whitespace = .indent_2 }, file.writer());
    try stderr.print("Metadata saved to: {s}\n", .{metadata_path.items});
}

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    const args = try process.argsAlloc(allocator);
    defer process.argsFree(allocator, args);

    const stderr = std.io.getStdErr().writer();

    // Parse arguments
    var directory: ?[]const u8 = null;
    var repo_url: ?[]const u8 = null;
    var prompt_file: ?[]const u8 = null;
    var cache_dir: []const u8 = "~/.cache/github";
    var output_dir: []const u8 = "output";
    var extension: []const u8 = ".md";
    var file_name: ?[]const u8 = null;
    var model: []const u8 = "openai/gpt-4o-mini";
    var base_url: ?[]const u8 = null;

    var i: usize = 1;
    while (i < args.len) {
        if (mem.eql(u8, args[i], "--help") or mem.eql(u8, args[i], "-h")) {
            try stderr.print(
                \\Usage: {s} [directory] [options]
                \\
                \\Analyse a codebase using an LLM agent.
                \\
                \\Positional arguments:
                \\  directory             Directory containing the codebase to analyse
                \\
                \\Options:
                \\  --repo REPO           GitHub repository URL to clone (e.g. https://github.com/owner/repo)
                \\  --prompt FILE         Path to a file containing the analysis prompt (required)
                \\  --cache-dir DIR       Directory to cache cloned repositories (default: ~/.cache/github)
                \\  --output-dir DIR      Directory to save results to (default: output)
                \\  --extension EXT       File extension for output files (default: .md)
                \\  --file-name FILE      Specific file name for output (overrides --extension)
                \\  --model MODEL         Model to use (format: vendor/model, default: openai/gpt-4o-mini)
                \\  --base-url URL        Base URL for the API (automatically set based on model if not provided)
                \\  -h, --help            Show this help message and exit
                \\
                \\Dependencies:
                \\  This script requires environment variables:
                \\  - OPENAI_API_KEY for OpenAI models
                \\  - GEMINI_API_KEY for Google models
                \\
            , .{args[0]});
            return;
        } else if (mem.eql(u8, args[i], "--repo")) {
            if (i + 1 >= args.len) return error.MissingArgument;
            repo_url = args[i + 1];
            i += 2;
        } else if (mem.eql(u8, args[i], "--prompt")) {
            if (i + 1 >= args.len) return error.MissingArgument;
            prompt_file = args[i + 1];
            i += 2;
        } else if (mem.eql(u8, args[i], "--cache-dir")) {
            if (i + 1 >= args.len) return error.MissingArgument;
            cache_dir = args[i + 1];
            i += 2;
        } else if (mem.eql(u8, args[i], "--output-dir")) {
            if (i + 1 >= args.len) return error.MissingArgument;
            output_dir = args[i + 1];
            i += 2;
        } else if (mem.eql(u8, args[i], "--extension")) {
            if (i + 1 >= args.len) return error.MissingArgument;
            extension = args[i + 1];
            i += 2;
        } else if (mem.eql(u8, args[i], "--file-name")) {
            if (i + 1 >= args.len) return error.MissingArgument;
            file_name = args[i + 1];
            i += 2;
        } else if (mem.eql(u8, args[i], "--model")) {
            if (i + 1 >= args.len) return error.MissingArgument;
            model = args[i + 1];
            i += 2;
        } else if (mem.eql(u8, args[i], "--base-url")) {
            if (i + 1 >= args.len) return error.MissingArgument;
            base_url = args[i + 1];
            i += 2;
        } else if (args[i][0] != '-') {
            directory = args[i];
            i += 1;
        } else {
            try stderr.print("Unknown option: {s}\n", .{args[i]});
            return error.UnknownOption;
        }
    }

    // Validate arguments
    if (prompt_file == null) {
        try stderr.print("Error: --prompt is required\n", .{});
        return error.MissingPrompt;
    }

    // Read prompt
    const prompt = try fs.cwd().readFileAlloc(allocator, prompt_file.?, 1024 * 1024);
    defer allocator.free(prompt);

    var repo_name: []const u8 = undefined;
    var analysis_dir: []const u8 = undefined;
    var cloned_dir: ?[]const u8 = null;

    // Handle repository or directory
    if (repo_url) |url| {
        const cloned = try cloneOrUpdateRepo(allocator, url, cache_dir);
        cloned_dir = cloned;
        analysis_dir = cloned;
        
        // Extract repo name from URL
        var parts = mem.split(u8, url, "/");
        var name: []const u8 = "";
        while (parts.next()) |part| {
            name = part;
        }
        if (mem.endsWith(u8, name, ".git")) {
            name = name[0 .. name.len - 4];
        }
        repo_name = try allocator.dupe(u8, name);
    } else {
        if (directory == null) {
            analysis_dir = ".";
        } else {
            analysis_dir = directory.?;
        }
        
        // Get absolute path
        const real_path = try fs.cwd().realpathAlloc(allocator, analysis_dir);
        defer allocator.free(real_path);
        
        // Extract base name
        const base = fs.path.basename(real_path);
        repo_name = try allocator.dupe(u8, base);
    }
    defer allocator.free(repo_name);
    defer if (cloned_dir) |dir| allocator.free(dir);

    // Run the agent
    var agent = try TechWriterAgent.init(allocator, model, base_url);
    defer agent.deinit();

    const analysis_result = try agent.run(prompt, analysis_dir);
    defer allocator.free(analysis_result);

    // Save results
    const output_file = try saveResults(allocator, analysis_result, repo_name, model, output_dir, extension, file_name);
    defer allocator.free(output_file);

    // Create metadata
    try createMetadata(allocator, output_file, model, repo_url orelse "", repo_name);
}