#!/usr/bin/env python3
"""
Streamlit Data Storage Solutions for Knowledge R Us
Implements multiple persistence options for better data reliability
"""

import streamlit as st
import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import bcrypt

class StreamlitDataManager:
    """Enhanced data manager using Streamlit's persistence options"""
    
    def __init__(self):
        # Try multiple storage approaches
        self.use_sqlite = True
        self.db_path = "knowledge_r_us.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for persistent storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_date TEXT NOT NULL
                )
            ''')
            
            # Create kid profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kid_profiles (
                    kid_id TEXT PRIMARY KEY,
                    parent_username TEXT NOT NULL,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    age_group TEXT NOT NULL,
                    interests TEXT NOT NULL,
                    avatar TEXT NOT NULL,
                    created_date TEXT NOT NULL,
                    FOREIGN KEY (parent_username) REFERENCES users (username)
                )
            ''')
            
            # Create progress table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kid_progress (
                    kid_id TEXT PRIMARY KEY,
                    total_score INTEGER DEFAULT 0,
                    questions_answered INTEGER DEFAULT 0,
                    articles_read INTEGER DEFAULT 0,
                    stars INTEGER DEFAULT 0,
                    diamonds INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    level_progress INTEGER DEFAULT 0,
                    difficulty_level INTEGER DEFAULT 1,
                    correct_streak INTEGER DEFAULT 0,
                    wrong_streak INTEGER DEFAULT 0,
                    completed_articles TEXT DEFAULT '[]',
                    achievements TEXT DEFAULT '[]',
                    last_activity TEXT,
                    FOREIGN KEY (kid_id) REFERENCES kid_profiles (kid_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            # Insert demo data if tables are empty
            self._insert_demo_data()
            
        except Exception as e:
            print(f"Database initialization error: {e}")
            self.use_sqlite = False
    
    def _insert_demo_data(self):
        """Insert demo data if database is empty"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if demo user exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'demo_parent'")
            if cursor.fetchone()[0] == 0:
                # Insert demo user
                demo_password = bcrypt.hashpw("demo123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute('''
                    INSERT INTO users (username, email, name, password_hash, created_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', ("demo_parent", "demo@example.com", "Demo Parent", demo_password, str(datetime.now())))
                
                # Insert demo kid
                cursor.execute('''
                    INSERT INTO kid_profiles (kid_id, parent_username, name, age, age_group, interests, avatar, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', ("demo_kid_1", "demo_parent", "Alex", 10, "9-11", '["science", "technology"]', "🧑‍🚀", str(datetime.now())))
                
                # Insert demo progress
                cursor.execute('''
                    INSERT INTO kid_progress (kid_id, last_activity)
                    VALUES (?, ?)
                ''', ("demo_kid_1", str(datetime.now())))
                
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            print(f"Demo data insertion error: {e}")
    
    def register_parent(self, username: str, email: str, name: str, password: str) -> bool:
        """Register a new parent account using SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if username exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] > 0:
                conn.close()
                return False
            
            # Hash password and insert user
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('''
                INSERT INTO users (username, email, name, password_hash, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, name, password_hash, str(datetime.now())))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Registration error: {e}")
            return False
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user login using SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                stored_hash = result[0]
                return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
            
            return False
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information from SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT email, name, created_date FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "email": result[0],
                    "name": result[1],
                    "created_date": result[2]
                }
            
            return None
            
        except Exception as e:
            print(f"Get user info error: {e}")
            return None
    
    def create_kid_profile(self, parent_username: str, name: str, age: int, interests: List[str], avatar: str = "👶") -> str:
        """Create a new kid profile using SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate unique kid ID
            kid_id = f"{parent_username}_{name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"
            
            # Determine age group
            if age <= 8:
                age_group = "6-8"
            elif age <= 11:
                age_group = "9-11"
            else:
                age_group = "12-14"
            
            # Insert kid profile
            cursor.execute('''
                INSERT INTO kid_profiles (kid_id, parent_username, name, age, age_group, interests, avatar, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (kid_id, parent_username, name, age, age_group, json.dumps(interests), avatar, str(datetime.now())))
            
            # Initialize progress
            cursor.execute('''
                INSERT INTO kid_progress (kid_id, last_activity)
                VALUES (?, ?)
            ''', (kid_id, str(datetime.now())))
            
            conn.commit()
            conn.close()
            return kid_id
            
        except Exception as e:
            print(f"Create kid profile error: {e}")
            return ""
    
    def get_kid_profiles(self, parent_username: str) -> List[Dict]:
        """Get all kid profiles for a parent using SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT kid_id, name, age, age_group, interests, avatar, created_date
                FROM kid_profiles WHERE parent_username = ?
            ''', (parent_username,))
            
            profiles = []
            for row in cursor.fetchall():
                profiles.append({
                    "kid_id": row[0],
                    "name": row[1],
                    "age": row[2],
                    "age_group": row[3],
                    "interests": json.loads(row[4]),
                    "avatar": row[5],
                    "created_date": row[6]
                })
            
            conn.close()
            return profiles
            
        except Exception as e:
            print(f"Get kid profiles error: {e}")
            return []
    
    def get_kid_progress(self, kid_id: str) -> Dict:
        """Get progress data for a kid using SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT total_score, questions_answered, articles_read, stars, diamonds, level, level_progress,
                       difficulty_level, correct_streak, wrong_streak, completed_articles, achievements, last_activity
                FROM kid_progress WHERE kid_id = ?
            ''', (kid_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "total_score": result[0] or 0,
                    "questions_answered": result[1] or 0,
                    "articles_read": result[2] or 0,
                    "stars": result[3] or 0,
                    "diamonds": result[4] or 0,
                    "level": result[5] or 1,
                    "level_progress": result[6] or 0,
                    "difficulty_level": result[7] or 1,
                    "correct_streak": result[8] or 0,
                    "wrong_streak": result[9] or 0,
                    "completed_articles": json.loads(result[10] or "[]"),
                    "achievements": json.loads(result[11] or "[]"),
                    "last_activity": result[12]
                }
            
            return {}
            
        except Exception as e:
            print(f"Get kid progress error: {e}")
            return {}
    
    def update_kid_progress(self, kid_id: str, score_increment: int = 0, questions_increment: int = 0, article_id: str = None):
        """Update progress for a specific kid using SQLite with proper logic"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current progress
            current_progress = self.get_kid_progress(kid_id)
            if not current_progress:
                # Initialize progress if it doesn't exist
                cursor.execute('''
                    INSERT INTO kid_progress (kid_id, last_activity)
                    VALUES (?, ?)
                ''', (kid_id, str(datetime.now())))
                current_progress = self.get_kid_progress(kid_id)
            
            # Update basic stats
            new_total_score = current_progress.get("total_score", 0) + score_increment
            new_questions_answered = current_progress.get("questions_answered", 0) + questions_increment
            
            # Update stars and diamonds
            new_stars = current_progress.get("stars", 0)
            new_diamonds = current_progress.get("diamonds", 0)
            
            # Award stars for correct answers (10 points)
            if score_increment == 10:
                new_stars += 1
            elif score_increment == 5:  # Half points
                new_stars += 1
                
            # Award diamonds for exceptional performance
            if new_total_score > 0 and new_total_score % 30 == 0:
                new_diamonds += 1
            
            # Update level and level progress
            new_level = max(1, min(10, (new_total_score // 100) + 1))
            new_level_progress = new_total_score % 100
            
            # Update difficulty based on performance
            new_correct_streak = current_progress.get("correct_streak", 0)
            new_wrong_streak = current_progress.get("wrong_streak", 0)
            new_difficulty_level = current_progress.get("difficulty_level", 1)
            
            if score_increment > 0:  # Correct answer
                new_correct_streak += 1
                new_wrong_streak = 0
                # Increase difficulty after 3 correct answers in a row
                if new_correct_streak >= 3 and new_difficulty_level < 3:
                    new_difficulty_level += 1
                    new_correct_streak = 0
            elif score_increment == 0 and questions_increment > 0:  # Wrong answer
                new_wrong_streak += 1
                new_correct_streak = 0
                # Decrease difficulty after 2 wrong answers in a row
                if new_wrong_streak >= 2 and new_difficulty_level > 1:
                    new_difficulty_level -= 1
                    new_wrong_streak = 0
            
            # Handle article completion
            completed_articles = current_progress.get("completed_articles", [])
            if article_id and article_id not in completed_articles:
                completed_articles.append(article_id)
                # Award extra diamond for completing article
                new_diamonds += 1
            
            # Update database
            cursor.execute('''
                UPDATE kid_progress SET 
                    total_score = ?, questions_answered = ?, stars = ?, diamonds = ?,
                    level = ?, level_progress = ?, difficulty_level = ?, correct_streak = ?, wrong_streak = ?,
                    completed_articles = ?, last_activity = ?
                WHERE kid_id = ?
            ''', (
                new_total_score,
                new_questions_answered,
                new_stars,
                new_diamonds,
                new_level,
                new_level_progress,
                new_difficulty_level,
                new_correct_streak,
                new_wrong_streak,
                json.dumps(completed_articles),
                str(datetime.now()),
                kid_id
            ))
            
            conn.commit()
            conn.close()
            
            print(f"DEBUG: Updated progress for {kid_id}: score={new_total_score}, difficulty={new_difficulty_level}, completed_articles={len(completed_articles)}")
            
        except Exception as e:
            print(f"Update kid progress error: {e}")
    
    def get_difficulty_level(self, kid_id: str) -> int:
        """Get current difficulty level for a kid"""
        progress = self.get_kid_progress(kid_id)
        return progress.get('difficulty_level', 1)
    
    def mark_article_completed(self, kid_id: str, article_id: str):
        """Mark an article as completed for a kid"""
        progress = self.get_kid_progress(kid_id)
        completed_articles = progress.get('completed_articles', [])
        
        if article_id not in completed_articles:
            completed_articles.append(article_id)
            self.update_kid_progress(kid_id, completed_articles=completed_articles)
    
    def is_article_completed(self, kid_id: str, article_id: str) -> bool:
        """Check if an article is completed by a kid"""
        progress = self.get_kid_progress(kid_id)
        completed_articles = progress.get('completed_articles', [])
        return article_id in completed_articles
    
    def get_completed_articles(self, kid_id: str) -> List[str]:
        """Get list of completed articles for a kid"""
        progress = self.get_kid_progress(kid_id)
        return progress.get('completed_articles', [])
