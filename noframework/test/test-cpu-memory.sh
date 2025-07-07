#!/bin/bash

# Test script to figure out proper CPU and memory measurement on macOS

echo "=== Testing CPU and Memory Measurement on macOS ==="
echo

# Test 1: Simple sleep command
echo "Test 1: Sleep for 2 seconds (should show ~0% CPU)"
/usr/bin/time -l sleep 2 2>&1 | tee test1.out
echo

# Test 2: CPU-intensive task
echo "Test 2: CPU-intensive calculation (should show high CPU%)"
/usr/bin/time -l bash -c 'for i in {1..1000000}; do echo $((i*i)) > /dev/null; done' 2>&1 | tee test2.out
echo

# Test 3: Memory-intensive task
echo "Test 3: Memory allocation (should show higher memory)"
/usr/bin/time -l bash -c 'arr=(); for i in {1..100000}; do arr+=($i); done; sleep 0.1' 2>&1 | tee test3.out
echo

# Test 4: Real-world example - running a simple script
echo "Test 4: Running ls command"
/usr/bin/time -l ls -la /usr/bin 2>&1 | head -20 | tee test4.out
echo

echo "=== Parsing Results ==="
echo

for testfile in test*.out; do
    echo "Parsing $testfile:"
    
    # Extract the time stats line
    stats_line=$(grep -E "^\s+[0-9]+\.[0-9]+ real\s+[0-9]+\.[0-9]+ user\s+[0-9]+\.[0-9]+ sys" "$testfile")
    
    if [[ -n "$stats_line" ]]; then
        real_time=$(echo "$stats_line" | awk '{print $1}')
        user_time=$(echo "$stats_line" | awk '{print $3}')
        sys_time=$(echo "$stats_line" | awk '{print $5}')
        
        echo "  Raw: real=$real_time user=$user_time sys=$sys_time"
        
        # Calculate CPU percentage
        if [[ "$real_time" != "0.00" ]]; then
            cpu_percent=$(echo "scale=1; (($user_time + $sys_time) / $real_time) * 100" | bc)
            echo "  CPU: $cpu_percent%"
        else
            echo "  CPU: Cannot calculate (real_time=0)"
        fi
    else
        echo "  ERROR: Could not find time stats"
    fi
    
    # Extract memory
    mem_line=$(grep "peak memory footprint" "$testfile")
    if [[ -n "$mem_line" ]]; then
        mem_bytes=$(echo "$mem_line" | awk '{print $1}')
        mem_mb=$(echo "scale=2; $mem_bytes / 1024 / 1024" | bc)
        echo "  Memory: $mem_mb MB"
    else
        echo "  ERROR: Could not find memory stats"
    fi
    
    echo
done

echo "=== Testing with different time formats ==="
echo

# Test GNU time if available
if command -v gtime >/dev/null 2>&1; then
    echo "GNU time available, testing format:"
    gtime -f "real:%e user:%U sys:%S cpu:%P mem:%MKB" sleep 1
else
    echo "GNU time (gtime) not available"
fi

echo
echo "=== Raw time output for debugging ==="
echo "Full output of: /usr/bin/time -l echo test"
/usr/bin/time -l echo test 2>&1

# Cleanup
rm -f test*.out