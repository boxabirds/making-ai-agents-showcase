#!/bin/bash

# Tech Writer Evaluation Script
# Tests tech writer implementations and provides performance analytics

set -euo pipefail

# Default configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EVAL_OUTPUT_DIR="${SCRIPT_DIR}/output"
EVAL_PROMPT="${SCRIPT_DIR}/eval.prompt.txt"
TEST_REPO="${TEST_REPO:-https://github.com/axios/axios}"
MODEL="${MODEL:-openai/gpt-4o-mini}"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")

# Options
ALL_NOFRAMEWORK=false
CSV_OUTPUT=""
JSON_OUTPUT=""
SINGLE_SCRIPT=""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Platform detection for stats collection
PLATFORM="unknown"
TIME_CMD=""
case "$(uname -s)" in
    Linux*)
        PLATFORM="linux"
        if command -v /usr/bin/time >/dev/null 2>&1; then
            TIME_CMD="/usr/bin/time -v"
        fi
        ;;
    Darwin*)
        PLATFORM="macos"
        if command -v /usr/bin/time >/dev/null 2>&1; then
            TIME_CMD="/usr/bin/time -l"
        fi
        ;;
    MINGW*|MSYS*|CYGWIN*)
        PLATFORM="windows"
        ;;
esac

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS] [script-path]

Run evaluation on tech writer implementations.

Options:
    --all-noframework    Test all implementations in noframework directory
    --csv <file>        Export results to CSV file
    --json <file>       Export detailed stats to JSON file
    -h, --help          Show this help message

Arguments:
    script-path         Path to a specific tech-writer.sh script to test

Examples:
    # Test a single implementation
    $0 ../noframework/python/tech-writer.sh

    # Test all noframework implementations
    $0 --all-noframework

    # Test all with CSV export
    $0 --all-noframework --csv results.csv

Environment Variables:
    MODEL               LLM model to use (default: openai/gpt-4o-mini)
    TEST_REPO          Repository to test (default: https://github.com/axios/axios)
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all-noframework)
                ALL_NOFRAMEWORK=true
                shift
                ;;
            --csv)
                CSV_OUTPUT="$2"
                shift 2
                ;;
            --json)
                JSON_OUTPUT="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -*)
                echo "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                SINGLE_SCRIPT="$1"
                shift
                ;;
        esac
    done

    # Validate arguments
    if [[ "$ALL_NOFRAMEWORK" == "false" ]] && [[ -z "$SINGLE_SCRIPT" ]]; then
        echo "Error: Must specify either --all-noframework or a script path"
        usage
        exit 1
    fi

    if [[ "$ALL_NOFRAMEWORK" == "true" ]] && [[ -n "$SINGLE_SCRIPT" ]]; then
        echo "Error: Cannot use --all-noframework with a specific script path"
        usage
        exit 1
    fi
}

# Create output directory
mkdir -p "$EVAL_OUTPUT_DIR"

# Global variables for stats collection
LAST_WALL_TIME=""
LAST_CPU_PERCENT=""
LAST_MEMORY_MB=""
LAST_EXIT_CODE=""
LAST_USER_TIME=""
LAST_SYS_TIME=""

# Parse stats from time command output
parse_stats_linux() {
    local output="$1"
    LAST_CPU_PERCENT=$(echo "$output" | grep -E "Percent of CPU" | awk -F': ' '{print $2}' | tr -d '%')
    LAST_MEMORY_MB=$(echo "$output" | grep -E "Maximum resident set size" | awk -F': ' '{print $2}' | awk '{print $1/1024}')
    local wall_time=$(echo "$output" | grep -E "Elapsed \(wall clock\)" | awk -F': ' '{print $2}' | awk '{print $1}')
    # Convert MM:SS.SS to seconds
    if [[ "$wall_time" =~ ^([0-9]+):([0-9]+\.[0-9]+)$ ]]; then
        LAST_WALL_TIME=$(echo "${BASH_REMATCH[1]} * 60 + ${BASH_REMATCH[2]}" | bc)
    else
        LAST_WALL_TIME="$wall_time"
    fi
}

