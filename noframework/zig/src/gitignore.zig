const std = @import("std");
const mem = std.mem;
const fs = std.fs;

pub const GitIgnore = struct {
    allocator: mem.Allocator,
    patterns: std.ArrayList(Pattern),
    
    const Pattern = struct {
        pattern: []const u8,
        is_negation: bool,
        is_directory: bool,
        is_absolute: bool,
        match_anywhere: bool,
        
        fn init(allocator: mem.Allocator, line: []const u8) !Pattern {
            var pattern = mem.trim(u8, line, " \t\r\n");
            if (pattern.len == 0) return error.EmptyPattern;
            
            var is_negation = false;
            var is_directory = false;
            var is_absolute = false;
            var match_anywhere = true;
            
            // Handle negation
            if (pattern[0] == '!') {
                is_negation = true;
                pattern = pattern[1..];
            }
            
            // Handle directory patterns
            if (pattern[pattern.len - 1] == '/') {
                is_directory = true;
                pattern = pattern[0 .. pattern.len - 1];
            }
            
            // Handle absolute patterns
            if (pattern[0] == '/') {
                is_absolute = true;
                pattern = pattern[1..];
                match_anywhere = false;
            } else if (mem.indexOf(u8, pattern, "/") != null) {
                match_anywhere = false;
            }
            
            return Pattern{
                .pattern = try allocator.dupe(u8, pattern),
                .is_negation = is_negation,
                .is_directory = is_directory,
                .is_absolute = is_absolute,
                .match_anywhere = match_anywhere,
            };
        }
        
        fn deinit(self: *Pattern, allocator: mem.Allocator) void {
            allocator.free(self.pattern);
        }
        
        fn matches(self: *const Pattern, path: []const u8, is_dir: bool) bool {
            // Convert pattern to use for matching
            const pattern = self.pattern;
            
            // Special handling for directory patterns
            if (self.is_directory) {
                // Directory pattern like "node_modules/" should match:
                // - "node_modules" as a directory
                // - "node_modules/anything" as files within
                if (is_dir) {
                    // Check if path matches the pattern without trailing /
                    if (self.matchesPath(pattern, path)) return true;
                } else {
                    // Check if file is within this directory
                    var check_path = std.ArrayList(u8).init(std.heap.page_allocator);
                    defer check_path.deinit();
                    check_path.appendSlice(pattern) catch return false;
                    check_path.append('/') catch return false;
                    
                    // Check if path starts with pattern/
                    if (mem.startsWith(u8, path, check_path.items)) return true;
                    
                    // Also check with pattern matching
                    return self.matchesPath(pattern, path);
                }
            } else {
                return self.matchesPath(pattern, path);
            }
            
            return false;
        }
        
        fn matchesPath(self: *const Pattern, pattern: []const u8, path: []const u8) bool {
            if (self.match_anywhere) {
                // Pattern can match anywhere in the path
                if (globMatch(pattern, path)) return true;
                
                // Also check each component of the path
                var iter = mem.tokenize(u8, path, "/");
                while (iter.next()) |component| {
                    if (globMatch(pattern, component)) return true;
                }
                
                // Check if pattern matches the end of any directory component
                var i: usize = 0;
                while (i < path.len) {
                    if (path[i] == '/') {
                        const subpath = path[i + 1 ..];
                        if (globMatch(pattern, subpath)) return true;
                    }
                    i += 1;
                }
            } else {
                // Pattern must match from the beginning or as a complete path component
                if (self.is_absolute) {
                    return globMatch(pattern, path);
                } else {
                    // Check if pattern matches the path or any suffix after a /
                    if (globMatch(pattern, path)) return true;
                    
                    var i: usize = 0;
                    while (i < path.len) {
                        if (path[i] == '/') {
                            const subpath = path[i + 1 ..];
                            if (globMatch(pattern, subpath)) return true;
                        }
                        i += 1;
                    }
                }
            }
            
            return false;
        }
    };
    
    pub fn init(allocator: mem.Allocator) GitIgnore {
        return .{
            .allocator = allocator,
            .patterns = std.ArrayList(Pattern).init(allocator),
        };
    }
    
    pub fn deinit(self: *GitIgnore) void {
        for (self.patterns.items) |*pattern| {
            pattern.deinit(self.allocator);
        }
        self.patterns.deinit();
    }
    
    pub fn addPattern(self: *GitIgnore, line: []const u8) !void {
        const trimmed = mem.trim(u8, line, " \t\r\n");
        
        // Skip empty lines and comments
        if (trimmed.len == 0 or trimmed[0] == '#') return;
        
        const pattern = Pattern.init(self.allocator, trimmed) catch |err| switch (err) {
            error.EmptyPattern => return,
            else => return err,
        };
        
        try self.patterns.append(pattern);
    }
    
    pub fn loadFromFile(allocator: mem.Allocator, path: []const u8) !GitIgnore {
        var gitignore = GitIgnore.init(allocator);
        errdefer gitignore.deinit();
        
        // Always ignore .git directory
        try gitignore.addPattern(".git/");
        
        const file = fs.cwd().openFile(path, .{}) catch |err| switch (err) {
            error.FileNotFound => return gitignore,
            else => return err,
        };
        defer file.close();
        
        const content = try file.readToEndAlloc(allocator, 1024 * 1024);
        defer allocator.free(content);
        
        var lines = mem.tokenize(u8, content, "\n");
        while (lines.next()) |line| {
            try gitignore.addPattern(line);
        }
        
        return gitignore;
    }
    
    pub fn shouldIgnore(self: *const GitIgnore, path: []const u8, is_dir: bool) bool {
        var should_ignore = false;
        
        // Check each pattern in order (later patterns can override earlier ones)
        for (self.patterns.items) |*pattern| {
            if (pattern.matches(path, is_dir)) {
                should_ignore = !pattern.is_negation;
            }
        }
        
        return should_ignore;
    }
};

