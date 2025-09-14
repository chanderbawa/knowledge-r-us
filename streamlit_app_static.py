#!/usr/bin/env python3
"""
Knowledge R Us - Proof of Concept Demo
Educational news app that adapts content for different age groups
"""

import streamlit as st
import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple
import random

# Sample news articles for demo (in production, these would come from news APIs)
SAMPLE_ARTICLES = [
    {
        "title": "NASA Discovers Water on Mars",
        "content": "Scientists at NASA have confirmed the presence of liquid water beneath the surface of Mars. The discovery was made using advanced radar technology on the Mars Reconnaissance Orbiter. This finding could have significant implications for the possibility of life on Mars and future human missions to the red planet. The water appears to be in underground lakes, similar to those found beneath Antarctica on Earth.",
        "category": "science",
        "image_url": "https://via.placeholder.com/400x200/FF6B6B/FFFFFF?text=Mars+Water+Discovery",
        "date": "2024-01-15"
    },
    {
        "title": "New Species of Butterfly Discovered in Amazon",
        "content": "Researchers have identified a new species of butterfly in the Amazon rainforest. The butterfly, named Heliconius amazonia, has unique wing patterns that help it blend with local flowers. Scientists believe there may be thousands more undiscovered species in the rainforest. The discovery highlights the importance of protecting these ecosystems from deforestation.",
        "category": "nature",
        "image_url": "https://via.placeholder.com/400x200/4ECDC4/FFFFFF?text=Amazon+Butterfly",
        "date": "2024-01-14"
    },
    {
        "title": "Solar Panel Efficiency Reaches Record High",
        "content": "Engineers have developed solar panels that can convert 47% of sunlight into electricity, breaking previous efficiency records. The new technology uses multiple layers of different materials to capture more of the sun's energy spectrum. This breakthrough could make solar energy much more affordable and help combat climate change by reducing our dependence on fossil fuels.",
        "category": "technology",
        "image_url": "https://via.placeholder.com/400x200/45B7D1/FFFFFF?text=Solar+Technology",
        "date": "2024-01-13"
    }
]

class ContentAdapter:
    """Adapts news content for different age groups"""
    
    AGE_GROUPS = {
        "6-8": {"reading_level": 1, "vocab_complexity": "simple"},
        "9-11": {"reading_level": 2, "vocab_complexity": "moderate"},
        "12-14": {"reading_level": 3, "vocab_complexity": "intermediate"},
        "15-18": {"reading_level": 4, "vocab_complexity": "advanced"}
    }
    
    VOCABULARY_REPLACEMENTS = {
        "simple": {
            "scientists": "smart people who study things",
            "researchers": "people who find out new things",
            "technology": "cool new tools",
            "implications": "what this means",
            "significant": "very important",
            "confirmed": "made sure",
            "advanced": "very good",
            "efficiency": "how well something works"
        },
        "moderate": {
            "implications": "what this could mean",
            "significant": "important",
            "confirmed": "proved",
            "efficiency": "how well it works"
        }
    }
    
    def adapt_content(self, article: Dict, age_group: str) -> Dict:
        """Adapt article content for specific age group"""
        adapted = article.copy()
        
        if age_group in ["6-8", "9-11"]:
            adapted["content"] = self._simplify_text(article["content"], age_group)
            adapted["title"] = self._simplify_text(article["title"], age_group)
        
        return adapted
    
    def _simplify_text(self, text: str, age_group: str) -> str:
        """Simplify text based on age group"""
        simplified = text
        
        # Replace complex vocabulary
        vocab_level = self.AGE_GROUPS[age_group]["vocab_complexity"]
        if vocab_level in self.VOCABULARY_REPLACEMENTS:
            for complex_word, simple_word in self.VOCABULARY_REPLACEMENTS[vocab_level].items():
                simplified = re.sub(r'\b' + complex_word + r'\b', simple_word, simplified, flags=re.IGNORECASE)
        
        # Simplify sentences for younger kids
        if age_group == "6-8":
            sentences = simplified.split('. ')
            short_sentences = []
            for sentence in sentences:
                if len(sentence.split()) > 15:  # Break long sentences
                    words = sentence.split()
                    mid = len(words) // 2
                    short_sentences.append(' '.join(words[:mid]) + '.')
                    short_sentences.append(' '.join(words[mid:]))
                else:
                    short_sentences.append(sentence)
            simplified = ' '.join(short_sentences)
        
        return simplified

