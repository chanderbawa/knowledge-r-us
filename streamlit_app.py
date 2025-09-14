#!/usr/bin/env python3
"""
Knowledge R Us - Cloud-Compatible Educational News App
Real news content with age-adaptive learning and user authentication
"""

import streamlit as st
import json
import bcrypt
import logging
from datetime import datetime
import feedparser
import re
from typing import Dict, List
# Import authentication system
from auth_system import UserProfileManager, show_login_page, show_profile_selection, show_kid_dashboard
from streamlit_data_storage import StreamlitDataManager
from llm_api_integration import setup_llm_provider
from pwa_config import add_pwa_config, add_mobile_styles, add_install_prompt

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
        
        if age_group == "6-8":
            # Significantly simplify for youngest group
            adapted["content"] = self._simplify_text(article["content"], age_group)
            adapted["title"] = self._simplify_text(article["title"], age_group)
        elif age_group == "9-11":
            # Moderate simplification but keep more content
            adapted["content"] = self._moderate_simplify(article["content"])
            adapted["title"] = self._simplify_text(article["title"], age_group)
        else:
            # Keep full content for older students (12-14, 15-18)
            # Just clean up any remaining HTML or formatting issues
            adapted["content"] = self._clean_content(article["content"])
        
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
    
    def _moderate_simplify(self, text: str) -> str:
        """Moderate simplification for ages 9-11 - keep content but make it accessible"""
        # Replace some complex vocabulary but keep most content
        vocab_replacements = self.VOCABULARY_REPLACEMENTS.get("moderate", {})
        simplified = text
        
        for complex_word, simple_word in vocab_replacements.items():
            simplified = re.sub(r'\b' + complex_word + r'\b', simple_word, simplified, flags=re.IGNORECASE)
        
        # Break very long sentences but keep all content
        sentences = simplified.split('. ')
        processed_sentences = []
        
        for sentence in sentences:
            if len(sentence.split()) > 25:  # If sentence is very long
                # Find a natural break point (comma, semicolon, etc.)
                parts = re.split(r'[,;]', sentence, 1)
                if len(parts) > 1:
                    processed_sentences.append(parts[0].strip() + '.')
                    processed_sentences.append(parts[1].strip())
                else:
                    processed_sentences.append(sentence)
            else:
                processed_sentences.append(sentence)
        
        return '. '.join(processed_sentences)
    
    def _clean_content(self, text: str) -> str:
        """Clean content for older students without simplification"""
        # Remove any remaining HTML tags
        cleaned = re.sub(r'<[^>]+>', '', text)
        # Clean up whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        # Ensure proper paragraph breaks
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        return cleaned

def generate_article_id(article: Dict) -> str:
    """Generate a unique ID for an article based on title and content"""
    import hashlib
    content = f"{article['title']}{article.get('content', '')[:100]}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def check_if_article_completed(article_index: int) -> bool:
    """Check if all questions for an article have been answered"""
    # Generate question keys for this article
    question_types = ['math', 'science', 'ela']
    all_answered = True
    
    for q_type in question_types:
        question_key = f"question_{article_index}_{q_type}"
        if question_key not in st.session_state.answered_questions:
            all_answered = False
            break
    
    return all_answered

@st.cache_data(ttl=3600)
def fetch_news_articles(category: str = "science", max_articles: int = 3, completed_articles: List[str] = None) -> List[Dict]:
    """Fetch real news articles from RSS feeds without hallucination"""
    articles = []
    completed_articles = completed_articles or []
    
    if category not in NEWS_SOURCES:
        return get_fallback_articles(completed_articles)
    
    for rss_url in NEWS_SOURCES[category][:2]:  # Use 2 sources for more variety
        try:
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:max_articles * 3]:  # Get more to filter completed ones
                try:
                    # Generate article ID based on URL for consistency
                    article_id = generate_article_id({
                        'title': entry.title,
                        'url': entry.get('link', ''),
                        'content': entry.get('summary', entry.get('description', ''))
                    })
                    
                    # Skip if article is completed
                    if article_id in completed_articles:
                        continue
                    
                    # Extract content - use ONLY what's in the RSS feed
                    content = entry.get('summary', entry.get('description', ''))
                    if not content or len(content.strip()) < 50:
                        continue
                    
                    # Clean content but preserve original facts
                    cleaned_content = re.sub(r'<[^>]+>', '', content)  # Remove HTML
                    cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()  # Clean whitespace
                    
                    # Ensure we have substantial content
                    if len(cleaned_content) < 100:
                        continue
                    
                    article = {
                        'id': article_id,
                        'title': entry.title,
                        'content': cleaned_content,  # Use original content without modification
                        'category': category,
                        'url': entry.get('link', ''),
                        'published': entry.get('published', str(datetime.now())),
                        'source': 'RSS Feed'  # Mark as real news
                    }
                    
                    articles.append(article)
                    
                    if len(articles) >= max_articles:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing entry: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching from {rss_url}: {e}")
            continue
    
    # If no articles found, return filtered fallback
    if not articles:
        return get_fallback_articles(completed_articles)[:max_articles]
    
    return articles[:max_articles]

