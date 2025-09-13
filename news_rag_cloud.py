#!/usr/bin/env python3
"""
Cloud-Compatible News RAG System for Knowledge R Us
Uses Hugging Face Transformers instead of Ollama for Streamlit Cloud deployment
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

# Cloud-compatible LLM integration
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class CloudNewsRAGSystem:
    """Cloud-compatible RAG system for news content processing"""
    
    def __init__(self, 
                 chroma_path: str = "./chroma_db",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 llm_model: str = "microsoft/DialoGPT-medium"):
        
        self.chroma_path = chroma_path
        self.embedding_model_name = embedding_model
        self.llm_model_name = llm_model
        
        # Initialize components
        self.embedding_model = SentenceTransformer(embedding_model)
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self._get_or_create_collection()
        
        # Initialize lightweight LLM for cloud deployment
        self._init_llm()
        
        # News sources configuration
        self.news_sources = {
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
        
    def _init_llm(self):
        """Initialize lightweight LLM for cloud deployment"""
        try:
            # Use a smaller, cloud-friendly model
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
            self.model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")
            
            # Set pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            logger.info("LLM initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            self.tokenizer = None
            self.model = None
        
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
    
    def fetch_news_from_rss(self, category: str, max_articles: int = 5) -> List[Dict]:
        """Fetch news articles from RSS feeds with error handling"""
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
                        # Simple article extraction without news-please for faster processing
                        article_data = {
                            "title": entry.title,
                            "content": getattr(entry, 'summary', entry.title),
                            "url": entry.link,
                            "published": datetime.now(),
                            "category": category,
                            "source": rss_url,
                            "authors": [],
                            "image_url": None
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
            doc_text = f"{article['title']}\n\n{article['content'][:500]}"
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
        """Rule-based content adaptation (faster than LLM for cloud deployment)"""
        
        # Use rule-based adaptation for better performance in cloud
        content = article['content']
        title = article['title']
        
        if age_group == "6-8":
            # Simple vocabulary replacements
            replacements = {
                "scientists": "smart people who study things",
                "researchers": "people who find out new things",
                "technology": "cool new tools",
                "discovered": "found",
                "significant": "very important",
                "advanced": "very good"
            }
            
            for old, new in replacements.items():
                content = content.replace(old, new)
                title = title.replace(old, new)
                
            # Simplify sentences
            sentences = content.split('. ')
            simple_sentences = []
            for sentence in sentences[:3]:  # Limit to 3 sentences for young kids
                if len(sentence.split()) > 15:
                    words = sentence.split()
                    simple_sentences.append(' '.join(words[:10]) + '.')
                else:
                    simple_sentences.append(sentence)
            content = ' '.join(simple_sentences)
            
        elif age_group == "9-11":
            # Moderate simplification
            replacements = {
                "significant": "important",
                "discovered": "found out",
                "researchers": "scientists"
            }
            
            for old, new in replacements.items():
                content = content.replace(old, new)
                title = title.replace(old, new)
        
        return {
            **article,
            'title': title,
            'content': content,
            'adapted_for_age': age_group
        }
    
    def generate_stem_questions(self, article: Dict, age_group: str) -> List[Dict]:
        """Generate STEM questions using rule-based approach for cloud compatibility"""
        
        questions = []
        title = article['title'].lower()
        content = article['content'].lower()
        
        # Math questions based on content analysis
        if age_group == "6-8":
            if "mars" in title or "space" in title:
                questions.append({
                    "type": "math",
                    "question": "If we send 2 robots to Mars and they find 3 rocks each, how many rocks in total?",
                    "options": ["4", "5", "6", "7"],
                    "correct": "6",
                    "explanation": "2 robots × 3 rocks = 6 rocks total!"
                })
            elif "butterfly" in title or "animal" in title:
                questions.append({
                    "type": "math",
                    "question": "If a butterfly has 4 wings and we see 2 butterflies, how many wings total?",
                    "options": ["6", "7", "8", "9"],
                    "correct": "8",
                    "explanation": "2 butterflies × 4 wings = 8 wings!"
                })
            else:
                questions.append({
                    "type": "math",
                    "question": "If scientists study 5 things each day for 2 days, how many things total?",
                    "options": ["8", "9", "10", "11"],
                    "correct": "10",
                    "explanation": "5 things × 2 days = 10 things!"
                })
        
        elif age_group == "9-11":
            if "percent" in content or "%" in content:
                questions.append({
                    "type": "math",
                    "question": "If something is 75% complete, what percentage is left to finish?",
                    "options": ["20%", "25%", "30%", "35%"],
                    "correct": "25%",
                    "explanation": "100% - 75% = 25% remaining"
                })
            else:
                questions.append({
                    "type": "math",
                    "question": "If a discovery happened 50 years ago and it's now 2024, what year was it?",
                    "options": ["1974", "1975", "1976", "1977"],
                    "correct": "1974",
                    "explanation": "2024 - 50 = 1974"
                })
        
        # Science questions
        if "mars" in title or "space" in title:
            if age_group == "6-8":
                questions.append({
                    "type": "science",
                    "question": "What planet is called the 'Red Planet'?",
                    "options": ["Earth", "Mars", "Jupiter", "Venus"],
                    "correct": "Mars",
                    "explanation": "Mars looks red because of iron oxide (rust) on its surface!"
                })
            else:
                questions.append({
                    "type": "science",
                    "question": "Why is Mars exploration important for humans?",
                    "options": ["It's close to Earth", "It might have had life", "It's very cold", "It's very small"],
                    "correct": "It might have had life",
                    "explanation": "Scientists study Mars to learn if life could exist there!"
                })
        
        elif "environment" in title or "climate" in title:
            questions.append({
                "type": "science",
                "question": "What helps plants make oxygen?",
                "options": ["Water", "Sunlight", "Soil", "All of these"],
                "correct": "All of these",
                "explanation": "Plants need water, sunlight, and nutrients from soil to make oxygen!"
            })
        
        else:
            # Generic science question
            questions.append({
                "type": "science",
                "question": "What do scientists use to learn about the world?",
                "options": ["Experiments", "Observations", "Questions", "All of these"],
                "correct": "All of these",
                "explanation": "Scientists use experiments, observations, and questions to discover new things!"
            })
        
        return questions
    
    def refresh_news_database(self, categories: List[str] = None) -> None:
        """Refresh the news database with latest articles"""
        if categories is None:
            categories = list(self.news_sources.keys())
            
        logger.info(f"Refreshing news database for categories: {categories}")
        
        for category in categories:
            articles = self.fetch_news_from_rss(category, max_articles=3)
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
        
        # If no articles found, create some sample articles
        if not raw_articles:
            raw_articles = self._get_fallback_articles()
        
        # Adapt content for age group
        adapted_articles = []
        for article in raw_articles:
            adapted = self.adapt_content_for_age(article, age_group)
            questions = self.generate_stem_questions(adapted, age_group)
            adapted['questions'] = questions
            adapted_articles.append(adapted)
        
        return adapted_articles
    
    def _get_fallback_articles(self) -> List[Dict]:
        """Fallback articles when no real news is available"""
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

# Initialize global RAG system instance
cloud_rag_system = None

def get_cloud_rag_system() -> CloudNewsRAGSystem:
    """Get or create global cloud RAG system instance"""
    global cloud_rag_system
    if cloud_rag_system is None:
        cloud_rag_system = CloudNewsRAGSystem()
    return cloud_rag_system
