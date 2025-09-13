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
        
        if age_group == "6-8":
            # Significantly simplify for youngest group
            adapted["content"] = self._simplify_text(article["content"], age_group)
            adapted["title"] = self._simplify_text(article["title"], age_group)
        elif age_group == "9-11":
            # Moderate simplification but keep more content
            adapted["content"] = self._moderate_simplify(article["content"])
            adapted["title"] = self._simplify_text(article["title"], age_group)
        else:
            # Keep full content for older students (12-14, 15-17)
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

@st.cache_data(ttl=3600)
def fetch_news_articles(category: str = "science", max_articles: int = 3) -> List[Dict]:
    """Fetch news articles from RSS feeds with enhanced content extraction"""
    articles = []
    
    if category not in NEWS_SOURCES:
        return get_fallback_articles()
    
    for rss_url in NEWS_SOURCES[category][:1]:  # Limit to 1 source for reliability
        try:
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:max_articles]:
                try:
                    # Extract more comprehensive content
                    content = ""
                    if hasattr(entry, 'content') and entry.content:
                        # Get the first content entry
                        content = entry.content[0].value if isinstance(entry.content, list) else entry.content
                    elif hasattr(entry, 'summary') and entry.summary:
                        content = entry.summary
                    elif hasattr(entry, 'description') and entry.description:
                        content = entry.description
                    else:
                        content = entry.title
                    
                    # Clean HTML tags and limit length appropriately
                    import re
                    content = re.sub(r'<[^>]+>', '', content)  # Remove HTML tags
                    content = re.sub(r'\s+', ' ', content).strip()  # Clean whitespace
                    
                    # Don't limit content too aggressively - allow more for older kids
                    content = content[:2500] if len(content) > 2500 else content
                    
                    article_data = {
                        "title": entry.title,
                        "content": content,
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
    """Fallback articles when RSS feeds fail - with age-appropriate content depth"""
    return [
        {
            "title": "Scientists Discover New Planet",
            "content": "Astronomers have made an exciting discovery in deep space - a new planet outside our solar system called an exoplanet. This distant world, located about 100 light-years from Earth, has captured scientists' attention because it might have conditions suitable for liquid water.\n\nUsing powerful space telescopes like the James Webb Space Telescope, researchers detected this planet by observing tiny changes in starlight as the planet passed in front of its host star. This method, called the transit technique, allows scientists to learn about the planet's size, atmosphere, and potential for supporting life.\n\nThe discovery is particularly significant because the planet orbits within its star's 'habitable zone' - the region where temperatures are just right for liquid water to exist. While we can't visit this planet with current technology, studying it helps us understand how planetary systems form and whether life might exist elsewhere in the universe. This research represents years of careful observation and data analysis by international teams of astronomers.",
            "category": "science",
            "url": "https://example.com/planet",
            "published": str(datetime.now())
        },
        {
            "title": "New Robot Helps Clean Ocean",
            "content": "Marine engineers have developed an innovative autonomous robot designed to tackle one of our planet's biggest environmental challenges: ocean pollution. This solar-powered device, roughly the size of a small boat, uses advanced sensors and artificial intelligence to identify and collect plastic waste floating on the ocean's surface.\n\nThe robot operates by scanning the water with cameras and using machine learning algorithms to distinguish between marine life and debris. Once plastic is detected, mechanical arms extend to carefully collect the waste without harming sea creatures. The collected plastic is stored in onboard compartments that can hold up to 500 kilograms of debris.\n\nEarly trials in the Pacific Ocean have shown promising results, with the robot collecting over 2,000 pieces of plastic waste in just one month. The technology represents a significant step forward in ocean conservation efforts. Scientists estimate that if deployed at scale, these robots could help remove millions of tons of plastic from our oceans, protecting marine ecosystems and the food chain that depends on healthy seas.",
            "category": "technology", 
            "url": "https://example.com/robot",
            "published": str(datetime.now())
        },
        {
            "title": "Trees Help Fight Climate Change",
            "content": "Climate scientists have published new research highlighting the crucial role that forests play in combating global warming. Trees act as natural carbon capture systems, absorbing carbon dioxide from the atmosphere during photosynthesis and storing it in their wood, roots, and surrounding soil.\n\nThe study, conducted across multiple continents, found that mature forests can absorb up to 2.6 tons of carbon dioxide per acre annually. This process not only removes greenhouse gases from the atmosphere but also produces oxygen as a byproduct. Additionally, forests create cooling effects through transpiration - the process by which trees release water vapor through their leaves, naturally air-conditioning their surroundings.\n\nResearchers emphasize that protecting existing forests and planting new trees are among the most cost-effective strategies for addressing climate change. However, they note that different tree species and forest management practices can significantly impact carbon storage capacity. The findings support global reforestation initiatives and highlight the importance of sustainable forestry practices in our fight against climate change.",
            "category": "environment",
            "url": "https://example.com/trees", 
            "published": str(datetime.now())
        }
    ]

class QuestionGenerator:
    """Generates STEM + ELA questions based on articles and age groups"""
    
    def generate_questions(self, article: Dict, age_group: str) -> List[Dict]:
        """Generate age-appropriate questions for Math, Science, and ELA"""
        questions = []
        
        # Math questions
        math_q = self._generate_math_question(article, age_group)
        if math_q:
            questions.append(math_q)
        
        # Science questions
        science_q = self._generate_science_question(article, age_group)
        if science_q:
            questions.append(science_q)
        
        # ELA (English Language Arts) questions
        ela_q = self._generate_ela_question(article, age_group)
        if ela_q:
            questions.append(ela_q)
        
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
                    "hint": "Try multiplying: How many planets × How many moons each planet has?",
                    "explanation": "3 planets × 2 moons = 6 moons total!",
                    "reasoning": "This is multiplication! When we have groups of the same size, we multiply the number of groups by the size of each group."
                }
            elif "robot" in title or "ocean" in title:
                return {
                    "type": "math", 
                    "question": "If a robot cleans 5 pieces of trash per hour for 3 hours, how many pieces total?",
                    "options": ["12", "15", "18", "20"],
                    "correct": "15",
                    "hint": "Think about rate × time. How much per hour × how many hours?",
                    "explanation": "5 pieces × 3 hours = 15 pieces!",
                    "reasoning": "This shows rate problems! When something happens at a steady rate, we multiply the rate by the time."
                }
            else:
                return {
                    "type": "math",
                    "question": "If we plant 4 trees each day for 2 days, how many trees total?",
                    "options": ["6", "7", "8", "9"],
                    "correct": "8", 
                    "hint": "How many trees per day × how many days?",
                    "explanation": "4 trees × 2 days = 8 trees!",
                    "reasoning": "This is repeated addition! 4 + 4 = 8, or we can multiply 4 × 2 = 8."
                }
        
        elif age_group == "9-11":
            if "percent" in content or "climate" in title:
                return {
                    "type": "math",
                    "question": "If trees absorb 25% of carbon dioxide, how much is left in the air?",
                    "options": ["70%", "75%", "80%", "85%"],
                    "correct": "75%",
                    "hint": "Start with 100% and subtract what the trees absorb.",
                    "explanation": "100% - 25% = 75% remains in the air",
                    "reasoning": "Percentages show parts of a whole. If trees take away 25%, we subtract from the total 100%."
                }
            else:
                return {
                    "type": "math",
                    "question": "If a discovery was made 10 years ago and it's 2024, what year was it?",
                    "options": ["2012", "2013", "2014", "2015"],
                    "correct": "2014",
                    "hint": "Count backwards from 2024. What is 2024 minus 10?",
                    "explanation": "2024 - 10 = 2014",
                    "reasoning": "To find a past year, we subtract the number of years ago from the current year."
                }
        
        elif age_group in ["12-14", "15-17"]:
            if "planet" in title:
                return {
                    "type": "math",
                    "question": "If a planet is 100 light-years away and light travels 300,000 km/s, how long to reach it?",
                    "options": ["50 years", "100 years", "200 years", "300 years"],
                    "correct": "100 years",
                    "hint": "A light-year is the distance light travels in one year. How long for 100 light-years?",
                    "explanation": "At light speed, it takes 100 years to travel 100 light-years!",
                    "reasoning": "A light-year is a unit of distance, not time. It's the distance light travels in one year, so 100 light-years takes 100 years at light speed."
                }
            else:
                return {
                    "type": "math",
                    "question": "If ocean cleanup removes 1,000 kg of plastic daily, how much in a year?",
                    "options": ["300,000 kg", "365,000 kg", "400,000 kg", "500,000 kg"],
                    "correct": "365,000 kg",
                    "hint": "How many days are in a year? Multiply that by the daily amount.",
                    "explanation": "1,000 kg × 365 days = 365,000 kg per year",
                    "reasoning": "This is a rate calculation: daily rate × number of days in a year gives the annual total."
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
                    "hint": "Think about tools that make far away things look bigger and closer.",
                    "explanation": "Telescopes help us see things that are very far away in space!",
                    "reasoning": "Telescopes are special tools that collect light and magnify distant objects, making planets and stars visible from Earth."
                }
            else:
                return {
                    "type": "science",
                    "question": "Why is finding water on other planets important?",
                    "options": ["It's pretty", "Life needs water", "It's rare", "It's cold"],
                    "correct": "Life needs water",
                    "hint": "Think about what all living things on Earth need to survive.",
                    "explanation": "Water is essential for life as we know it!",
                    "reasoning": "All known life forms require water for biological processes like metabolism, so finding water suggests a planet might support life."
                }
        
        elif "robot" in title or "ocean" in title:
            if age_group == "6-8":
                return {
                    "type": "science",
                    "question": "Why is it important to clean the ocean?",
                    "options": ["To look nice", "To help sea animals", "To swim better", "To find treasure"],
                    "correct": "To help sea animals",
                    "hint": "Think about who lives in the ocean and what happens when it's dirty.",
                    "explanation": "Clean oceans help fish, dolphins, and other sea animals stay healthy!",
                    "reasoning": "Ocean pollution harms marine ecosystems. Clean water provides oxygen and food that sea creatures need to survive."
                }
            else:
                return {
                    "type": "science",
                    "question": "What type of pollution do ocean-cleaning robots target?",
                    "options": ["Oil spills", "Plastic waste", "Chemical waste", "All of these"],
                    "correct": "All of these",
                    "hint": "Think about all the different ways humans pollute the ocean.",
                    "explanation": "Modern cleanup robots can target various types of ocean pollution!",
                    "reasoning": "Ocean pollution comes from many sources. Advanced robots use different technologies to detect and remove various pollutants."
                }
        
        elif "tree" in title or "climate" in title:
            if age_group == "6-8":
                return {
                    "type": "science",
                    "question": "What do trees make that we need to breathe?",
                    "options": ["Water", "Oxygen", "Food", "Shelter"],
                    "correct": "Oxygen",
                    "hint": "What invisible gas do your lungs need from the air?",
                    "explanation": "Trees make oxygen that we breathe and take in carbon dioxide!",
                    "reasoning": "Trees perform photosynthesis, using sunlight to convert carbon dioxide and water into glucose and oxygen. We need oxygen to live!"
                }
            else:
                return {
                    "type": "science",
                    "question": "How do trees help fight climate change?",
                    "options": ["They absorb CO2", "They provide shade", "They prevent erosion", "All of these"],
                    "correct": "All of these",
                    "hint": "Trees help the environment in many different ways. Think about all their benefits.",
                    "explanation": "Trees help climate in multiple ways: absorbing CO2, cooling areas, and preventing soil erosion!",
                    "reasoning": "Trees are climate heroes! They remove CO2 (a greenhouse gas), cool temperatures through shade and transpiration, and their roots prevent soil erosion."
                }
        
        else:
            return {
                "type": "science",
                "question": "What is the scientific method?",
                "options": ["Guessing answers", "Observe, hypothesize, test", "Reading books", "Asking friends"],
                "correct": "Observe, hypothesize, test",
                "hint": "Think about the steps scientists follow to discover new things.",
                "explanation": "Scientists observe, make hypotheses, and test them to learn new things!",
                "reasoning": "The scientific method is a systematic way to understand the world: observe phenomena, form hypotheses (educated guesses), then test them with experiments."
            }
    
    def _generate_ela_question(self, article: Dict, age_group: str) -> Dict:
        """Generate ELA (English Language Arts) questions based on article content"""
        title = article["title"].lower()
        content = article["content"].lower()
        
        if age_group == "6-8":
            if "planet" in title or "space" in title:
                return {
                    "type": "ela",
                    "question": "What is the main idea of this article?",
                    "options": ["Cooking food", "Finding new planets", "Playing games", "Building houses"],
                    "correct": "Finding new planets",
                    "hint": "Look at the title and think about what the whole article is about.",
                    "explanation": "The article talks about discovering new planets in space!",
                    "reasoning": "The main idea is the most important thing an article tells us. We find it by looking at what the whole article is about."
                }
            elif "robot" in title or "ocean" in title:
                return {
                    "type": "ela",
                    "question": "Which word best describes the robot in the article?",
                    "options": ["Helpful", "Scary", "Tiny", "Loud"],
                    "correct": "Helpful",
                    "hint": "Think about what the robot does for the ocean and sea animals.",
                    "explanation": "The robot helps by cleaning trash from the ocean!",
                    "reasoning": "We use describing words (adjectives) to tell what something is like. The robot helps clean, so 'helpful' describes it best."
                }
            else:
                return {
                    "type": "ela",
                    "question": "What does the word 'scientists' mean in this article?",
                    "options": ["People who cook", "People who study things", "People who sing", "People who drive"],
                    "correct": "People who study things",
                    "hint": "Think about what scientists do to learn new things.",
                    "explanation": "Scientists are people who study and learn about the world!",
                    "reasoning": "Context clues help us understand new words. The article shows scientists discovering and learning things."
                }
        
        elif age_group == "9-11":
            if "climate" in title or "tree" in title:
                return {
                    "type": "ela",
                    "question": "What is the author's purpose in writing this article?",
                    "options": ["To entertain", "To inform", "To persuade", "To confuse"],
                    "correct": "To inform",
                    "hint": "Think about whether the author is teaching you facts or trying to make you laugh.",
                    "explanation": "The author wants to teach us facts about trees and climate!",
                    "reasoning": "Authors write for different purposes: to inform (teach facts), entertain (make us laugh), or persuade (convince us). This article teaches us facts."
                }
            else:
                return {
                    "type": "ela",
                    "question": "Which sentence shows cause and effect in the article?",
                    "options": ["The discovery was amazing", "Scientists used telescopes", "Because of this research, we learned more", "The planet is far away"],
                    "correct": "Because of this research, we learned more",
                    "hint": "Look for words like 'because', 'so', or 'as a result' that show one thing causing another.",
                    "explanation": "This sentence shows that research (cause) led to learning more (effect)!",
                    "reasoning": "Cause and effect shows how one thing makes another thing happen. Signal words like 'because' help us spot these relationships."
                }
        
        elif age_group in ["12-14", "15-17"]:
            if "technology" in title or "robot" in title:
                return {
                    "type": "ela",
                    "question": "What literary device does the author use when describing the robot as 'tireless'?",
                    "options": ["Simile", "Metaphor", "Personification", "Alliteration"],
                    "correct": "Personification",
                    "hint": "Think about giving human qualities to non-human things.",
                    "explanation": "Calling a robot 'tireless' gives it human-like qualities!",
                    "reasoning": "Personification gives human characteristics to non-human things. Robots don't get tired like humans do, so this is personification."
                }
            else:
                return {
                    "type": "ela",
                    "question": "What tone does the author use when discussing this scientific discovery?",
                    "options": ["Pessimistic", "Optimistic", "Angry", "Bored"],
                    "correct": "Optimistic",
                    "hint": "Look at the word choices. Does the author seem excited or worried about the discovery?",
                    "explanation": "The author uses positive words showing excitement about the discovery!",
                    "reasoning": "Tone is the author's attitude toward the subject. Positive words like 'exciting', 'breakthrough', and 'promising' show optimism."
                }
        
        return {
            "type": "ela",
            "question": "What type of text is this article?",
            "options": ["Fiction story", "News article", "Poem", "Recipe"],
            "correct": "News article",
            "hint": "Think about where you might read this and what kind of information it gives.",
            "explanation": "This is a news article that tells us about real events!",
            "reasoning": "News articles inform readers about current events and real happenings in the world, which is what this text does."
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
                attempt_key = f"attempts_{question_key}"
                
                # Initialize attempt counter
                if attempt_key not in st.session_state:
                    st.session_state[attempt_key] = 0
                
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
                        st.session_state[attempt_key] += 1
                        
                        if answer == question["correct"]:
                            st.success(f"🎉 Correct! {question['explanation']}")
                            st.info(f"💡 **Why this is right:** {question['reasoning']}")
                            st.session_state.answered_questions.add(question_key)
                            st.session_state.score += 10
                            st.session_state.questions_answered += 1
                            st.balloons()
                        else:
                            if st.session_state[attempt_key] == 1:
                                # First wrong attempt - show hint
                                st.error(f"❌ Not quite right. Let me give you a hint!")
                                st.info(f"💡 **Hint:** {question['hint']}")
                                st.info("Try again! You can do it! 🌟")
                            else:
                                # Second attempt - show answer and explanation
                                st.error(f"❌ That's still not right, but great effort!")
                                st.success(f"✅ **The correct answer is:** {question['correct']}")
                                st.info(f"📚 **Explanation:** {question['explanation']}")
                                st.info(f"💡 **Why this is right:** {question['reasoning']}")
                                st.session_state.answered_questions.add(question_key)
                                st.session_state.questions_answered += 1
                                # Give partial credit for trying
                                st.session_state.score += 5
                        
                        # Rerun to update sidebar
                        st.rerun()
                    else:
                        st.info("You've already answered this question!")
                
                # Show attempt status
                if st.session_state[attempt_key] > 0 and question_key not in st.session_state.answered_questions:
                    if st.session_state[attempt_key] == 1:
                        st.caption("💪 One more try! You've got this!")
                
                st.divider()  # Separate questions visually

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
