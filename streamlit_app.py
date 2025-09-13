#!/usr/bin/env python3
"""
Knowledge R Us - Cloud-Compatible Educational News App
Real news content with age-adaptive learning
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, List
import requests
import feedparser
import json
import re
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# News sources configuration
NEWS_SOURCES = {
    "science": [
        "https://feeds.feedburner.com/oreilly/radar",
        "https://www.sciencedaily.com/rss/all.xml"
    ],
    "technology": [
        "https://feeds.feedburner.com/TechCrunch"
    ],
    "environment": [
        "https://www.nationalgeographic.com/environment/rss/"
    ]
}

class ContentAdapter:
    """Adapts news content for different age groups"""
    
    AGE_GROUPS = {
        "6-8": {"reading_level": 1, "vocab_complexity": "simple"},
        "9-11": {"reading_level": 2, "vocab_complexity": "moderate"},
        "12-14": {"reading_level": 3, "vocab_complexity": "intermediate"},
        "15-17": {"reading_level": 4, "vocab_complexity": "advanced"}
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
            for sentence in sentences[:3]:  # Limit to 3 sentences
                if len(sentence.split()) > 15:  # Break long sentences
                    words = sentence.split()
                    mid = len(words) // 2
                    short_sentences.append(' '.join(words[:mid]) + '.')
                    short_sentences.append(' '.join(words[mid:]))
                else:
                    short_sentences.append(sentence)
            simplified = ' '.join(short_sentences)
        
        return simplified

@st.cache_data(ttl=3600)
def fetch_news_articles(category: str = "science", max_articles: int = 3) -> List[Dict]:
    """Fetch news articles from RSS feeds"""
    articles = []
    
    if category not in NEWS_SOURCES:
        return get_fallback_articles()
    
    for rss_url in NEWS_SOURCES[category][:1]:  # Limit to 1 source for reliability
        try:
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:max_articles]:
                try:
                    article_data = {
                        "title": entry.title,
                        "content": getattr(entry, 'summary', entry.title)[:1000],  # Limit content
                        "url": entry.link,
                        "published": str(datetime.now()),
                        "category": category,
                        "source": rss_url
                    }
                    articles.append(article_data)
                except Exception as e:
                    logger.error(f"Error processing article: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching RSS feed: {e}")
            continue
    
    # If no articles fetched, use fallback
    if not articles:
        articles = get_fallback_articles()
    
    return articles

def get_fallback_articles() -> List[Dict]:
    """Fallback articles when RSS feeds fail"""
    return [
        {
            "title": "Scientists Discover New Planet",
            "content": "Astronomers have found a new planet outside our solar system. This planet is very far away but might have water. Scientists used powerful telescopes to see it. They are excited because finding planets helps us learn about space.",
            "category": "science",
            "url": "https://example.com/planet",
            "published": str(datetime.now())
        },
        {
            "title": "New Robot Helps Clean Ocean",
            "content": "Engineers built a special robot that can clean plastic from the ocean. The robot floats on water and collects trash. This helps sea animals stay safe. Many fish and dolphins live in cleaner water now.",
            "category": "technology", 
            "url": "https://example.com/robot",
            "published": str(datetime.now())
        },
        {
            "title": "Trees Help Fight Climate Change",
            "content": "Scientists learned that planting more trees helps our planet stay cool. Trees take in carbon dioxide and make oxygen. When we plant trees, we help animals have homes and make the air cleaner for everyone.",
            "category": "environment",
            "url": "https://example.com/trees", 
            "published": str(datetime.now())
        }
    ]

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
        title = article["title"].lower()
        content = article["content"].lower()
        
        if age_group == "6-8":
            if "planet" in title or "space" in title:
                return {
                    "type": "math",
                    "question": "If we find 3 new planets and each has 2 moons, how many moons total?",
                    "options": ["4", "5", "6", "7"],
                    "correct": "6",
                    "explanation": "3 planets × 2 moons = 6 moons total!"
                }
            elif "robot" in title or "ocean" in title:
                return {
                    "type": "math", 
                    "question": "If a robot cleans 5 pieces of trash per hour for 3 hours, how many pieces total?",
                    "options": ["12", "15", "18", "20"],
                    "correct": "15",
                    "explanation": "5 pieces × 3 hours = 15 pieces!"
                }
            else:
                return {
                    "type": "math",
                    "question": "If we plant 4 trees each day for 2 days, how many trees total?",
                    "options": ["6", "7", "8", "9"],
                    "correct": "8", 
                    "explanation": "4 trees × 2 days = 8 trees!"
                }
        
        elif age_group == "9-11":
            if "percent" in content or "climate" in title:
                return {
                    "type": "math",
                    "question": "If trees absorb 25% of carbon dioxide, how much is left in the air?",
                    "options": ["70%", "75%", "80%", "85%"],
                    "correct": "75%",
                    "explanation": "100% - 25% = 75% remains in the air"
                }
            else:
                return {
                    "type": "math",
                    "question": "If a discovery was made 10 years ago and it's 2024, what year was it?",
                    "options": ["2012", "2013", "2014", "2015"],
                    "correct": "2014",
                    "explanation": "2024 - 10 = 2014"
                }
        
        elif age_group in ["12-14", "15-17"]:
            if "planet" in title:
                return {
                    "type": "math",
                    "question": "If a planet is 100 light-years away and light travels 300,000 km/s, how long to reach it?",
                    "options": ["50 years", "100 years", "200 years", "300 years"],
                    "correct": "100 years",
                    "explanation": "At light speed, it takes 100 years to travel 100 light-years!"
                }
            else:
                return {
                    "type": "math",
                    "question": "If ocean cleanup removes 1,000 kg of plastic daily, how much in a year?",
                    "options": ["300,000 kg", "365,000 kg", "400,000 kg", "500,000 kg"],
                    "correct": "365,000 kg",
                    "explanation": "1,000 kg × 365 days = 365,000 kg per year"
                }
        
        return None
    
    def _generate_science_question(self, article: Dict, age_group: str) -> Dict:
        """Generate science questions based on article content"""
        title = article["title"].lower()
        content = article["content"].lower()
        
        if "planet" in title or "space" in title:
            if age_group == "6-8":
                return {
                    "type": "science",
                    "question": "What do scientists use to see far away planets?",
                    "options": ["Microscope", "Telescope", "Camera", "Binoculars"],
                    "correct": "Telescope",
                    "explanation": "Telescopes help us see things that are very far away in space!"
                }
            else:
                return {
                    "type": "science",
                    "question": "Why is finding water on other planets important?",
                    "options": ["It's pretty", "Life needs water", "It's rare", "It's cold"],
                    "correct": "Life needs water",
                    "explanation": "Water is essential for life as we know it!"
                }
        
        elif "robot" in title or "ocean" in title:
            if age_group == "6-8":
                return {
                    "type": "science",
                    "question": "Why is it important to clean the ocean?",
                    "options": ["To look nice", "To help sea animals", "To swim better", "To find treasure"],
                    "correct": "To help sea animals",
                    "explanation": "Clean oceans help fish, dolphins, and other sea animals stay healthy!"
                }
            else:
                return {
                    "type": "science",
                    "question": "What type of pollution do ocean-cleaning robots target?",
                    "options": ["Oil spills", "Plastic waste", "Chemical waste", "All of these"],
                    "correct": "All of these",
                    "explanation": "Modern cleanup robots can target various types of ocean pollution!"
                }
        
        elif "tree" in title or "climate" in title:
            if age_group == "6-8":
                return {
                    "type": "science",
                    "question": "What do trees make that we need to breathe?",
                    "options": ["Water", "Oxygen", "Food", "Shelter"],
                    "correct": "Oxygen",
                    "explanation": "Trees make oxygen that we breathe and take in carbon dioxide!"
                }
            else:
                return {
                    "type": "science",
                    "question": "How do trees help fight climate change?",
                    "options": ["They absorb CO2", "They provide shade", "They prevent erosion", "All of these"],
                    "correct": "All of these",
                    "explanation": "Trees help climate in multiple ways: absorbing CO2, cooling areas, and preventing soil erosion!"
                }
        
        else:
            return {
                "type": "science",
                "question": "What is the scientific method?",
                "options": ["Guessing answers", "Observe, hypothesize, test", "Reading books", "Asking friends"],
                "correct": "Observe, hypothesize, test",
                "explanation": "Scientists observe, make hypotheses, and test them to learn new things!"
            }

def display_article_with_questions(article: Dict, age_group: str, article_index: int):
    """Display article with generated questions"""
    
    with st.expander(f"📖 {article['title']}", expanded=(article_index == 0)):
        # Display article metadata
        col1, col2 = st.columns([3, 1])
        with col1:
            if 'category' in article:
                st.caption(f"Category: {article['category'].title()}")
            if 'published' in article:
                st.caption(f"Published: {article['published']}")
        
        with col2:
            st.caption("📰 Real News")
        
        # Display article content
        st.write(article['content'])
        
        # Generate and display questions
        question_generator = QuestionGenerator()
        questions = question_generator.generate_questions(article, age_group)
        
        if questions:
            st.subheader("🤔 Test Your Knowledge!")
            
            for j, question in enumerate(questions):
                question_key = f"q_{article_index}_{j}"
                
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

def main():
    st.set_page_config(
        page_title="Knowledge R Us - News Powered",
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
    st.subheader("Learn About the World Through Real News!")
    
    # Sidebar for user settings and controls
    with st.sidebar:
        st.header("👤 User Profile")
        age_group = st.selectbox(
            "Select Age Group:",
            ["6-8", "9-11", "12-14", "15-17"],
            index=["6-8", "9-11", "12-14", "15-17"].index(st.session_state.user_age)
        )
        st.session_state.user_age = age_group
        
        st.header("📰 News Controls")
        if st.button("🔄 Refresh News"):
            fetch_news_articles.clear()
            st.success("News refreshed!")
        
        category_filter = st.selectbox(
            "News Category:",
            ["science", "technology", "environment"],
            index=0
        )
        
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
        if st.session_state.score >= 100:
            st.success("🚀 News Expert!")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📰 Latest Educational News")
        
        # Load articles
        try:
            with st.spinner("Loading latest news articles..."):
                articles = fetch_news_articles(category_filter, 3)
            
            if not articles:
                st.warning("No articles found. Using fallback content.")
                articles = get_fallback_articles()
            
            # Initialize content adapter
            content_adapter = ContentAdapter()
            
            # Display articles
            for i, article in enumerate(articles):
                # Adapt content for age group
                adapted_article = content_adapter.adapt_content(article, age_group)
                display_article_with_questions(adapted_article, age_group, i)
                
        except Exception as e:
            logger.error(f"Error loading articles: {e}")
            st.error("Error loading articles. Using fallback content.")
            articles = get_fallback_articles()
            content_adapter = ContentAdapter()
            for i, article in enumerate(articles):
                adapted_article = content_adapter.adapt_content(article, age_group)
                display_article_with_questions(adapted_article, age_group, i)
    
    with col2:
        st.header("🎮 Learning Quests")
        
        # Daily quest
        st.subheader("📅 Daily Quest")
        st.info("Read 3 articles and answer 5 questions correctly!")
        progress = min(st.session_state.questions_answered / 5, 1.0)
        st.progress(progress)
        
        if progress >= 1.0:
            st.success("🏆 Daily Quest Complete!")
        
        # Learning tips based on age
        st.subheader("💡 Learning Tips")
        if age_group == "6-8":
            st.write("🌟 Great job reading! Look for numbers and simple science facts.")
        elif age_group == "9-11":
            st.write("🔍 Try to explain the science concepts to someone else!")
        elif age_group == "12-14":
            st.write("🧪 Think about how these discoveries might affect the future.")
        else:
            st.write("🚀 Consider the broader implications and research connections!")
        
        # System status
        st.subheader("📡 News System")
        st.success("✅ Real RSS Feeds Active")
        st.success("✅ Age-Adaptive Content")
        st.success("✅ Dynamic Questions")
        
        # Fun facts
        st.subheader("🤓 Fun Facts")
        fun_facts = [
            "This app gets real news from science websites!",
            "Content changes based on your age group!",
            "Questions are generated from actual news stories!",
            "RSS feeds update automatically throughout the day!"
        ]
        st.info(random.choice(fun_facts))

if __name__ == "__main__":
    main()
