#!/bin/bash

# Benchmark script with time breakdown using available macOS tools
# This version works without sudo

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Enhanced Benchmarking with Time Breakdown ===${NC}"
echo

# Function to monitor network activity using netstat
monitor_network() {
    local pid=$1
    local interval=0.5
    local net_log=$(mktemp)
    
    # Get initial network stats
    local init_bytes=$(netstat -ib | grep -E '^en[0-9]|^lo0' | awk '{sum+=$7+$10} END {print sum}')
    
    # Monitor in background
    while kill -0 $pid 2>/dev/null; do
        sleep $interval
    done
    
    # Get final network stats
    local final_bytes=$(netstat -ib | grep -E '^en[0-9]|^lo0' | awk '{sum+=$7+$10} END {print sum}')
    local net_bytes=$((final_bytes - init_bytes))
    
    echo "$net_bytes" > "$net_log"
    echo "$net_log"
}

# Function to monitor disk I/O using iostat
monitor_disk() {
    local pid=$1
    local disk_log=$(mktemp)
    
    # Get initial disk stats
    local init_stats=$(iostat -Id disk0 2>/dev/null | tail -1 | awk '{print $3}')
    
    # Wait for process to complete
    while kill -0 $pid 2>/dev/null; do
        sleep 0.5
    done
    
    # Get final disk stats
    local final_stats=$(iostat -Id disk0 2>/dev/null | tail -1 | awk '{print $3}')
    local disk_mb=$(echo "scale=2; ($final_stats - $init_stats) / 1024" | bc)
    
    echo "$disk_mb" > "$disk_log"
    echo "$disk_log"
}

# Function to analyze git operations
analyze_git_time() {
    local log_file=$1
    local git_start=""
    local git_end=""
    local git_time=0
    
    # Look for git clone/pull operations in the log
    if grep -q "Cloning repository\|Updating existing repository" "$log_file"; then
        # Extract timestamps
        git_start=$(grep -E "Cloning repository|Updating existing repository" "$log_file" | head -1 | awk '{print $1 " " $2}')
        git_end=$(grep -A10 -E "Cloning repository|Updating existing repository" "$log_file" | grep -E "Starting analysis|Step 1" | head -1 | awk '{print $1 " " $2}')
        
        if [[ -n "$git_start" ]] && [[ -n "$git_end" ]]; then
            # Convert to seconds (simplified - assumes same day)
            local start_sec=$(date -j -f "%Y-%m-%d %H:%M:%S" "$git_start" +%s 2>/dev/null || echo 0)
            local end_sec=$(date -j -f "%Y-%m-%d %H:%M:%S" "$git_end" +%s 2>/dev/null || echo 0)
            git_time=$((end_sec - start_sec))
        fi
    fi
    
    echo "$git_time"
}

# Test with bash implementation
echo -e "${YELLOW}Testing bash implementation with enhanced monitoring...${NC}"
echo

# Prepare test
TEST_DIR=$(mktemp -d)
LOG_FILE="$TEST_DIR/benchmark.log"
TIME_OUTPUT="$TEST_DIR/time.out"

# Start the process with time command
echo "Starting benchmark..."
/usr/bin/time -l -o "$TIME_OUTPUT" bash /Users/julian/expts/awesome-agent-showcase/noframework/bash/tech-writer.sh \
    --repo 'https://github.com/axios/axios' \
    --prompt '/Users/julian/expts/awesome-agent-showcase/eval/eval.prompt.txt' \
    --output-dir "$TEST_DIR" \
    --file-name 'benchmark.md' \
    --model 'openai/gpt-4o-mini' > "$LOG_FILE" 2>&1 &

PID=$!

# Start monitors
echo "Starting monitors..."
NET_LOG=$(monitor_network $PID &)
DISK_LOG=$(monitor_disk $PID &)

# Wait for completion
wait $PID
EXIT_CODE=$?

echo
echo -e "${GREEN}=== Benchmark Results ===${NC}"
echo

# Parse time output
if [[ -f "$TIME_OUTPUT" ]]; then
    echo "Basic timing:"
    grep -E "real|user|sys" "$TIME_OUTPUT" | head -1
    echo
    
    # Extract values
    stats_line=$(grep -E "^\s+[0-9]+\.[0-9]+ real\s+[0-9]+\.[0-9]+ user\s+[0-9]+\.[0-9]+ sys" "$TIME_OUTPUT")
    if [[ -n "$stats_line" ]]; then
        real_time=$(echo "$stats_line" | awk '{print $1}')
        user_time=$(echo "$stats_line" | awk '{print $3}')
        sys_time=$(echo "$stats_line" | awk '{print $5}')
        
        echo "Time breakdown:"
        echo "  Total time: ${real_time}s"
        echo "  CPU time (user): ${user_time}s"
        echo "  CPU time (system): ${sys_time}s"
        
        # Calculate I/O wait time (approximation)
        cpu_total=$(echo "scale=2; $user_time + $sys_time" | bc)
        io_wait=$(echo "scale=2; $real_time - $cpu_total" | bc)
        echo "  I/O wait time: ~${io_wait}s"
        
        # Analyze git time from logs
        git_time=$(analyze_git_time "$LOG_FILE")
        if [[ "$git_time" -gt 0 ]]; then
            echo "  Git operations: ~${git_time}s"
            process_time=$(echo "scale=2; $real_time - $git_time" | bc)
            echo "  Processing time: ~${process_time}s"
        fi
    fi
    
    echo
    echo "Memory usage:"
    grep "peak memory footprint" "$TIME_OUTPUT"
fi

# Network stats (if available)
if [[ -f "$NET_LOG" ]]; then
    net_bytes=$(cat "$NET_LOG")
    if [[ "$net_bytes" -gt 0 ]]; then
        net_mb=$(echo "scale=2; $net_bytes / 1024 / 1024" | bc)
        echo
        echo "Network usage: ~${net_mb} MB transferred"
    fi
fi

# Disk stats (if available)
if [[ -f "$DISK_LOG" ]]; then
    disk_mb=$(cat "$DISK_LOG")
    if [[ -n "$disk_mb" ]] && [[ "$disk_mb" != "0" ]]; then
        echo "Disk I/O: ~${disk_mb} MB"
    fi
fi

echo
echo -e "${YELLOW}Note: For more accurate measurements, consider:${NC}"
echo "1. Using sudo with dtrace/fs_usage/nettop for detailed I/O tracking"
echo "2. Installing Xcode for instruments command"
echo "3. Using specialized profiling tools like iperf for network benchmarking"

# Cleanup
rm -rf "$TEST_DIR"