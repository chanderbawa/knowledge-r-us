#!/usr/bin/env python3
"""
Knowledge R Us - RAG-Powered Educational News App
Dynamic content generation using news-please, ChromaDB, and Ollama
"""

import streamlit as st
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
import traceback

# Import our cloud-compatible RAG system
from news_rag_cloud import get_cloud_rag_system, CloudNewsRAGSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_rag_system():
    """Initialize RAG system with error handling"""
    try:
        rag = get_cloud_rag_system()
        return rag
    except Exception as e:
        logger.error(f"Error initializing RAG system: {e}")
        st.error(f"Error initializing RAG system: {e}")
        return None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_articles(age_group: str, topic: str = None, count: int = 3):
    """Get articles with caching to improve performance"""
    try:
        rag = get_cloud_rag_system()
        return rag.get_educational_articles(age_group, topic, count)
    except Exception as e:
        logger.error(f"Error getting articles: {e}")
        return []

def refresh_news_database():
    """Refresh news database with latest articles"""
    try:
        rag = get_cloud_rag_system()
        with st.spinner("Fetching latest news articles..."):
            rag.refresh_news_database()
        st.success("News database updated successfully!")
        # Clear cache to get fresh articles
        get_cached_articles.clear()
    except Exception as e:
        logger.error(f"Error refreshing news database: {e}")
        st.error(f"Error refreshing news database: {e}")

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
            if 'adapted_for_age' in article:
                st.caption(f"Adapted for ages {article['adapted_for_age']}")
        
        # Display article content
        st.write(article['content'])
        
        # Display questions if available
        if 'questions' in article and article['questions']:
            st.subheader("🤔 Test Your Knowledge!")
            
            for j, question in enumerate(article['questions']):
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
        else:
            st.info("Questions are being generated... Please refresh to see them.")

def main():
    st.set_page_config(
        page_title="Knowledge R Us - RAG Powered",
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
    if 'rag_initialized' not in st.session_state:
        st.session_state.rag_initialized = False
    
    # Header
    st.title("🌟 Knowledge R Us")
    st.subheader("Learn About the World Through Real News! (RAG-Powered)")
    
    # Initialize RAG system
    if not st.session_state.rag_initialized:
        with st.spinner("Initializing AI-powered news system..."):
            rag = initialize_rag_system()
            if rag:
                st.session_state.rag_initialized = True
                st.success("AI system ready!")
            else:
                st.error("Failed to initialize AI system. Using fallback mode.")
                return
    
    # Sidebar for user settings and controls
    with st.sidebar:
        st.header("👤 User Profile")
        age_group = st.selectbox(
            "Select Age Group:",
            ["6-8", "9-11", "12-14", "15-17"],
            index=["6-8", "9-11", "12-14", "15-17"].index(st.session_state.user_age)
        )
        st.session_state.user_age = age_group
        
        st.header("🔄 News Controls")
        if st.button("🔄 Refresh News Database"):
            refresh_news_database()
        
        topic_filter = st.selectbox(
            "Topic Filter:",
            ["All Topics", "Science", "Technology", "Environment", "Space", "Health"],
            index=0
        )
        
        article_count = st.slider(
            "Number of Articles:",
            min_value=1,
            max_value=5,
            value=3
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
        
        # Get topic filter for API
        topic_query = None if topic_filter == "All Topics" else topic_filter.lower()
        
        # Load articles
        try:
            with st.spinner("Loading personalized articles..."):
                articles = get_cached_articles(age_group, topic_query, article_count)
            
            if not articles:
                st.warning("No articles found. Try refreshing the news database or check your internet connection.")
                st.info("Click 'Refresh News Database' in the sidebar to fetch latest articles.")
                return
            
            # Display articles
            for i, article in enumerate(articles):
                display_article_with_questions(article, age_group, i)
                
        except Exception as e:
            logger.error(f"Error loading articles: {e}")
            st.error("Error loading articles. Please try refreshing the news database.")
            st.code(str(e))
    
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
        st.subheader("🤖 AI System Status")
        if st.session_state.rag_initialized:
            st.success("✅ RAG System Active")
            st.success("✅ LLM Content Adaptation")
            st.success("✅ Dynamic Question Generation")
        else:
            st.error("❌ AI System Offline")
        
        # Fun facts about the system
        st.subheader("🤓 About This System")
        st.info("""
        This app uses:
        • **news-please** for real-time news extraction
        • **ChromaDB** for intelligent article search
        • **Ollama + Llama2** for content adaptation
        • **AI-generated** STEM questions
        """)

if __name__ == "__main__":
    main()
