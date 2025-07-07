#!/bin/bash

# Enhanced timing functions for the eval script
# These can be integrated into eval-tech-writer.sh

# Function to measure detailed timing with breakdown
measure_with_breakdown() {
    local script_path="$1"
    local cmd_args="$2"
    local log_file="$3"
    local timeout_duration="${4:-300}"
    
    # Prepare temp files
    local time_output=$(mktemp)
    local stdout_log=$(mktemp)
    local stderr_log=$(mktemp)
    
    # Get initial system state
    local start_time=$(date +%s.%N)
    local init_net=$(netstat -ib | grep -E '^en[0-9]' | awk '{sum+=$7+$10} END {print sum}')
    
    # Run the command with detailed timing
    if [[ "$(uname)" == "Darwin" ]]; then
        # Use caffeinate to prevent sleep during benchmark
        caffeinate -i /usr/bin/time -l -o "$time_output" timeout $timeout_duration bash -c "
            cd '$(dirname "$script_path")' && ./$(basename "$script_path") $cmd_args
        " > "$stdout_log" 2> "$stderr_log" &
    else
        /usr/bin/time -v -o "$time_output" timeout $timeout_duration bash -c "
            cd '$(dirname "$script_path")' && ./$(basename "$script_path") $cmd_args
        " > "$stdout_log" 2> "$stderr_log" &
    fi
    
    local pid=$!
    
    # Monitor the process
    local sample_interval=1
    local samples=0
    local cpu_samples=()
    
    while kill -0 $pid 2>/dev/null; do
        # Sample CPU usage
        if [[ "$(uname)" == "Darwin" ]]; then
            # Use ps to get CPU usage
            local cpu=$(ps -p $pid -o %cpu 2>/dev/null | tail -1 | tr -d ' ')
            [[ -n "$cpu" ]] && cpu_samples+=("$cpu")
        fi
        
        sleep $sample_interval
        ((samples++))
    done
    
    wait $pid
    local exit_code=$?
    
    # Get final system state
    local end_time=$(date +%s.%N)
    local final_net=$(netstat -ib | grep -E '^en[0-9]' | awk '{sum+=$7+$10} END {print sum}')
    
    # Calculate network usage
    local net_bytes=$((final_net - init_net))
    local net_mb=$(echo "scale=2; $net_bytes / 1024 / 1024" | bc)
    
    # Combine logs
    cat "$stdout_log" "$stderr_log" >> "$log_file"
    
    # Parse time output
    local stats_output=$(cat "$time_output" 2>/dev/null)
    
    # Parse timing data
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS format
        local stats_line=$(echo "$stats_output" | grep -E "^\s+[0-9]+\.[0-9]+ real\s+[0-9]+\.[0-9]+ user\s+[0-9]+\.[0-9]+ sys")
        if [[ -n "$stats_line" ]]; then
            LAST_REAL_TIME=$(echo "$stats_line" | awk '{print $1}')
            LAST_USER_TIME=$(echo "$stats_line" | awk '{print $3}')
            LAST_SYS_TIME=$(echo "$stats_line" | awk '{print $5}')
            LAST_WALL_TIME="$LAST_REAL_TIME"
            
            # Calculate CPU percentage
            if [[ "$LAST_REAL_TIME" != "0.00" ]]; then
                local cpu_calc=$(echo "scale=2; ($LAST_USER_TIME + $LAST_SYS_TIME) / $LAST_REAL_TIME * 100" | bc)
                LAST_CPU_PERCENT=$(echo "scale=1; $cpu_calc / 1" | bc)
            fi
            
            # Memory
            local mem_bytes=$(echo "$stats_output" | grep "peak memory footprint" | awk '{print $1}')
            if [[ -n "$mem_bytes" ]]; then
                LAST_MEMORY_MB=$(echo "scale=2; $mem_bytes / 1024 / 1024" | bc)
            fi
        fi
    fi
    
    # Calculate average CPU from samples
    if [[ ${#cpu_samples[@]} -gt 0 ]]; then
        local cpu_sum=0
        for cpu in "${cpu_samples[@]}"; do
            cpu_sum=$(echo "scale=2; $cpu_sum + $cpu" | bc)
        done
        LAST_AVG_CPU=$(echo "scale=1; $cpu_sum / ${#cpu_samples[@]}" | bc)
    fi
    
    # Calculate I/O wait time
    if [[ -n "$LAST_REAL_TIME" ]] && [[ -n "$LAST_USER_TIME" ]] && [[ -n "$LAST_SYS_TIME" ]]; then
        local cpu_time=$(echo "scale=2; $LAST_USER_TIME + $LAST_SYS_TIME" | bc)
        LAST_IO_WAIT=$(echo "scale=2; $LAST_REAL_TIME - $cpu_time" | bc)
    fi
    
    # Detect git operations from log
    LAST_GIT_TIME=0
    if grep -q "Cloning repository\|Updating existing repository" "$log_file"; then
        # Simple heuristic: if we see git operations and high I/O wait, attribute some to git
        if [[ -n "$LAST_IO_WAIT" ]] && (( $(echo "$LAST_IO_WAIT > 2" | bc) )); then
            # Estimate git time as portion of I/O wait
            LAST_GIT_TIME=$(echo "scale=2; $LAST_IO_WAIT * 0.7" | bc)
        fi
    fi
    
    # Set network usage
    LAST_NET_MB="$net_mb"
    
    # Cleanup
    rm -f "$time_output" "$stdout_log" "$stderr_log"
    
    return $exit_code
}

# Function to display enhanced results
display_enhanced_results() {
    local impl_name="$1"
    local exit_code="$2"
    local output_file="$3"
    local log_file="$4"
    
    if [[ $exit_code -eq 0 ]]; then
        # Check if output file was created and has content
        if [[ -f "$output_file" ]]; then
            local file_size=$(wc -c < "$output_file" | tr -d ' ')
            if [[ $file_size -gt 50 ]]; then
                local lines=$(wc -l < "$output_file" | tr -d ' ')
                echo -e "${GREEN}✓ Success${NC} - Generated $lines lines in ${LAST_WALL_TIME}s" | tee -a "$log_file"
                
                # Show detailed timing breakdown
                echo "  Timing breakdown:" | tee -a "$log_file"
                echo "    CPU time: ${LAST_USER_TIME}s user + ${LAST_SYS_TIME}s system" | tee -a "$log_file"
                
                if [[ -n "$LAST_CPU_PERCENT" ]]; then
                    echo "    CPU usage: ${LAST_CPU_PERCENT}%" | tee -a "$log_file"
                fi
                
                if [[ -n "$LAST_AVG_CPU" ]] && [[ "$LAST_AVG_CPU" != "0" ]]; then
                    echo "    Avg CPU: ${LAST_AVG_CPU}%" | tee -a "$log_file"
                fi
                
                if [[ -n "$LAST_IO_WAIT" ]]; then
                    echo "    I/O wait: ~${LAST_IO_WAIT}s" | tee -a "$log_file"
                fi
                
                if [[ -n "$LAST_GIT_TIME" ]] && [[ "$LAST_GIT_TIME" != "0" ]]; then
                    echo "    Git ops: ~${LAST_GIT_TIME}s (estimated)" | tee -a "$log_file"
                fi
                
                if [[ -n "$LAST_MEMORY_MB" ]]; then
                    echo "    Memory: ${LAST_MEMORY_MB} MB" | tee -a "$log_file"
                fi
                
                if [[ -n "$LAST_NET_MB" ]] && [[ "$LAST_NET_MB" != "0" ]]; then
                    echo "    Network: ~${LAST_NET_MB} MB" | tee -a "$log_file"
                fi
                
                # Show preview
                echo "Preview:" | tee -a "$log_file"
                head -5 "$output_file" | sed 's/^/  /' | tee -a "$log_file"
                echo "  ..." | tee -a "$log_file"
            else
                echo -e "${YELLOW}⚠ Warning${NC} - Output file too small (${file_size} bytes)" | tee -a "$log_file"
            fi
        else
            echo -e "${RED}✗ Failed${NC} - No output file generated" | tee -a "$log_file"
        fi
    else
        echo -e "${RED}✗ Failed${NC} - Exit code: $exit_code" | tee -a "$log_file"
    fi
    
    echo "" | tee -a "$log_file"
}

# Export functions and variables for use in eval script
export -f measure_with_breakdown
export -f display_enhanced_results
export LAST_REAL_TIME=""
export LAST_USER_TIME=""
export LAST_SYS_TIME=""
export LAST_WALL_TIME=""
export LAST_CPU_PERCENT=""
export LAST_AVG_CPU=""
export LAST_MEMORY_MB=""
export LAST_IO_WAIT=""
export LAST_GIT_TIME=""
export LAST_NET_MB=""

echo "Enhanced timing functions loaded. To use in eval-tech-writer.sh:"
echo "1. Source this file: source enhanced-eval-timing.sh"
echo "2. Replace run_single_test() with measure_with_breakdown()"
echo "3. Update results display to use display_enhanced_results()"