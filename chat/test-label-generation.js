// Test script for quick action label generation
// Run this in the browser console after loading test-quick-action-labels.html

async function testLabelGeneration() {
    console.log('Testing Quick Action Label Generation...\n');
    
    // Test headings
    const testHeadings = [
        "Introduction to Machine Learning",
        "What is Machine Learning?",
        "Getting Started with Python",
        "Understanding Neural Networks",
        "Frequently Asked Questions",
        "How do I choose the right algorithm?",
        "Advanced Topics in AI",
        "Natural Language Processing"
    ];
    
    console.log('Input headings:');
    testHeadings.forEach((h, i) => console.log(`${i + 1}. ${h}`));
    
    try {
        console.log('\nGenerating labels...');
        const labels = await window.generateQuickActionLabels(testHeadings);
        
        console.log('\nGenerated labels:');
        labels.forEach((label, i) => {
            console.log(`${i + 1}. "${testHeadings[i]}" → "${label}"`);
        });
        
        console.log('\n✅ Label generation successful!');
    } catch (error) {
        console.error('\n❌ Label generation failed:', error);
    }
}

// Run the test
testLabelGeneration();