#!/usr/bin/env python3
"""
LLM-powered Question Generator for Knowledge R Us
Uses local LLM with RAG to generate contextually relevant questions from news articles
"""

import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import streamlit as st

class LLMQuestionGenerator:
    """Generate intelligent, contextually relevant questions using LLM+RAG"""
    
    def __init__(self):
        self.difficulty_levels = {
            1: "Easy",
            2: "Medium", 
            3: "Hard"
        }
        
        # Age-specific teacher personas for question generation
        self.teacher_personas = {
            "6-8": {
                "grade_level": "Elementary (Grades 1-3)",
                "persona": "You are a friendly elementary school teacher for grades 1-3 (ages 6-8). You explain things simply using everyday words that young children understand. You make learning fun and engaging.",
                "math_style": "Use simple addition, subtraction, counting, and basic concepts. Numbers should be small (under 50). Use concrete examples kids can visualize.",
                "science_style": "Focus on basic observations, simple cause-and-effect, and things kids can see in their daily life. Use simple vocabulary.",
                "ela_style": "Focus on basic vocabulary, simple sentence structure, and main ideas. Use words kids know and can relate to their experiences."
            },
            "9-11": {
                "grade_level": "Elementary (Grades 4-6)",
                "persona": "You are an experienced elementary school teacher for grades 4-6 (ages 9-11). You challenge students with more complex concepts while keeping explanations clear and engaging.",
                "math_style": "Use multiplication, division, fractions, percentages, and word problems. Numbers can be larger. Include real-world applications.",
                "science_style": "Introduce scientific method, more complex processes, and technical vocabulary with explanations. Connect to real scientific discoveries.",
                "ela_style": "Focus on vocabulary building, reading comprehension, context clues, and more complex sentence structures. Introduce academic vocabulary."
            },
            "12-14": {
                "grade_level": "Middle School (Grades 7-8)",
                "persona": "You are a middle school teacher for grades 7-8 (ages 12-14). You challenge students with pre-algebra, advanced science concepts, and critical thinking while maintaining engagement.",
                "math_style": "Use pre-algebra, ratios, proportions, basic geometry, data analysis, and multi-step word problems. Include statistical concepts and graphing.",
                "science_style": "Cover scientific method, hypothesis testing, more complex biological and physical processes, chemistry basics, and environmental science. Use proper scientific terminology.",
                "ela_style": "Focus on advanced vocabulary, literary analysis, argument structure, research skills, and academic writing. Introduce rhetorical devices and text analysis."
            },
            "15-18": {
                "grade_level": "High School (Grades 9-12)",
                "persona": "You are a high school teacher for grades 9-12 (ages 15-18). You prepare students for college-level thinking with advanced concepts, critical analysis, and real-world applications.",
                "math_style": "Use algebra, geometry, trigonometry, statistics, calculus concepts, and complex problem-solving. Include advanced mathematical reasoning and proofs.",
                "science_style": "Cover advanced biology, chemistry, physics, environmental science, and current research. Use college-level terminology and connect to current scientific debates and discoveries.",
                "ela_style": "Focus on advanced literary analysis, rhetorical analysis, research methodology, academic writing, and critical thinking. Include analysis of bias, perspective, and argumentation."
            }
        }
        
    def generate_questions(self, article: Dict, age_group: str, difficulty_level: int = 1) -> List[Dict]:
        """Generate contextually relevant questions using LLM prompts"""
        questions = []
        
        # Extract key information from article
        article_context = self._extract_article_context(article)
        
        # Get teacher persona for this age group (default to 9-11 if not found)
        persona = self.teacher_personas.get(age_group, self.teacher_personas["9-11"])
        
        # Generate different types of questions using LLM prompts
        subjects = ["math", "science", "ela"]
        for subject in subjects:
            question = self._generate_llm_question(article_context, age_group, subject, difficulty_level, persona)
            if question:
                questions.append(question)
            
        return questions
    
    def _extract_article_context(self, article: Dict) -> Dict:
        """Extract key context from article for question generation"""
        title = article.get("title", "")
        content = article.get("content", "")
        category = article.get("category", "science")
        
        # Extract numbers, measurements, and key facts
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', content)
        measurements = re.findall(r'\b\d+(?:\.\d+)?\s*(?:kg|lb|meter|mile|km|inch|foot|feet|cm|mm|gram|ton|percent|%|degree|celsius|fahrenheit)\b', content, re.IGNORECASE)
        
        # Extract key scientific/technical concepts
        key_concepts = []
        concept_patterns = [
            r'\b(planet|star|galaxy|telescope|space|astronaut|rocket|satellite)\b',
            r'\b(robot|AI|artificial intelligence|machine learning|algorithm|computer)\b',
            r'\b(climate|environment|carbon|greenhouse|pollution|renewable|solar|wind)\b',
            r'\b(medicine|drug|treatment|patient|doctor|hospital|health|disease|vaccine)\b',
            r'\b(research|study|scientist|experiment|data|analysis|discovery|breakthrough)\b'
        ]
        
        for pattern in concept_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            key_concepts.extend([match.lower() for match in matches])
        
        return {
            "title": title,
            "content": content,
            "category": category,
            "numbers": numbers,
            "measurements": measurements,
            "key_concepts": key_concepts,
            "word_count": len(content.split())
        }
    
    def _generate_llm_question(self, context: Dict, age_group: str, subject: str, difficulty_level: int, persona: Dict) -> Dict:
        """Generate a question using LLM prompts with teacher persona"""
        
        title = context["title"]
        content = context["content"][:500]  # Truncate for prompt
        numbers = context["numbers"][:3]    # First 3 numbers
        
        # Create subject-specific prompt
        subject_style = persona.get(f"{subject}_style", "")
        base_persona = persona.get("persona", "")
        
        prompt = f"""
{base_persona}

Article Title: "{title}"
Article Content: {content}
Available Numbers: {numbers}
Difficulty Level: {self.difficulty_levels[difficulty_level]}

{subject_style}

Generate ONE {subject.upper()} question based on this article. The question should:
1. Be directly related to the article content
2. Be appropriate for ages {age_group}
3. Have 4 multiple choice options
4. Include the correct answer
5. Provide a helpful hint
6. Include an explanation of why the answer is correct

Return ONLY a JSON object with this exact structure:
{{
    "type": "{subject}",
    "question": "Your question here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": "The correct option",
    "hint": "A helpful hint",
    "explanation": "Why this answer is correct",
    "reasoning": "Educational reasoning behind the concept",
    "wrong_explanation": "What to look for in the article if wrong"
}}
"""
        
        # Simulate LLM response (in production, replace with actual LLM call)
        return self._simulate_llm_response(prompt, context, age_group, subject, difficulty_level)
    
    def _simulate_llm_response(self, prompt: str, context: Dict, age_group: str, subject: str, difficulty_level: int) -> Dict:
        """Simulate LLM response - replace with actual LLM API call in production"""
        
        # Try to use actual LLM API if available
        try:
            from llm_api_integration import llm_client
            
            # Attempt to generate using LLM
            llm_response = llm_client.generate_question(prompt)
            if llm_response and self._validate_question_format(llm_response):
                print(f"Generated {subject} question using LLM API")
                return llm_response
        except ImportError:
            print("LLM API integration not available")
        except Exception as e:
            print(f"LLM API failed: {e}")
        
        # Fall back to simple contextual generation
        print(f"Using simplified fallback for {subject} question")
        return self._generate_simple_fallback(context, age_group, subject, difficulty_level)
    
    def _validate_question_format(self, question: Dict) -> bool:
        """Validate that LLM response has correct format"""
        required_fields = ["type", "question", "options", "correct", "hint", "explanation"]
        
        if not isinstance(question, dict):
            return False
        
        for field in required_fields:
            if field not in question:
                return False
        
        # Validate options is a list with 4 items
        if not isinstance(question["options"], list) or len(question["options"]) != 4:
            return False
        
        # Validate correct answer is in options
        if question["correct"] not in question["options"]:
            return False
        
        return True
    
    def _generate_simple_fallback(self, context: Dict, age_group: str, subject: str, difficulty_level: int) -> Dict:
        """Generate simple fallback questions when LLM is unavailable"""
        title = context["title"]
        numbers = context["numbers"][:3] if context["numbers"] else []
        
        # Age-appropriate complexity
        if age_group in ["6-8"]:
            complexity = "simple"
        elif age_group in ["9-11"]:
            complexity = "intermediate"
        elif age_group in ["12-14"]:
            complexity = "advanced"
        else:  # 15-18
            complexity = "college_prep"
        
        if subject == "math":
            return self._generate_fallback_math(title, numbers, complexity)
        elif subject == "science":
            return self._generate_fallback_science(title, complexity)
        elif subject == "ela":
            return self._generate_fallback_ela(title, complexity)
        
        return None
    
    def _generate_fallback_math(self, title: str, numbers: List[str], complexity: str) -> Dict:
        """Generate math fallback based on complexity level"""
        if numbers:
            num = int(float(numbers[0])) if numbers[0].replace('.','').isdigit() else 10
            
            if complexity == "simple":
                return {
                    "type": "math",
                    "question": f"The article mentions {num}. What is {num} + 5?",
                    "options": [str(num+3), str(num+4), str(num+5), str(num+6)],
                    "correct": str(num+5),
                    "hint": f"Add 5 to {num}",
                    "explanation": f"{num} + 5 = {num+5}",
                    "reasoning": "Addition helps us find totals.",
                    "wrong_explanation": f"Count up from {num}: add 5 more."
                }
            elif complexity == "intermediate":
                return {
                    "type": "math",
                    "question": f"If the article mentions {num}%, what fraction is this?",
                    "options": [f"{num}/50", f"{num}/100", f"{num}/200", f"{num}/10"],
                    "correct": f"{num}/100",
                    "hint": "Percent means 'out of 100'",
                    "explanation": f"{num}% = {num}/100",
                    "reasoning": "Percentages are fractions with denominator 100.",
                    "wrong_explanation": "Percent (%) means 'per hundred' or 'out of 100'."
                }
            elif complexity == "advanced":
                ratio = round(num * 1.5, 1)
                return {
                    "type": "math",
                    "question": f"If {num} increases by 50%, what is the new value?",
                    "options": [str(num), str(ratio-0.5), str(ratio), str(ratio+0.5)],
                    "correct": str(ratio),
                    "hint": "50% increase means multiply by 1.5",
                    "explanation": f"{num} × 1.5 = {ratio}",
                    "reasoning": "Percentage increase: original × (1 + rate)",
                    "wrong_explanation": f"50% of {num} is {num*0.5}, so add that to {num}."
                }
            else:  # college_prep
                return {
                    "type": "math",
                    "question": f"What is the statistical significance of the {num}% mentioned in the study?",
                    "options": ["It's always significant", "Depends on sample size and p-value", "Only if >50%", "Not determinable"],
                    "correct": "Depends on sample size and p-value",
                    "hint": "Statistical significance requires more than just the percentage",
                    "explanation": "Statistical significance depends on sample size, p-value, and confidence intervals.",
                    "reasoning": "Understanding statistical concepts is crucial for interpreting research data.",
                    "wrong_explanation": "Look for information about study methodology and statistical analysis."
                }
        
        # Default if no numbers
        if complexity == "simple":
            return {
                "type": "math",
                "question": "What is 7 + 8?",
                "options": ["14", "15", "16", "17"],
                "correct": "15",
                "hint": "Count up from 7",
                "explanation": "7 + 8 = 15",
                "reasoning": "Addition combines numbers.",
                "wrong_explanation": "Try counting on your fingers."
            }
        else:
            return {
                "type": "math",
                "question": "What is 15% of 200?",
                "options": ["25", "30", "35", "40"],
                "correct": "30",
                "hint": "15% = 15/100 = 0.15",
                "explanation": "200 × 0.15 = 30",
                "reasoning": "To find percentage: multiply by decimal form.",
                "wrong_explanation": "Convert 15% to 0.15 and multiply by 200."
            }
    
    def _generate_fallback_science(self, title: str, complexity: str) -> Dict:
        """Generate science fallback based on complexity level"""
        if complexity == "simple":
            return {
                "type": "science",
                "question": "What do scientists do to learn about the world?",
                "options": ["Guess answers", "Do experiments", "Make up stories", "Copy others"],
                "correct": "Do experiments",
                "hint": "Scientists test their ideas",
                "explanation": "Scientists do experiments to test ideas and learn new things!",
                "reasoning": "The scientific method uses experiments to discover facts.",
                "wrong_explanation": "Scientists use careful testing, not guessing."
            }
        elif complexity == "intermediate":
            return {
                "type": "science",
                "question": "What is the first step in the scientific method?",
                "options": ["Do experiment", "Ask a question", "Write conclusion", "Tell others"],
                "correct": "Ask a question",
                "hint": "Scientists start by wondering about something",
                "explanation": "Scientists begin by asking questions about what they observe.",
                "reasoning": "Questions drive scientific investigation and discovery.",
                "wrong_explanation": "The scientific method starts with curiosity and questions."
            }
        elif complexity == "advanced":
            return {
                "type": "science",
                "question": "Why is peer review important in scientific research?",
                "options": ["To make friends", "To check accuracy and validity", "To copy ideas", "To save time"],
                "correct": "To check accuracy and validity",
                "hint": "Other scientists check the work",
                "explanation": "Peer review ensures research meets scientific standards and is accurate.",
                "reasoning": "Scientific knowledge builds on verified, reviewed research.",
                "wrong_explanation": "Peer review is quality control for scientific research."
            }
        else:  # college_prep
            return {
                "type": "science",
                "question": "How does this research contribute to the broader scientific literature?",
                "options": ["It doesn't matter", "It builds on previous studies and adds new knowledge", "It replaces all old research", "It's just opinion"],
                "correct": "It builds on previous studies and adds new knowledge",
                "hint": "Science is cumulative and builds on itself",
                "explanation": "Scientific research contributes to our collective understanding by building on and extending previous work.",
                "reasoning": "Science advances through incremental contributions to knowledge.",
                "wrong_explanation": "Look for how this study relates to and extends previous research."
            }
    
    def _generate_fallback_ela(self, title: str, complexity: str) -> Dict:
        """Generate ELA fallback based on complexity level"""
        if complexity == "simple":
            return {
                "type": "ela",
                "question": f"What is the main topic of '{title}'?",
                "options": ["Sports", "News and information", "Cartoons", "Games"],
                "correct": "News and information",
                "hint": "Think about what type of article this is",
                "explanation": "This is a news article that gives us information about real events!",
                "reasoning": "News articles inform us about what's happening in the world.",
                "wrong_explanation": "Look at the title and content - this reports real information."
            }
        elif complexity == "intermediate":
            return {
                "type": "ela",
                "question": "What is the author's purpose in writing this article?",
                "options": ["To entertain", "To inform readers", "To sell something", "To tell jokes"],
                "correct": "To inform readers",
                "hint": "Think about why someone writes news articles",
                "explanation": "News articles are written to inform readers about important events and discoveries.",
                "reasoning": "Authors have different purposes: to inform, persuade, or entertain.",
                "wrong_explanation": "News articles primarily aim to inform the public about current events."
            }
        elif complexity == "advanced":
            return {
                "type": "ela",
                "question": "What type of evidence does the author use to support their claims?",
                "options": ["Personal opinions only", "Scientific data and expert quotes", "Random guesses", "Social media posts"],
                "correct": "Scientific data and expert quotes",
                "hint": "Look for credible sources in the article",
                "explanation": "Good journalism uses scientific data, expert interviews, and credible sources.",
                "reasoning": "Strong arguments require evidence from reliable, authoritative sources.",
                "wrong_explanation": "Quality news articles cite experts, studies, and verifiable data."
            }
        else:  # college_prep
            return {
                "type": "ela",
                "question": "How might the author's choice of sources affect the article's credibility and perspective?",
                "options": ["Sources don't matter", "Different sources provide different viewpoints and credibility levels", "All sources are equal", "Only famous people matter"],
                "correct": "Different sources provide different viewpoints and credibility levels",
                "hint": "Consider who is quoted and their expertise",
                "explanation": "Source selection affects credibility, bias, and the range of perspectives presented.",
                "reasoning": "Critical readers evaluate sources for expertise, bias, and representativeness.",
                "wrong_explanation": "Analyze the types of sources used and their potential perspectives or limitations."
            }
    
    def get_supported_age_groups(self) -> List[str]:
        """Return list of supported age groups"""
        return list(self.teacher_personas.keys())
    
    def get_age_group_info(self, age_group: str) -> Dict:
        """Get information about a specific age group"""
        return self.teacher_personas.get(age_group, {})