class QuestionGenerator:
    """Generates STEM questions based on articles and age groups"""
    
    def generate_questions(self, article: Dict, age_group: str) -> List[Dict]:
        """Generate age-appropriate STEM questions"""
        questions = []
        
        # Math questions
        math_q = self._generate_math_question(article, age_group)
        if math_q:
            questions.append(math_q)
        
        # Science questions
        science_q = self._generate_science_question(article, age_group)
        if science_q:
            questions.append(science_q)
        
        return questions
    
    def _generate_math_question(self, article: Dict, age_group: str) -> Dict:
        """Generate math questions based on article content"""
        title = article["title"]
        content = article["content"]
        
        if age_group == "6-8":
            if "Mars" in title:
                return {
                    "type": "math",
                    "question": "If NASA sent 3 robots to Mars and found 2 underground lakes, how many things did they discover in total?",
                    "options": ["4", "5", "6", "7"],
                    "correct": "5",
                    "explanation": "3 robots + 2 lakes = 5 things total!"
                }
            elif "butterfly" in title.lower():
                return {
                    "type": "math",
                    "question": "Scientists found 1 new butterfly species. If there are 4 wings on each butterfly, how many wings in total?",
                    "options": ["2", "3", "4", "5"],
                    "correct": "4",
                    "explanation": "1 butterfly × 4 wings = 4 wings!"
                }
        
        elif age_group == "9-11":
            if "Mars" in title:
                return {
                    "type": "math",
                    "question": "If Mars is about 225 million kilometers from Earth, how many millions is that?",
                    "options": ["200", "225", "250", "300"],
                    "correct": "225",
                    "explanation": "Mars is about 225 million kilometers away from Earth!"
                }
            elif "47%" in content:
                return {
                    "type": "math",
                    "question": "If solar panels can convert 47% of sunlight to electricity, how much sunlight is NOT converted?",
                    "options": ["43%", "53%", "57%", "63%"],
                    "correct": "53%",
                    "explanation": "100% - 47% = 53% is not converted"
                }
        
        elif age_group in ["12-14", "15-18"]:
            if "Mars" in title:
                return {
                    "type": "math",
                    "question": "If it takes light 12.5 minutes to travel from Mars to Earth, and light travels at 300,000 km/s, what's the approximate distance?",
                    "options": ["150 million km", "225 million km", "300 million km", "400 million km"],
                    "correct": "225 million km",
                    "explanation": "12.5 minutes × 60 seconds × 300,000 km/s ≈ 225 million km"
                }
            elif "47%" in content:
                return {
                    "type": "math",
                    "question": "If a solar panel receives 1000 watts of sunlight and is 47% efficient, how much electricity does it produce?",
                    "options": ["430W", "470W", "530W", "570W"],
                    "correct": "470W",
                    "explanation": "1000W × 0.47 = 470W of electricity"
                }
        
        return None
    
    def _generate_science_question(self, article: Dict, age_group: str) -> Dict:
        """Generate science questions based on article content"""
        title = article["title"]
        content = article["content"]
        
        if "Mars" in title:
            if age_group == "6-8":
                return {
                    "type": "science",
                    "question": "What did scientists find on Mars?",
                    "options": ["Rocks", "Water", "Trees", "Animals"],
                    "correct": "Water",
                    "explanation": "Scientists found water under the ground on Mars!"
                }
            elif age_group == "9-11":
                return {
                    "type": "science",
                    "question": "What tool did scientists use to find water on Mars?",
                    "options": ["Telescope", "Radar technology", "Microscope", "Camera"],
                    "correct": "Radar technology",
                    "explanation": "Scientists used advanced radar technology on the Mars Reconnaissance Orbiter to find the water!"
                }
            elif age_group in ["12-14", "15-18"]:
                return {
                    "type": "science",
                    "question": "Why is finding water on Mars important for future missions?",
                    "options": ["For drinking", "For fuel production", "For growing plants", "All of the above"],
                    "correct": "All of the above",
                    "explanation": "Water can be used for drinking, split into hydrogen/oxygen for fuel, and for growing food!"
                }
        
        elif "butterfly" in title.lower():
            if age_group == "6-8":
                return {
                    "type": "science",
                    "question": "Where do butterflies live?",
                    "options": ["Ocean", "Desert", "Rainforest", "Space"],
                    "correct": "Rainforest",
                    "explanation": "Many butterflies live in rainforests where there are lots of flowers!"
                }
            elif age_group == "9-11":
                return {
                    "type": "science",
                    "question": "Why do butterflies have colorful wing patterns?",
                    "options": ["To look pretty", "To blend with flowers", "To scare enemies", "To fly faster"],
                    "correct": "To blend with flowers",
                    "explanation": "Butterflies use their wing patterns to blend with flowers and hide from predators!"
                }
            elif age_group in ["12-14", "15-18"]:
                return {
                    "type": "science",
                    "question": "What does the discovery of new butterfly species tell us about biodiversity?",
                    "options": ["There are few species left", "Ecosystems are simple", "Many species remain undiscovered", "All species are known"],
                    "correct": "Many species remain undiscovered",
                    "explanation": "Scientists believe thousands more species remain undiscovered, highlighting the importance of protecting ecosystems!"
                }
        
        return None

