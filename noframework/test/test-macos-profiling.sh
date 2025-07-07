#!/bin/bash

# Test various macOS profiling tools to measure process, disk, and network time

echo "=== Testing macOS Profiling Tools ==="
echo

# Test 1: Using dtrace (requires sudo)
echo "Test 1: dtrace capabilities (will skip if no sudo)"
if sudo -n true 2>/dev/null; then
    echo "dtrace available with sudo"
else
    echo "dtrace requires sudo - skipping"
fi
echo

# Test 2: Using fs_usage (requires sudo)
echo "Test 2: fs_usage for file system activity"
if command -v fs_usage >/dev/null 2>&1; then
    echo "fs_usage available (requires sudo to run)"
else
    echo "fs_usage not found"
fi
echo

# Test 3: Using nettop (requires sudo)
echo "Test 3: nettop for network activity"
if command -v nettop >/dev/null 2>&1; then
    echo "nettop available (requires sudo to run)"
else
    echo "nettop not found"
fi
echo

# Test 4: Using sample
echo "Test 4: sample command for CPU profiling"
if command -v sample >/dev/null 2>&1; then
    echo "sample available"
    # Test sampling a simple process
    sleep 1 &
    PID=$!
    sample $PID 1 2>&1 | head -20
    kill $PID 2>/dev/null || true
else
    echo "sample not found"
fi
echo

# Test 5: Using log stream for process events
echo "Test 5: log stream for process events"
if command -v log >/dev/null 2>&1; then
    echo "log command available"
else
    echo "log not found"
fi
echo

# Test 6: Using Activity Monitor's underlying tools
echo "Test 6: Using spindump (requires sudo)"
if command -v spindump >/dev/null 2>&1; then
    echo "spindump available (requires sudo)"
else
    echo "spindump not found"
fi
echo

# Test 7: Using instruments (part of Xcode)
echo "Test 7: Instruments command line tool"
if command -v instruments >/dev/null 2>&1; then
    echo "instruments available"
    instruments -s 2>&1 | grep -i "time\|network\|file" | head -10
else
    echo "instruments not found (requires Xcode)"
fi
echo

# Test 8: Using iotop (if installed)
echo "Test 8: iotop for disk I/O"
if command -v iotop >/dev/null 2>&1; then
    echo "iotop available"
else
    echo "iotop not found (can be installed via brew)"
fi
echo

# Test 9: Using dtruss (dtrace wrapper)
echo "Test 9: dtruss for system call tracing"
if command -v dtruss >/dev/null 2>&1; then
    echo "dtruss available (requires sudo)"
else
    echo "dtruss not found"
fi
echo

# Test 10: Check for homebrew tools
echo "Test 10: Checking for useful homebrew tools"
for tool in htop iftop nethogs; do
    if command -v $tool >/dev/null 2>&1; then
        echo "$tool is installed"
    else
        echo "$tool not found (can be installed via brew)"
    fi
done
echo

echo "=== Summary of Non-Sudo Options ==="
echo "1. /usr/bin/time -l: Basic timing and memory (what we're using now)"
echo "2. sample: CPU profiling without sudo"
echo "3. log stream: Can monitor process events"
echo "4. instruments: If Xcode is installed"
echo
echo "Most detailed profiling requires sudo access (dtrace, fs_usage, nettop)"