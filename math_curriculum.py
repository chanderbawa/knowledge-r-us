"""
Math Curriculum Generator
Creates grade-level appropriate math questions independent of news articles
"""

import random
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class MathCurriculumGenerator:
    """Generates grade-level appropriate math questions"""
    
    def __init__(self):
        self.grade_topics = {
            "6-8": {  # Elementary (Grades 1-3)
                1: ["addition", "subtraction", "counting", "shapes"],
                2: ["addition", "subtraction", "counting", "shapes", "basic_multiplication"],
                3: ["addition", "subtraction", "multiplication", "division", "fractions_basic"]
            },
            "9-11": {  # Elementary (Grades 4-6)
                1: ["multiplication", "division", "fractions", "decimals"],
                2: ["fractions", "decimals", "geometry", "word_problems"],
                3: ["percentages", "geometry", "measurement", "data_analysis"]
            },
            "12-14": {  # Middle School (Grades 7-8)
                1: ["integers", "ratios", "proportions", "basic_algebra"],
                2: ["algebra", "geometry", "statistics", "probability"],
                3: ["advanced_algebra", "coordinate_geometry", "functions"]
            },
            "15-18": {  # High School (Grades 9-12)
                1: ["algebra_1", "linear_equations", "quadratic_equations"],
                2: ["geometry", "trigonometry", "advanced_algebra"],
                3: ["precalculus", "calculus_basics", "statistics"]
            }
        }
    
    def generate_math_questions(self, age_group: str, difficulty_level: int = 1) -> List[Dict]:
        """Generate math questions for specific age group and difficulty"""
        try:
            topics = self.grade_topics.get(age_group, {}).get(difficulty_level, ["basic_math"])
            questions = []
            
            # Generate 2-3 questions from different topics
            selected_topics = random.sample(topics, min(3, len(topics)))
            
            for topic in selected_topics:
                question = self._generate_question_by_topic(topic, age_group, difficulty_level)
                if question:
                    questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating math questions: {e}")
            return self._get_fallback_math_questions(age_group, difficulty_level)
    
    def _generate_question_by_topic(self, topic: str, age_group: str, difficulty_level: int) -> Dict:
        """Generate a specific question based on topic"""
        
        if topic == "addition":
            return self._generate_addition_question(age_group, difficulty_level)
        elif topic == "subtraction":
            return self._generate_subtraction_question(age_group, difficulty_level)
        elif topic == "multiplication":
            return self._generate_multiplication_question(age_group, difficulty_level)
        elif topic == "division":
            return self._generate_division_question(age_group, difficulty_level)
        elif topic == "fractions" or topic == "fractions_basic":
            return self._generate_fractions_question(age_group, difficulty_level)
        elif topic == "decimals":
            return self._generate_decimals_question(age_group, difficulty_level)
        elif topic == "percentages":
            return self._generate_percentages_question(age_group, difficulty_level)
        elif topic == "geometry":
            return self._generate_geometry_question(age_group, difficulty_level)
        elif topic == "algebra" or topic == "basic_algebra":
            return self._generate_algebra_question(age_group, difficulty_level)
        elif topic == "word_problems":
            return self._generate_word_problem(age_group, difficulty_level)
        else:
            return self._generate_basic_math_question(age_group, difficulty_level)
    
    def _generate_addition_question(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate addition questions"""
        if age_group == "6-8":
            if difficulty_level == 1:
                a, b = random.randint(1, 10), random.randint(1, 10)
            else:
                a, b = random.randint(10, 50), random.randint(10, 50)
        else:
            a, b = random.randint(50, 200), random.randint(50, 200)
        
        correct = a + b
        options = [correct]
        
        # Generate wrong options
        while len(options) < 4:
            wrong = correct + random.randint(-10, 10)
            if wrong != correct and wrong > 0 and wrong not in options:
                options.append(wrong)
        
        random.shuffle(options)
        
        return {
            "type": "math",
            "question": f"What is {a} + {b}?",
            "options": options,
            "correct": correct,
            "explanation": f"Adding {a} and {b} gives us {correct}.",
            "reasoning": f"When we add {a} + {b}, we combine the two numbers to get {correct}.",
            "hint": f"Try counting up from {a} by {b}, or break it down into smaller parts.",
            "wrong_explanation": "Remember to carefully add each digit, starting from the ones place."
        }
    
    def _generate_subtraction_question(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate subtraction questions"""
        if age_group == "6-8":
            if difficulty_level == 1:
                a = random.randint(5, 20)
                b = random.randint(1, a)
            else:
                a = random.randint(20, 100)
                b = random.randint(1, a)
        else:
            a = random.randint(100, 500)
            b = random.randint(1, a)
        
        correct = a - b
        options = [correct]
        
        # Generate wrong options
        while len(options) < 4:
            wrong = correct + random.randint(-10, 10)
            if wrong != correct and wrong >= 0 and wrong not in options:
                options.append(wrong)
        
        random.shuffle(options)
        
        return {
            "type": "math",
            "question": f"What is {a} - {b}?",
            "options": options,
            "correct": correct,
            "explanation": f"Subtracting {b} from {a} gives us {correct}.",
            "reasoning": f"When we subtract {b} from {a}, we take away {b} to get {correct}.",
            "hint": f"Try counting backwards from {a} by {b}, or think of it as 'what plus {b} equals {a}?'",
            "wrong_explanation": "Remember to borrow from the next column when needed in subtraction."
        }
    
    def _generate_multiplication_question(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate multiplication questions"""
        if age_group == "6-8":
            a, b = random.randint(2, 5), random.randint(2, 10)
        elif age_group == "9-11":
            a, b = random.randint(2, 12), random.randint(2, 12)
        else:
            a, b = random.randint(5, 25), random.randint(2, 15)
        
        correct = a * b
        options = [correct]
        
        # Generate wrong options
        while len(options) < 4:
            wrong = correct + random.randint(-20, 20)
            if wrong != correct and wrong > 0 and wrong not in options:
                options.append(wrong)
        
        random.shuffle(options)
        
        return {
            "type": "math",
            "question": f"What is {a} × {b}?",
            "options": options,
            "correct": correct,
            "explanation": f"Multiplying {a} by {b} gives us {correct}.",
            "reasoning": f"{a} × {b} means adding {a} together {b} times, which equals {correct}.",
            "hint": f"Think of it as {b} groups of {a}, or use the multiplication table.",
            "wrong_explanation": "Remember that multiplication is repeated addition."
        }
    
    def _generate_fractions_question(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate fractions questions"""
        if age_group == "6-8":
            # Simple fractions
            numerators = [1, 1, 2, 3]
            denominators = [2, 4, 4, 4]
        else:
            numerators = [1, 2, 3, 5, 7]
            denominators = [3, 5, 8, 6, 10]
        
        num1, den1 = random.choice(list(zip(numerators, denominators)))
        num2, den2 = random.choice(list(zip(numerators, denominators)))
        
        # Simple addition of fractions with same denominator
        if den1 == den2:
            correct_num = num1 + num2
            correct_den = den1
            operation = "+"
        else:
            # For different denominators, use simpler comparison
            if num1/den1 > num2/den2:
                larger_frac = f"{num1}/{den1}"
                correct = f"{num1}/{den1}"
            else:
                larger_frac = f"{num2}/{den2}"
                correct = f"{num2}/{den2}"
            
            options = [f"{num1}/{den1}", f"{num2}/{den2}", f"{num1+1}/{den1}", f"{num2+1}/{den2}"]
            random.shuffle(options)
            
            return {
                "type": "math",
                "question": f"Which fraction is larger: {num1}/{den1} or {num2}/{den2}?",
                "options": options,
                "correct": correct,
                "explanation": f"{correct} is the larger fraction.",
                "reasoning": f"When comparing fractions, {correct} represents a larger part of the whole.",
                "hint": "Convert to decimals or find a common denominator to compare.",
                "wrong_explanation": "Remember to compare the actual values, not just the numbers."
            }
        
        # Same denominator addition
        options = [f"{correct_num}/{correct_den}"]
        while len(options) < 4:
            wrong_num = correct_num + random.randint(-2, 2)
            if wrong_num > 0 and f"{wrong_num}/{correct_den}" not in options:
                options.append(f"{wrong_num}/{correct_den}")
        
        random.shuffle(options)
        correct = f"{correct_num}/{correct_den}"
        
        return {
            "type": "math",
            "question": f"What is {num1}/{den1} + {num2}/{den2}?",
            "options": options,
            "correct": correct,
            "explanation": f"Adding fractions with the same denominator: {num1}/{den1} + {num2}/{den2} = {correct}.",
            "reasoning": f"When denominators are the same, we add the numerators: {num1} + {num2} = {correct_num}.",
            "hint": "When denominators are the same, just add the top numbers (numerators).",
            "wrong_explanation": "Remember to only add the numerators when denominators are the same."
        }
    
    def _generate_algebra_question(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate basic algebra questions"""
        if age_group in ["6-8", "9-11"]:
            # Simple missing number problems
            a = random.randint(5, 20)
            b = random.randint(1, 10)
            correct = a + b
            
            options = [b]
            while len(options) < 4:
                wrong = b + random.randint(-5, 5)
                if wrong != b and wrong > 0 and wrong not in options:
                    options.append(wrong)
            
            random.shuffle(options)
            
            return {
                "type": "math",
                "question": f"What number makes this equation true: {a} + ? = {correct}",
                "options": options,
                "correct": b,
                "explanation": f"The missing number is {b} because {a} + {b} = {correct}.",
                "reasoning": f"To find the missing number, we subtract {a} from {correct}: {correct} - {a} = {b}.",
                "hint": f"Think: what number plus {a} equals {correct}?",
                "wrong_explanation": "To find a missing addend, subtract the known addend from the sum."
            }
        else:
            # Simple linear equations
            x = random.randint(2, 10)
            a = random.randint(2, 8)
            b = a * x
            
            options = [x]
            while len(options) < 4:
                wrong = x + random.randint(-3, 3)
                if wrong != x and wrong > 0 and wrong not in options:
                    options.append(wrong)
            
            random.shuffle(options)
            
            return {
                "type": "math",
                "question": f"Solve for x: {a}x = {b}",
                "options": options,
                "correct": x,
                "explanation": f"x = {x} because {a} × {x} = {b}.",
                "reasoning": f"To solve {a}x = {b}, divide both sides by {a}: x = {b} ÷ {a} = {x}.",
                "hint": f"Divide both sides by {a} to isolate x.",
                "wrong_explanation": "To solve for x, divide both sides of the equation by the coefficient of x."
            }
    
    def _generate_geometry_question(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate geometry questions"""
        if age_group == "6-8":
            shapes = ["triangle", "square", "rectangle", "circle"]
            shape = random.choice(shapes)
            
            if shape == "triangle":
                correct = "3"
                question = "How many sides does a triangle have?"
            elif shape == "square":
                correct = "4"
                question = "How many sides does a square have?"
            elif shape == "rectangle":
                correct = "4"
                question = "How many sides does a rectangle have?"
            else:  # circle
                correct = "0"
                question = "How many sides does a circle have?"
            
            options = ["0", "3", "4", "5"]
            
        else:
            # Area and perimeter questions
            if random.choice([True, False]):
                # Rectangle area
                length = random.randint(3, 12)
                width = random.randint(2, 10)
                correct = length * width
                question = f"What is the area of a rectangle with length {length} and width {width}?"
                
                options = [correct]
                while len(options) < 4:
                    wrong = correct + random.randint(-10, 10)
                    if wrong != correct and wrong > 0 and wrong not in options:
                        options.append(wrong)
            else:
                # Rectangle perimeter
                length = random.randint(3, 12)
                width = random.randint(2, 10)
                correct = 2 * (length + width)
                question = f"What is the perimeter of a rectangle with length {length} and width {width}?"
                
                options = [correct]
                while len(options) < 4:
                    wrong = correct + random.randint(-8, 8)
                    if wrong != correct and wrong > 0 and wrong not in options:
                        options.append(wrong)
        
        random.shuffle(options)
        
        return {
            "type": "math",
            "question": question,
            "options": [str(opt) for opt in options],
            "correct": str(correct),
            "explanation": f"The answer is {correct}.",
            "reasoning": "This follows the basic principles of geometry.",
            "hint": "Think about the definition and properties of the shape.",
            "wrong_explanation": "Review the basic properties of geometric shapes."
        }
    
    def _generate_word_problem(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate word problems"""
        scenarios = [
            "Sarah has {a} apples. She gives {b} to her friend. How many apples does she have left?",
            "There are {a} students in class. {b} more students join. How many students are there now?",
            "A store has {a} books. They sell {b} books. How many books are left?",
            "Tom collects {a} stickers. His sister gives him {b} more. How many stickers does he have now?"
        ]
        
        scenario = random.choice(scenarios)
        
        if age_group == "6-8":
            a = random.randint(5, 20)
            b = random.randint(1, min(10, a))
        else:
            a = random.randint(20, 100)
            b = random.randint(5, 50)
        
        if "gives" in scenario or "sell" in scenario or "left" in scenario:
            correct = a - b
            operation = "subtraction"
        else:
            correct = a + b
            operation = "addition"
        
        question_text = scenario.format(a=a, b=b)
        
        options = [correct]
        while len(options) < 4:
            if operation == "subtraction":
                wrong = correct + random.randint(-5, 10)
            else:
                wrong = correct + random.randint(-10, 5)
            
            if wrong != correct and wrong >= 0 and wrong not in options:
                options.append(wrong)
        
        random.shuffle(options)
        
        return {
            "type": "math",
            "question": question_text,
            "options": [str(opt) for opt in options],
            "correct": str(correct),
            "explanation": f"The answer is {correct}.",
            "reasoning": f"This is a {operation} problem: {a} {'−' if operation == 'subtraction' else '+'} {b} = {correct}.",
            "hint": f"Identify whether you need to add or subtract based on the story.",
            "wrong_explanation": "Read the problem carefully to determine the correct operation."
        }
    
    def _generate_basic_math_question(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate basic math questions as fallback"""
        return self._generate_addition_question(age_group, difficulty_level)
    
    def _get_fallback_math_questions(self, age_group: str, difficulty_level: int) -> List[Dict]:
        """Fallback math questions if generation fails"""
        return [
            {
                "type": "math",
                "question": "What is 5 + 3?",
                "options": ["6", "7", "8", "9"],
                "correct": "8",
                "explanation": "5 + 3 = 8",
                "reasoning": "When we add 5 and 3, we get 8.",
                "hint": "Count up from 5: 6, 7, 8.",
                "wrong_explanation": "Remember to add carefully."
            }
        ]