def get_fallback_articles(completed_articles: List[str] = None) -> List[Dict]:
    """Fallback articles when RSS feeds fail - real science news content"""
    completed_articles = completed_articles or []
    
    fallback_articles = [
        {
            "id": "fallback_planet_discovery",
            "title": "Scientists Discover New Planet",
            "content": "Astronomers have made an exciting discovery in deep space - a new planet outside our solar system called an exoplanet. This distant world, located about 100 light-years from Earth, has captured scientists' attention because it might have conditions suitable for liquid water.\n\nUsing powerful space telescopes like the James Webb Space Telescope, researchers detected this planet by observing tiny changes in starlight as the planet passed in front of its host star. This method, called the transit technique, allows scientists to learn about the planet's size, atmosphere, and potential for supporting life.\n\nThe discovery is particularly significant because the planet orbits within its star's 'habitable zone' - the region where temperatures are just right for liquid water to exist. While we can't visit this planet with current technology, studying it helps us understand how planetary systems form and whether life might exist elsewhere in the universe.",
            "category": "science",
            "url": "https://example.com/planet",
            "published": str(datetime.now()),
            "source": "Fallback"
        },
        {
            "id": "fallback_ocean_robot",
            "title": "New Robot Helps Clean Ocean",
            "content": "Marine engineers have developed an innovative autonomous robot designed to tackle one of our planet's biggest environmental challenges: ocean pollution. This solar-powered device, roughly the size of a small boat, uses advanced sensors and artificial intelligence to identify and collect plastic waste floating on the ocean's surface.\n\nThe robot operates by scanning the water with cameras and using machine learning algorithms to distinguish between marine life and debris. Once plastic is detected, mechanical arms extend to carefully collect the waste without harming sea creatures. The collected plastic is stored in onboard compartments that can hold up to 500 kilograms of debris.\n\nEarly trials in the Pacific Ocean have shown promising results, with the robot collecting over 2,000 pieces of plastic waste in just one month. The technology represents a significant step forward in ocean conservation efforts. Scientists estimate that if deployed at scale, these robots could help remove millions of tons of plastic from our oceans, protecting marine ecosystems and the food chain that depends on healthy seas.",
            "category": "technology", 
            "url": "https://example.com/robot",
            "published": str(datetime.now()),
            "source": "Fallback"
        },
        {
            "id": "fallback_climate_trees",
            "title": "Trees Help Fight Climate Change",
            "content": "Climate scientists have published new research highlighting the crucial role that forests play in combating global warming. Trees act as natural carbon capture systems, absorbing carbon dioxide from the atmosphere during photosynthesis and storing it in their wood, roots, and surrounding soil.\n\nThe study, conducted across multiple continents, found that mature forests can absorb up to 2.6 tons of carbon dioxide per acre annually. This process not only removes greenhouse gases from the atmosphere but also produces oxygen as a byproduct. Additionally, forests create cooling effects through transpiration - the process by which trees release water vapor through their leaves, naturally air-conditioning their surroundings.\n\nResearchers emphasize that protecting existing forests and planting new trees are among the most cost-effective strategies for addressing climate change. However, they note that different tree species and forest management practices can significantly impact carbon storage capacity. The findings support global reforestation initiatives and highlight the importance of sustainable forestry practices in our fight against climate change.",
            "category": "environment",
            "url": "https://example.com/trees", 
            "published": str(datetime.now()),
            "source": "Fallback"
        }
    ]
    
    # Filter out completed articles
    return [article for article in fallback_articles if article["id"] not in completed_articles]

