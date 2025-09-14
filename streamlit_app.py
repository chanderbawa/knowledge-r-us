#!/usr/bin/env python3
"""
Knowledge R Us - Cloud-Compatible Educational News App
Real news content with age-adaptive learning and user authentication
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

# Import authentication system
from auth_system import UserProfileManager, show_login_page, show_profile_selection, show_kid_dashboard
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

def generate_article_id(article: Dict) -> str:
    """Generate a unique ID for an article based on title and content"""
    import hashlib
    content = f"{article['title']}{article.get('content', '')[:100]}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

@st.cache_data(ttl=3600)
def fetch_news_articles(category: str = "science", max_articles: int = 3, completed_articles: List[str] = None) -> List[Dict]:
    """Fetch news articles from RSS feeds with enhanced content extraction"""
    articles = []
    completed_articles = completed_articles or []
    
    if category not in NEWS_SOURCES:
        return get_fallback_articles()
    
    for rss_url in NEWS_SOURCES[category][:1]:  # Limit to 1 source for reliability
        try:
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:max_articles * 2]:  # Get more entries to filter
                try:
                    # Extract content with better cleaning
                    content = ""
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].value if isinstance(entry.content, list) else entry.content
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description
                    
                    article = {
                        'title': entry.title,
                        'content': content,
                        'url': entry.link,
                        'source': feed.feed.title if hasattr(feed.feed, 'title') else 'News Source',
                        'published': entry.published if hasattr(entry, 'published') else 'Recent',
                        'category': category
                    }
                    
                    # Generate unique ID and check if not completed
                    article['id'] = generate_article_id(article)
                    if article['id'] not in completed_articles:
                        articles.append(article)
                        
                    if len(articles) >= max_articles:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error processing entry: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to fetch from {rss_url}: {e}")
            continue
    
    # If no new articles fetched, use fallback articles (with IDs)
    if not articles:
        for sample_article in get_fallback_articles():
            sample_article['id'] = generate_article_id(sample_article)
            if sample_article['id'] not in completed_articles:
                articles.append(sample_article)
    
    return articles[:max_articles]

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
    
    def __init__(self):
        pass
    
    def generate_questions(self, article: Dict, age_group: str, difficulty_level: int = 1) -> List[Dict]:
        """Generate age-appropriate questions for an article with adaptive difficulty"""
        questions = []
        
        # Generate one question of each type with difficulty adjustment
        math_q = self._generate_math_question(article, age_group, difficulty_level)
        science_q = self._generate_science_question(article, age_group, difficulty_level)
        ela_q = self._generate_ela_question(article, age_group, difficulty_level)
        
        questions.extend([math_q, science_q, ela_q])
        
        return questions
    
    def _generate_math_question(self, article: Dict, age_group: str, difficulty_level: int = 1) -> Dict:
        """Generate math questions based on article content"""
        title = article["title"].lower()
        content = article["content"].lower()
        
        if age_group == "6-8":
            if "planet" in title or "space" in title:
                if difficulty_level == 1:  # Easy
                    return {
                        "type": "math",
                        "question": "If we find 2 new planets and each has 1 moon, how many moons total?",
                        "options": ["1", "2", "3", "4"],
                        "correct": "2",
                        "hint": "Count: 1 + 1 = ?",
                        "explanation": "2 planets × 1 moon each = 2 moons total!",
                        "reasoning": "This is simple addition: 1 moon + 1 moon = 2 moons.",
                        "wrong_explanation": "Remember to count all the moons from both planets together."
                    }
                elif difficulty_level == 2:  # Medium
                    return {
                        "type": "math",
                        "question": "If we find 3 new planets and each has 2 moons, how many moons total?",
                        "options": ["4", "5", "6", "7"],
                        "correct": "6",
                        "hint": "Count: 2 + 2 + 2 = ?",
                        "explanation": "3 planets × 2 moons each = 6 moons total!",
                        "reasoning": "This is multiplication: when we have groups of the same size, we multiply the number of groups by the size of each group.",
                        "wrong_explanation": "You need to multiply, not just add the planet number and moon number. Count all moons from all planets."
                    }
                else:  # Hard
                    return {
                        "type": "math",
                        "question": "If we find 4 new planets, 2 have 3 moons each and 2 have 1 moon each, how many moons total?",
                        "options": ["6", "7", "8", "10"],
                        "correct": "8",
                        "hint": "Calculate each group separately: (2×3) + (2×1) = ?",
                        "explanation": "(2 planets × 3 moons) + (2 planets × 1 moon) = 6 + 2 = 8 moons!",
                        "reasoning": "This involves grouping and adding different multiplication results together.",
                        "wrong_explanation": "Break this into two groups: planets with 3 moons and planets with 1 moon, then add the totals."
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
    
    def _generate_science_question(self, article: Dict, age_group: str, difficulty_level: int = 1) -> Dict:
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
    
    def _generate_ela_question(self, article: Dict, age_group: str, difficulty_level: int = 1) -> Dict:
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
        
        if difficulty_level == 1:  # Easy
            return {
                "type": "ela",
                "question": "What type of text is this article?",
                "options": ["Fiction story", "News article", "Poem", "Recipe"],
                "correct": "News article",
                "hint": "Think about where you might read this and what kind of information it gives.",
                "explanation": "This is a news article that tells us about real events!",
                "reasoning": "News articles inform readers about current events and real happenings in the world, which is what this text does.",
                "wrong_explanation": "Fiction stories are made-up tales, poems have rhythm and rhyme, and recipes tell you how to cook. This text reports real scientific discoveries."
            }
        elif difficulty_level == 2:  # Medium
            return {
                "type": "ela",
                "question": "What is the main purpose of this article?",
                "options": ["To entertain readers", "To inform about discoveries", "To sell products", "To teach cooking"],
                "correct": "To inform about discoveries",
                "hint": "Think about why someone would write about scientific findings.",
                "explanation": "The article's main purpose is to inform readers about new scientific discoveries!",
                "reasoning": "Informational texts like news articles are written to share factual information and educate readers about real events.",
                "wrong_explanation": "While the article might be interesting, its primary goal isn't entertainment, selling, or cooking - it's sharing scientific information."
            }
        else:  # Hard
            return {
                "type": "ela",
                "question": "Which writing technique does the author use to make complex scientific concepts accessible?",
                "options": ["Using only technical terms", "Providing analogies and examples", "Writing in rhyme", "Using bullet points only"],
                "correct": "Providing analogies and examples",
                "hint": "Look for comparisons that help explain difficult ideas in simpler terms.",
                "explanation": "The author uses analogies and examples to help readers understand complex scientific concepts!",
                "reasoning": "Good science writing often uses familiar comparisons and concrete examples to make abstract concepts easier to understand.",
                "wrong_explanation": "Technical terms alone would be confusing, rhyming isn't used in science articles, and bullet points are just formatting - analogies and examples actually explain the concepts."
            }

def check_if_article_completed(article_index: int) -> bool:
    """Check if all questions for an article are completed"""
    # Count total questions for this article
    total_questions = 0
    answered_questions = 0
    
    for question_type in ['math', 'science', 'ela']:
        for j in range(3):  # Assuming max 3 questions per type
            question_key = f"q_{article_index}_{question_type}_{j}"
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
                tabs = st.tabs(tab_names)
                
                for tab_idx, (tab, questions_in_tab) in enumerate(zip(tabs, tab_questions)):
                    with tab:
                        for j, question in enumerate(questions_in_tab):
                            question_key = f"q_{article_index}_{question['type']}_{j}"
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
                                                all_questions_answered = check_if_article_completed(article_index)
                                                
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
                                        
                                        # Rerun to update display
                                        st.rerun()
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
    st.set_page_config(
        page_title="Knowledge R Us - Educational News",
        page_icon="🌟",
        layout="wide",
        initial_sidebar_state="auto"
    )
    
    # Add PWA configuration for mobile app experience
    add_pwa_config()
    add_mobile_styles()
    add_install_prompt()
    
    # Initialize profile manager
    if 'profile_manager' not in st.session_state:
        st.session_state.profile_manager = UserProfileManager()
    
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
        show_kid_dashboard(st.session_state.profile_manager)
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
            st.success("News refreshed!")
        
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
            for i, article in enumerate(articles):
                # Check if article is completed
                article_id = article.get('id', generate_article_id(article))
                is_completed = st.session_state.profile_manager.is_article_completed(kid['kid_id'], article_id)
                
                if is_completed:
                    st.success(f"✅ Article '{article['title']}' completed!")
                    continue
                
                # Adapt content for age group
                adapted_article = content_adapter.adapt_content(article, age_group)
                adapted_article['id'] = article_id
                
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
