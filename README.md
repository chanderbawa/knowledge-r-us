# Knowledge R Us - Educational News App

## Overview
An interactive educational app that transforms news articles into age-appropriate learning experiences with STEM questions and gamification.

## Features
- **Age-Adaptive Content**: Articles automatically adjust vocabulary and complexity for different age groups (6-8, 9-11, 12-14, 15-17)
- **STEM Question Generation**: Math and science questions based on article content
- **Gamification**: Score tracking, achievements, and daily quests
- **Interactive Interface**: User-friendly web interface with progress tracking

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

## Demo Features

### 1. Age Selection
- Choose from 4 age groups in the sidebar
- Content automatically adapts based on selection

### 2. Sample Articles
- NASA Mars Water Discovery
- Amazon Butterfly Species
- Solar Panel Technology Breakthrough

### 3. Interactive Questions
- Age-appropriate math problems
- Science comprehension questions
- Immediate feedback and explanations

### 4. Gamification Elements
- Score tracking
- Achievement badges
- Daily quest progress
- Fun facts and learning tips

## Technical Architecture

### Core Components
- `ContentAdapter`: Simplifies vocabulary and sentence structure
- `QuestionGenerator`: Creates STEM questions based on content
- `Streamlit Interface`: Interactive web application

### Age Adaptation Logic
- **6-8 years**: Simple vocabulary, short sentences, basic counting
- **9-11 years**: Moderate complexity, elementary math concepts
- **12-14 years**: Intermediate vocabulary, fractions and percentages
- **15-17 years**: Advanced concepts, complex calculations

## Next Steps for Full Implementation
- Real news API integration
- Advanced NLP for better content adaptation
- User accounts and persistent progress
- Mobile app development
- Parent/teacher dashboard
- More sophisticated question generation

## Contact
This is the Knowledge R Us educational platform that adapts news content for different age groups with integrated STEM learning.
