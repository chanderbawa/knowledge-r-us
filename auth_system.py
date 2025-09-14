#!/usr/bin/env python3
"""
Authentication and User Profile Management for Knowledge R Us
Handles parent accounts, kid profiles, and session management
"""

import streamlit as st
import streamlit_authenticator as stauth
import bcrypt
import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
import pandas as pd

class UserProfileManager:
    """Manages user authentication and kid profiles"""
    
    def __init__(self):
        # Use absolute paths to ensure data persistence
        import os
        self.data_dir = os.path.dirname(os.path.abspath(__file__))
        self.users_file = os.path.join(self.data_dir, "users_data.json")
        self.profiles_file = os.path.join(self.data_dir, "kid_profiles.json")
        self.progress_file = os.path.join(self.data_dir, "user_progress.json")
        
        # Initialize data files if they don't exist
        self._initialize_data_files()
    
    def _initialize_data_files(self):
        """Initialize JSON data files if they don't exist"""
        if not os.path.exists(self.users_file):
            initial_users = {
                "usernames": {
                    "demo_parent": {
                        "email": "demo@example.com",
                        "name": "Demo Parent",
                        "password": self._hash_password("demo123"),
                        "created_date": str(datetime.now())
                    }
                }
            }
            self._save_json(self.users_file, initial_users)
        
        if not os.path.exists(self.profiles_file):
            initial_profiles = {
                "demo_parent": [
                    {
                        "kid_id": "demo_kid_1",
                        "name": "Alex",
                        "age": 10,
                        "age_group": "9-11",
                        "interests": ["science", "technology"],
                        "created_date": str(datetime.now()),
                        "avatar": "🧑‍🚀"
                    }
                ]
            }
            self._save_json(self.profiles_file, initial_profiles)
        
        if not os.path.exists(self.progress_file):
            initial_progress = {
                "demo_kid_1": {
                    "total_score": 0,
                    "questions_answered": 0,
                    "articles_read": 0,
                    "achievements": [],
                    "last_activity": str(datetime.now())
                }
            }
            self._save_json(self.progress_file, initial_progress)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def _load_json(self, filename: str) -> Dict:
        """Load JSON data from file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, filename: str, data: Dict):
        """Save data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_parent(self, username: str, email: str, name: str, password: str) -> bool:
        """Register a new parent account"""
        users_data = self._load_json(self.users_file)
        
        if username in users_data.get("usernames", {}):
            return False  # Username already exists
        
        if "usernames" not in users_data:
            users_data["usernames"] = {}
        
        users_data["usernames"][username] = {
            "email": email,
            "name": name,
            "password": self._hash_password(password),
            "created_date": str(datetime.now())
        }
        
        self._save_json(self.users_file, users_data)
        
        # Initialize empty profiles for new parent
        profiles_data = self._load_json(self.profiles_file)
        profiles_data[username] = []
        self._save_json(self.profiles_file, profiles_data)
        
        return True
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user login"""
        users_data = self._load_json(self.users_file)
        
        if username not in users_data.get("usernames", {}):
            return False
        
        stored_hash = users_data["usernames"][username]["password"]
        return self._verify_password(password, stored_hash)
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information"""
        users_data = self._load_json(self.users_file)
        return users_data.get("usernames", {}).get(username)
    
    def create_kid_profile(self, parent_username: str, name: str, age: int, interests: List[str], avatar: str = "👶") -> str:
        """Create a new kid profile"""
        profiles_data = self._load_json(self.profiles_file)
        
        if parent_username not in profiles_data:
            profiles_data[parent_username] = []
        
        # Generate unique kid ID
        kid_id = f"{parent_username}_{name.lower().replace(' ', '_')}_{len(profiles_data[parent_username])}"
        
        # Determine age group
        if age <= 8:
            age_group = "6-8"
        elif age <= 11:
            age_group = "9-11"
        elif age <= 14:
            age_group = "12-14"
        else:
            age_group = "15-17"
        
        new_profile = {
            "kid_id": kid_id,
            "name": name,
            "age": age,
            "age_group": age_group,
            "interests": interests,
            "created_date": str(datetime.now()),
            "avatar": avatar
        }
        
        profiles_data[parent_username].append(new_profile)
        self._save_json(self.profiles_file, profiles_data)
        
        # Initialize progress for new kid
        progress_data = self._load_json(self.progress_file)
        progress_data[kid_id] = {
            "total_score": 0,
            "questions_answered": 0,
            "articles_read": 0,
            "achievements": [],
            "last_activity": str(datetime.now()),
            "daily_progress": {}
        }
        self._save_json(self.progress_file, progress_data)
        
        return kid_id
    
    def get_kid_profiles(self, parent_username: str) -> List[Dict]:
        """Get all kid profiles for a parent"""
        profiles_data = self._load_json(self.profiles_file)
        return profiles_data.get(parent_username, [])
    
    def get_kid_progress(self, kid_id: str) -> Dict:
        """Get progress data for a kid"""
        progress_data = self._load_json(self.progress_file)
        return progress_data.get(kid_id, {})
    
    def update_kid_progress(self, kid_id: str, score_increment: int = 0, questions_increment: int = 0, article_id: str = None):
        """Update progress for a specific kid"""
        progress = self.load_user_progress()
        
        if kid_id not in progress:
            progress[kid_id] = {
                'total_score': 0,
                'questions_answered': 0,
                'achievements': [],
                'daily_streak': 0,
                'last_activity': None,
                'stars': 0,
                'diamonds': 0,
                'level': 1,
                'level_progress': 0,
                'completed_articles': [],
                'current_article_questions': {},
                'difficulty_level': 1,  # 1=Easy, 2=Medium, 3=Hard
                'correct_streak': 0,
                'wrong_streak': 0
            }
        
        # Update scores and questions
        progress[kid_id]['total_score'] += score_increment
        progress[kid_id]['questions_answered'] += questions_increment
        progress[kid_id]['last_activity'] = datetime.now().isoformat()
        
        # Track article completion if provided
        if article_id:
            # Ensure completed_articles and current_article_questions exist
            if 'completed_articles' not in progress[kid_id]:
                progress[kid_id]['completed_articles'] = []
            if 'current_article_questions' not in progress[kid_id]:
                progress[kid_id]['current_article_questions'] = {}
                
            # Mark article as completed if all questions answered
            if article_id not in progress[kid_id]['completed_articles']:
                progress[kid_id]['completed_articles'].append(article_id)
        
        # Update difficulty based on performance
        self._update_difficulty(progress[kid_id], score_increment > 0)
        
        # Award stars and diamonds based on performance
        self._award_recognition(progress[kid_id], score_increment, questions_increment)
        
        # Check for new achievements
        self._check_achievements(progress[kid_id])
        
        self.save_user_progress(progress)
    
    def _award_recognition(self, progress: Dict, score_increment: int, questions_increment: int):
        """Award stars and diamonds based on performance"""
        # Award stars for correct answers (10 points)
        if score_increment == 10:
            progress['stars'] += 1
            
        # Award diamonds for exceptional performance
        # Diamond for getting 3 questions right in a row
        if progress['total_score'] > 0 and progress['total_score'] % 30 == 0:
            progress['diamonds'] += 1
            
        # Level progression based on total score
        old_level = progress['level']
        new_level = min(10, (progress['total_score'] // 100) + 1)
        progress['level'] = new_level
        
        # Calculate level progress (0-100%)
        score_in_level = progress['total_score'] % 100
        progress['level_progress'] = score_in_level
        
        # Award bonus diamond for leveling up
        if new_level > old_level:
            progress['diamonds'] += 1
    
    def _update_difficulty(self, progress: Dict, is_correct: bool):
        """Update difficulty level based on performance"""
        # Ensure difficulty tracking fields exist
        if 'difficulty_level' not in progress:
            progress['difficulty_level'] = 1
        if 'correct_streak' not in progress:
            progress['correct_streak'] = 0
        if 'wrong_streak' not in progress:
            progress['wrong_streak'] = 0
            
        if is_correct:
            progress['correct_streak'] += 1
            progress['wrong_streak'] = 0
            
            # Increase difficulty after 3 correct answers in a row
            if progress['correct_streak'] >= 3 and progress['difficulty_level'] < 3:
                progress['difficulty_level'] += 1
                progress['correct_streak'] = 0
        else:
            progress['wrong_streak'] += 1
            progress['correct_streak'] = 0
            
            # Decrease difficulty after 2 wrong answers in a row
            if progress['wrong_streak'] >= 2 and progress['difficulty_level'] > 1:
                progress['difficulty_level'] -= 1
                progress['wrong_streak'] = 0
    
    def get_difficulty_level(self, kid_id: str) -> int:
        """Get current difficulty level for a kid"""
        progress = self.load_user_progress()
        if kid_id not in progress:
            return 1
        return progress[kid_id].get('difficulty_level', 1)
    
    def mark_article_completed(self, kid_id: str, article_id: str):
        """Mark an article as completed for a kid"""
        progress = self.load_user_progress()
        
        if kid_id not in progress:
            return
            
        if 'completed_articles' not in progress[kid_id]:
            progress[kid_id]['completed_articles'] = []
            
        if article_id not in progress[kid_id]['completed_articles']:
            progress[kid_id]['completed_articles'].append(article_id)
            
        self.save_user_progress(progress)
    
    def is_article_completed(self, kid_id: str, article_id: str) -> bool:
        """Check if an article is completed by a kid"""
        progress = self.load_user_progress()
        
        if kid_id not in progress:
            return False
            
        completed_articles = progress[kid_id].get('completed_articles', [])
        return article_id in completed_articles
    
    def get_completed_articles(self, kid_id: str) -> List[str]:
        """Get list of completed articles for a kid"""
        progress = self.load_user_progress()
        
        if kid_id not in progress:
            return []
            
        return progress[kid_id].get('completed_articles', [])
    
    def _check_achievements(self, progress: Dict):
        """Check and award achievements"""
        achievements = progress.get("achievements", [])
        
        # Define achievement thresholds
        completed_articles_count = len(progress.get('completed_articles', []))
        achievement_checks = [
            ("first_question", "🔰 First Question!", progress["questions_answered"] >= 1),
            ("first_article", "📰 First Article Complete!", completed_articles_count >= 1),
            ("star_learner", "⭐ Star Learner!", progress["total_score"] >= 50),
            ("knowledge_seeker", "🧠 Knowledge Seeker!", progress["questions_answered"] >= 5),
            ("news_expert", "🚀 News Expert!", progress["total_score"] >= 100),
            ("daily_reader", "📚 Daily Reader!", completed_articles_count >= 5),
            ("math_whiz", "🔢 Math Whiz!", progress["questions_answered"] >= 20),
            ("science_explorer", "🔬 Science Explorer!", progress["total_score"] >= 200),
            ("news_master", "🏆 News Master!", completed_articles_count >= 10)
        ]
        
        for achievement_id, achievement_name, condition in achievement_checks:
            if condition and achievement_id not in [a.get("id") for a in achievements]:
                achievements.append({
                    "id": achievement_id,
                    "name": achievement_name,
                    "earned_date": str(datetime.now())
                })
        
        progress["achievements"] = achievements
    
    def delete_kid_profile(self, parent_username: str, kid_id: str):
        """Delete a kid profile"""
        profiles_data = self._load_json(self.profiles_file)
        
        if parent_username in profiles_data:
            profiles_data[parent_username] = [
                profile for profile in profiles_data[parent_username] 
                if profile["kid_id"] != kid_id
            ]
            self._save_json(self.profiles_file, profiles_data)
        
        # Also delete progress data
        progress_data = self._load_json(self.progress_file)
        if kid_id in progress_data:
            del progress_data[kid_id]
            self._save_json(self.progress_file, progress_data)

def show_login_page(profile_manager: UserProfileManager):
    """Display login/registration page"""
    st.title("🌟 Welcome to Knowledge R Us")
    st.subheader("Educational News for Kids")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.header("Parent Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if profile_manager.authenticate_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_info = profile_manager.get_user_info(username)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        st.header("Register New Parent Account")
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            email = st.text_input("Email Address")
            name = st.text_input("Your Name")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_button = st.form_submit_button("Register")
            
            if register_button:
                if not all([new_username, email, name, new_password]):
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    if profile_manager.register_parent(new_username, email, name, new_password):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Username already exists")

def show_profile_selection(profile_manager: UserProfileManager):
    """Display kid profile selection and management"""
    st.title(f"👋 Welcome, {st.session_state.user_info['name']}!")
    
    # Get kid profiles
    kid_profiles = profile_manager.get_kid_profiles(st.session_state.username)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Select a Kid Profile")
        
        if kid_profiles:
            for profile in kid_profiles:
                with st.container():
                    profile_col1, profile_col2, profile_col3 = st.columns([1, 3, 1])
                    
                    with profile_col1:
                        st.write(f"{profile['avatar']}")
                    
                    with profile_col2:
                        st.write(f"**{profile['name']}** (Age {profile['age']})")
                        progress = profile_manager.get_kid_progress(profile['kid_id'])
                        st.caption(f"Score: {progress.get('total_score', 0)} | Questions: {progress.get('questions_answered', 0)}")
                    
                    with profile_col3:
                        if st.button("Select", key=f"select_{profile['kid_id']}"):
                            st.session_state.selected_kid = profile
                            st.session_state.kid_progress = progress
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("No kid profiles yet. Create one to get started!")
    
    with col2:
        st.header("Manage Profiles")
        
        # Add new kid profile
        with st.expander("➕ Add New Kid"):
            with st.form("new_kid_form"):
                kid_name = st.text_input("Kid's Name")
                kid_age = st.number_input("Age", min_value=6, max_value=17, value=10)
                interests = st.multiselect(
                    "Interests",
                    ["science", "technology", "environment", "space", "animals", "math"],
                    default=["science"]
                )
                avatar = st.selectbox("Avatar", ["👶", "🧒", "👧", "🧑‍🚀", "🧑‍🔬", "🧑‍💻", "🧑‍🎓"])
                
                if st.form_submit_button("Create Profile"):
                    if kid_name:
                        kid_id = profile_manager.create_kid_profile(
                            st.session_state.username, kid_name, kid_age, interests, avatar
                        )
                        st.success(f"Profile created for {kid_name}!")
                        st.rerun()
                    else:
                        st.error("Please enter a name")
        
        # Logout button
        if st.button("🚪 Logout"):
            for key in ['authenticated', 'username', 'user_info', 'selected_kid', 'kid_progress']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

def show_kid_dashboard(profile_manager: UserProfileManager, selected_kid: Dict):
    """Display kid dashboard with progress and achievements"""
    st.title(f"🌟 Welcome back, {selected_kid['name']}!")
    
    # Get kid's progress
    progress = profile_manager.get_kid_progress(selected_kid['kid_id'])
    
    # Display recognition metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Total Score", progress.get('total_score', 0))
    
    with col2:
        st.metric("⭐ Stars Earned", progress.get('stars', 0))
    
    with col3:
        st.metric("💎 Diamonds", progress.get('diamonds', 0))
    
    with col4:
        difficulty_level = progress.get('difficulty_level', 1)
        difficulty_names = {1: "Easy", 2: "Medium", 3: "Hard"}
        st.metric("🎯 Difficulty", f"{difficulty_names[difficulty_level]} ({difficulty_level})")
    
    with col5:
        st.metric("❓ Questions", progress.get('questions_answered', 0))
    
    # Level progress bar
    st.subheader(f"🎯 Level {progress.get('level', 1)} Progress")
    level_progress = progress.get('level_progress', 0)
    progress_bar = st.progress(level_progress / 100.0)
    st.write(f"Progress: {level_progress}/100 points to next level")
    
    # Recognition display
    st.subheader("🌟 Your Recognition")
    
    # Create visual display of stars and diamonds
    stars = progress.get('stars', 0)
    diamonds = progress.get('diamonds', 0)
    
    col_stars, col_diamonds = st.columns(2)
    
    with col_stars:
        st.write("**⭐ Stars Collected:**")
        if stars > 0:
            # Display stars in rows of 10
            star_display = ""
            for i in range(min(stars, 50)):  # Limit display to 50 stars
                star_display += "⭐"
                if (i + 1) % 10 == 0:
                    star_display += "\n"
            st.text(star_display)
            if stars > 50:
                st.write(f"... and {stars - 50} more stars!")
        else:
            st.write("Answer questions correctly to earn stars!")
    
    with col_diamonds:
        st.write("**💎 Diamonds Earned:**")
        if diamonds > 0:
            diamond_display = "💎 " * min(diamonds, 20)  # Limit display to 20 diamonds
            st.text(diamond_display)
            if diamonds > 20:
                st.write(f"... and {diamonds - 20} more diamonds!")
        else:
            st.write("Get 3 correct answers in a row or level up to earn diamonds!")
    
    # Show achievements
    achievements = progress.get('achievements', [])
    if achievements:
        st.subheader("🏆 Your Achievements")
        for achievement in achievements[-3:]:  # Show last 3 achievements
            st.success(f"{achievement['name']} - Earned on {achievement['earned_date'][:10]}")
    
    # Daily quest progress
    st.subheader("📅 Today's Quest")
    daily_goal = 3  # Questions per day
    questions_today = progress.get('questions_answered', 0) % daily_goal
    
    progress_bar = st.progress(min(questions_today / daily_goal, 1.0))
    st.write(f"Progress: {questions_today}/{daily_goal} questions answered today")
    
    if questions_today >= daily_goal:
        st.success("🎉 Daily quest completed! Great job!")
    else:
        st.info(f"Keep going! {daily_goal - questions_today} more questions to complete today's quest.")
    
    # Recognition tips
    with st.expander("🎯 How to Earn More Recognition"):
        st.write("""
        **⭐ Stars:** Earn 1 star for each correct answer!
        
        **💎 Diamonds:** 
        - Get 3 correct answers in a row (every 30 points)
        - Level up to the next level
        
        **🎯 Levels:** 
        - Level 1: 0-99 points
        - Level 2: 100-199 points  
        - Level 3: 200-299 points
        - ... and so on up to Level 10!
        
        Keep learning to collect more stars and diamonds! 🌟
        """)
    
    # Start learning button
    if st.button("🚀 Start Learning!", type="primary", use_container_width=True):
        st.session_state.learning_mode = True
        st.rerun()