class QuestionGenerator:
    """Generates contextually relevant STEM + ELA questions using LLM+RAG approach"""
    
    def __init__(self):
        # Import the new LLM-based generator
        from llm_question_generator import LLMQuestionGenerator
        self.llm_generator = LLMQuestionGenerator()
    
    def generate_questions(self, article: Dict, age_group: str, difficulty_level: int = 1) -> List[Dict]:
        """Generate contextually relevant questions based on article content"""
        # Use the new LLM-based generator for intelligent questions
        return self.llm_generator.generate_questions(article, age_group, difficulty_level)
    
    # Legacy methods removed - now using intelligent LLM-based question generation

def check_if_article_completed(article_id: str) -> bool:
    """Check if all questions for an article are completed"""
    # Count total questions for this article using article ID
    total_questions = 0
    answered_questions = 0
    
    for question_type in ['math', 'science', 'ela']:
        for j in range(3):  # Assuming max 3 questions per type
            question_key = f"q_{article_id}_{question_type}_{j}"
            if question_key in st.session_state.get('answered_questions', set()):
                answered_questions += 1
            # Check if question exists by looking for attempt counter
            attempt_key = f"attempts_{question_key}"
            if attempt_key in st.session_state:
                total_questions += 1
    
    return total_questions > 0 and answered_questions >= total_questions

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
        
        # Generate and display questions with adaptive difficulty
        question_generator = QuestionGenerator()
        
        # Get difficulty level for authenticated users
        difficulty_level = 1
        if hasattr(st.session_state, 'selected_kid') and hasattr(st.session_state, 'profile_manager'):
            difficulty_level = st.session_state.profile_manager.get_difficulty_level(st.session_state.selected_kid['kid_id'])
        
        questions = question_generator.generate_questions(article, age_group, difficulty_level)
        
        if questions:
            st.subheader("🤔 Test Your Knowledge!")
            
            # Organize questions by type
            math_questions = [q for q in questions if q['type'] == 'math']
            science_questions = [q for q in questions if q['type'] == 'science']
            ela_questions = [q for q in questions if q['type'] == 'ela']
            
            # Create tabs for different question types
            tab_names = []
            tab_questions = []
            
            if math_questions:
                tab_names.append("🔢 Math")
                tab_questions.append(math_questions)
            
            if science_questions:
                tab_names.append("🔬 Science")
                tab_questions.append(science_questions)
            
            if ela_questions:
                tab_names.append("📚 ELA")
                tab_questions.append(ela_questions)
            
            if tab_names:
                # Initialize active tab for this article
                active_tab_key = f"active_tab_article_{article_index}"
                if active_tab_key not in st.session_state:
                    st.session_state[active_tab_key] = 0
                
                # Create custom tab selector that preserves state
                selected_tab = st.selectbox(
                    "Select Subject:",
                    options=list(range(len(tab_names))),
                    format_func=lambda x: tab_names[x],
                    index=st.session_state[active_tab_key],
                    key=f"tab_selector_{article_index}"
                )
                
                # Update active tab in session state
                st.session_state[active_tab_key] = selected_tab
                
                # Show debug info
                with st.expander("🔧 Debug Info"):
                    st.write("**Database Status:**")
                    profile_manager = st.session_state.profile_manager
                    import os
                    st.write(f"- Database exists: {os.path.exists(profile_manager.db_path)}")
                    st.write(f"- Database path: {profile_manager.db_path}")
                    
                    users = profile_manager.get_all_users()
                    st.write(f"- Total users: {len(users)}")
                    
                    for user in users:
                        kids = profile_manager.get_kid_profiles(user['user_id'])
                        st.write(f"  - {user['username']}: {len(kids)} kids")
                
                # Display questions for selected tab only
                questions_in_tab = tab_questions[selected_tab]
                st.markdown(f"### {tab_names[selected_tab]} Questions")
                
                for j, question in enumerate(questions_in_tab):
                    # Use article ID instead of index to ensure unique keys across different articles
                    article_id = article.get('id', f"article_{article_index}")
                    question_key = f"q_{article_id}_{question['type']}_{j}"
                    attempt_key = f"attempts_{question_key}"
                    
                    # Initialize attempt counter
                    if attempt_key not in st.session_state:
                        st.session_state[attempt_key] = 0
                    
                    # Show question with status indicator
                    if question_key in st.session_state.answered_questions:
                        st.write(f"**Question {j+1}:** ✅")
                        st.write(question["question"])
                    elif st.session_state[attempt_key] > 0:
                        st.write(f"**Question {j+1}:** ❌")
                        st.write(question["question"])
                    else:
                        st.write(f"**Question {j+1}:**")
                        st.write(question["question"])
                    
                    # Only show interactive elements if question hasn't been answered correctly
                    if question_key not in st.session_state.answered_questions:
                        # Create radio button for answers
                        answer = st.radio(
                            "Choose your answer:",
                            question["options"],
                            key=question_key,
                            index=None
                        )
                        
                        # Check answer button
                        if st.button(f"Check Answer", key=f"check_{question_key}"):
                            if answer is None:
                                st.warning("⚠️ Please select an answer first!")
                            else:
                                st.session_state[attempt_key] += 1
                                
                                if answer == question["correct"]:
                                    # Calculate points based on attempt number
                                    if st.session_state[attempt_key] == 1:
                                        points = 10  # Full points for first attempt
                                        star_message = "⭐ **You earned a STAR!** ⭐"
                                    else:
                                        points = 5   # Half points for second attempt
                                        star_message = "⭐ **You earned a STAR!** (Half points for retry) ⭐"
                                    
                                    # Store feedback in session state for persistence
                                    feedback_key = f"feedback_{question_key}"
                                    st.session_state[feedback_key] = {
                                        'type': 'correct',
                                        'message': f"🎉 Correct! {question['explanation']}",
                                        'reasoning': f"💡 **Why this is right:** {question['reasoning']}",
                                        'star_message': star_message
                                    }
                                    
                                    st.session_state.answered_questions.add(question_key)
                                    st.session_state.score += points
                                    st.session_state.questions_answered += 1
                                    
                                    # Update kid progress if authenticated
                                    if hasattr(st.session_state, 'selected_kid') and hasattr(st.session_state, 'profile_manager'):
                                        old_progress = st.session_state.profile_manager.get_kid_progress(st.session_state.selected_kid['kid_id'])
                                        
                                        # Check if this completes the article
                                        article_id = article.get('id', f"article_{article_index}")
                                        all_questions_answered = check_if_article_completed(article_id)
                                        
                                        st.session_state.profile_manager.update_kid_progress(
                                            st.session_state.selected_kid['kid_id'], 
                                            score_increment=points, 
                                            questions_increment=1,
                                            article_id=article_id if all_questions_answered else None
                                        )
                                        new_progress = st.session_state.profile_manager.get_kid_progress(st.session_state.selected_kid['kid_id'])
                                        
                                        # Check if diamond was earned
                                        if new_progress.get('diamonds', 0) > old_progress.get('diamonds', 0):
                                            st.success("💎 **DIAMOND EARNED!** 💎 Amazing work!")
                                        
                                        # Check if level up occurred
                                        if new_progress.get('level', 1) > old_progress.get('level', 1):
                                            st.success(f"🎯 **LEVEL UP!** You reached Level {new_progress.get('level', 1)}! 💎")
                                        
                                        # Check if article completed
                                        if all_questions_answered:
                                            st.success(f"🎉 **ARTICLE COMPLETED!** You finished '{article['title']}'!")
                                            st.info("🔄 Refresh to see new articles!")
                                    
                                    st.balloons()
                                else:
                                    feedback_key = f"feedback_{question_key}"
                                    if st.session_state[attempt_key] == 1:
                                        # First wrong attempt - show detailed explanation and hint
                                        wrong_explanation = question.get('wrong_explanation', 'That answer is not correct.')
                                        st.session_state[feedback_key] = {
                                            'type': 'hint',
                                            'message': "❌ Not quite right. Let me explain why:",
                                            'wrong_explanation': f"🔍 **Why this is wrong:** {wrong_explanation}",
                                            'hint': f"💡 **Hint:** {question['hint']}",
                                            'encouragement': "Try again! You can do it! 🌟"
                                        }
                                    else:
                                        # Second attempt - show answer and explanation
                                        st.session_state[feedback_key] = {
                                            'type': 'final',
                                            'message': "❌ That's still not right, but great effort!",
                                            'correct_answer': f"✅ **The correct answer is:** {question['correct']}",
                                            'explanation': f"📚 **Explanation:** {question['explanation']}",
                                            'reasoning': f"💡 **Why this is right:** {question['reasoning']}"
                                        }
                                        st.session_state.answered_questions.add(question_key)
                                        st.session_state.questions_answered += 1
                                        # No points for wrong answer after 2 attempts
                                        
                                        # Update kid progress if authenticated (no points)
                                        if hasattr(st.session_state, 'selected_kid') and hasattr(st.session_state, 'profile_manager'):
                                            st.session_state.profile_manager.update_kid_progress(
                                                st.session_state.selected_kid['kid_id'], 
                                                score_increment=0, 
                                                questions_increment=1
                                            )
                    else:
                        # Question already answered - show completion status
                        st.success("✅ **Question completed!**")
                    
                    # Display persistent feedback
                    feedback_key = f"feedback_{question_key}"
                    if feedback_key in st.session_state:
                        feedback = st.session_state[feedback_key]
                        
                        if feedback['type'] == 'correct':
                            st.success(feedback['message'])
                            st.info(feedback['reasoning'])
                            if 'star_message' in feedback:
                                st.success(feedback['star_message'])
                        elif feedback['type'] == 'hint':
                            st.error(feedback['message'])
                            if 'wrong_explanation' in feedback:
                                st.warning(feedback['wrong_explanation'])
                            st.info(feedback['hint'])
                            st.info(feedback['encouragement'])
                        elif feedback['type'] == 'final':
                            st.error(feedback['message'])
                            st.success(feedback['correct_answer'])
                            st.info(feedback['explanation'])
                            st.info(feedback['reasoning'])
                    
                    # Show attempt status
                    if st.session_state[attempt_key] > 0 and question_key not in st.session_state.answered_questions:
                        if st.session_state[attempt_key] == 1:
                            st.caption("💪 One more try! You've got this!")
                    
                    if j < len(questions_in_tab) - 1:  # Don't add divider after last question
                        st.divider()