def main():
    st.set_page_config(
        page_title="Knowledge R Us - Demo",
        page_icon="🌟",
        layout="wide"
    )
    
    # Initialize session state
    if 'user_age' not in st.session_state:
        st.session_state.user_age = "9-11"
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'questions_answered' not in st.session_state:
        st.session_state.questions_answered = 0
    if 'answered_questions' not in st.session_state:
        st.session_state.answered_questions = set()
    
    # Header
    st.title("🌟 Knowledge R Us")
    st.subheader("Learn About the World Through News!")
    
    # Sidebar for user settings
    with st.sidebar:
        st.header("👤 User Profile")
        age_group = st.selectbox(
            "Select Age Group:",
            ["6-8", "9-11", "12-14", "15-18"],
            index=["6-8", "9-11", "12-14", "15-18"].index(st.session_state.user_age)
        )
        st.session_state.user_age = age_group
        
        st.header("🏆 Progress")
        st.metric("Score", st.session_state.score)
        st.metric("Questions Answered", st.session_state.questions_answered)
        
        # Achievement badges
        st.header("🎖️ Achievements")
        if st.session_state.questions_answered >= 1:
            st.success("🔰 First Question!")
        if st.session_state.score >= 50:
            st.success("⭐ Star Learner!")
        if st.session_state.questions_answered >= 5:
            st.success("🧠 Knowledge Seeker!")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📰 Today's Articles")
        
        # Initialize adapters
        content_adapter = ContentAdapter()
        question_generator = QuestionGenerator()
        
        # Display articles
        for i, article in enumerate(SAMPLE_ARTICLES):
            with st.expander(f"📖 {article['title']}", expanded=(i == 0)):
                # Adapt content for age group
                adapted_article = content_adapter.adapt_content(article, age_group)
                
                # Display article
                st.image(article["image_url"], width=400)
                st.write(adapted_article["content"])
                st.caption(f"Category: {article['category'].title()} | Date: {article['date']}")
                
                # Generate and display questions
                questions = question_generator.generate_questions(article, age_group)
                
                if questions:
                    st.subheader("🤔 Test Your Knowledge!")
                    
                    for j, question in enumerate(questions):
                        question_key = f"q_{i}_{j}"
                        
                        st.write(f"**{question['type'].title()} Question:**")
                        st.write(question["question"])
                        
                        # Create radio button for answers
                        answer = st.radio(
                            "Choose your answer:",
                            question["options"],
                            key=question_key,
                            index=None
                        )
                        
                        # Check answer button
                        if st.button(f"Check Answer", key=f"check_{question_key}"):
                            if question_key not in st.session_state.answered_questions:
                                st.session_state.answered_questions.add(question_key)
                                if answer == question["correct"]:
                                    st.success(f"🎉 Correct! {question['explanation']}")
                                    st.session_state.score += 10
                                    st.session_state.questions_answered += 1
                                    st.balloons()
                                else:
                                    st.error(f"❌ Not quite right. {question['explanation']}")
                                    st.session_state.questions_answered += 1
                                
                                # Rerun to update sidebar
                                st.rerun()
                            else:
                                st.info("You've already answered this question!")
    
    with col2:
        st.header("🎮 Learning Quests")
        
        # Daily quest
        st.subheader("📅 Daily Quest")
        st.info("Read 2 articles and answer 3 questions correctly!")
        progress = min(st.session_state.questions_answered / 3, 1.0)
        st.progress(progress)
        
        if progress >= 1.0:
            st.success("🏆 Daily Quest Complete!")
        
        # Learning tips based on age
        st.subheader("💡 Learning Tips")
        if age_group == "6-8":
            st.write("🌟 Great job reading! Try to find numbers in the stories.")
        elif age_group == "9-11":
            st.write("🔍 Look for science words and try to explain them to someone else!")
        elif age_group == "12-14":
            st.write("🧪 Think about how science connects to everyday life.")
        else:
            st.write("🚀 Consider the broader implications of these discoveries!")
        
        # Fun facts
        st.subheader("🤓 Fun Facts")
        fun_facts = [
            "Mars is called the 'Red Planet' because of iron oxide (rust) on its surface!",
            "Butterflies taste with their feet!",
            "Solar panels work even on cloudy days!",
            "The Amazon rainforest produces 20% of the world's oxygen!"
        ]
        st.info(random.choice(fun_facts))

if __name__ == "__main__":
    main()
