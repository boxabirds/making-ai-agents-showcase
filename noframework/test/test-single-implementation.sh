#!/bin/bash

# Test a single implementation to see the actual time output

echo "Testing bash implementation with time command..."
echo

# Create a test output directory
mkdir -p test-output

# Run with time command and capture everything
echo "Running: /usr/bin/time -l bash ../bash/tech-writer.sh --repo 'https://github.com/axios/axios' --prompt '../../eval/eval.prompt.txt' --output-dir 'test-output' --file-name 'test.md' --model 'openai/gpt-4o-mini'"
echo

/usr/bin/time -l bash ../bash/tech-writer.sh \
    --repo 'https://github.com/axios/axios' \
    --prompt '../../eval/eval.prompt.txt' \
    --output-dir 'test-output' \
    --file-name 'test.md' \
    --model 'openai/gpt-4o-mini' 2>&1 | tee full-output.txt

echo
echo "=== Analyzing the output ==="
echo

# Extract just the time stats
stats_line=$(grep -E "^\s+[0-9]+\.[0-9]+ real\s+[0-9]+\.[0-9]+ user\s+[0-9]+\.[0-9]+ sys" full-output.txt)

if [[ -n "$stats_line" ]]; then
    echo "Found stats line: $stats_line"
    
    real_time=$(echo "$stats_line" | awk '{print $1}')
    user_time=$(echo "$stats_line" | awk '{print $3}')
    sys_time=$(echo "$stats_line" | awk '{print $5}')
    
    echo "Parsed values:"
    echo "  real_time: $real_time"
    echo "  user_time: $user_time"
    echo "  sys_time: $sys_time"
    
    if [[ "$real_time" != "0.00" ]] && command -v bc >/dev/null 2>&1; then
        cpu_percent=$(echo "scale=1; (($user_time + $sys_time) / $real_time) * 100" | bc)
        echo "  CPU: $cpu_percent%"
    else
        echo "  CPU: Cannot calculate"
    fi
else
    echo "ERROR: Could not find time stats line"
    echo "Looking for pattern: ^\\s+[0-9]+\\.[0-9]+ real\\s+[0-9]+\\.[0-9]+ user\\s+[0-9]+\\.[0-9]+ sys"
fi

# Show memory
mem_line=$(grep "peak memory footprint" full-output.txt)
if [[ -n "$mem_line" ]]; then
    echo "Memory line: $mem_line"
    mem_bytes=$(echo "$mem_line" | awk '{print $1}')
    mem_mb=$(echo "scale=2; $mem_bytes / 1024 / 1024" | bc)
    echo "  Memory: $mem_mb MB"
fi

# Cleanup
rm -rf test-output full-output.txt