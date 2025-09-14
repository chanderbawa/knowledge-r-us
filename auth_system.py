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
        self.users_file = "users_data.json"
        self.profiles_file = "kid_profiles.json"
        self.progress_file = "user_progress.json"
        
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
    
    def update_kid_progress(self, kid_id: str, score_increment: int = 0, questions_increment: int = 0, articles_increment: int = 0):
        """Update kid's progress"""
        progress_data = self._load_json(self.progress_file)
        
        if kid_id not in progress_data:
            progress_data[kid_id] = {
                "total_score": 0,
                "questions_answered": 0,
                "articles_read": 0,
                "achievements": [],
                "last_activity": str(datetime.now()),
                "daily_progress": {}
            }
        
        progress = progress_data[kid_id]
        progress["total_score"] += score_increment
        progress["questions_answered"] += questions_increment
        progress["articles_read"] += articles_increment
        progress["last_activity"] = str(datetime.now())
        
        # Track daily progress
        today = str(date.today())
        if today not in progress["daily_progress"]:
            progress["daily_progress"][today] = {"score": 0, "questions": 0, "articles": 0}
        
        progress["daily_progress"][today]["score"] += score_increment
        progress["daily_progress"][today]["questions"] += questions_increment
        progress["daily_progress"][today]["articles"] += articles_increment
        
        # Check for new achievements
        self._check_achievements(progress)
        
        self._save_json(self.progress_file, progress_data)
    
    def _check_achievements(self, progress: Dict):
        """Check and award achievements"""
        achievements = progress.get("achievements", [])
        
        # Define achievement thresholds
        achievement_checks = [
            ("first_question", "🔰 First Question!", progress["questions_answered"] >= 1),
            ("star_learner", "⭐ Star Learner!", progress["total_score"] >= 50),
            ("knowledge_seeker", "🧠 Knowledge Seeker!", progress["questions_answered"] >= 5),
            ("news_expert", "🚀 News Expert!", progress["total_score"] >= 100),
            ("daily_reader", "📚 Daily Reader!", progress["articles_read"] >= 10),
            ("math_whiz", "🔢 Math Whiz!", progress["questions_answered"] >= 20),
            ("science_explorer", "🔬 Science Explorer!", progress["total_score"] >= 200)
        ]
        
        for achievement_id, achievement_name, condition in achievement_checks:
            if condition and achievement_id not in [a["id"] for a in achievements]:
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

def show_kid_dashboard(profile_manager: UserProfileManager):
    """Display dashboard for selected kid"""
    kid = st.session_state.selected_kid
    progress = st.session_state.kid_progress
    
    # Header with kid info and switch profile option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"{kid['avatar']} {kid['name']}'s Learning Journey")
        st.caption(f"Age {kid['age']} • {kid['age_group']} years")
    
    with col2:
        if st.button("🔄 Switch Profile"):
            del st.session_state.selected_kid
            del st.session_state.kid_progress
            st.rerun()
    
    # Progress overview
    st.header("📊 Progress Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Score", progress.get('total_score', 0))
    with col2:
        st.metric("Questions Answered", progress.get('questions_answered', 0))
    with col3:
        st.metric("Articles Read", progress.get('articles_read', 0))
    with col4:
        achievements = progress.get('achievements', [])
        st.metric("Achievements", len(achievements))
    
    # Achievements
    if achievements:
        st.header("🏆 Achievements")
        achievement_cols = st.columns(min(len(achievements), 4))
        for i, achievement in enumerate(achievements):
            with achievement_cols[i % 4]:
                st.success(achievement['name'])
    
    # Ready to learn button
    st.header("🚀 Ready to Learn?")
    if st.button("Start Learning!", type="primary"):
        st.session_state.learning_mode = True
        st.rerun()
