#!/bin/bash

# Build script to create self-contained index.html
# Inlines all CSS and JavaScript dependencies

set -e  # Exit on error

echo "🔨 Building self-contained index.html..."

# Create build directory
rm -rf build
mkdir -p build/assets

# Copy all image assets
echo "📦 Copying image assets..."
cp -r assets/*.png assets/*.svg assets/*.ico build/assets/ 2>/dev/null || true

# Copy report.md
echo "📄 Copying report.md..."
cp report.md build/report.md

echo "📜 Processing JavaScript dependencies..."

# Create temporary directory for processing
temp_dir=$(mktemp -d)
trap "rm -rf $temp_dir" EXIT

# Extract and process JavaScript modules
cat > "$temp_dir/modules.js" << 'EOF'
// Inlined JavaScript modules
EOF

# Process base-component.js
if [ -f "src/components/base-component.js" ]; then
    echo "  - Processing base-component.js"
    echo "" >> "$temp_dir/modules.js"
    echo "// === base-component.js ===" >> "$temp_dir/modules.js"
    cat src/components/base-component.js | grep -v '^import' | sed 's/^export //' >> "$temp_dir/modules.js"
fi

# Process state-manager.js
if [ -f "src/state-manager.js" ]; then
    echo "  - Processing state-manager.js"
    echo "" >> "$temp_dir/modules.js"
    echo "// === state-manager.js ===" >> "$temp_dir/modules.js"
    cat src/state-manager.js | grep -v '^import' | sed 's/^export //' >> "$temp_dir/modules.js"
fi

# Process dom-helpers.js
if [ -f "src/utils/dom-helpers.js" ]; then
    echo "  - Processing dom-helpers.js"
    echo "" >> "$temp_dir/modules.js"
    echo "// === dom-helpers.js ===" >> "$temp_dir/modules.js"
    cat src/utils/dom-helpers.js | grep -v '^import' | sed 's/^export //' >> "$temp_dir/modules.js"
fi

# Process document-parser.js
if [ -f "src/components/document-parser.js" ]; then
    echo "  - Processing document-parser.js"
    echo "" >> "$temp_dir/modules.js"
    echo "// === document-parser.js ===" >> "$temp_dir/modules.js"
    cat src/components/document-parser.js | grep -v '^import' | sed 's/^export //' >> "$temp_dir/modules.js"
fi

# Add initialization
echo "" >> "$temp_dir/modules.js"
echo "// Initialize document parser globally" >> "$temp_dir/modules.js"
echo "window.documentParser = new DocumentParser();" >> "$temp_dir/modules.js"

# Process input-group-component.js separately (it's a web component)
if [ -f "src/components/input-group-component.js" ]; then
    echo "  - Processing input-group-component.js"
    cp src/components/input-group-component.js "$temp_dir/input-group-component.js"
fi

echo "🔧 Building final HTML..."

# Start building the final HTML
{
    # Process the HTML line by line
    while IFS= read -r line; do
        # Skip the external script tag for input-group-component
        if [[ "$line" =~ \<script\ src=\"\./src/components/input-group-component\.js ]]; then
            continue
        fi
        
        # When we hit the highlight.js scripts, inject our modules after them
        if [[ "$line" =~ \<script\ src=\"https://cdnjs\.cloudflare\.com/ajax/libs/highlight\.js.*bash\.min\.js ]]; then
            echo "$line"
            echo ""
            echo "    <!-- Inlined JavaScript modules -->"
            echo "    <script>"
            cat "$temp_dir/modules.js"
            echo "    </script>"
            echo ""
            echo "    <!-- Inlined input-group component -->"
            echo "    <script>"
            cat "$temp_dir/input-group-component.js"
            echo "    </script>"
            continue
        fi
        
        # Replace the import statement in the main script module
        if [[ "$line" =~ import.*documentParser.*from ]]; then
            echo "        // Document parser is now available globally"
            continue
        fi
        
        echo "$line"
    done < index.html
} > build/index.html

# Update asset paths to be relative
echo "📝 Updating asset paths..."
sed -i.bak 's|src="assets/|src="assets/|g' build/index.html
rm -f build/index.html.bak

# Final report
echo ""
echo "✅ Build complete!"
echo "📁 Output files:"
echo "   - build/index.html ($(wc -l < build/index.html) lines)"
echo "   - build/report.md"
if [ -n "$(ls -A build/assets 2>/dev/null)" ]; then
    echo "   - build/assets/ ($(ls -1 build/assets | wc -l) images)"
fi
echo ""
echo "🚀 To test: cd build && python3 -m http.server 8080"