parse_stats_macos() {
    local output="$1"
    # macOS time output format has leading whitespace: "        0.00 real         0.00 user         0.00 sys"
    local stats_line=$(echo "$output" | grep -E "^\s+[0-9]+\.[0-9]+ real\s+[0-9]+\.[0-9]+ user\s+[0-9]+\.[0-9]+ sys")
    
    if [[ -n "$stats_line" ]]; then
        local real_time=$(echo "$stats_line" | awk '{print $1}')
        local user_time=$(echo "$stats_line" | awk '{print $3}')
        local sys_time=$(echo "$stats_line" | awk '{print $5}')
        
        LAST_WALL_TIME="$real_time"
        LAST_USER_TIME="$user_time"
        LAST_SYS_TIME="$sys_time"
        
        # CPU calculation from user + sys time
        if [[ "$real_time" != "0.00" ]]; then
            # Use scale=4 for more precision
            cpu_calc=$(echo "scale=4; ($user_time + $sys_time) / $real_time * 100" | bc)
            # Format to 2 decimal places
            LAST_CPU_PERCENT=$(printf "%.2f" "$cpu_calc")
        else
            LAST_CPU_PERCENT=""
        fi
    fi
    
    # Memory in bytes, convert to MB
    # Use maximum resident set size, not peak memory footprint
    local mem_bytes=$(echo "$output" | grep "maximum resident set size" | awk '{print $1}')
    if [[ -n "$mem_bytes" ]]; then
        LAST_MEMORY_MB=$(echo "scale=2; $mem_bytes / 1024 / 1024" | bc)
    fi
}

# Check prerequisites
check_prerequisites() {
    local missing=()
    
    # Check for required environment variables
    if [[ -z "${OPENAI_API_KEY:-}" ]] && [[ -z "${GEMINI_API_KEY:-}" ]]; then
        echo -e "${RED}ERROR: No API keys found. Set OPENAI_API_KEY or GEMINI_API_KEY${NC}"
        exit 1
    fi
    
    # Check for eval prompt
    if [[ ! -f "$EVAL_PROMPT" ]]; then
        echo -e "${RED}ERROR: Evaluation prompt not found: $EVAL_PROMPT${NC}"
        exit 1
    fi
    
    # Check for required commands
    command -v jq >/dev/null 2>&1 || missing+=("jq")
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${RED}ERROR: Missing required commands: ${missing[*]}${NC}"
        echo "Please install them first."
        exit 1
    fi
}

