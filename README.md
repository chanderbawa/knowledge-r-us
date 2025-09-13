# Knowledge R Us - Educational News App

## Overview
A cloud-compatible educational platform that transforms real news articles into age-appropriate learning experiences with comprehensive STEM + ELA questions, hint systems, and gamification elements.

## Features
- **Real News Integration**: Live RSS feeds from Science Daily, TechCrunch, and National Geographic
- **Age-Adaptive Content**: Multi-paragraph articles that automatically adjust vocabulary and complexity for different age groups (6-8, 9-11, 12-14, 15-17)
- **Comprehensive Question System**: Math, Science, and ELA questions generated from actual article content
- **Smart Hint System**: Wrong answers trigger helpful hints with retry opportunities
- **Learning Validation**: Detailed reasoning explanations for correct answers to reinforce understanding
- **Gamification**: Score tracking, achievement badges, daily quests, and progress monitoring
- **Cloud-Ready**: Streamlit Cloud compatible without heavy dependencies

## Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the App
```bash
# Start the Streamlit app
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## Current Capabilities

### 1. Real News Content
- **Live RSS Feeds**: Automatically fetches articles from Science Daily, TechCrunch, and National Geographic
- **Rich Content**: Multi-paragraph articles with detailed explanations for ages 9+
- **Fallback System**: High-quality backup articles when feeds are unavailable
- **Content Categories**: Science, Technology, and Environment topics

### 2. Age-Adaptive Learning
- **Ages 6-8**: Simplified vocabulary, short sentences, basic concepts
- **Ages 9-11**: Moderate complexity with accessible explanations
- **Ages 12-14**: Intermediate content with technical details
- **Ages 15-17**: Full complexity articles with advanced concepts

### 3. Comprehensive Question System
- **Math Questions**: Multiplication, percentages, rate problems, light-years calculations
- **Science Questions**: Scientific method, ecosystems, space exploration, climate science
- **ELA Questions**: Main idea, author's purpose, literary devices, vocabulary in context
- **Content-Based**: All questions dynamically generated from actual article content

### 4. Interactive Learning Features
- **Hint System**: First wrong answer provides helpful hints
- **Retry Mechanism**: Students can attempt questions twice
- **Learning Validation**: Detailed reasoning explanations for correct answers
- **Partial Credit**: Points awarded for effort even after second attempt

### 5. Gamification & Progress
- **Scoring System**: 10 points for correct answers, 5 for effort
- **Achievement Badges**: First Question, Star Learner, Knowledge Seeker, News Expert
- **Daily Quests**: Read 3 articles and answer 5 questions correctly
- **Progress Tracking**: Real-time score and question counters

## Technical Architecture

### Core Components
- **`ContentAdapter`**: Multi-level content adaptation with vocabulary replacement and sentence restructuring
- **`QuestionGenerator`**: Generates Math, Science, and ELA questions with hints and reasoning
- **`RSS Feed Parser`**: Extracts rich content from multiple news sources with HTML cleaning
- **`Streamlit Interface`**: Cloud-compatible web application with session state management

### Content Processing Pipeline
1. **RSS Feed Extraction**: Fetches articles from Science Daily, TechCrunch, National Geographic
2. **Content Cleaning**: Removes HTML tags, normalizes whitespace, preserves paragraph structure
3. **Age Adaptation**: 
   - **Ages 6-8**: Vocabulary replacement + sentence shortening (3 sentences max)
   - **Ages 9-11**: Moderate simplification + natural sentence breaks
   - **Ages 12-17**: Full content with formatting cleanup only
4. **Question Generation**: Content-aware questions across 3 subjects per article
5. **Interactive Learning**: Hint system + retry mechanism + reasoning validation

### Dependencies
- **Lightweight Stack**: `streamlit`, `requests`, `feedparser`, `python-dotenv`, `numpy`, `pandas`
- **Cloud Compatible**: No ChromaDB, no heavy ML libraries
- **RSS Sources**: Real-time news feeds with fallback content system

## Deployment

### Streamlit Cloud
The app is optimized for Streamlit Cloud deployment:
```bash
# Deploy directly from GitHub repository
# Requirements.txt contains only essential dependencies
# No SQLite/ChromaDB compatibility issues
```

### Local Development
```bash
git clone <repository>
cd knowledge-r-us
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Educational Impact

### Learning Outcomes
- **Cross-Curricular**: Integrates Math, Science, and ELA in single articles
- **Real-World Connection**: Current events make learning relevant and engaging
- **Scaffolded Support**: Hint system builds confidence and persistence
- **Metacognitive Development**: Reasoning explanations promote deeper understanding

### Age-Appropriate Progression
- **Elementary (6-11)**: Foundation building with supportive feedback
- **Middle School (12-14)**: Critical thinking with technical vocabulary
- **High School (15-17)**: Advanced analysis with full complexity content

## Contact
Knowledge R Us - Transforming news into personalized learning experiences across Math, Science, and ELA for students aged 6-17.
