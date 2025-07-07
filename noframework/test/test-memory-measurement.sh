#!/bin/bash

# Test memory measurement on macOS

echo "=== Testing Memory Measurement on macOS ==="
echo

# Test 1: Direct execution of different implementations
echo "Test 1: Running different implementations directly with /usr/bin/time -l"
echo

# Test bash implementation
echo "--- Bash implementation ---"
/usr/bin/time -l bash -c 'echo "test" | head -1' 2>&1 | grep -E "maximum resident|peak memory"
echo

# Test Python
echo "--- Python hello world ---"
/usr/bin/time -l python3 -c "print('hello')" 2>&1 | grep -E "maximum resident|peak memory"
echo

# Test a memory-intensive Python script
echo "--- Python with large array ---"
/usr/bin/time -l python3 -c "arr = [i for i in range(1000000)]; print(len(arr))" 2>&1 | grep -E "maximum resident|peak memory"
echo

# Test Node.js
echo "--- Node.js hello world ---"
/usr/bin/time -l node -e "console.log('hello')" 2>&1 | grep -E "maximum resident|peak memory"
echo

# Test Go binary
echo "--- Go hello world ---"
/usr/bin/time -l sh -c 'echo "package main; import \"fmt\"; func main() { fmt.Println(\"hello\") }" > /tmp/test.go && go run /tmp/test.go' 2>&1 | grep -E "maximum resident|peak memory"
echo

# Test 2: What exactly is being measured?
echo "Test 2: Understanding the measurement"
echo

# Run a simple command and look at full output
echo "--- Full time output for 'echo test' ---"
/usr/bin/time -l echo "test" 2>&1 | tail -20
echo

# Test 3: Is it measuring the shell wrapper?
echo "Test 3: Testing the wrapper script measurement"
echo

# Create a test script that uses memory
cat > /tmp/memory-test.sh << 'EOF'
#!/bin/bash
# Allocate some memory
arr=()
for i in {1..100000}; do
    arr+=("This is a test string number $i")
done
echo "Allocated ${#arr[@]} strings"
EOF
chmod +x /tmp/memory-test.sh

echo "--- Direct script execution ---"
/usr/bin/time -l /tmp/memory-test.sh 2>&1 | grep -E "maximum resident|peak memory"
echo

echo "--- Via bash -c ---"
/usr/bin/time -l bash -c '/tmp/memory-test.sh' 2>&1 | grep -E "maximum resident|peak memory"
echo

# Test 4: The actual tech-writer scripts
echo "Test 4: Testing actual tech-writer memory usage"
echo

# Test with a smaller task to avoid network delays
TEST_PROMPT="What programming language is this?"

# Bash implementation
if [[ -f /Users/julian/expts/awesome-agent-showcase/noframework/bash/tech-writer.sh ]]; then
    echo "--- Bash tech-writer (minimal task) ---"
    echo "$TEST_PROMPT" > /tmp/test-prompt.txt
    /usr/bin/time -l /Users/julian/expts/awesome-agent-showcase/noframework/bash/tech-writer.sh \
        --repo 'https://github.com/axios/axios' \
        --prompt '/tmp/test-prompt.txt' \
        --output-dir '/tmp' \
        --file-name 'mem-test.md' \
        --model 'openai/gpt-4o-mini' 2>&1 | grep -E "maximum resident|peak memory" | head -2
fi
echo

# Python implementation  
if [[ -f /Users/julian/expts/awesome-agent-showcase/noframework/python/tech-writer.sh ]]; then
    echo "--- Python tech-writer (minimal task) ---"
    /usr/bin/time -l /Users/julian/expts/awesome-agent-showcase/noframework/python/tech-writer.sh \
        --repo 'https://github.com/axios/axios' \
        --prompt '/tmp/test-prompt.txt' \
        --output-dir '/tmp' \
        --file-name 'mem-test-py.md' \
        --model 'openai/gpt-4o-mini' 2>&1 | grep -E "maximum resident|peak memory" | head -2
fi
echo

# Test 5: Check if it's the measurement resolution
echo "Test 5: Memory measurement resolution"
echo

# Check page size
pagesize=$(pagesize)
echo "System page size: $pagesize bytes"
echo "1.17 MB = $(echo "1.17 * 1024 * 1024" | bc) bytes"
echo "1.17 MB in pages: $(echo "1.17 * 1024 * 1024 / $pagesize" | bc) pages"
echo "1.18 MB = $(echo "1.18 * 1024 * 1024" | bc) bytes"
echo "1.18 MB in pages: $(echo "1.18 * 1024 * 1024 / $pagesize" | bc) pages"

# Cleanup
rm -f /tmp/test.go /tmp/memory-test.sh /tmp/test-prompt.txt /tmp/mem-test*.md