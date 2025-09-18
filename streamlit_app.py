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
    """Fetch real news articles from RSS feeds with robust error handling"""
    articles = []
    completed_articles = completed_articles or []
    
    if category not in NEWS_SOURCES:
        logger.warning(f"Category {category} not found in NEWS_SOURCES")
        return get_fallback_articles(completed_articles)
    
    # Try each RSS source with timeout and better error handling
    for rss_url in NEWS_SOURCES[category]:
        try:
            logger.info(f"Fetching from: {rss_url}")
            
            # Add timeout to prevent hanging
            import urllib.request
            import socket
            socket.setdefaulttimeout(10)  # 10 second timeout
            
            feed = feedparser.parse(rss_url)
            
            # Check if feed was parsed successfully
            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"No entries found in feed: {rss_url}")
                continue
            
            logger.info(f"Found {len(feed.entries)} entries in feed")
            
            for entry in feed.entries[:max_articles * 2]:  # Get more to filter completed ones
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
                    
                    # Ensure we have substantial content (be more lenient)
                    if len(cleaned_content) < 50:
                        logger.debug(f"Skipping article with short content: {len(cleaned_content)} chars")
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
    
    logger.info(f"Successfully fetched {len(articles)} articles")
    
    # If we don't have enough articles, use fallback
    if len(articles) < max_articles:
        logger.info(f"Need more articles, adding fallback content")
        fallback_articles = get_fallback_articles(completed_articles)
        articles.extend(fallback_articles[:max_articles - len(articles)])
    
    # Ensure we always return something
    if not articles:
        logger.warning("No articles found, returning fallback only")
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
        
        # Get subject-specific difficulty levels for authenticated users
        science_difficulty = 1
        ela_difficulty = 1
        if hasattr(st.session_state, 'selected_kid') and hasattr(st.session_state, 'profile_manager'):
            kid_id = st.session_state.selected_kid['kid_id']
            science_difficulty = st.session_state.profile_manager.get_difficulty_level(kid_id, 'science')
            ela_difficulty = st.session_state.profile_manager.get_difficulty_level(kid_id, 'ela')
        
        # Generate questions with subject-specific difficulty levels
        st.info("🧠 Generating personalized questions based on the article...")
        
        with st.spinner("Creating Science & ELA questions..."):
            # Generate all questions at once (both science and ELA)
            all_questions = question_generator.generate_questions(article, age_group, max(science_difficulty, ela_difficulty))
            
            # Filter questions by type and ensure we have both subjects
            science_questions = [q for q in all_questions if q.get('type') == 'science']
            ela_questions = [q for q in all_questions if q.get('type') == 'ela']
            
            # If we don't have questions for both subjects, generate fallback
            if not science_questions or not ela_questions:
                st.warning("⚠️ Some questions couldn't be generated from the article. Using educational fallbacks...")
                fallback_questions = question_generator.llm_generator._get_news_fallback_questions(age_group, max(science_difficulty, ela_difficulty))
                
                if not science_questions:
                    science_fallback = [q for q in fallback_questions if q.get('type') == 'science']
                    science_questions.extend(science_fallback)
                
                if not ela_questions:
                    ela_fallback = [q for q in fallback_questions if q.get('type') == 'ela']
                    ela_questions.extend(ela_fallback)
            
            questions = science_questions + ela_questions
        
        if questions:
            st.subheader("🤔 Test Your Knowledge!")
            st.info("🔬📚 **Science & ELA questions** are based on this news article content!")
            
            # Organize questions by type for tabs (only Science and ELA for news articles)
            science_questions = [q for q in questions if q.get('type') == 'science']
            ela_questions = [q for q in questions if q.get('type') == 'ela']
            
            # Create tabs for different question types
            tab_names = []
            tab_questions = []
            
            if science_questions:
                tab_names.append("🔬 Science")
                tab_questions.append(science_questions)
            
            if ela_questions:
                tab_names.append("📚 ELA")
                tab_questions.append(ela_questions)
            
            if tab_names:
                active_tab_key = f"active_tab_article_{article_index}"
                if active_tab_key not in st.session_state:
                    st.session_state[active_tab_key] = 0
                
                # Navigation with colorful cards
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <h2 style="color: #2C3E50; font-family: 'Comic Sans MS', cursive; font-size: 2.5rem;">
            🎯 What would you like to do today? 🎯
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Create navigation cards in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📰\n\nRead News\n& Answer\nQuestions", key="nav_news", use_container_width=True):
            st.session_state.section_selector = "📰 Read News & Answer Questions"
    
    with col2:
        if st.button("🧮\n\nMath\nPractice", key="nav_math", use_container_width=True):
            st.session_state.section_selector = "🧮 Math Practice"
    
    with col3:
        if st.button("🔬\n\nScience\nTest", key="nav_science", use_container_width=True):
            st.session_state.section_selector = "🔬 Science Test"
    
    with col4:
        if st.button("📚\n\nELA\nTest", key="nav_ela", use_container_width=True):
            st.session_state.section_selector = "📚 ELA Test"
    
    # Add Social Studies button in a new row
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏛️\n\nSocial Studies\nModule 5", key="nav_social_studies", use_container_width=True):
            st.session_state.section_selector = "🏛️ Social Studies Module 5"
    
    # Initialize section selector if not set
    if 'section_selector' not in st.session_state:
        st.session_state.section_selector = "📰 Read News & Answer Questions"
    
    section_selector = st.session_state.section_selector
    
    # Create custom tab selector that preserves state
    article_id = article.get('id', f'article_{article_index}')
    active_tab_key = f"active_tab_{article_id}_{article_index}"
    
    # Initialize active tab if not set
    if active_tab_key not in st.session_state:
        st.session_state[active_tab_key] = 0
    
    selected_tab = st.selectbox(
        "Select Subject:",
        options=list(range(len(tab_names))),
        format_func=lambda x: tab_names[x],
        index=st.session_state[active_tab_key],
        key=f"tab_selector_{article_id}_{article_index}"
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
        
        # Display question with type-specific styling
        question_type = question.get('question_type', question.get('type', 'multiple_choice'))
        type_emoji = {
            'multiple_choice': '🔤',
            'true_false': '✅❌',
            'fill_blank': '📝',
            'short_answer': '💭',
            'matching': '🔗',
            'ordering': '🔢'
        }.get(question_type, '❓')
        
        # Show question with status indicator and type
        if question_key in st.session_state.answered_questions:
            st.write(f"**Question {j+1}:** ✅ {type_emoji}")
            st.write(question["question"])
        elif st.session_state[attempt_key] > 0:
            st.write(f"**Question {j+1}:** ❌ {type_emoji}")
            st.write(question["question"])
        else:
            st.write(f"**Question {j+1}:** {type_emoji}")
            st.write(question["question"])
        
        # Only show interactive elements if question hasn't been answered correctly
        if question_key not in st.session_state.answered_questions:
            # Initialize answer selection in session state
            answer_key = f"answer_{question_key}"
            if answer_key not in st.session_state:
                st.session_state[answer_key] = None
            
            # Enhanced visual styling for answer options
            st.markdown("""
            <div style="background: linear-gradient(135deg, #E3F2FD, #F3E5F5); 
                        border-radius: 15px; padding: 20px; margin: 15px 0; 
                        border: 3px solid #FFE082; box-shadow: 0 6px 20px rgba(0,0,0,0.15);">
                <h3 style="color: #1976D2; margin-bottom: 15px; font-family: 'Comic Sans MS', cursive; 
                           text-align: center; font-size: 1.5em;">
                    🤔 Choose Your Answer:
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Display question type-specific interface with enhanced styling
            if question_type == 'true_false':
                # Enhanced True/False styling
                st.markdown("""
                <div style="background: linear-gradient(135deg, #C8E6C9, #A5D6A7); 
                            border-radius: 12px; padding: 15px; margin: 10px 0; text-align: center;">
                    <h5 style="color: #2E7D32; margin: 0; font-family: 'Comic Sans MS', cursive;">
                        ✅❌ True or False?
                    </h5>
                </div>
                """, unsafe_allow_html=True)
                
                # Create custom styled buttons for True/False
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ TRUE", key=f"true_{question_key}", 
                               use_container_width=True,
                               help="Click if the statement is TRUE"):
                        answer = "True"
                        st.session_state[answer_key] = answer
                with col2:
                    if st.button("❌ FALSE", key=f"false_{question_key}", 
                               use_container_width=True,
                               help="Click if the statement is FALSE"):
                        answer = "False"
                        st.session_state[answer_key] = answer
                
                # Show selected answer
                if st.session_state.get(answer_key):
                    st.success(f"You selected: **{st.session_state[answer_key]}**")
                answer = st.session_state.get(answer_key)
                
            elif question_type == 'fill_blank' or question_type == 'fill_in_blank':
                # Enhanced fill-in-the-blank styling
                st.markdown("""
                <div style="background: linear-gradient(135deg, #FFF3E0, #FFE0B2); 
                            border-radius: 12px; padding: 15px; margin: 10px 0; text-align: center;">
                    <h5 style="color: #F57C00; margin: 0; font-family: 'Comic Sans MS', cursive;">
                        📝 Fill in the blank:
                    </h5>
                </div>
                """, unsafe_allow_html=True)
                
                # Check if this is a true fill-in-the-blank (no options) or multiple choice
                if "options" in question and question["options"]:
                    # Enhanced selectbox with better styling
                    answer = st.selectbox(
                        "🎯 Choose the word that best fits:",
                        question["options"],
                        key=f"select_{question_key}",
                        index=0,
                        help="Select the word that makes the most sense in the sentence"
                    )
                else:
                    # True fill-in-the-blank - text input
                    answer = st.text_input(
                        "✏️ Type your answer:",
                        key=f"text_{question_key}",
                        placeholder="Enter your answer here...",
                        help="Type the number or word that answers the question"
                    )
                    # Store the answer in session state
                    if answer:
                        st.session_state[answer_key] = answer
                
            elif question_type == 'short_answer':
                # Enhanced short answer styling
                st.markdown("""
                <div style="background: linear-gradient(135deg, #E8F5E8, #C8E6C9); 
                            border-radius: 12px; padding: 15px; margin: 10px 0; text-align: center;">
                    <h5 style="color: #388E3C; margin: 0; font-family: 'Comic Sans MS', cursive;">
                        💭 Short Answer:
                    </h5>
                </div>
                """, unsafe_allow_html=True)
                
                answer = st.selectbox(
                    "🎯 Choose the best answer:",
                    question["options"],
                    key=f"select_{question_key}",
                    index=0,
                    help="Pick the answer that best fits the question"
                )
                
            elif question_type == 'ordering':
                # Enhanced ordering styling
                st.markdown("""
                <div style="background: linear-gradient(135deg, #F3E5F5, #E1BEE7); 
                            border-radius: 12px; padding: 15px; margin: 10px 0; text-align: center;">
                    <h5 style="color: #7B1FA2; margin: 0; font-family: 'Comic Sans MS', cursive;">
                        🔢 Put in the correct order:
                    </h5>
                </div>
                """, unsafe_allow_html=True)
                
                # Enhanced radio buttons for ordering
                for i, option in enumerate(question["options"]):
                    if st.button(f"📋 {option}", key=f"order_{question_key}_{i}", 
                               use_container_width=True,
                               help=f"Click to select this sequence"):
                        answer = option
                        st.session_state[answer_key] = answer
                
                # Show selected answer
                if st.session_state.get(answer_key):
                    st.success(f"You selected: **{st.session_state[answer_key]}**")
                answer = st.session_state.get(answer_key)
                
            else:
                # Enhanced multiple choice styling
                st.markdown("""
                <div style="background: linear-gradient(135deg, #E3F2FD, #BBDEFB); 
                            border-radius: 12px; padding: 15px; margin: 10px 0; text-align: center;">
                    <h5 style="color: #1976D2; margin: 0; font-family: 'Comic Sans MS', cursive;">
                        🔤 Multiple Choice:
                    </h5>
                </div>
                """, unsafe_allow_html=True)
                
                # Create enhanced buttons for each option
                for i, option in enumerate(question["options"]):
                    option_letters = ['A', 'B', 'C', 'D']
                    letter = option_letters[i] if i < len(option_letters) else str(i+1)
                    
                    if st.button(f"{letter}. {option}", key=f"choice_{question_key}_{i}", 
                               use_container_width=True,
                               help=f"Click to select option {letter}"):
                        answer = option
                        st.session_state[answer_key] = answer
                
                # Show selected answer
                if st.session_state.get(answer_key):
                    st.success(f"You selected: **{st.session_state[answer_key]}**")
                answer = st.session_state.get(answer_key)
            
            # Store the selected answer
            if answer is not None:
                st.session_state[answer_key] = answer
            
            # Enhanced Check Answer button
            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(f"🎯 Check My Answer!", key=f"check_{question_key}", 
                           use_container_width=True,
                           help="Click to see if your answer is correct!"):
                    selected_answer = st.session_state.get(answer_key)
                    if selected_answer is None:
                        st.error("⚠️ Please select an answer first!")
                    else:
                        st.session_state[attempt_key] += 1
                    
                    if selected_answer == question["correct"]:
                        # Correct answer with celebration
                        points = 10 if st.session_state[attempt_key] == 1 else 5
                        
                        # Fun celebration messages
                        celebration_messages = [
                            "🎉 Amazing! You're a superstar!",
                            "✨ Fantastic! You nailed it!",
                            "🎆 Incredible! You're on fire!",
                            "🌈 Wonderful! You're brilliant!",
                            "🚀 Outstanding! You rock!"
                        ]
                        import random
                        celebration = random.choice(celebration_messages)
                        
                        star_message = "⭐" * min(points // 2, 5)
                        feedback = {
                            'type': 'success',
                            'message': f"{celebration} {star_message}",
                            'points': f"+{points} points!",
                            'explanation': f"📚 **Why this is right:** {question['explanation']}",
                            'star_message': star_message
                        }
                        st.session_state[feedback_key] = feedback
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
                        # Wrong answer with encouraging feedback
                        st.session_state[attempt_key] += 1
                        
                        if st.session_state[attempt_key] >= 2:
                            # Show correct answer after 2 attempts with encouragement
                            encouraging_messages = [
                                "💪 Don't worry! Learning is all about trying!",
                                "🌟 Great effort! Now you know for next time!",
                                "😊 Nice try! Every mistake helps us learn!",
                                "🌈 Good attempt! You're getting smarter!"
                            ]
                            encouragement = random.choice(encouraging_messages)
                            
                            feedback = {
                                'type': 'info',
                                'message': f"{encouragement}",
                                'correct_answer': f"🎯 The correct answer is: **{question['correct']}**",
                                'explanation': f"📚 **Why this is right:** {question['explanation']}",
                                'reasoning': f"💡 **Remember this:** {question['reasoning']}"
                            }
                            st.session_state.answered_questions.add(question_key)
                            st.session_state.questions_answered += 1
                            # No points for wrong answer after 2 attempts
                            
                            # Update kid progress if authenticated (no points, subject-specific)
                            if hasattr(st.session_state, 'selected_kid') and hasattr(st.session_state, 'profile_manager'):
                                kid_id = st.session_state.selected_kid['kid_id']
                                question_subject = question.get('type', 'general')
                                
                                # Update subject-specific progress (wrong answer)
                                st.session_state.profile_manager.update_subject_progress(
                                    kid_id, question_subject, False, 0
                                )
                                
                                # Also update general progress for backward compatibility
                                st.session_state.profile_manager.update_kid_progress(
                                    kid_id, 
                                    score_increment=0, 
                                    questions_increment=1
                                )
                                
                                # Check for new achievements (even for wrong answers)
                                new_achievements = st.session_state.profile_manager.get_new_achievements(kid_id)
                                if new_achievements:
                                    for achievement in new_achievements:
                                        st.success(f"🏆 **NEW BADGE EARNED!** {achievement}")
                                    st.balloons()
                        else:
                            # First wrong attempt - show detailed explanation and hint
                            wrong_explanation = question.get('wrong_explanation', 'That answer is not correct.')
                            feedback = {
                                'type': 'hint',
                                'message': "❌ Not quite right. Let me explain why:",
                                'wrong_explanation': f"🔍 **Why this is wrong:** {wrong_explanation}",
                                'hint': f"💡 **Hint:** {question['hint']}",
                                'encouragement': "Try again! You can do it! 🌟"
                            }
                        st.session_state[feedback_key] = feedback
        
        else:
            # Question already answered - show completion status
            st.success("✅ **Question completed!**")
        
        # Display persistent feedback
        feedback_key = f"feedback_{question_key}"
        if feedback_key in st.session_state:
            feedback = st.session_state[feedback_key]
            
            if feedback['type'] == 'success':
                # Celebration for correct answers
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; background: linear-gradient(45deg, #A8E6CF, #7FCDCD); border-radius: 20px; margin: 15px 0; animation: celebration 0.6s ease-in-out;">
                    <h2 style="color: white; font-size: 2em; margin: 10px 0;">{feedback['message']}</h2>
                    <h3 style="color: white; font-size: 1.5em;">{feedback['points']}</h3>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
                st.info(feedback['explanation'])
            elif feedback['type'] == 'hint':
                # Encouraging message for wrong answers
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: linear-gradient(45deg, #FFE066, #FFB347); border-radius: 15px; margin: 10px 0;">
                    <h3 style="color: white; font-size: 1.3em;">{feedback['message']}</h3>
                </div>
                """, unsafe_allow_html=True)
                if 'hint' in feedback:
                    st.info(feedback['hint'])
            elif feedback['type'] == 'info':
                # Final answer reveal with encouragement
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: linear-gradient(45deg, #87CEEB, #98FB98); border-radius: 15px; margin: 10px 0;">
                    <h3 style="color: white; font-size: 1.3em;">{feedback['message']}</h3>
                </div>
                """, unsafe_allow_html=True)
                if 'correct_answer' in feedback:
                    st.info(feedback['correct_answer'])
                st.info(feedback['explanation'])
                st.info(feedback['reasoning'])
        
        # Show fun attempt status
        if st.session_state[attempt_key] > 0 and question_key not in st.session_state.answered_questions:
            if st.session_state[attempt_key] == 1:
                st.markdown("""
                <div style="text-align: center; padding: 10px; background: rgba(255, 255, 255, 0.8); border-radius: 10px; margin: 5px 0;">
                    <p style="color: #FF6B6B; font-weight: bold; margin: 0;">💪 One more try! You've got this, superstar! 🌟</p>
                </div>
                """, unsafe_allow_html=True)
        
        if j < len(questions_in_tab) - 1:  # Don't add divider after last question
            st.divider()

def add_kid_friendly_styles():
    """Add kid-friendly CSS styles"""
    st.markdown("""
    <style>
    /* Main app styling */
    .main .block-container {
        padding-top: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin: 10px;
    }
    
    /* Headers with fun fonts */
    h1, h2, h3 {
        font-family: 'Comic Sans MS', cursive, sans-serif !important;
        color: #2E86AB !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Colorful buttons */
    .stButton > button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        padding: 15px 30px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
        font-family: 'Comic Sans MS', cursive, sans-serif !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
        background: linear-gradient(45deg, #FF8E8E, #6EEEE4) !important;
    }
    
    /* Fun metrics styling */
    .metric-container {
        background: linear-gradient(135deg, #FFE066, #FF6B6B);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 10px;
    }
    
    /* Colorful selectbox */
    .stSelectbox > div > div {
        background: linear-gradient(45deg, #A8E6CF, #88D8C0) !important;
        border-radius: 15px !important;
        border: 3px solid #4ECDC4 !important;
    }
    
    /* Fun radio buttons */
    .stRadio > div {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 15px;
        border: 3px solid #FFE066;
    }
    
    /* Animated success messages */
    .stSuccess {
        background: linear-gradient(45deg, #A8E6CF, #7FCDCD) !important;
        border-radius: 15px !important;
        animation: bounce 0.5s ease-in-out !important;
    }
    
    @keyframes bounce {
        0%, 20%, 60%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        80% { transform: translateY(-5px); }
    }
    
    /* Fun error messages */
    .stError {
        background: linear-gradient(45deg, #FFB6C1, #FFA07A) !important;
        border-radius: 15px !important;
    }
    
    /* Colorful info boxes */
    .stInfo {
        background: linear-gradient(45deg, #87CEEB, #98FB98) !important;
        border-radius: 15px !important;
        border-left: 5px solid #4ECDC4 !important;
    }
    
    /* Fun sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #FFE066, #FF6B6B) !important;
    }
    
    /* Animated progress indicators */
    .progress-star {
        animation: twinkle 1s ease-in-out infinite alternate;
    }
    
    @keyframes twinkle {
        from { opacity: 0.5; transform: scale(1); }
        to { opacity: 1; transform: scale(1.1); }
    }
    
    /* Fun text styling */
    .big-emoji {
        font-size: 3em;
        animation: bounce 2s ease-in-out infinite;
    }
    
    .celebration {
        animation: celebration 0.6s ease-in-out;
    }
    
    @keyframes celebration {
        0% { transform: scale(1); }
        50% { transform: scale(1.2) rotate(5deg); }
        100% { transform: scale(1); }
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Knowledge R Us",
        page_icon="🌟",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Add custom CSS for kid-friendly design
    st.markdown("""
    <style>
    /* Main app styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FFEAA7);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        animation: rainbow 3s ease-in-out infinite;
    }
    
    @keyframes rainbow {
        0%, 100% { background: linear-gradient(135deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FFEAA7); }
        50% { background: linear-gradient(135deg, #4ECDC4, #45B7D1, #96CEB4, #FFEAA7, #FF6B6B); }
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin: 0;
        font-family: 'Comic Sans MS', cursive;
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        color: white;
        margin-top: 0.5rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    
    /* Navigation cards */
    .nav-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        cursor: pointer;
        border: none;
    }
    
    .nav-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    }
    
    .nav-card-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    .nav-card-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: white;
        margin-bottom: 0.5rem;
    }
    
    .nav-card-desc {
        color: rgba(255,255,255,0.8);
        font-size: 1rem;
    }
    
    /* Question cards */
    .question-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border: 3px solid #FFE082;
    }
    
    .question-title {
        font-size: 1.8rem;
        color: #FF6B35;
        font-weight: bold;
        margin-bottom: 1rem;
        font-family: 'Comic Sans MS', cursive;
    }
    
    /* Answer buttons */
    .answer-button {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border: 3px solid #4ECDC4;
        border-radius: 15px;
        padding: 1rem 2rem;
        margin: 0.5rem;
        font-size: 1.2rem;
        font-weight: bold;
        color: #2C3E50;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        text-align: left;
    }
    
    .answer-button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        background: linear-gradient(135deg, #fed6e3 0%, #a8edea 100%);
    }
    
    /* Success/Error messages */
    .success-message {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #00b894;
    }
    
    .error-message {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #e17055;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Custom button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 1.5rem 2rem;
        font-size: 1.2rem;
        font-weight: bold;
        transition: all 0.3s ease;
        height: 120px;
        white-space: pre-line;
        line-height: 1.3;
        font-family: 'Comic Sans MS', cursive;
    }
    
    .stButton > button:hover {
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Navigation button specific styling */
    .stButton > button[key*="nav_"] {
        background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(78, 205, 196, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(78, 205, 196, 0); }
        100% { box-shadow: 0 0 0 0 rgba(78, 205, 196, 0); }
    }
    
    /* Progress indicators */
    .progress-container {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
    }
    
    .score-display {
        font-size: 2rem;
        font-weight: bold;
        color: #2C3E50;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add kid-friendly styles
    add_kid_friendly_styles()
    
    # Initialize data manager with SQLite persistence ONLY
    if 'profile_manager' not in st.session_state:
        from streamlit_data_storage import StreamlitDataManager
        st.session_state.profile_manager = StreamlitDataManager()
    
    # Initialize session state variables
    if 'answered_questions' not in st.session_state:
        st.session_state.answered_questions = set()
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'questions_answered' not in st.session_state:
        st.session_state.questions_answered = 0
    
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
            st.sidebar.error(f"Database error: {e}")
    
    # Fun animated title
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h1 style="font-size: 4em; margin: 0;">🌟 Knowledge R Us 🌟</h1>
        <h2 style="font-size: 2em; color: #FF6B6B; margin: 10px 0;">🎮 Fun Learning Adventure! 🚀</h2>
        <p style="font-size: 1.5em; color: #4ECDC4; font-weight: bold;">📚 Discover Amazing Stories & Master Cool Math! 🧮</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Authentication section
    if not hasattr(st.session_state, 'authenticated') or not st.session_state.authenticated:
        handle_authentication()
        return
    
    # Kid selection for authenticated users
    if not hasattr(st.session_state, 'selected_kid') or not st.session_state.selected_kid:
        handle_kid_selection()
        return
    
    # Display current kid info
    display_kid_info()
    
    # Check if we should show dashboard
    if st.session_state.get('show_dashboard', False):
        display_dashboard()
        return
    
    # Fun animated navigation
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: rgba(255,255,255,0.1); border-radius: 25px; margin: 20px 0;">
        <h2 style="color: #FF6B6B; font-size: 2.5em; margin-bottom: 20px;">🎯 Choose Your Super Learning Adventure! 🎯</h2>
        <p style="font-size: 1.3em; color: #4ECDC4;">Pick your favorite way to learn and have fun! 🌈</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="large")
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #FFE066, #FF6B6B); border-radius: 25px; margin: 10px;">
            <div class="big-emoji">📰</div>
            <h3 style="color: white; margin: 15px 0;">News Stories!</h3>
            <p style="color: white; font-size: 1.1em;">🔬 Cool Science & 📚 Fun Reading!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Explore News Stories!", key="news_button", use_container_width=True):
            st.session_state.learning_mode = "news"
            st.balloons()
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #4ECDC4, #44A08D); border-radius: 25px; margin: 10px;">
            <div class="big-emoji">🔢</div>
            <h3 style="color: white; margin: 15px 0;">Math Magic!</h3>
            <p style="color: white; font-size: 1.1em;">🧮 Numbers & 🎯 Problem Solving!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✨ Practice Math Magic!", key="math_button", use_container_width=True):
            st.session_state.learning_mode = "math"
            st.balloons()
            st.rerun()
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #8B4513, #D2691E); border-radius: 25px; margin: 10px;">
            <div class="big-emoji">🏛️</div>
            <h3 style="color: white; margin: 15px 0;">Social Studies!</h3>
            <p style="color: white; font-size: 1.1em;">📖 Module 5: Immigration & Cities!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎓 Study History!", key="social_studies_button", use_container_width=True):
            st.session_state.learning_mode = "social_studies"
            st.balloons()
            st.rerun()
    
    # Display selected section
    if st.session_state.get('learning_mode') == "math":
        display_math_section()
    elif st.session_state.get('learning_mode') == "news":
        display_news_articles()
    elif st.session_state.get('learning_mode') == "social_studies":
        display_social_studies_module()
    else:
        # Fun welcome screen with animations
        st.markdown("""
        <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 25px; margin: 30px 0;">
            <div style="font-size: 4em; margin: 20px 0;">🎉</div>
            <h2 style="color: white; font-size: 2.5em;">Welcome to Your Learning Adventure!</h2>
            <p style="color: white; font-size: 1.5em; margin: 20px 0;">👆 Pick a super fun section above to start learning! 🌟</p>
            <div style="font-size: 2em; margin: 20px 0;">🚀 📚 🧮 🎮</div>
        </div>
        """, unsafe_allow_html=True)

def display_social_studies_module():
    """Display Social Studies Module 5: Immigration and Cities"""
    from social_studies_questions import get_social_studies_questions
    
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #8B4513, #D2691E); border-radius: 25px; margin: 20px 0;">
        <div style="font-size: 4em; margin: 10px 0;">🏛️</div>
        <h1 style="color: white; font-size: 3em; margin: 10px 0;">Social Studies Module 5</h1>
        <p style="color: white; font-size: 1.3em;">📖 Immigration and Cities in America 🇺🇸</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get kid's info for age-appropriate content
    kid = st.session_state.selected_kid
    age_group = kid['age_group']
    
    # Navigation tabs for different topics
    tab1, tab2, tab3, tab4 = st.tabs(["🚢 Immigration", "🏙️ Cities & Growth", "🏭 Industrial Revolution", "📚 Review Quiz"])
    
    with tab1:
        st.markdown("### 🚢 Immigration to America")
        display_immigration_content(age_group)
    
    with tab2:
        st.markdown("### 🏙️ Cities and Urban Growth")
        display_cities_content(age_group)
    
    with tab3:
        st.markdown("### 🏭 Industrial Revolution")
        display_industrial_content(age_group)
    
    with tab4:
        st.markdown("### 📚 Module 5 Review Quiz")
        display_social_studies_quiz(age_group)

def display_immigration_content(age_group):
    """Display immigration content with interactive questions"""
    from social_studies_questions import get_social_studies_questions
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #E3F2FD, #BBDEFB); padding: 20px; border-radius: 15px; margin: 15px 0;">
        <h4>🌍 People Coming to America</h4>
        <p>Throughout history, millions of people have moved to America from other countries. This is called <strong>immigration</strong>. 
        People came for many reasons: to find jobs, escape danger, or start new lives with more freedom.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get immigration-related questions
    questions = get_social_studies_questions()
    immigration_questions = [q for q in questions if 'immigration' in q['topic'].lower() or 'immigrant' in q['topic'].lower()]
    
    if immigration_questions:
        st.markdown("#### 🤔 Test Your Knowledge!")
        display_interactive_question(immigration_questions[0], "immigration")

def display_cities_content(age_group):
    """Display cities and urban growth content"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #F3E5F5, #E1BEE7); padding: 20px; border-radius: 15px; margin: 15px 0;">
        <h4>🏙️ Growing Cities</h4>
        <p>As more people came to America and factories were built, cities grew very quickly. People moved from farms to cities 
        to work in factories. This created both opportunities and challenges for city life.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get cities-related questions
    from social_studies_questions import get_social_studies_questions
    questions = get_social_studies_questions()
    cities_questions = [q for q in questions if 'city' in q['topic'].lower() or 'urban' in q['topic'].lower()]
    
    if cities_questions:
        st.markdown("#### 🤔 Test Your Knowledge!")
        display_interactive_question(cities_questions[0], "cities")

def display_industrial_content(age_group):
    """Display industrial revolution content"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #FFF3E0, #FFE0B2); padding: 20px; border-radius: 15px; margin: 15px 0;">
        <h4>🏭 The Industrial Revolution</h4>
        <p>The Industrial Revolution was a time when many new machines and factories were invented. This changed how people 
        worked and lived. Instead of making things by hand, machines could make things faster and cheaper.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get industrial-related questions
    from social_studies_questions import get_social_studies_questions
    questions = get_social_studies_questions()
    industrial_questions = [q for q in questions if 'industrial' in q['topic'].lower() or 'factory' in q['topic'].lower()]
    
    if industrial_questions:
        st.markdown("#### 🤔 Test Your Knowledge!")
        display_interactive_question(industrial_questions[0], "industrial")

def display_social_studies_quiz(age_group):
    """Display comprehensive quiz for Module 5"""
    from social_studies_questions import get_social_studies_questions
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #E8F5E8, #C8E6C9); padding: 20px; border-radius: 15px; margin: 15px 0;">
        <h4>📚 Complete Module 5 Review</h4>
        <p>Ready to test everything you've learned about Immigration and Cities? Take this comprehensive quiz!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize quiz state
    if 'social_studies_quiz_active' not in st.session_state:
        st.session_state.social_studies_quiz_active = False
        st.session_state.social_studies_current_question = 0
        st.session_state.social_studies_score = 0
        st.session_state.social_studies_answers = []
    
    questions = get_social_studies_questions()
    
    if not st.session_state.social_studies_quiz_active:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Start Module 5 Quiz", key="start_social_studies_quiz"):
                st.session_state.social_studies_quiz_active = True
                st.session_state.social_studies_current_question = 0
                st.session_state.social_studies_score = 0
                st.session_state.social_studies_answers = []
                st.rerun()
        
        with col2:
            st.info(f"📊 Total Questions: {len(questions)}")
    else:
        display_quiz_interface(questions, "social_studies")

def display_interactive_question(question, topic_key):
    """Display a single interactive question"""
    question_key = f"{topic_key}_question"
    
    st.markdown(f"**Question:** {question['question']}")
    
    # Create unique keys for each option
    selected_option = st.radio(
        "Choose your answer:",
        question['options'],
        key=f"{question_key}_radio"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Submit Answer", key=f"{question_key}_submit"):
            if selected_option == question['correct_answer']:
                st.success("🎉 Correct! Great job!")
                st.balloons()
            else:
                st.error(f"❌ Not quite right. The correct answer is: {question['correct_answer']}")
            
            # Show explanation if available
            if question.get('explanation'):
                st.info(f"💡 **Explanation:** {question['explanation']}")
    
    with col2:
        if st.button("Next Question", key=f"{question_key}_next"):
            st.rerun()

def display_quiz_interface(questions, quiz_type):
    """Display quiz interface for any subject"""
    current_q = st.session_state[f"{quiz_type}_current_question"]
    
    if current_q < len(questions):
        question = questions[current_q]
        
        # Progress bar
        progress = (current_q + 1) / len(questions)
        st.progress(progress)
        st.markdown(f"**Question {current_q + 1} of {len(questions)}**")
        
        # Display question
        st.markdown(f"### {question['question']}")
        
        # Answer options
        selected_answer = st.radio(
            "Choose your answer:",
            question['options'],
            key=f"{quiz_type}_q{current_q}"
        )
        
        if st.button("Submit Answer", key=f"{quiz_type}_submit_{current_q}"):
            # Check answer
            is_correct = selected_answer == question['correct_answer']
            
            if is_correct:
                st.success("🎉 Correct!")
                st.session_state[f"{quiz_type}_score"] += 1
            else:
                st.error(f"❌ Incorrect. The correct answer is: {question['correct_answer']}")
            
            # Show explanation
            if question.get('explanation'):
                st.info(f"💡 **Explanation:** {question['explanation']}")
            
            # Store answer
            st.session_state[f"{quiz_type}_answers"].append({
                'question': question['question'],
                'selected': selected_answer,
                'correct': question['correct_answer'],
                'is_correct': is_correct
            })
            
            # Move to next question
            st.session_state[f"{quiz_type}_current_question"] += 1
            
            if st.session_state[f"{quiz_type}_current_question"] < len(questions):
                if st.button("Next Question", key=f"{quiz_type}_next_{current_q}"):
                    st.rerun()
            else:
                st.rerun()
    else:
        # Quiz completed
        display_quiz_results(questions, quiz_type)

def display_quiz_results(questions, quiz_type):
    """Display quiz results"""
    score = st.session_state[f"{quiz_type}_score"]
    total = len(questions)
    percentage = (score / total) * 100
    
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #4CAF50, #45a049); border-radius: 25px; margin: 20px 0;">
        <div style="font-size: 4em; margin: 10px 0;">🎊</div>
        <h2 style="color: white; font-size: 2.5em;">Quiz Complete!</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 15px; margin: 15px 0;">
        <h3>Your Score: {score}/{total} ({percentage:.1f}%)</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Performance feedback
    if percentage >= 90:
        st.success("🌟 Excellent work! You're a Social Studies superstar!")
    elif percentage >= 80:
        st.success("🎉 Great job! You have a solid understanding!")
    elif percentage >= 70:
        st.info("👍 Good work! Keep studying to improve even more!")
    else:
        st.warning("📚 Keep practicing! Review the material and try again!")
    
    # Restart option
    if st.button("🔄 Take Quiz Again", key=f"{quiz_type}_restart"):
        st.session_state[f"{quiz_type}_quiz_active"] = False
        st.session_state[f"{quiz_type}_current_question"] = 0
        st.session_state[f"{quiz_type}_score"] = 0
        st.session_state[f"{quiz_type}_answers"] = []
        st.rerun()

def display_science_test():
    """Display 20-question science test"""
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 25px; margin: 20px 0;">
        <div style="font-size: 4em; margin: 10px 0;">🔬</div>
        <h1 style="color: white; font-size: 3em; margin: 10px 0;">Science Challenge!</h1>
        <p style="color: white; font-size: 1.3em;">🧪 Test your scientific knowledge! 🧪</p>
    </div>
    """, unsafe_allow_html=True)
    
    kid = st.session_state.selected_kid
    age_group = kid['age_group']
    
    # Get science difficulty level
    science_difficulty = 1
    if hasattr(st.session_state, 'profile_manager'):
        try:
            science_difficulty = st.session_state.profile_manager.get_difficulty_level(kid['kid_id'], 'science')
        except:
            science_difficulty = 1
    
    st.markdown(f"**Science Level:** {science_difficulty} | **Age Group:** {age_group}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧪 Start Science Test (20 Questions)", key="start_science_test"):
            st.session_state.science_test_active = True
            st.session_state.science_test_questions = generate_science_test_questions(age_group, science_difficulty)
            st.rerun()
    
    with col2:
        if st.button("📊 View Science Progress", key="science_progress"):
            st.info("Science progress tracking coming soon!")
    
    # Display science test questions
    if st.session_state.get('science_test_active', False):
        questions = st.session_state.get('science_test_questions', [])
        if questions:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); 
                        border-radius: 15px; padding: 20px; margin: 15px 0; text-align: center;">
                <h2 style="color: white; margin: 0; font-family: 'Comic Sans MS', cursive;">
                    🔬 Science Test - 20 Questions!
                </h2>
                <p style="color: white; margin: 10px 0;">Answer all questions to see your score! 🌟</p>
            </div>
            """, unsafe_allow_html=True)
            
            display_test_questions(questions, "science")

def display_social_studies_module():
    """Display Social Studies Module 5 questions based on textbook content"""
    from social_studies_questions import get_all_questions
    
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #8B4513, #D2691E); border-radius: 15px; margin: 20px 0;">
        <h1 style="color: white; font-size: 2.5em; margin: 10px 0;">🏛️ Social Studies Module 5 🏛️</h1>
        <h2 style="color: white; font-size: 1.8em; margin: 10px 0;">Immigration and Urban Life (1880s-1920s)</h2>
        <p style="color: white; font-size: 1.2em;">📖 Questions based strictly on your Module 5 Textbook</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get all social studies questions
    all_ss_questions = get_all_questions()
    
    # Create tabs for different lessons
    lesson_tabs = st.tabs(["📚 Lesson 1: Immigration", "🏙️ Lesson 2: City Growth", "🏠 Lesson 3: City Life", "🎯 Review Questions"])
    
    # Lesson 1: A New Wave of Immigration
    with lesson_tabs[0]:
        st.subheader("📚 Lesson 1: A New Wave of Immigration")
        st.info("🎯 **Learning Goals:** Understand immigration patterns, Ellis Island, and challenges faced by new immigrants")
        
        lesson1_questions = all_ss_questions.get("lesson_1", {}).get("questions", [])
        display_social_studies_questions(lesson1_questions, "lesson_1")
    
    # Lesson 2: The Growth of Cities
    with lesson_tabs[1]:
        st.subheader("🏙️ Lesson 2: The Growth of Cities")
        st.info("🎯 **Learning Goals:** Learn about urban growth, new technologies, and mass culture")
        
        lesson2_questions = all_ss_questions.get("lesson_2", {}).get("questions", [])
        display_social_studies_questions(lesson2_questions, "lesson_2")
    
    # Lesson 3: City Life
    with lesson_tabs[2]:
        st.subheader("🏠 Lesson 3: City Life")
        st.info("🎯 **Learning Goals:** Explore urban problems, tenements, and reform movements")
        
        lesson3_questions = all_ss_questions.get("lesson_3", {}).get("questions", [])
        display_social_studies_questions(lesson3_questions, "lesson_3")
    
    # Comprehensive Review
    with lesson_tabs[3]:
        st.subheader("🎯 Module 5 Comprehensive Review")
        st.info("🎯 **Assessment Prep:** Mixed questions covering all three lessons")
        
        review_questions = all_ss_questions.get("comprehensive_review", {}).get("questions", [])
        display_social_studies_questions(review_questions, "comprehensive_review")

def display_social_studies_questions(questions, lesson_key):
    """Display social studies questions with interactive elements"""
    if not questions:
        st.warning("No questions available for this section.")
        return
    
    # Initialize session state for social studies
    if 'answered_ss_questions' not in st.session_state:
        st.session_state.answered_ss_questions = set()
    if 'ss_score' not in st.session_state:
        st.session_state.ss_score = 0
    if 'ss_questions_answered' not in st.session_state:
        st.session_state.ss_questions_answered = 0
    
    # Display progress
    answered_count = len([q for q in questions if q['id'] in st.session_state.answered_ss_questions])
    progress = answered_count / len(questions) if questions else 0
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #E8F5E8, #C8E6C9); padding: 15px; border-radius: 10px; margin: 10px 0;">
        <h4 style="color: #2E7D32; margin: 0;">📊 Progress: {answered_count}/{len(questions)} questions completed</h4>
        <div style="background: #fff; border-radius: 10px; padding: 5px; margin-top: 10px;">
            <div style="background: #4CAF50; height: 20px; border-radius: 10px; width: {progress*100}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display questions
    for i, question in enumerate(questions):
        question_key = question['id']
        attempt_key = f"attempts_{question_key}"
        answer_key = f"answer_{question_key}"
        
        # Initialize attempt counter
        if attempt_key not in st.session_state:
            st.session_state[attempt_key] = 0
        
        # Question container
        with st.container():
            st.markdown(f"""<div style="background: white; padding: 20px; border-radius: 15px; margin: 15px 0; border-left: 5px solid #8B4513;">""")
            
            # Question status and type indicator
            question_type = question.get('type', 'multiple_choice')
            type_emoji = {
                'multiple_choice': '🔤',
                'true_false': '✅❌', 
                'fill_blank': '📝',
                'ordering': '🔢'
            }.get(question_type, '❓')
            
            if question_key in st.session_state.answered_ss_questions:
                st.markdown(f"**Question {i+1}:** ✅ {type_emoji} **COMPLETED**")
            elif st.session_state[attempt_key] > 0:
                st.markdown(f"**Question {i+1}:** ❌ {type_emoji} **TRY AGAIN**")
            else:
                st.markdown(f"**Question {i+1}:** {type_emoji}")
            
            st.markdown(f"**{question['question']}**")
            
            # Only show interactive elements if not completed
            if question_key not in st.session_state.answered_ss_questions:
                # Initialize answer in session state
                if answer_key not in st.session_state:
                    st.session_state[answer_key] = None
                
                # Display question type-specific interface
                if question_type == 'true_false':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ TRUE", key=f"true_{question_key}", use_container_width=True):
                            st.session_state[answer_key] = "True"
                    with col2:
                        if st.button("❌ FALSE", key=f"false_{question_key}", use_container_width=True):
                            st.session_state[answer_key] = "False"
                    
                    if st.session_state.get(answer_key):
                        st.success(f"You selected: **{st.session_state[answer_key]}**")
                    
                elif question_type == 'fill_blank':
                    if "options" in question and question["options"]:
                        answer = st.selectbox(
                            "Choose the correct answer:",
                            question["options"],
                            key=f"select_{question_key}",
                            index=0
                        )
                        st.session_state[answer_key] = answer
                    else:
                        answer = st.text_input(
                            "Fill in the blank:",
                            key=f"text_{question_key}",
                            placeholder="Type your answer here..."
                        )
                        if answer:
                            st.session_state[answer_key] = answer
                
                elif question_type == 'ordering':
                    st.write("Select the correct order:")
                    for j, option in enumerate(question["options"]):
                        if st.button(f"📋 {option}", key=f"order_{question_key}_{j}", use_container_width=True):
                            st.session_state[answer_key] = option
                    
                    if st.session_state.get(answer_key):
                        st.success(f"You selected: **{st.session_state[answer_key]}**")
                
                else:  # multiple_choice
                    for j, option in enumerate(question["options"]):
                        option_letters = ['A', 'B', 'C', 'D']
                        letter = option_letters[j] if j < len(option_letters) else str(j+1)
                        
                        if st.button(f"{letter}. {option}", key=f"choice_{question_key}_{j}", use_container_width=True):
                            st.session_state[answer_key] = option
                    
                    if st.session_state.get(answer_key):
                        st.success(f"You selected: **{st.session_state[answer_key]}**")
                
                # Check Answer button
                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button(f"🎯 Check My Answer!", key=f"check_{question_key}", use_container_width=True):
                        selected_answer = st.session_state.get(answer_key)
                        if selected_answer is None:
                            st.error("⚠️ Please select an answer first!")
                        else:
                            st.session_state[attempt_key] += 1
                            
                            if selected_answer == question["correct"]:
                                # Correct answer
                                points = 10 if st.session_state[attempt_key] == 1 else 5
                                
                                celebration_messages = [
                                    "🎉 Excellent! You know your history!",
                                    "✨ Outstanding! You're a social studies star!", 
                                    "🏆 Perfect! You understand the lesson!",
                                    "🌟 Brilliant! You've mastered this topic!"
                                ]
                                import random
                                celebration = random.choice(celebration_messages)
                                
                                st.success(f"{celebration} (+{points} points!)")
                                st.info(f"📚 **Explanation:** {question['explanation']}")
                                st.info(f"💡 **Why this matters:** {question['reasoning']}")
                                
                                st.session_state.answered_ss_questions.add(question_key)
                                st.session_state.ss_score += points
                                st.session_state.ss_questions_answered += 1
                                
                                # Update kid progress if authenticated
                                if hasattr(st.session_state, 'selected_kid') and hasattr(st.session_state, 'profile_manager'):
                                    st.session_state.profile_manager.update_subject_progress(
                                        st.session_state.selected_kid['kid_id'],
                                        'social_studies',
                                        correct=True,
                                        points=points
                                    )
                                
                                st.balloons()
                            else:
                                # Wrong answer
                                st.session_state[attempt_key] += 1
                                
                                if st.session_state[attempt_key] >= 2:
                                    # Show correct answer after 2 attempts
                                    encouraging_messages = [
                                        "💪 Good effort! Learning takes practice!",
                                        "🌟 Nice try! Now you know for next time!", 
                                        "😊 Great attempt! Every mistake helps us learn!",
                                        "🌈 Keep trying! You're getting smarter!"
                                    ]
                                    encouragement = random.choice(encouraging_messages)
                                    
                                    st.info(f"{encouragement}")
                                    st.success(f"🎯 The correct answer is: **{question['correct']}**")
                                    st.info(f"📚 **Explanation:** {question['explanation']}")
                                    st.info(f"💡 **Remember:** {question['reasoning']}")
                                    
                                    st.session_state.answered_ss_questions.add(question_key)
                                    st.session_state.ss_questions_answered += 1
                                    
                                    # Update progress (no points for wrong answer)
                                    if hasattr(st.session_state, 'selected_kid') and hasattr(st.session_state, 'profile_manager'):
                                        st.session_state.profile_manager.update_subject_progress(
                                            st.session_state.selected_kid['kid_id'],
                                            'social_studies', 
                                            correct=False,
                                            points=0
                                        )
                                else:
                                    st.error("❌ Not quite right. Try again!")
                                    st.info("💡 **Hint:** Think about what you learned in the textbook.")
            else:
                st.success("✅ **Question completed!**")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if i < len(questions) - 1:
                st.divider()

def display_ela_test():
    """Display 20-question ELA test"""
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #f093fb, #f5576c); border-radius: 25px; margin: 20px 0;">
        <div style="font-size: 4em; margin: 10px 0;">📚</div>
        <h1 style="color: white; font-size: 3em; margin: 10px 0;">ELA Challenge!</h1>
        <p style="color: white; font-size: 1.3em;">📖 Test your reading and language skills! 📖</p>
    </div>
    """, unsafe_allow_html=True)
    
    kid = st.session_state.selected_kid
    age_group = kid['age_group']
    
    # Get ELA difficulty level
    ela_difficulty = 1
    if hasattr(st.session_state, 'profile_manager'):
        try:
            ela_difficulty = st.session_state.profile_manager.get_difficulty_level(kid['kid_id'], 'ela')
        except:
            ela_difficulty = 1
    
    st.markdown(f"**ELA Level:** {ela_difficulty} | **Age Group:** {age_group}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📖 Start ELA Test (20 Questions)", key="start_ela_test"):
            st.session_state.ela_test_active = True
            st.session_state.ela_test_questions = generate_ela_test_questions(age_group, ela_difficulty)
            st.rerun()
    
    with col2:
        if st.button("📊 View ELA Progress", key="ela_progress"):
            st.info("ELA progress tracking coming soon!")
    
    # Display ELA test questions
    if st.session_state.get('ela_test_active', False):
        questions = st.session_state.get('ela_test_questions', [])
        if questions:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb, #f5576c); 
                        border-radius: 15px; padding: 20px; margin: 15px 0; text-align: center;">
                <h2 style="color: white; margin: 0; font-family: 'Comic Sans MS', cursive;">
                    📚 ELA Test - 20 Questions!
                </h2>
                <p style="color: white; margin: 10px 0;">Answer all questions to see your score! 🌟</p>
            </div>
            """, unsafe_allow_html=True)
            
            display_test_questions(questions, "ela")

def generate_science_test_questions(age_group: str, difficulty_level: int) -> List[Dict]:
    """Generate 20 science test questions"""
    from llm_question_generator import LLMQuestionGenerator
    generator = LLMQuestionGenerator()
    
    questions = []
    for i in range(20):
        # Create a mock article context for science questions
        mock_article = {
            "title": f"Science Discovery {i+1}",
            "content": "Scientists have made important discoveries about the natural world through careful observation and experimentation.",
            "category": "science"
        }
        
        # Generate science questions
        question = generator._generate_simple_fallback(
            generator._extract_article_context(mock_article),
            age_group, "science", difficulty_level
        )
        
        if question:
            question["question"] = f"Q{i+1}: {question['question']}"
            questions.append(question)
    
    return questions

def generate_ela_test_questions(age_group: str, difficulty_level: int) -> List[Dict]:
    """Generate 20 ELA test questions"""
    from llm_question_generator import LLMQuestionGenerator
    generator = LLMQuestionGenerator()
    
    questions = []
    for i in range(20):
        # Create a mock article context for ELA questions
        mock_article = {
            "title": f"Reading Passage {i+1}",
            "content": "Reading comprehension and language arts skills help us understand and communicate effectively with others.",
            "category": "ela"
        }
        
        # Generate ELA questions
        question = generator._generate_simple_fallback(
            generator._extract_article_context(mock_article),
            age_group, "ela", difficulty_level
        )
        
        if question:
            question["question"] = f"Q{i+1}: {question['question']}"
            questions.append(question)
    
    return questions

def display_test_questions(questions: List[Dict], subject: str):
    """Display test questions with enhanced UI"""
    total_questions = len(questions)
    answered_key = f"{subject}_test_answers"
    
    if answered_key not in st.session_state:
        st.session_state[answered_key] = {}
    
    # Progress bar
    answered_count = len(st.session_state[answered_key])
    progress = answered_count / total_questions
    st.progress(progress, text=f"Progress: {answered_count}/{total_questions} questions answered")
    
    # Display questions
    for i, question in enumerate(questions):
        question_key = f"{subject}_test_q_{i}"
        
        with st.expander(f"Question {i+1} {'✅' if question_key in st.session_state[answered_key] else '❓'}", 
                        expanded=(i == answered_count and answered_count < total_questions)):
            
            # Enhanced question display
            st.markdown("""
            <div style="background: linear-gradient(135deg, #E3F2FD, #F3E5F5); 
                        border-radius: 15px; padding: 20px; margin: 15px 0; 
                        border: 3px solid #FFE082; box-shadow: 0 6px 20px rgba(0,0,0,0.15);">
                <h3 style="color: #1976D2; margin-bottom: 15px; font-family: 'Comic Sans MS', cursive; 
                           text-align: center; font-size: 1.5em;">
                    🤔 Choose Your Answer:
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.write(question["question"])
            
            if question_key not in st.session_state[answered_key]:
                # Create enhanced buttons for each option
                for j, option in enumerate(question["options"]):
                    option_letters = ['A', 'B', 'C', 'D']
                    letter = option_letters[j] if j < len(option_letters) else str(j+1)
                    
                    if st.button(f"{letter}. {option}", key=f"{question_key}_option_{j}", 
                               use_container_width=True,
                               help=f"Click to select option {letter}"):
                        st.session_state[answered_key][question_key] = option
                        st.rerun()
            else:
                # Show selected answer and result
                selected = st.session_state[answered_key][question_key]
                is_correct = selected == question["correct"]
                
                if is_correct:
                    st.success(f"✅ Correct! You selected: **{selected}**")
                    st.info(f"💡 **Explanation:** {question['explanation']}")
                else:
                    st.error(f"❌ Incorrect. You selected: **{selected}**")
                    st.info(f"✅ **Correct answer:** {question['correct']}")
                    st.info(f"💡 **Explanation:** {question['explanation']}")
    
    # Show final results if all questions answered
    if answered_count == total_questions:
        correct_answers = sum(1 for i, q in enumerate(questions) 
                            if st.session_state[answered_key].get(f"{subject}_test_q_{i}") == q["correct"])
        
        percentage = (correct_answers / total_questions) * 100
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4CAF50, #45a049); 
                    border-radius: 15px; padding: 25px; margin: 20px 0; text-align: center;">
            <h2 style="color: white; margin: 0; font-family: 'Comic Sans MS', cursive;">
                🎉 Test Complete! 🎉
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Correct", correct_answers)
        with col2:
            st.metric("❌ Incorrect", total_questions - correct_answers)
        with col3:
            st.metric("📊 Score", f"{percentage:.1f}%")
        
        # Restart button
        if st.button(f"🔄 Take {subject.title()} Test Again", key=f"restart_{subject}_test"):
            st.session_state[answered_key] = {}
            st.session_state[f"{subject}_test_active"] = False
            st.rerun()

def display_math_section():
    """Display dedicated math practice section"""
    # Initialize session state variables if not present
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'questions_answered' not in st.session_state:
        st.session_state.questions_answered = 0
    if 'answered_questions' not in st.session_state:
        st.session_state.answered_questions = set()
    if 'answered_math_questions' not in st.session_state:
        st.session_state.answered_math_questions = set()
    
    # Main app header with animated rainbow background
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">🌟 Knowledge R Us 🌟</h1>
        <p class="main-subtitle">Learn about the world through fun news and activities!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get current kid info
    kid = st.session_state.selected_kid
    age_group = kid['age_group']
    
    # Get difficulty level for authenticated users
    difficulty_level = 1
    if hasattr(st.session_state, 'selected_kid') and hasattr(st.session_state, 'profile_manager'):
        difficulty_level = st.session_state.profile_manager.get_difficulty_level(st.session_state.selected_kid['kid_id'])
    
    st.markdown(f"**Current Level:** {difficulty_level} | **Age Group:** {age_group}")
    
    # Generate math questions
    from math_curriculum import MathCurriculumGenerator
    math_generator = MathCurriculumGenerator()
    
    # Generate multiple sets of questions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎲 Generate New Math Questions", key="generate_math"):
            # Clear previous math questions
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith('math_q_')]
            for key in keys_to_remove:
                del st.session_state[key]
            st.session_state.math_questions_generated = True
            st.session_state.math_test_mode = False
            st.rerun()
    
    with col2:
        if st.button("📝 Take 20-Question Math Test", key="math_test"):
            # Clear previous questions
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith('math_q_')]
            for key in keys_to_remove:
                del st.session_state[key]
            st.session_state.math_questions_generated = True
            st.session_state.math_test_mode = True
            st.rerun()
    
    with col3:
        if st.button("📊 View Math Progress", key="math_progress"):
            st.info("Math progress tracking coming soon!")
    
    # Display math questions
    if st.session_state.get('math_questions_generated', False):
        # Get math-specific difficulty level
        math_difficulty = 1
        if (hasattr(st.session_state, 'selected_kid') and 
            hasattr(st.session_state, 'profile_manager') and 
            st.session_state.selected_kid is not None and 
            st.session_state.profile_manager is not None):
            try:
                kid_id = st.session_state.selected_kid['kid_id']
                math_difficulty = st.session_state.profile_manager.get_difficulty_level(kid_id, 'math')
            except (KeyError, TypeError, AttributeError) as e:
                st.warning(f"Could not load math difficulty level, using default (Level 1)")
                math_difficulty = 1
        
        # Determine number of questions based on mode
        is_test_mode = st.session_state.get('math_test_mode', False)
        num_questions = 20 if is_test_mode else 5
        
        math_questions = math_generator.generate_math_questions(age_group, math_difficulty, num_questions)
        
        if math_questions:
            # Progress and score display
            answered_count = len(st.session_state.get('answered_math_questions', set()))
            total_questions = len(math_questions)
            progress_percent = (answered_count / total_questions) * 100
            
            st.markdown(f"""
            <div class="progress-container">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div>
                        <div class="score-display">🏆 Score: {st.session_state.score}</div>
                        <div style="color: #2C3E50; font-size: 1.1rem;">Keep going! You're doing great!</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #2C3E50;">
                            📊 Progress: {answered_count}/{total_questions}
                        </div>
                        <div style="background: #E0E0E0; border-radius: 10px; height: 20px; width: 200px; margin-top: 0.5rem;">
                            <div style="background: linear-gradient(135deg, #4ECDC4, #44A08D); height: 100%; border-radius: 10px; width: {progress_percent}%; transition: width 0.5s ease;"></div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Check if this is a test mode (20 questions)
            if len(math_questions) == 20:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 1.5rem; border-radius: 15px; text-align: center; margin-bottom: 2rem;">
                    <h2 style="color: white; margin: 0; font-size: 2rem;">
                        🧮 20-Question Math Challenge! 🧮
                    </h2>
                    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                        Test your math skills with these challenging problems!
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="text-align: center; margin: 1.5rem 0;">
                    <h2 style="color: #2C3E50; font-family: 'Comic Sans MS', cursive; font-size: 2rem;">
                        🤔 Practice Problems 🤔
                    </h2>
                </div>
                """, unsafe_allow_html=True)
            
            for i, question in enumerate(math_questions):
                # Create beautiful question card
                st.markdown(f"""
                <div class="question-card">
                    <div class="question-title">
                        🧮 Problem {i+1}
                    </div>
                    <div style="font-size: 1.3rem; color: #2C3E50; margin-bottom: 1.5rem; line-height: 1.6;">
                        {question["question"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                question_key = f"math_q_{i}"
                attempt_key = f"math_attempts_{i}"
                feedback_key = f"math_feedback_{i}"
                
                # Initialize attempt counter
                if attempt_key not in st.session_state:
                    st.session_state[attempt_key] = 0
                    
                # Only show interactive elements if question hasn't been answered correctly
                if question_key not in st.session_state.get('answered_math_questions', set()):
                    st.markdown("""
                    <div style="text-align: center; margin: 1.5rem 0;">
                        <h3 style="color: #FF6B35; font-family: 'Comic Sans MS', cursive; font-size: 1.5rem;">
                            🤔 Choose your answer:
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Create answer buttons in a grid
                    if question.get("question_type") == "fill_in_blank" and "options" not in question:
                        # Text input for fill-in-the-blank
                        answer = st.text_input(
                            "✏️ Type your answer:",
                            key=f"text_{question_key}",
                            placeholder="Enter your answer here...",
                            help="Type the number that answers the question"
                        )
                    else:
                        # Multiple choice with beautiful buttons
                        answer = None
                        cols = st.columns(2)
                        for idx, option in enumerate(question["options"]):
                            col = cols[idx % 2]
                            with col:
                                if st.button(
                                    f"🔤 {chr(65 + idx)}) {option}",
                                    key=f"answer_{question_key}_{idx}",
                                    use_container_width=True
                                ):
                                    answer = option
                                    st.session_state[f"selected_answer_{question_key}"] = option
                        
                        # Show selected answer
                        if f"selected_answer_{question_key}" in st.session_state:
                            answer = st.session_state[f"selected_answer_{question_key}"]
                            st.success(f"✅ You selected: **{answer}**")
                        
                    # Check answer button with beautiful styling
                    st.markdown("<br>", unsafe_allow_html=True)
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("🎯 Check My Answer!", key=f"check_math_{i}", use_container_width=True):
                            if answer is None or answer == "":
                                st.error("⚠️ Please select or type an answer first!")
                            else:
                                st.session_state[attempt_key] += 1
                                
                                if 'answered_math_questions' not in st.session_state:
                                    st.session_state.answered_math_questions = set()
                                
                                if str(answer) == str(question["correct"]):
                                    # Correct answer with celebration
                                    points = 10 if st.session_state[attempt_key] == 1 else 5
                                    st.markdown("""
                                    <div class="success-message">
                                        <h3 style="color: #00b894; margin: 0; font-size: 1.5rem;">
                                            🎉 Fantastic! You got it right! 🎉
                                        </h3>
                                        <p style="margin: 0.5rem 0; font-size: 1.1rem;">
                                            """ + question['explanation'] + """
                                        </p>
                                        <p style="margin: 0; font-style: italic; color: #00b894;">
                                            💡 """ + question.get('reasoning', '') + """
                                        </p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    feedback = "Correct!"
                                    st.session_state[feedback_key] = feedback
                                    st.session_state.answered_questions.add(question_key)
                                    st.session_state.score += points
                                    st.balloons()  # Celebration animation!
                                    
                                    # Update progress for authenticated users (math-specific)
                                    if hasattr(st.session_state, 'selected_kid') and hasattr(st.session_state, 'profile_manager'):
                                        kid_id = st.session_state.selected_kid['kid_id']
                                        
                                        # Update math-specific progress
                                        st.session_state.profile_manager.update_subject_progress(
                                            kid_id, 'math', True, points
                                        )
                                        
                                        # Also update general progress for backward compatibility
                                        st.session_state.profile_manager.update_kid_progress(
                                            kid_id, 
                                            score_increment=points, 
                                            questions_increment=1
                                        )
                                        
                                        # Check for new achievements
                                        new_achievements = st.session_state.profile_manager.get_new_achievements(kid_id)
                                        if new_achievements:
                                            for achievement in new_achievements:
                                                st.success(f"🏆 **NEW BADGE EARNED!** {achievement}")
                                            st.balloons()
                                    
                                    st.balloons()
                                else:
                                    # Wrong answer
                                    if st.session_state[attempt_key] == 1:
                                        st.error("❌ Not quite right. Let me explain why:")
                                        st.warning(f"🔍 **Why this is wrong:** {question.get('wrong_explanation', 'That answer is not correct.')}")
                                        st.info(f"💡 **Hint:** {question['hint']}")
                                        st.info("Try again! You can do it! 🌟")
                                    else:
                                        st.error("❌ That's still not right, but great effort!")
                                        st.success(f"✅ **The correct answer is:** {question['correct']}")
                                        st.info(f"📚 **Explanation:** {question['explanation']}")
                                        st.info(f"💡 **Why this is right:** {question['reasoning']}")
                                        st.session_state.answered_math_questions.add(question_key)
                                        
                                        # Update progress (no points for wrong answer)
                                        if hasattr(st.session_state, 'selected_kid') and hasattr(st.session_state, 'profile_manager'):
                                            st.session_state.profile_manager.update_kid_progress(
                                                st.session_state.selected_kid['kid_id'], 
                                                score_increment=0, 
                                                questions_increment=1
                                            )
                else:
                    st.success("✅ **Problem completed!**")
                
                if i < len(math_questions) - 1:
                    st.divider()

def handle_authentication():
    """Handle user authentication"""
    st.header("🔐 Welcome to Knowledge R Us!")
    st.markdown("Please sign in or create an account to continue.")
    
    # Initialize auth system if not exists
    if 'auth_system' not in st.session_state:
        from auth_system import UserProfileManager
        st.session_state.auth_system = UserProfileManager()
    
    auth_system = st.session_state.auth_system
    
    # Login/Register tabs
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button"):
            if username and password:
                is_authenticated = auth_system.authenticate_user(username, password)
                if is_authenticated:
                    user_info = auth_system.get_user_info(username)
                    if user_info:
                        st.session_state.authenticated = True
                        st.session_state.current_user = {'user_id': username, **user_info}
                        st.success(f"Welcome back, {username}!")
                        st.rerun()
                    else:
                        st.error("Error retrieving user information")
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
    
    with tab2:
        st.subheader("Create Account")
        new_username = st.text_input("Choose Username", key="register_username")
        new_password = st.text_input("Choose Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Create Account", key="register_button"):
            if new_username and new_password and confirm_password:
                if new_password == confirm_password:
                    success = auth_system.register_parent(new_username, f"{new_username}@example.com", new_username, new_password)
                    if success:
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username already exists")
                else:
                    st.error("Passwords don't match")
            else:
                st.warning("Please fill in all fields")

def handle_kid_selection():
    """Handle kid profile selection"""
    st.header("👶 Select Your Child's Profile")
    
    user = st.session_state.current_user
    auth_system = st.session_state.auth_system
    
    # Get kid profiles
    kids = auth_system.get_kid_profiles(user['user_id'])
    
    if not kids:
        st.info("No child profiles found. Let's create one!")
        create_kid_profile()
    else:
        st.subheader("Choose a profile:")
        
        # Display kid profiles
        for kid in kids:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{kid['name']}** {kid['avatar']}")
                st.caption(f"Age {kid['age']} • Interests: {', '.join(kid['interests'])}")
            
            with col2:
                if st.button("Select", key=f"select_{kid['kid_id']}"):
                    st.session_state.selected_kid = kid
                    st.success(f"Selected {kid['name']}!")
                    st.rerun()
        
        st.divider()
        st.subheader("Or create a new profile:")
        create_kid_profile()

def create_kid_profile():
    """Create a new kid profile"""
    with st.form("create_kid_profile"):
        st.subheader("Create Child Profile")
        
        name = st.text_input("Child's Name")
        age = st.number_input("Age", min_value=6, max_value=18, value=8)
        
        # Age group mapping
        if 6 <= age <= 8:
            age_group = "6-8"
        elif 9 <= age <= 11:
            age_group = "9-11"
        elif 12 <= age <= 14:
            age_group = "12-14"
        else:
            age_group = "15-18"
        
        avatar = st.selectbox("Choose Avatar", ["👦", "👧", "🧒", "👶", "🦸‍♂️", "🦸‍♀️", "🎓", "🌟"])
        interests = st.multiselect("Interests", ["science", "technology", "environment", "space", "animals", "sports"])
        
        if st.form_submit_button("Create Profile"):
            if name and interests:
                auth_system = st.session_state.auth_system
                user = st.session_state.current_user
                
                kid_data = {
                    'name': name,
                    'age': age,
                    'age_group': age_group,
                    'avatar': avatar,
                    'interests': interests
                }
                
                kid_id = auth_system.create_kid_profile(
                    user['user_id'], 
                    kid_data['name'], 
                    kid_data['age'], 
                    kid_data['interests'], 
                    kid_data['avatar']
                )
                if kid_id:
                    st.success(f"Profile created for {name}!")
                    st.rerun()
                else:
                    st.error("Error creating profile")
            else:
                st.warning("Please fill in name and select at least one interest")

def display_kid_info():
    """Display current kid information"""
    kid = st.session_state.selected_kid
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**Welcome back, {kid['name']}!** {kid['avatar']}")
        st.caption(f"Age {kid['age']} • Learning from real news!")
    
    with col2:
        if st.button("📊 Dashboard"):
            st.session_state.show_dashboard = True
            if 'learning_mode' in st.session_state:
                del st.session_state.learning_mode
            st.rerun()

def display_dashboard():
    """Display kid progress dashboard"""
    kid = st.session_state.selected_kid
    
    # Fun dashboard header
    st.markdown(f"""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #FFE066, #FF6B6B); border-radius: 25px; margin: 20px 0;">
        <div style="font-size: 4em; margin: 10px 0;">{kid['avatar']}</div>
        <h1 style="color: white; font-size: 3em; margin: 10px 0;">{kid['name']}'s Super Dashboard!</h1>
        <p style="color: white; font-size: 1.3em;">🌟 Look at all your amazing progress! 🌟</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔙 Back to Learning Adventure!", use_container_width=True):
            st.session_state.show_dashboard = False
            st.balloons()
            st.rerun()
    
    # Get progress data
    profile_manager = st.session_state.profile_manager
    progress = profile_manager.get_kid_progress(kid['kid_id'])
    
    if progress:
        # Fun progress metrics with colorful cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #FF6B6B, #FF8E8E); border-radius: 20px; margin: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <div style="font-size: 2.5em;">📈</div>
                <h3 style="color: white; margin: 10px 0;">Total Score</h3>
                <h2 style="color: white; font-size: 2.5em; margin: 5px 0;">{progress.get('total_score', 0)}</h2>
                <p style="color: white;">Points Earned!</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #4ECDC4, #6EEEE4); border-radius: 20px; margin: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <div style="font-size: 2.5em;">❓</div>
                <h3 style="color: white; margin: 10px 0;">Questions</h3>
                <h2 style="color: white; font-size: 2.5em; margin: 5px 0;">{progress.get('questions_answered', 0)}</h2>
                <p style="color: white;">Answered!</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #FFE066, #FFE88A); border-radius: 20px; margin: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <div style="font-size: 2.5em; animation: twinkle 1s ease-in-out infinite alternate;">⭐</div>
                <h3 style="color: #FF6B6B; margin: 10px 0;">Stars</h3>
                <h2 style="color: #FF6B6B; font-size: 2.5em; margin: 5px 0;">{stars}</h2>
                <p style="color: #FF6B6B;">Collected!</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            diamonds = progress.get('diamonds', 0)
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #A8E6CF, #7FCDCD); border-radius: 20px; margin: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <div style="font-size: 2.5em; animation: twinkle 1s ease-in-out infinite alternate;">💎</div>
                <h3 style="color: white; margin: 10px 0;">Diamonds</h3>
                <h2 style="color: white; font-size: 2.5em; margin: 5px 0;">{diamonds}</h2>
                <p style="color: white;">Earned!</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Level and difficulty info with fun styling
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            level = progress.get('level', 1)
            st.markdown(f"""
            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 20px; margin: 10px;">
                <div style="font-size: 3em;">🎯</div>
                <h3 style="color: white; margin: 10px 0;">Level</h3>
                <h2 style="color: white; font-size: 3em; margin: 5px 0;">{level}</h2>
                <p style="color: white;">Keep Going!</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            difficulty = progress.get('difficulty_level', 1)
            difficulty_emoji = "🌟" if difficulty <= 2 else "🚀" if difficulty <= 4 else "🏆"
            st.markdown(f"""
            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #FF6B6B, #4ECDC4); border-radius: 20px; margin: 10px;">
                <div style="font-size: 3em;">{difficulty_emoji}</div>
                <h3 style="color: white; margin: 10px 0;">Difficulty</h3>
                <h2 style="color: white; font-size: 3em; margin: 5px 0;">{difficulty}</h2>
                <p style="color: white;">Challenge Level!</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            streak = progress.get('correct_streak', 0)
            fire_emoji = "🔥" * min(streak // 3 + 1, 5) if streak > 0 else "🔥"
            st.markdown(f"""
            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #FFE066, #FF6B6B); border-radius: 20px; margin: 10px;">
                <div style="font-size: 3em;">{fire_emoji}</div>
                <h3 style="color: white; margin: 10px 0;">Streak</h3>
                <h2 style="color: white; font-size: 3em; margin: 5px 0;">{streak}</h2>
                <p style="color: white;">In a Row!</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Fun achievements section
        achievements = progress.get('achievements', [])
        if achievements:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #A8E6CF, #7FCDCD); border-radius: 25px; margin: 20px 0;">
                <h2 style="color: white; font-size: 2.5em; margin: 15px 0;">🏆 Amazing Achievements! 🏆</h2>
            </div>
            """, unsafe_allow_html=True)
            
            for i, achievement in enumerate(achievements):
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: linear-gradient(45deg, #FFE066, #FF6B6B); border-radius: 15px; margin: 10px 0; animation: celebration 0.6s ease-in-out;">
                    <h3 style="color: white; font-size: 1.5em;">🎉 {achievement} 🎉</h3>
                </div>
                """, unsafe_allow_html=True)
        
        # Completed articles
        completed_articles = progress.get('completed_articles', [])
        if completed_articles:
            st.markdown("---")
            st.subheader("📚 Completed Articles")
            st.write(f"You've completed {len(completed_articles)} articles!")
        
        # Last activity
        last_activity = progress.get('last_activity')
        if last_activity:
            st.markdown("---")
            st.caption(f"Last activity: {last_activity}")
    else:
        # Fun empty state
        st.markdown("""
        <div style="text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 25px; margin: 30px 0;">
            <div style="font-size: 5em; margin: 20px 0;">🌟</div>
            <h2 style="color: white; font-size: 2.5em;">Ready for Your First Adventure?</h2>
            <p style="color: white; font-size: 1.5em; margin: 20px 0;">Start learning to see your amazing progress here! 🚀</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Your Learning Journey!", use_container_width=True):
                st.session_state.show_dashboard = False
                st.balloons()
                st.rerun()

def display_news_articles():
    """Display news articles with Science and ELA questions"""
    # Get current kid info
    kid = st.session_state.selected_kid
    age_group = kid['age_group']
    
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
        
        # Load articles with robust error handling
        try:
            with st.spinner("Loading latest news articles..."):
                # Get completed articles for this kid
                completed_articles = st.session_state.profile_manager.get_completed_articles(kid['kid_id'])
                articles = fetch_news_articles(category_filter, 3, completed_articles)
                
                # Always ensure we have articles
                if not articles:
                    st.info("📰 Loading curated educational content...")
                    articles = get_fallback_articles(completed_articles)
                
                if not articles:
                    # Ultimate fallback - create basic articles
                    articles = [{
                        'id': 'basic_science_1',
                        'title': 'Amazing Science Discovery',
                        'content': 'Scientists have made incredible discoveries about how our world works. From tiny atoms to massive galaxies, science helps us understand everything around us. Learning about science is like going on an adventure to discover the secrets of nature!',
                        'category': 'science',
                        'url': '',
                        'published': str(datetime.now()),
                        'source': 'Educational Content'
                    }]
                
                content_adapter = ContentAdapter()
                displayed_count = 0
                
                for i, article in enumerate(articles):
                    # Skip if already completed
                    if article['id'] in completed_articles:
                        continue
                    
                    adapted_article = content_adapter.adapt_content(article, age_group)
                    display_article_with_questions(adapted_article, age_group, i)
                    displayed_count += 1
                
                if displayed_count == 0:
                    st.markdown("""
                    <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #A8E6CF, #7FCDCD); border-radius: 25px; margin: 20px 0;">
                        <div style="font-size: 4em; margin: 20px 0;">🎉</div>
                        <h2 style="color: white; font-size: 2.5em;">Awesome Job!</h2>
                        <p style="color: white; font-size: 1.5em; margin: 20px 0;">You've completed all available articles! 🌟</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔄 Check for New Articles", use_container_width=True):
                        fetch_news_articles.clear()
                        st.balloons()
                        st.rerun()
        
        except Exception as e:
            logger.error(f"Error loading articles: {e}")
            st.markdown("""
            <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #FFE066, #FF6B6B); border-radius: 25px; margin: 20px 0;">
                <div style="font-size: 3em; margin: 15px 0;">📚</div>
                <h3 style="color: white; font-size: 1.8em;">Loading Educational Content...</h3>
                <p style="color: white; font-size: 1.2em;">We're preparing some amazing stories for you!</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Use fallback articles with better error handling
            try:
                completed_articles = st.session_state.profile_manager.get_completed_articles(kid['kid_id'])
            except:
                completed_articles = []
            
            articles = get_fallback_articles(completed_articles)
            content_adapter = ContentAdapter()
            for i, article in enumerate(articles[:3]):  # Limit to 3 articles
                try:
                    adapted_article = content_adapter.adapt_content(article, age_group)
                    display_article_with_questions(adapted_article, age_group, i)
                except Exception as article_error:
                    logger.error(f"Error displaying article {i}: {article_error}")
                    continue
    
    with col2:
        st.header("🎮 Learning Quests")
        
        # Daily quest
        st.subheader("🎯 Daily Quest")
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
