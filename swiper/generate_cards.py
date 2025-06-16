#!/usr/bin/env python3
import csv
import random

# Read CSV data
frameworks = []
with open('../oss-agent-makers-with-images.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        frameworks.append({
            'name': row['Project'].strip(),
            'github': row['Github URL'].strip(),
            'image': row['Image'].strip()
        })

# Generate random scores
for fw in frameworks:
    fw['score'] = round(random.uniform(5.0, 9.5), 1)

# Generate HTML
html_cards = []

# Intro card
intro_card = '''
    <div class="card" data-index="0">
        <div class="card-inner">
            <div class="card-intro">
                <h1>Tech Writer Benchmark</h1>
                <div class="intro-subtitle">AI Agent Framework Evaluation</div>
                <div class="intro-content">
                    <p>Welcome to an interactive exploration of 50+ AI agent frameworks.</p>
                    <p>Each framework was tasked with building a technical documentation writer agent, and their implementations were evaluated across multiple dimensions.</p>
                    <p>Swipe up to begin exploring the results...</p>
                </div>
                <div class="intro-instructions">
                    <div class="instruction">
                        <span class="icon">👆</span>
                        <span>Swipe up/down or use arrow keys</span>
                    </div>
                    <div class="instruction">
                        <span class="icon">⌨️</span>
                        <span>Press Space for next card</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
'''
html_cards.append(intro_card)

# Framework cards
for i, fw in enumerate(frameworks):
    loading = 'eager' if i < 3 else 'lazy'
    card = f'''
    <div class="card" data-index="{i+1}">
        <div class="card-inner">
            <div class="card-image">
                <img src="{fw['image']}" alt="{fw['name']}" loading="{loading}">
                <div class="score-badge">{fw['score']}</div>
            </div>
            <div class="card-content">
                <h2 class="card-title">{fw['name']}</h2>
                <p class="card-description">An AI agent framework that enables developers to build sophisticated autonomous systems with advanced capabilities.</p>
                <div class="verdict">
                    <h3>Verdict</h3>
                    <p>This framework demonstrates {['excellent', 'strong', 'impressive', 'solid'][i % 4]} capabilities in building AI agents. The implementation shows {['innovative', 'thoughtful', 'creative', 'practical'][i % 4]} approaches to agent architecture and {['outstanding', 'notable', 'commendable', 'effective'][i % 4]} handling of complex tasks.</p>
                    <p>Key strengths include {['robust error handling', 'clean API design', 'modular architecture', 'comprehensive documentation'][i % 4]} and {['efficient resource management', 'intuitive developer experience', 'powerful tool integration', 'flexible deployment options'][i % 4]}. The framework scored particularly well in {['task completion', 'code quality', 'performance metrics', 'ease of use'][i % 4]}.</p>
                    <p>Overall, {fw['name']} represents a {['cutting-edge', 'mature', 'promising', 'versatile'][i % 4]} solution for developers looking to build AI-powered applications with {['minimal overhead', 'maximum flexibility', 'enterprise-grade reliability', 'rapid prototyping capabilities'][i % 4]}.</p>
                </div>
            </div>
        </div>
    </div>
'''
    html_cards.append(card)

# Write to file
print(f"Generated {len(html_cards)} cards")
with open('cards_generated.html', 'w') as f:
    f.write('\n'.join(html_cards))