# Test a single tech writer implementation with stats
test_tech_writer_with_stats() {
    local name="$1"
    local script_path="$2"
    local log_file="$3"
    
    # Reset stats
    LAST_WALL_TIME=""
    LAST_CPU_PERCENT=""
    LAST_MEMORY_MB=""
    LAST_EXIT_CODE=0
    
    echo -e "\n${BLUE}Testing: $name${NC}" | tee -a "$log_file"
    echo "Script: $script_path" | tee -a "$log_file"
    
    # Check if script exists
    if [[ ! -f "$script_path" ]]; then
        echo -e "${RED}✗ Script not found${NC}" | tee -a "$log_file"
        LAST_EXIT_CODE=1
        return 1
    fi
    
    # Make sure it's executable
    if [[ ! -x "$script_path" ]]; then
        chmod +x "$script_path" 2>/dev/null || true
    fi
    
    # Prepare output filename
    local output_file="${EVAL_OUTPUT_DIR}/eval-${name}-${TIMESTAMP}.md"
    
    # Build command
    local cmd_args="--repo '$TEST_REPO' --prompt '$EVAL_PROMPT' --output-dir '$EVAL_OUTPUT_DIR' --file-name '$(basename "$output_file")' --model '$MODEL'"
    
    echo "Command: $script_path $cmd_args" | tee -a "$log_file"
    
    # Run the command with stats collection
    local start_time=$(date +%s)
    local stats_output=""
    local cmd_output=""
    local exit_code=0
    
    # Use timeout command
    local timeout_cmd="timeout"
    if [[ "$(uname)" == "Darwin" ]] && command -v gtimeout >/dev/null 2>&1; then
        timeout_cmd="gtimeout"
    fi
    
    # Execute with time command if available
    if [[ -n "$TIME_CMD" ]]; then
        # Create temp file for time output
        local time_output=$(mktemp)
        
        # Run with time command
        if $TIME_CMD -o "$time_output" $timeout_cmd 300 bash -c "cd '$(dirname "$script_path")' && ./$(basename "$script_path") $cmd_args" >> "$log_file" 2>&1; then
            exit_code=0
        else
            exit_code=$?
        fi
        
        # Read and parse time output
        stats_output=$(cat "$time_output" 2>/dev/null)
        rm -f "$time_output"
        
        # Parse stats based on platform
        case "$PLATFORM" in
            linux)
                parse_stats_linux "$stats_output"
                ;;
            macos)
                parse_stats_macos "$stats_output"
                ;;
        esac
    else
        # Fallback to simple timing
        if $timeout_cmd 300 bash -c "cd '$(dirname "$script_path")' && ./$(basename "$script_path") $cmd_args" >> "$log_file" 2>&1; then
            exit_code=0
        else
            exit_code=$?
        fi
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Use measured wall time if available, otherwise use simple duration
    if [[ -z "$LAST_WALL_TIME" ]]; then
        LAST_WALL_TIME="$duration"
    fi
    
    LAST_EXIT_CODE=$exit_code
    
    # Check results
    if [[ $exit_code -eq 0 ]]; then
        # Check if output file was created
        if [[ -f "$output_file" ]]; then
            local file_size=$(wc -c < "$output_file" | tr -d ' ')
            if [[ $file_size -gt 50 ]]; then
                local lines=$(wc -l < "$output_file" | tr -d ' ')
                echo -e "${GREEN}✓ Success${NC} - Generated $lines lines in ${LAST_WALL_TIME}s" | tee -a "$log_file"
                
                # Show stats if available
                if [[ -n "$LAST_CPU_PERCENT" ]]; then
                    echo "  CPU: ${LAST_CPU_PERCENT}%" | tee -a "$log_file"
                fi
                if [[ -n "$LAST_MEMORY_MB" ]]; then
                    echo "  Memory: ${LAST_MEMORY_MB} MB" | tee -a "$log_file"
                fi
                if [[ -n "$LAST_USER_TIME" ]] && [[ -n "$LAST_SYS_TIME" ]]; then
                    # Use scale=3 for millisecond precision
                    local cpu_time=$(echo "scale=3; $LAST_USER_TIME + $LAST_SYS_TIME" | bc)
                    # Format with printf to ensure we always show 3 decimal places
                    cpu_time=$(printf "%.3f" "$cpu_time")
                    echo "  CPU time: ${cpu_time}s" | tee -a "$log_file"
                fi
                
                # Extract preview
                echo "Preview:" | tee -a "$log_file"
                head -5 "$output_file" | sed 's/^/  /' | tee -a "$log_file"
                echo "  ..." | tee -a "$log_file"
                
                return 0
            else
                echo -e "${RED}✗ Failed${NC} - Output file too small (${file_size} bytes)" | tee -a "$log_file"
                return 1
            fi
        else
            echo -e "${RED}✗ Failed${NC} - No output file created" | tee -a "$log_file"
            return 1
        fi
    else
        if [[ $exit_code -eq 124 ]]; then
            echo -e "${RED}✗ Failed${NC} - Timeout after 300s" | tee -a "$log_file"
        else
            echo -e "${RED}✗ Failed${NC} - Exit code: $exit_code" | tee -a "$log_file"
        fi
        return 1
    fi
}

# Array to store all results
declare -a ALL_RESULTS

