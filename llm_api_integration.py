#!/usr/bin/env python3
"""
LLM API Integration for Knowledge R Us
Provides actual LLM API calls to replace simulated responses
"""

import json
import requests
from typing import Dict, Optional
import streamlit as st

class LLMAPIClient:
    """Client for making LLM API calls"""
    
    def __init__(self):
        # Configuration for different LLM providers
        self.providers = {
            "openai": {
                "api_url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-3.5-turbo",
                "headers": lambda api_key: {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            },
            "anthropic": {
                "api_url": "https://api.anthropic.com/v1/messages",
                "model": "claude-3-haiku-20240307",
                "headers": lambda api_key: {
                    "x-api-key": api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
            },
            "local": {
                "api_url": "http://localhost:11434/api/generate",  # Ollama default
                "model": "llama2:7b",
                "headers": lambda api_key: {
                    "Content-Type": "application/json"
                }
            }
        }
        
        # Default to local LLM for privacy and cost
        self.current_provider = "local"
        self.api_key = None
    
    def set_provider(self, provider: str, api_key: Optional[str] = None):
        """Set the LLM provider and API key"""
        if provider in self.providers:
            self.current_provider = provider
            self.api_key = api_key
            return True
        return False
    
    def generate_question(self, prompt: str) -> Optional[Dict]:
        """Generate a question using the configured LLM provider"""
        
        provider_config = self.providers[self.current_provider]
        
        try:
            if self.current_provider == "openai":
                return self._call_openai(prompt, provider_config)
            elif self.current_provider == "anthropic":
                return self._call_anthropic(prompt, provider_config)
            elif self.current_provider == "local":
                return self._call_local_llm(prompt, provider_config)
        except Exception as e:
            print(f"LLM API Error: {e}")
            return None
    
    def _call_openai(self, prompt: str, config: Dict) -> Optional[Dict]:
        """Call OpenAI API"""
        if not self.api_key:
            print("OpenAI API key required")
            return None
            
        payload = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": "You are a helpful teacher creating educational questions."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        headers = config["headers"](self.api_key)
        response = requests.post(config["api_url"], json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return self._parse_json_response(content)
        else:
            print(f"OpenAI API error: {response.status_code}")
            return None
    
    def _call_anthropic(self, prompt: str, config: Dict) -> Optional[Dict]:
        """Call Anthropic Claude API"""
        if not self.api_key:
            print("Anthropic API key required")
            return None
            
        payload = {
            "model": config["model"],
            "max_tokens": 500,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        headers = config["headers"](self.api_key)
        response = requests.post(config["api_url"], json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            content = result["content"][0]["text"]
            return self._parse_json_response(content)
        else:
            print(f"Anthropic API error: {response.status_code}")
            return None
    
    def _call_local_llm(self, prompt: str, config: Dict) -> Optional[Dict]:
        """Call local LLM (Ollama)"""
        payload = {
            "model": config["model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500
            }
        }
        
        headers = config["headers"](None)
        
        try:
            response = requests.post(config["api_url"], json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                return self._parse_json_response(content)
            else:
                print(f"Local LLM error: {response.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            print("Local LLM not available - install Ollama and run 'ollama serve'")
            return None
        except requests.exceptions.Timeout:
            print("Local LLM timeout - response took too long")
            return None
    
    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse JSON response from LLM"""
        try:
            # Try to find JSON in the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
            else:
                print("No JSON found in LLM response")
                return None
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw content: {content}")
            return None

# Global LLM client instance
llm_client = LLMAPIClient()

def setup_llm_provider():
    """Setup LLM provider in Streamlit sidebar"""
    with st.sidebar:
        st.header("🤖 LLM Settings")
        
        provider = st.selectbox(
            "LLM Provider",
            ["local", "openai", "anthropic"],
            help="Local requires Ollama installed"
        )
        
        api_key = None
        if provider != "local":
            api_key = st.text_input(
                f"{provider.title()} API Key",
                type="password",
                help=f"Enter your {provider.title()} API key"
            )
        
        if st.button("Update LLM Settings"):
            if llm_client.set_provider(provider, api_key):
                st.success(f"LLM provider set to {provider}")
            else:
                st.error("Invalid provider configuration")
        
        # Show current status
        st.info(f"Current: {llm_client.current_provider}")
        
        if provider == "local":
            st.caption("Make sure Ollama is running: `ollama serve`")