// Simple glob pattern matching with support for ** (matches any number of directories)
fn globMatch(pattern: []const u8, text: []const u8) bool {
    // Handle ** pattern for directory matching
    if (mem.indexOf(u8, pattern, "**") != null) {
        return globMatchWithDoublestar(pattern, text);
    }
    
    var p_idx: usize = 0;
    var t_idx: usize = 0;
    var star_idx: ?usize = null;
    var star_match: ?usize = null;
    
    while (t_idx < text.len) {
        if (p_idx < pattern.len and (pattern[p_idx] == '?' or pattern[p_idx] == text[t_idx])) {
            p_idx += 1;
            t_idx += 1;
        } else if (p_idx < pattern.len and pattern[p_idx] == '*') {
            // Don't match across directory boundaries
            if (p_idx + 1 < pattern.len and pattern[p_idx + 1] == '/') {
                // */ pattern - match only within current directory component
                while (t_idx < text.len and text[t_idx] != '/') {
                    t_idx += 1;
                }
                p_idx += 1; // Skip the *
            } else {
                star_idx = p_idx;
                star_match = t_idx;
                p_idx += 1;
            }
        } else if (star_idx != null) {
            p_idx = star_idx.? + 1;
            star_match = star_match.? + 1;
            t_idx = star_match.?;
        } else {
            return false;
        }
    }
    
    // Check remaining pattern characters
    while (p_idx < pattern.len and pattern[p_idx] == '*') {
        p_idx += 1;
    }
    
    return p_idx == pattern.len;
}

fn globMatchWithDoublestar(pattern: []const u8, text: []const u8) bool {
    // Split pattern by ** and match each part
    var parts = mem.split(u8, pattern, "**");
    var text_pos: usize = 0;
    var first = true;
    
    while (parts.next()) |part| {
        if (part.len == 0) continue;
        
        // Remove leading/trailing slashes from part
        var clean_part = part;
        if (clean_part.len > 0 and clean_part[0] == '/') {
            clean_part = clean_part[1..];
        }
        if (clean_part.len > 0 and clean_part[clean_part.len - 1] == '/') {
            clean_part = clean_part[0 .. clean_part.len - 1];
        }
        
        if (clean_part.len == 0) continue;
        
        // For the first part, it must match at the beginning
        if (first) {
            first = false;
            if (!mem.startsWith(u8, text, clean_part)) {
                // Try to match after any number of directories
                var found = false;
                var search_pos: usize = 0;
                while (search_pos < text.len) {
                    if (mem.startsWith(u8, text[search_pos..], clean_part)) {
                        text_pos = search_pos + clean_part.len;
                        found = true;
                        break;
                    }
                    // Skip to next directory
                    if (mem.indexOf(u8, text[search_pos..], "/")) |idx| {
                        search_pos = search_pos + idx + 1;
                    } else {
                        break;
                    }
                }
                if (!found) return false;
            } else {
                text_pos = clean_part.len;
            }
        } else {
            // Find this part anywhere after the current position
            if (mem.indexOf(u8, text[text_pos..], clean_part)) |idx| {
                text_pos = text_pos + idx + clean_part.len;
            } else {
                return false;
            }
        }
    }
    
    return true;
}

// Tests
test "glob matching" {
    try std.testing.expect(globMatch("*.txt", "file.txt"));
    try std.testing.expect(globMatch("*.txt", "test.txt"));
    try std.testing.expect(!globMatch("*.txt", "file.md"));
    try std.testing.expect(globMatch("test*", "test123"));
    try std.testing.expect(globMatch("*test*", "mytestfile"));
    try std.testing.expect(globMatch("?.txt", "a.txt"));
    try std.testing.expect(!globMatch("?.txt", "ab.txt"));
    try std.testing.expect(globMatch("**/*.js", "src/lib/file.js"));
}

test "gitignore patterns" {
    const allocator = std.testing.allocator;
    
    var gitignore = GitIgnore.init(allocator);
    defer gitignore.deinit();
    
    try gitignore.addPattern("*.log");
    try gitignore.addPattern("temp/");
    try gitignore.addPattern("/build");
    try gitignore.addPattern("!important.log");
    
    try std.testing.expect(gitignore.shouldIgnore("test.log", false));
    try std.testing.expect(gitignore.shouldIgnore("dir/test.log", false));
    try std.testing.expect(!gitignore.shouldIgnore("important.log", false));
    try std.testing.expect(gitignore.shouldIgnore("temp", true));
    try std.testing.expect(gitignore.shouldIgnore("build", false));
    try std.testing.expect(!gitignore.shouldIgnore("src/build", false));
}