# Run all noframework implementations
run_all_noframework() {
    local log_file="${EVAL_OUTPUT_DIR}/eval-all-${TIMESTAMP}.log"
    
    echo "Tech Writer Evaluation - All Implementations" | tee "$log_file"
    echo "===========================================" | tee -a "$log_file"
    echo "Generated: $(date)" | tee -a "$log_file"
    echo "Model: $MODEL" | tee -a "$log_file"
    echo "Repository: $TEST_REPO" | tee -a "$log_file"
    echo "Platform: $PLATFORM" | tee -a "$log_file"
    echo "" | tee -a "$log_file"
    
    # Find all implementations
    local implementations=()
    while IFS= read -r script; do
        local impl_name=$(basename "$(dirname "$script")")
        implementations+=("$impl_name:$script")
    done < <(find "$PROJECT_ROOT/noframework" -name "tech-writer.sh" -type f | sort)
    
    local total=${#implementations[@]}
    local count=0
    
    echo "Found $total implementations to test" | tee -a "$log_file"
    echo "" | tee -a "$log_file"
    
    # Test each implementation
    for impl in "${implementations[@]}"; do
        count=$((count + 1))
        local name="${impl%%:*}"
        local script="${impl#*:}"
        
        echo -e "\n${YELLOW}[$count/$total]${NC} Testing $name..." | tee -a "$log_file"
        
        if test_tech_writer_with_stats "$name" "$script" "$log_file"; then
            local status="PASS"
        else
            local status="FAIL"
        fi
        
        # Calculate CPU time for storage
        local cpu_time_for_storage=""
        if [[ -n "$LAST_USER_TIME" ]] && [[ -n "$LAST_SYS_TIME" ]]; then
            cpu_time_for_storage=$(echo "scale=3; $LAST_USER_TIME + $LAST_SYS_TIME" | bc)
            cpu_time_for_storage=$(printf "%.3f" "$cpu_time_for_storage")
        else
            cpu_time_for_storage="$LAST_WALL_TIME"  # Fallback to wall time if CPU time not available
        fi
        
        # Store result with CPU time instead of wall time
        ALL_RESULTS+=("$name|$status|$cpu_time_for_storage|$LAST_CPU_PERCENT|$LAST_MEMORY_MB")
    done
    
    # Generate report
    generate_comparison_report "$log_file"
    
    # Export if requested
    [[ -n "$CSV_OUTPUT" ]] && export_csv
    [[ -n "$JSON_OUTPUT" ]] && export_json
}

# Generate comparison report
generate_comparison_report() {
    local log_file="$1"
    
    echo -e "\n\n${YELLOW}=== COMPARISON REPORT ===${NC}" | tee -a "$log_file"
    echo "" | tee -a "$log_file"
    
    # Header
    printf "%-15s %-8s %-10s %-10s %-12s\n" "Implementation" "Status" "CPU Time (s)" "CPU (%)" "Memory (MB)" | tee -a "$log_file"
    printf "%-15s %-8s %-10s %-10s %-12s\n" "--------------" "------" "-----------" "--------" "-----------" | tee -a "$log_file"
    
    # Process results
    local fastest_time=999999
    local fastest_impl=""
    local lowest_mem=999999
    local lowest_mem_impl=""
    local total_passed=0
    
    for result in "${ALL_RESULTS[@]}"; do
        IFS='|' read -r impl status time cpu mem <<< "$result"
        
        # Format values
        [[ -z "$time" ]] && time="N/A"
        [[ -z "$cpu" ]] && cpu="N/A"
        [[ -z "$mem" ]] && mem="N/A"
        
        # Track stats
        if [[ "$status" == "PASS" ]]; then
            total_passed=$((total_passed + 1))
            
            # Track fastest
            if [[ "$time" != "N/A" ]] && (( $(echo "$time < $fastest_time" | bc -l) )); then
                fastest_time="$time"
                fastest_impl="$impl"
            fi
            
            # Track lowest memory
            if [[ "$mem" != "N/A" ]] && (( $(echo "$mem < $lowest_mem" | bc -l) )); then
                lowest_mem="$mem"
                lowest_mem_impl="$impl"
            fi
        fi
        
        # Status symbol
        local status_symbol="✗"
        local status_color="$RED"
        if [[ "$status" == "PASS" ]]; then
            status_symbol="✓"
            status_color="$GREEN"
        fi
        
        # Print row
        printf "%-15s ${status_color}%-8s${NC} %-10s %-10s %-12s\n" \
            "$impl" "$status_symbol $status" "$time" "$cpu" "$mem" | tee -a "$log_file"
    done
    
    # Summary
    echo "" | tee -a "$log_file"
    echo "Summary:" | tee -a "$log_file"
    echo "- Total implementations: ${#ALL_RESULTS[@]}" | tee -a "$log_file"
    echo "- Passed: $total_passed" | tee -a "$log_file"
    echo "- Failed: $((${#ALL_RESULTS[@]} - total_passed))" | tee -a "$log_file"
    
    if [[ -n "$fastest_impl" ]]; then
        echo "- Fastest: $fastest_impl (${fastest_time}s)" | tee -a "$log_file"
    fi
    if [[ -n "$lowest_mem_impl" ]]; then
        echo "- Most memory efficient: $lowest_mem_impl (${lowest_mem} MB)" | tee -a "$log_file"
    fi
    
    # Platform note
    if [[ "$PLATFORM" == "windows" ]] || [[ -z "$TIME_CMD" ]]; then
        echo "" | tee -a "$log_file"
        echo "Note: CPU and memory stats not available on this platform" | tee -a "$log_file"
    fi
}

# Export results to CSV
export_csv() {
    echo "Implementation,Status,CPU Time (s),CPU (%),Memory (MB)" > "$CSV_OUTPUT"
    for result in "${ALL_RESULTS[@]}"; do
        IFS='|' read -r impl status time cpu mem <<< "$result"
        echo "$impl,$status,$time,$cpu,$mem" >> "$CSV_OUTPUT"
    done
    echo "Results exported to: $CSV_OUTPUT"
}

# Export results to JSON
export_json() {
    local json="{"
    json+="\"timestamp\":\"$(date -Iseconds)\","
    json+="\"model\":\"$MODEL\","
    json+="\"repository\":\"$TEST_REPO\","
    json+="\"platform\":\"$PLATFORM\","
    json+="\"results\":["
    
    local first=true
    for result in "${ALL_RESULTS[@]}"; do
        IFS='|' read -r impl status time cpu mem <<< "$result"
        
        [[ "$first" == "false" ]] && json+=","
        first=false
        
        json+="{\"implementation\":\"$impl\","
        json+="\"status\":\"$status\","
        json+="\"cpu_time_seconds\":${time:-null},"
        json+="\"cpu_percent\":${cpu:-null},"
        json+="\"memory_mb\":${mem:-null}}"
    done
    
    json+="]}"
    
    echo "$json" | jq . > "$JSON_OUTPUT"
    echo "Results exported to: $JSON_OUTPUT"
}

# Test single implementation (backward compatibility)
test_single_implementation() {
    local script_path="$1"
    local impl_name=$(basename "$(dirname "$script_path")")
    local log_file="${EVAL_OUTPUT_DIR}/eval-${impl_name}-${TIMESTAMP}.log"
    
    echo "Tech Writer Evaluation - $(date)" | tee "$log_file"
    echo "=======================================" | tee -a "$log_file"
    echo "Implementation: $impl_name" | tee -a "$log_file"
    echo "Script: $script_path" | tee -a "$log_file"
    echo "Test Repository: $TEST_REPO" | tee -a "$log_file"
    echo "Model: $MODEL" | tee -a "$log_file"
    echo "" | tee -a "$log_file"
    
    echo -e "\n${YELLOW}Starting Tech Writer Evaluation${NC}" | tee -a "$log_file"
    echo "=======================================" | tee -a "$log_file"
    
    if test_tech_writer_with_stats "$impl_name" "$script_path" "$log_file"; then
        echo -e "\n${GREEN}Test passed!${NC}" | tee -a "$log_file"
        exit 0
    else
        echo -e "\n${RED}Test failed.${NC}" | tee -a "$log_file"
        exit 1
    fi
}

# Main
main() {
    parse_args "$@"
    check_prerequisites
    
    if [[ "$ALL_NOFRAMEWORK" == "true" ]]; then
        run_all_noframework
    else
        # Check if script exists
        if [[ ! -f "$SINGLE_SCRIPT" ]]; then
            echo -e "${RED}ERROR: Script not found: $SINGLE_SCRIPT${NC}"
            exit 1
        fi
        test_single_implementation "$SINGLE_SCRIPT"
    fi
}

# Run main
main "$@"