def main():
    """Main application function"""
    st.set_page_config(
        page_title="Knowledge R Us",
        page_icon="🌟",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize data manager with SQLite persistence ONLY
    if 'profile_manager' not in st.session_state:
        from streamlit_data_storage import StreamlitDataManager
        st.session_state.profile_manager = StreamlitDataManager()
    
    # Remove any old data manager references
    if 'data_manager' in st.session_state:
        del st.session_state.data_manager
    
    # Setup LLM provider in sidebar (only once)
    with st.sidebar:
        st.header("🤖 AI Settings")
        setup_llm_provider()
    
    # Debug: Show data storage information
    if st.sidebar.button("🔍 Debug Info"):
        st.sidebar.write("**Storage Type:** SQLite Database")
        st.sidebar.write(f"**Database:** {st.session_state.profile_manager.db_path}")
        
        # Show database content
        try:
            import sqlite3
            conn = sqlite3.connect(st.session_state.profile_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT username FROM users")
            users = [row[0] for row in cursor.fetchall()]
            st.sidebar.write(f"**Users in DB:** {users}")
            
            cursor.execute("SELECT parent_username, COUNT(*) FROM kid_profiles GROUP BY parent_username")
            profiles = dict(cursor.fetchall())
            st.sidebar.write(f"**Kid Profiles:** {profiles}")
            
            conn.close()
        except Exception as e:
            st.sidebar.write(f"**DB Error:** {e}")
        
        # Show session state
        st.sidebar.write("**Session State:**")
        st.sidebar.write(f"Authenticated: {st.session_state.get('authenticated', False)}")
        st.sidebar.write(f"Username: {st.session_state.get('username', 'None')}")
        st.sidebar.write(f"Selected Kid: {st.session_state.get('selected_kid', {}).get('name', 'None')}")
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'questions_answered' not in st.session_state:
        st.session_state.questions_answered = 0
    if 'answered_questions' not in st.session_state:
        st.session_state.answered_questions = set()
    
    # Authentication flow
    if not st.session_state.authenticated:
        show_login_page(st.session_state.profile_manager)
        return
    
    # Profile selection flow
    if 'selected_kid' not in st.session_state:
        show_profile_selection(st.session_state.profile_manager)
        return
    
    # Kid dashboard flow
    if 'learning_mode' not in st.session_state:
        show_kid_dashboard(st.session_state.profile_manager, st.session_state.selected_kid)
        return
    
    # Main learning interface
    kid = st.session_state.selected_kid
    age_group = kid['age_group']
    
    # Header with kid info
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"🌟 {kid['name']}'s Learning Adventure")
        st.caption(f"Age {kid['age']} • Learning from real news!")
    
    with col2:
        if st.button("📊 Dashboard"):
            del st.session_state.learning_mode
            st.rerun()
    
    # Sidebar for controls and progress
    with st.sidebar:
        st.header(f"{kid['avatar']} {kid['name']}")
        
        # Get current progress
        current_progress = st.session_state.profile_manager.get_kid_progress(kid['kid_id'])
        st.session_state.kid_progress = current_progress
        
        st.header("📰 News Controls")
        if st.button("🔄 Refresh News"):
            fetch_news_articles.clear()
            # Clear session state for question answers to allow fresh questions
            keys_to_remove = []
            for key in st.session_state.keys():
                if key.startswith(('q_', 'attempts_', 'feedback_')):
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del st.session_state[key]
            # Clear answered questions set
            if 'answered_questions' in st.session_state:
                st.session_state.answered_questions.clear()
            st.success("News refreshed and questions reset!")
        
        # Filter by kid's interests
        interests = kid.get('interests', ['science'])
        if 'science' in interests:
            default_category = 'science'
        elif 'technology' in interests:
            default_category = 'technology'
        elif 'environment' in interests:
            default_category = 'environment'
        else:
            default_category = 'science'
            
        category_filter = st.selectbox(
            "News Category:",
            ["science", "technology", "environment"],
            index=["science", "technology", "environment"].index(default_category)
        )
        
        st.header("🏆 Progress")
        st.metric("Score", current_progress.get('total_score', 0))
        st.metric("Questions Answered", current_progress.get('questions_answered', 0))
        st.metric("Articles Read", current_progress.get('articles_read', 0))
        
        # Achievement badges
        st.header("🎖️ Achievements")
        achievements = current_progress.get('achievements', [])
        if achievements:
            for achievement in achievements[-4:]:  # Show last 4 achievements
                st.success(achievement['name'])
        else:
            st.info("Complete questions to earn achievements!")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📰 Latest Educational News")
        
        # Load articles
        try:
            with st.spinner("Loading latest news articles..."):
                # Get completed articles for this kid
                completed_articles = st.session_state.profile_manager.get_completed_articles(kid['kid_id'])
                articles = fetch_news_articles(category_filter, 3, completed_articles)
            
            if not articles:
                st.warning("No articles found. Using fallback content.")
                articles = get_fallback_articles()
                # Add IDs to fallback articles
                for article in articles:
                    if 'id' not in article:
                        article['id'] = generate_article_id(article)
            
            # Initialize content adapter
            content_adapter = ContentAdapter()
            
            # Display articles and track completion
            displayed_count = 0
            for i, article in enumerate(articles):
                # Check if article is completed
                article_id = article.get('id', generate_article_id(article))
                is_completed = st.session_state.profile_manager.is_article_completed(kid['kid_id'], article_id)
                
                if is_completed:
                    # Skip completed articles entirely - they shouldn't appear
                    continue
                
                # Adapt content for age group
                adapted_article = content_adapter.adapt_content(article, age_group)
                adapted_article['id'] = article_id
                
                display_article_with_questions(adapted_article, age_group, displayed_count)
                displayed_count += 1
                
                # Only show one article at a time to focus learning
                break
            
            if displayed_count == 0:
                st.info("🎉 Great job! You've completed all available articles. New articles will be available soon!")
                if st.button("🔄 Check for New Articles"):
                    fetch_news_articles.clear()
                    st.rerun()
                
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
        daily_questions = current_progress.get('questions_answered', 0)
        progress = min(daily_questions / 5, 1.0)
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
        
        # Personalized encouragement
        st.subheader(f"🌟 For {kid['name']}")
        total_score = current_progress.get('total_score', 0)
        if total_score == 0:
            st.info("Welcome! Start by reading an article and answering questions.")
        elif total_score < 50:
            st.info("You're doing great! Keep learning to unlock more achievements.")
        elif total_score < 100:
            st.info("Awesome progress! You're becoming a real knowledge expert!")
        else:
            st.info("Amazing! You're a true Knowledge R Us champion! 🏆")
        
        # System status
        st.subheader("📡 News System")
        st.success("✅ Real RSS Feeds Active")
        st.success("✅ Age-Adaptive Content")
        st.success("✅ Personalized Learning")

if __name__ == "__main__":
    main()
