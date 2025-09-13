#!/usr/bin/env python3
"""
News RAG System for Knowledge R Us
Integrates news-please, ChromaDB, and Ollama for dynamic content generation
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path

# News extraction
from newsplease import NewsPlease
import feedparser

# Vector database and embeddings
import chromadb
from sentence_transformers import SentenceTransformer

# LLM integration
import ollama
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class NewsRAGSystem:
    """RAG system for news content processing and age adaptation"""
    
    def __init__(self, 
                 chroma_path: str = "./chroma_db",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 llm_model: str = "llama2:7b"):
        
        self.chroma_path = chroma_path
        self.embedding_model_name = embedding_model
        self.llm_model = llm_model
        
        # Initialize components
        self.embedding_model = SentenceTransformer(embedding_model)
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self._get_or_create_collection()
        
        # News sources configuration
        self.news_sources = {
            "science": [
                "https://feeds.feedburner.com/oreilly/radar",
                "https://www.sciencedaily.com/rss/all.xml",
                "https://www.nasa.gov/news/releases/latest/index.html"
            ],
            "technology": [
                "https://feeds.feedburner.com/TechCrunch",
                "https://www.wired.com/feed/rss"
            ],
            "environment": [
                "https://www.nationalgeographic.com/environment/rss/",
                "https://www.epa.gov/newsreleases/rss.xml"
            ]
        }
        
    def _get_or_create_collection(self):
        """Get or create ChromaDB collection for news articles"""
        try:
            collection = self.chroma_client.get_collection("news_articles")
            logger.info("Retrieved existing news collection")
        except:
            collection = self.chroma_client.create_collection(
                name="news_articles",
                metadata={"description": "Educational news articles for Knowledge R Us"}
            )
            logger.info("Created new news collection")
        return collection
    
    def fetch_news_from_rss(self, category: str, max_articles: int = 10) -> List[Dict]:
        """Fetch news articles from RSS feeds"""
        articles = []
        
        if category not in self.news_sources:
            logger.warning(f"Category {category} not found in news sources")
            return articles
            
        for rss_url in self.news_sources[category]:
            try:
                feed = feedparser.parse(rss_url)
                logger.info(f"Fetched {len(feed.entries)} articles from {rss_url}")
                
                for entry in feed.entries[:max_articles]:
                    try:
                        # Use news-please to extract full article content
                        article = NewsPlease.from_url(entry.link)
                        
                        if article and article.maintext:
                            article_data = {
                                "title": article.title or entry.title,
                                "content": article.maintext,
                                "url": entry.link,
                                "published": article.date_publish or datetime.now(),
                                "category": category,
                                "source": rss_url,
                                "authors": article.authors or [],
                                "image_url": getattr(article, 'image_url', None)
                            }
                            articles.append(article_data)
                            
                    except Exception as e:
                        logger.error(f"Error processing article {entry.link}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error fetching RSS feed {rss_url}: {e}")
                continue
                
        logger.info(f"Successfully fetched {len(articles)} articles for category {category}")
        return articles
    
    def add_articles_to_vector_db(self, articles: List[Dict]) -> None:
        """Add articles to ChromaDB vector database"""
        if not articles:
            return
            
        documents = []
        metadatas = []
        ids = []
        
        for i, article in enumerate(articles):
            # Create document text for embedding
            doc_text = f"{article['title']}\n\n{article['content'][:1000]}"  # Limit content length
            documents.append(doc_text)
            
            # Create metadata
            metadata = {
                "title": article['title'],
                "category": article['category'],
                "url": article['url'],
                "published": str(article['published']),
                "source": article['source'],
                "full_content": article['content']
            }
            metadatas.append(metadata)
            
            # Create unique ID
            article_id = f"{article['category']}_{i}_{hash(article['url']) % 10000}"
            ids.append(article_id)
        
        # Add to collection
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(articles)} articles to vector database")
        except Exception as e:
            logger.error(f"Error adding articles to vector database: {e}")
    
    def search_relevant_articles(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search for relevant articles using vector similarity"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            articles = []
            if results['metadatas'] and results['metadatas'][0]:
                for metadata in results['metadatas'][0]:
                    articles.append({
                        "title": metadata['title'],
                        "content": metadata['full_content'],
                        "category": metadata['category'],
                        "url": metadata['url'],
                        "published": metadata['published']
                    })
            
            logger.info(f"Found {len(articles)} relevant articles for query: {query}")
            return articles
            
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return []
    
    def adapt_content_for_age(self, article: Dict, age_group: str) -> Dict:
        """Use LLM to adapt content for specific age group"""
        
        age_prompts = {
            "6-8": """
            Rewrite this news article for children aged 6-8 years old:
            - Use very simple words (replace complex words with simple ones)
            - Use short sentences (10 words or less)
            - Explain things like you're talking to a young child
            - Make it fun and engaging
            - Keep the main facts but make them easy to understand
            
            Original article:
            Title: {title}
            Content: {content}
            
            Rewritten article for ages 6-8:
            """,
            
            "9-11": """
            Rewrite this news article for children aged 9-11 years old:
            - Use age-appropriate vocabulary (explain technical terms simply)
            - Use clear, medium-length sentences
            - Include interesting facts that would engage this age group
            - Make connections to things they might know
            
            Original article:
            Title: {title}
            Content: {content}
            
            Rewritten article for ages 9-11:
            """,
            
            "12-14": """
            Rewrite this news article for teenagers aged 12-14 years old:
            - Use more sophisticated vocabulary but explain complex concepts
            - Include scientific or technical details that are educational
            - Make it engaging for middle school students
            - Connect to their interests and experiences
            
            Original article:
            Title: {title}
            Content: {content}
            
            Rewritten article for ages 12-14:
            """,
            
            "15-17": """
            Rewrite this news article for teenagers aged 15-17 years old:
            - Use advanced vocabulary and concepts
            - Include detailed scientific, technical, or analytical information
            - Make connections to real-world implications
            - Encourage critical thinking
            
            Original article:
            Title: {title}
            Content: {content}
            
            Rewritten article for ages 15-17:
            """
        }
        
        if age_group not in age_prompts:
            return article
            
        prompt = age_prompts[age_group].format(
            title=article['title'],
            content=article['content'][:2000]  # Limit content length for LLM
        )
        
        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 800
                }
            )
            
            adapted_content = response['response'].strip()
            
            # Extract title and content from response
            lines = adapted_content.split('\n')
            adapted_title = article['title']  # Default to original
            adapted_text = adapted_content
            
            # Try to parse title if it's in the response
            for i, line in enumerate(lines):
                if line.strip().startswith('Title:'):
                    adapted_title = line.replace('Title:', '').strip()
                    adapted_text = '\n'.join(lines[i+1:]).strip()
                    break
            
            return {
                **article,
                'title': adapted_title,
                'content': adapted_text,
                'adapted_for_age': age_group
            }
            
        except Exception as e:
            logger.error(f"Error adapting content with LLM: {e}")
            return article
    
    def generate_stem_questions(self, article: Dict, age_group: str) -> List[Dict]:
        """Generate STEM questions using LLM"""
        
        question_prompt = f"""
        Based on this article, create 2 educational questions (1 math, 1 science) appropriate for children aged {age_group}:

        Article Title: {article['title']}
        Article Content: {article['content'][:1500]}

        For age group {age_group}, create:

        1. MATH QUESTION:
        - Make it relevant to the article content
        - Appropriate difficulty for age {age_group}
        - Include 4 multiple choice options
        - Provide the correct answer and explanation

        2. SCIENCE QUESTION:
        - Test understanding of the article's scientific concepts
        - Appropriate for age {age_group}
        - Include 4 multiple choice options
        - Provide the correct answer and explanation

        Format your response as:
        MATH:
        Question: [question text]
        A) [option 1]
        B) [option 2]
        C) [option 3]
        D) [option 4]
        Correct: [A/B/C/D]
        Explanation: [explanation]

        SCIENCE:
        Question: [question text]
        A) [option 1]
        B) [option 2]
        C) [option 3]
        D) [option 4]
        Correct: [A/B/C/D]
        Explanation: [explanation]
        """
        
        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=question_prompt,
                options={
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            )
            
            questions = self._parse_questions_from_response(response['response'])
            logger.info(f"Generated {len(questions)} questions for article: {article['title']}")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions with LLM: {e}")
            return []
    
    def _parse_questions_from_response(self, response: str) -> List[Dict]:
        """Parse LLM response into structured questions"""
        questions = []
        
        try:
            sections = response.split('SCIENCE:')
            
            # Parse math question
            if len(sections) >= 1:
                math_section = sections[0].replace('MATH:', '').strip()
                math_q = self._parse_single_question(math_section, 'math')
                if math_q:
                    questions.append(math_q)
            
            # Parse science question
            if len(sections) >= 2:
                science_section = sections[1].strip()
                science_q = self._parse_single_question(science_section, 'science')
                if science_q:
                    questions.append(science_q)
                    
        except Exception as e:
            logger.error(f"Error parsing questions: {e}")
            
        return questions
    
    def _parse_single_question(self, text: str, question_type: str) -> Optional[Dict]:
        """Parse a single question from text"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            question_text = ""
            options = []
            correct = ""
            explanation = ""
            
            for line in lines:
                if line.startswith('Question:'):
                    question_text = line.replace('Question:', '').strip()
                elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                    options.append(line[3:].strip())  # Remove "A) " prefix
                elif line.startswith('Correct:'):
                    correct_letter = line.replace('Correct:', '').strip()
                    # Convert letter to option text
                    if correct_letter in ['A', 'B', 'C', 'D']:
                        correct_index = ord(correct_letter) - ord('A')
                        if correct_index < len(options):
                            correct = options[correct_index]
                elif line.startswith('Explanation:'):
                    explanation = line.replace('Explanation:', '').strip()
            
            if question_text and len(options) == 4 and correct and explanation:
                return {
                    "type": question_type,
                    "question": question_text,
                    "options": options,
                    "correct": correct,
                    "explanation": explanation
                }
                
        except Exception as e:
            logger.error(f"Error parsing single question: {e}")
            
        return None
    
    def refresh_news_database(self, categories: List[str] = None) -> None:
        """Refresh the news database with latest articles"""
        if categories is None:
            categories = list(self.news_sources.keys())
            
        logger.info(f"Refreshing news database for categories: {categories}")
        
        for category in categories:
            articles = self.fetch_news_from_rss(category, max_articles=5)
            if articles:
                self.add_articles_to_vector_db(articles)
        
        logger.info("News database refresh completed")
    
    def get_educational_articles(self, age_group: str, topic: str = None, count: int = 3) -> List[Dict]:
        """Get educational articles adapted for specific age group"""
        
        # Search query based on topic or general educational content
        if topic:
            query = f"educational {topic} science technology discovery"
        else:
            query = "science technology discovery education learning"
        
        # Get relevant articles
        raw_articles = self.search_relevant_articles(query, n_results=count)
        
        # Adapt content for age group
        adapted_articles = []
        for article in raw_articles:
            adapted = self.adapt_content_for_age(article, age_group)
            questions = self.generate_stem_questions(adapted, age_group)
            adapted['questions'] = questions
            adapted_articles.append(adapted)
        
        return adapted_articles

# Initialize global RAG system instance
rag_system = None

def get_rag_system() -> NewsRAGSystem:
    """Get or create global RAG system instance"""
    global rag_system
    if rag_system is None:
        rag_system = NewsRAGSystem()
    return rag_system
