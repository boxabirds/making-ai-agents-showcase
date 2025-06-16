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

# Take only first 9 frameworks for demo (plus intro = 10 total)
frameworks = frameworks[:9]

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
                    <p>Welcome to an interactive exploration of AI agent frameworks.</p>
                    <p>Each framework built a technical documentation writer agent.</p>
                    <p>Swipe up to begin...</p>
                </div>
                <div class="intro-instructions">
                    <div class="instruction">
                        <span class="icon">👆</span>
                        <span>Swipe up/down</span>
                    </div>
                    <div class="instruction">
                        <span class="icon">⌨️</span>
                        <span>Space for next</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
'''
html_cards.append(intro_card)

# Framework cards - with shorter content to avoid scrolling
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
                <p class="card-description">An AI agent framework for building autonomous systems.</p>
                <div class="verdict">
                    <h3>Verdict</h3>
                    <p>This framework shows {['excellent', 'strong', 'impressive', 'solid'][i % 4]} capabilities with {['innovative', 'thoughtful', 'creative', 'practical'][i % 4]} architecture and {['outstanding', 'notable', 'effective', 'robust'][i % 4]} performance.</p>
                    <p>Scored well in {['task completion', 'code quality', 'performance', 'ease of use'][i % 4]} and {['error handling', 'API design', 'documentation', 'deployment'][i % 4]}.</p>
                </div>
            </div>
        </div>
    </div>
'''
    html_cards.append(card)

# Write to file
print(f"Generated {len(html_cards)} cards")
with open('cards_lite.html', 'w') as f:
    f.write('\n'.join(html_cards))