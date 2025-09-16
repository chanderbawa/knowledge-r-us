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
                1: ["multi_digit_multiplication", "long_division", "complex_fractions", "decimals", "challenging_word_problems"],
                2: ["mixed_fractions", "decimal_operations", "area_perimeter", "multi_step_word_problems", "basic_algebra"],
                3: ["percentages", "advanced_geometry", "measurement_conversions", "data_analysis", "pre_algebra"]
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
    
    def generate_math_questions(self, age_group: str, difficulty_level: int = 1, num_questions: int = 3) -> List[Dict]:
        """Generate math questions for specific age group and difficulty"""
        try:
            topics = self.grade_topics.get(age_group, {}).get(difficulty_level, ["basic_math"])
            questions = []
            
            # Generate specified number of questions
            for i in range(num_questions):
                # Cycle through topics if we need more questions than topics
                topic = topics[i % len(topics)]
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
        elif topic == "word_problems" or topic == "challenging_word_problems" or topic == "multi_step_word_problems":
            return self._generate_word_problem(age_group, difficulty_level)
        elif topic == "multi_digit_multiplication":
            return self._generate_multi_digit_multiplication(age_group, difficulty_level)
        elif topic == "long_division":
            return self._generate_long_division(age_group, difficulty_level)
        elif topic == "complex_fractions" or topic == "mixed_fractions":
            return self._generate_complex_fractions(age_group, difficulty_level)
        elif topic == "decimal_operations":
            return self._generate_decimal_operations(age_group, difficulty_level)
        elif topic == "area_perimeter":
            return self._generate_area_perimeter(age_group, difficulty_level)
        elif topic == "pre_algebra":
            return self._generate_pre_algebra(age_group, difficulty_level)
        elif topic == "measurement_conversions":
            return self._generate_measurement_conversions(age_group, difficulty_level)
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
            "options": [str(opt) for opt in options],
            "correct": str(correct),
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
            "options": [str(opt) for opt in options],
            "correct": str(correct),
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
            "options": [str(opt) for opt in options],
            "correct": str(correct),
            "explanation": f"{a} × {b} = {correct}",
            "reasoning": f"When we multiply {a} by {b}, we get {correct}.",
            "hint": f"Think of {a} groups of {b}, or add {b} to itself {a} times.",
            "wrong_explanation": "Try using repeated addition or the multiplication table."
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
        """Generate word problems with varying difficulty and question types"""
        
        # Determine if this should be fill-in-the-blank (30% chance for 9-11 age group)
        is_fill_in = age_group == "9-11" and random.random() < 0.3
        
        if age_group == "9-11":
            # More challenging scenarios for 9-year-olds
            if difficulty_level >= 2:
                # Multi-step problems
                scenarios = [
                    "Emma bought {a} packs of trading cards with {b} cards in each pack. She gave away {c} cards to friends. How many cards does she have left?",
                    "A school has {a} classrooms with {b} students in each room. If {c} new students join the school and are distributed equally, how many students will be in each classroom?",
                    "Jake earns ${a} per week doing chores. He saves ${b} each week and spends the rest. After {c} weeks, how much money has he spent in total?",
                    "A bakery makes {a} dozen cookies each day. They sell {b} cookies per hour for {c} hours. How many cookies are left at the end of the day?",
                    "Maria has {a} stickers. She gives {b} stickers to each of her {c} friends. How many stickers does she have remaining?"
                ]
                
                scenario = random.choice(scenarios)
                a = random.randint(15, 50)
                b = random.randint(8, 25)
                c = random.randint(3, 12)
                
                # Calculate based on scenario type
                if "packs" in scenario and "gave away" in scenario:
                    correct = (a * b) - c
                elif "distributed equally" in scenario:
                    total_students = (a * b) + c
                    correct = total_students // a
                elif "saves" in scenario and "spends" in scenario:
                    spent_per_week = a - b
                    correct = spent_per_week * c
                elif "dozen" in scenario and "sell" in scenario:
                    total_cookies = a * 12
                    sold_cookies = b * c
                    correct = total_cookies - sold_cookies
                elif "gives" in scenario and "each of her" in scenario:
                    correct = a - (b * c)
                else:
                    correct = a + b + c
                    
            else:
                # Single-step but harder numbers
                scenarios = [
                    "A movie theater has {a} seats arranged in {b} rows. How many seats are in each row if they are distributed equally?",
                    "Sophie collected {a} shells at the beach. She wants to put them in groups of {b}. How many complete groups can she make?",
                    "A pizza is cut into {a} slices. If {b} friends share it equally, how many slices does each person get?",
                    "Alex runs {a} laps around a track that is {b} meters long. How many total meters did he run?"
                ]
                
                scenario = random.choice(scenarios)
                a = random.randint(48, 144)
                b = random.randint(6, 24)
                
                if "distributed equally" in scenario or "each row" in scenario:
                    correct = a // b
                elif "groups of" in scenario or "complete groups" in scenario:
                    correct = a // b
                elif "share it equally" in scenario or "each person" in scenario:
                    correct = a // b
                else:
                    correct = a * b
        else:
            # Simpler problems for younger kids
            scenarios = [
                "Sarah has {a} apples. She gives {b} to her friend. How many apples does she have left?",
                "There are {a} students in class. {b} more students join. How many students are there now?",
                "A store has {a} books. They sell {b} books. How many books are left?"
            ]
            
            scenario = random.choice(scenarios)
            a = random.randint(15, 35)
            b = random.randint(5, 15)
            
            if "gives" in scenario or "sell" in scenario or "left" in scenario:
                correct = a - b
                operation = "subtraction"
            else:
                correct = a + b
                operation = "addition"
        
        question_text = scenario.format(a=a, b=b, c=c if 'c' in locals() else 0)
        
        if is_fill_in:
            # Fill-in-the-blank question (no multiple choice)
            return {
                "type": "math",
                "question_type": "fill_in_blank",
                "question": question_text,
                "correct": str(correct),
                "explanation": f"The answer is {correct}.",
                "reasoning": "Work through the problem step by step, identifying what operation(s) to use.",
                "hint": "Break down the problem into smaller steps and solve each part.",
                "wrong_explanation": "Double-check your calculations and make sure you're using the right operations."
            }
        else:
            # Multiple choice
            options = [correct]
            while len(options) < 4:
                if correct > 50:
                    wrong = correct + random.randint(-20, 20)
                else:
                    wrong = correct + random.randint(-8, 8)
                
                if wrong != correct and wrong >= 0 and wrong not in options:
                    options.append(wrong)
            
            random.shuffle(options)
            
            return {
                "type": "math",
                "question_type": "multiple_choice",
                "question": question_text,
                "options": [str(opt) for opt in options],
                "correct": str(correct),
                "explanation": f"The answer is {correct}.",
                "reasoning": "Work through the problem step by step, identifying what operation(s) to use.",
                "hint": "Break down the problem into smaller steps and solve each part.",
                "wrong_explanation": "Double-check your calculations and make sure you're using the right operations."
            }
    
    def _generate_multi_digit_multiplication(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate multi-digit multiplication problems"""
        if age_group == "9-11":
            a = random.randint(23, 89)
            b = random.randint(12, 47)
        else:
            a = random.randint(12, 25)
            b = random.randint(11, 19)
        
        correct = a * b
        
        # 40% chance of fill-in-the-blank for 9-11 age group
        is_fill_in = age_group == "9-11" and random.random() < 0.4
        
        if is_fill_in:
            return {
                "type": "math",
                "question_type": "fill_in_blank",
                "question": f"What is {a} × {b}?",
                "correct": str(correct),
                "explanation": f"{a} × {b} = {correct}",
                "reasoning": f"Break it down: {a} × {b} can be solved using the standard multiplication algorithm.",
                "hint": "Try breaking one number into tens and ones, then multiply each part.",
                "wrong_explanation": "Double-check your multiplication steps and alignment of place values."
            }
        else:
            options = [correct]
            while len(options) < 4:
                wrong = correct + random.randint(-150, 150)
                if wrong != correct and wrong > 0 and wrong not in options:
                    options.append(wrong)
            
            random.shuffle(options)
            
            return {
                "type": "math",
                "question_type": "multiple_choice",
                "question": f"What is {a} × {b}?",
                "options": [str(opt) for opt in options],
                "correct": str(correct),
                "explanation": f"{a} × {b} = {correct}",
                "reasoning": f"Using the standard multiplication algorithm: {a} × {b} = {correct}.",
                "hint": "Try breaking one number into tens and ones, then multiply each part.",
                "wrong_explanation": "Double-check your multiplication steps and alignment of place values."
            }
    
    def _generate_long_division(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate long division problems"""
        if age_group == "9-11":
            divisor = random.randint(12, 25)
            quotient = random.randint(15, 45)
            remainder = random.randint(0, divisor - 1)
            dividend = (divisor * quotient) + remainder
        else:
            divisor = random.randint(6, 12)
            quotient = random.randint(8, 20)
            remainder = 0
            dividend = divisor * quotient
        
        if remainder == 0:
            correct = quotient
            question = f"What is {dividend} ÷ {divisor}?"
        else:
            correct = f"{quotient} R{remainder}"
            question = f"What is {dividend} ÷ {divisor}? (Include remainder if needed)"
        
        # 50% chance of fill-in-the-blank for 9-11 age group
        is_fill_in = age_group == "9-11" and random.random() < 0.5
        
        if is_fill_in:
            return {
                "type": "math",
                "question_type": "fill_in_blank",
                "question": question,
                "correct": str(correct),
                "explanation": f"{dividend} ÷ {divisor} = {correct}",
                "reasoning": "Use long division: divide, multiply, subtract, bring down, repeat.",
                "hint": "Start by seeing how many times the divisor goes into the first digits of the dividend.",
                "wrong_explanation": "Check each step of your long division carefully."
            }
        else:
            options = [str(correct)]
            while len(options) < 4:
                if remainder == 0:
                    wrong_q = quotient + random.randint(-5, 5)
                    wrong = str(wrong_q) if wrong_q > 0 else str(quotient + 1)
                else:
                    wrong_q = quotient + random.randint(-3, 3)
                    wrong_r = random.randint(0, divisor - 1)
                    wrong = f"{wrong_q} R{wrong_r}" if wrong_q > 0 else f"{quotient + 1} R{wrong_r}"
                
                if wrong != str(correct) and wrong not in options:
                    options.append(wrong)
            
            random.shuffle(options)
            
            return {
                "type": "math",
                "question_type": "multiple_choice",
                "question": question,
                "options": options,
                "correct": str(correct),
                "explanation": f"{dividend} ÷ {divisor} = {correct}",
                "reasoning": "Use long division: divide, multiply, subtract, bring down, repeat.",
                "hint": "Start by seeing how many times the divisor goes into the first digits of the dividend.",
                "wrong_explanation": "Check each step of your long division carefully."
            }
    
    def _generate_complex_fractions(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate complex fraction problems"""
        if age_group == "9-11":
            # Mixed numbers and improper fractions
            whole = random.randint(2, 8)
            num = random.randint(1, 7)
            den = random.randint(num + 1, 12)
            
            improper_num = (whole * den) + num
            question = f"Convert {whole} {num}/{den} to an improper fraction"
            correct = f"{improper_num}/{den}"
        else:
            # Simple fraction addition
            den = random.choice([4, 6, 8, 10])
            num1 = random.randint(1, den - 2)
            num2 = random.randint(1, den - num1)
            
            question = f"What is {num1}/{den} + {num2}/{den}?"
            correct_num = num1 + num2
            correct = f"{correct_num}/{den}"
        
        # 35% chance of fill-in-the-blank for 9-11 age group
        is_fill_in = age_group == "9-11" and random.random() < 0.35
        
        if is_fill_in:
            return {
                "type": "math",
                "question_type": "fill_in_blank",
                "question": question,
                "correct": correct,
                "explanation": f"The answer is {correct}.",
                "reasoning": "For mixed to improper: multiply whole by denominator, add numerator." if "Convert" in question else "Add numerators, keep denominator the same.",
                "hint": "Remember the steps for converting between mixed and improper fractions." if "Convert" in question else "When denominators are the same, just add the numerators.",
                "wrong_explanation": "Review the rules for working with fractions."
            }
        else:
            options = [correct]
            while len(options) < 4:
                if "Convert" in question:
                    wrong_num = improper_num + random.randint(-3, 3)
                    wrong = f"{wrong_num}/{den}" if wrong_num > 0 else f"{improper_num + 1}/{den}"
                else:
                    wrong_num = correct_num + random.randint(-2, 2)
                    wrong = f"{wrong_num}/{den}" if wrong_num > 0 else f"{correct_num + 1}/{den}"
                
                if wrong != correct and wrong not in options:
                    options.append(wrong)
            
            random.shuffle(options)
            
            return {
                "type": "math",
                "question_type": "multiple_choice",
                "question": question,
                "options": options,
                "correct": correct,
                "explanation": f"The answer is {correct}.",
                "reasoning": "For mixed to improper: multiply whole by denominator, add numerator." if "Convert" in question else "Add numerators, keep denominator the same.",
                "hint": "Remember the steps for converting between mixed and improper fractions." if "Convert" in question else "When denominators are the same, just add the numerators.",
                "wrong_explanation": "Review the rules for working with fractions."
            }
    
    def _generate_decimal_operations(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate decimal operation problems"""
        if age_group == "9-11":
            a = round(random.uniform(5.5, 25.9), 1)
            b = round(random.uniform(2.3, 15.7), 1)
            operation = random.choice(['+', '-'])
        else:
            a = round(random.uniform(1.1, 9.9), 1)
            b = round(random.uniform(0.5, 5.5), 1)
            operation = '+'
        
        if operation == '+':
            correct = round(a + b, 1)
        else:
            correct = round(a - b, 1)
        
        question = f"What is {a} {operation} {b}?"
        
        # 25% chance of fill-in-the-blank for 9-11 age group
        is_fill_in = age_group == "9-11" and random.random() < 0.25
        
        if is_fill_in:
            return {
                "type": "math",
                "question_type": "fill_in_blank",
                "question": question,
                "correct": str(correct),
                "explanation": f"{a} {operation} {b} = {correct}",
                "reasoning": "Line up the decimal points and perform the operation.",
                "hint": "Make sure to align the decimal points when adding or subtracting decimals.",
                "wrong_explanation": "Double-check your decimal point alignment and calculation."
            }
        else:
            options = [correct]
            while len(options) < 4:
                wrong = round(correct + random.uniform(-2.5, 2.5), 1)
                if wrong != correct and wrong > 0 and wrong not in options:
                    options.append(wrong)
            
            random.shuffle(options)
            
            return {
                "type": "math",
                "question_type": "multiple_choice",
                "question": question,
                "options": [str(opt) for opt in options],
                "correct": str(correct),
                "explanation": f"{a} {operation} {b} = {correct}",
                "reasoning": "Line up the decimal points and perform the operation.",
                "hint": "Make sure to align the decimal points when adding or subtracting decimals.",
                "wrong_explanation": "Double-check your decimal point alignment and calculation."
            }
    
    def _generate_area_perimeter(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate area and perimeter problems"""
        if age_group == "9-11":
            length = random.randint(8, 25)
            width = random.randint(6, 20)
            shape_type = random.choice(['area', 'perimeter'])
        else:
            length = random.randint(4, 12)
            width = random.randint(3, 10)
            shape_type = 'perimeter'
        
        if shape_type == 'area':
            correct = length * width
            question = f"What is the area of a rectangle with length {length} cm and width {width} cm?"
            unit = "square cm"
        else:
            correct = 2 * (length + width)
            question = f"What is the perimeter of a rectangle with length {length} cm and width {width} cm?"
            unit = "cm"
        
        # 30% chance of fill-in-the-blank for 9-11 age group
        is_fill_in = age_group == "9-11" and random.random() < 0.3
        
        if is_fill_in:
            return {
                "type": "math",
                "question_type": "fill_in_blank",
                "question": question,
                "correct": f"{correct} {unit}",
                "explanation": f"The answer is {correct} {unit}.",
                "reasoning": f"{'Area = length × width' if shape_type == 'area' else 'Perimeter = 2 × (length + width)'}",
                "hint": f"{'Multiply length times width for area' if shape_type == 'area' else 'Add all four sides for perimeter'}",
                "wrong_explanation": f"Remember the formula for {'area' if shape_type == 'area' else 'perimeter'} of a rectangle."
            }
        else:
            options = [f"{correct} {unit}"]
            while len(options) < 4:
                wrong = correct + random.randint(-15, 15)
                wrong_option = f"{wrong} {unit}"
                if wrong > 0 and wrong_option not in options:
                    options.append(wrong_option)
            
            random.shuffle(options)
            
            return {
                "type": "math",
                "question_type": "multiple_choice",
                "question": question,
                "options": options,
                "correct": f"{correct} {unit}",
                "explanation": f"The answer is {correct} {unit}.",
                "reasoning": f"{'Area = length × width' if shape_type == 'area' else 'Perimeter = 2 × (length + width)'}",
                "hint": f"{'Multiply length times width for area' if shape_type == 'area' else 'Add all four sides for perimeter'}",
                "wrong_explanation": f"Remember the formula for {'area' if shape_type == 'area' else 'perimeter'} of a rectangle."
            }
    
    def _generate_pre_algebra(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate pre-algebra problems"""
        if age_group == "9-11":
            # Simple equations like x + 5 = 12
            unknown = random.randint(3, 25)
            addend = random.randint(4, 18)
            total = unknown + addend
            
            question = f"If x + {addend} = {total}, what is x?"
            correct = unknown
        else:
            # Very basic patterns
            start = random.randint(2, 8)
            step = random.randint(2, 5)
            sequence = [start + i * step for i in range(4)]
            
            question = f"What comes next in this pattern: {', '.join(map(str, sequence))}?"
            correct = sequence[-1] + step
        
        # 40% chance of fill-in-the-blank for 9-11 age group
        is_fill_in = age_group == "9-11" and random.random() < 0.4
        
        if is_fill_in:
            return {
                "type": "math",
                "question_type": "fill_in_blank",
                "question": question,
                "correct": str(correct),
                "explanation": f"The answer is {correct}.",
                "reasoning": f"{'Subtract ' + str(addend) + ' from both sides to isolate x' if 'x +' in question else 'The pattern increases by ' + str(step if 'pattern' in question else 1) + ' each time'}",
                "hint": f"{'What number plus ' + str(addend) + ' equals ' + str(total) + '?' if 'x +' in question else 'Look for the pattern in how the numbers change'}",
                "wrong_explanation": "Think about what operation will help you solve for the unknown value."
            }
        else:
            options = [correct]
            while len(options) < 4:
                wrong = correct + random.randint(-8, 8)
                if wrong != correct and wrong > 0 and wrong not in options:
                    options.append(wrong)
            
            random.shuffle(options)
            
            return {
                "type": "math",
                "question_type": "multiple_choice",
                "question": question,
                "options": [str(opt) for opt in options],
                "correct": str(correct),
                "explanation": f"The answer is {correct}.",
                "reasoning": f"{'Subtract ' + str(addend) + ' from both sides to isolate x' if 'x +' in question else 'The pattern increases by ' + str(step if 'pattern' in question else 1) + ' each time'}",
                "hint": f"{'What number plus ' + str(addend) + ' equals ' + str(total) + '?' if 'x +' in question else 'Look for the pattern in how the numbers change'}",
                "wrong_explanation": "Think about what operation will help you solve for the unknown value."
            }
    
    def _generate_measurement_conversions(self, age_group: str, difficulty_level: int) -> Dict:
        """Generate measurement conversion problems"""
        if age_group == "9-11":
            conversions = [
                ("feet", "inches", 12, random.randint(3, 8)),
                ("yards", "feet", 3, random.randint(4, 12)),
                ("hours", "minutes", 60, random.randint(2, 6)),
                ("pounds", "ounces", 16, random.randint(2, 8))
            ]
        else:
            conversions = [
                ("feet", "inches", 12, random.randint(1, 4)),
                ("hours", "minutes", 60, random.randint(1, 3))
            ]
        
        from_unit, to_unit, factor, amount = random.choice(conversions)
        correct = amount * factor
        
        question = f"How many {to_unit} are in {amount} {from_unit}?"
        
        # 35% chance of fill-in-the-blank for 9-11 age group
        is_fill_in = age_group == "9-11" and random.random() < 0.35
        
        if is_fill_in:
            return {
                "type": "math",
                "question_type": "fill_in_blank",
                "question": question,
                "correct": str(correct),
                "explanation": f"{amount} {from_unit} = {correct} {to_unit}",
                "reasoning": f"Multiply by {factor} to convert from {from_unit} to {to_unit}.",
                "hint": f"Remember: 1 {from_unit[:-1] if from_unit.endswith('s') else from_unit} = {factor} {to_unit}",
                "wrong_explanation": "Check the conversion factor and make sure you're multiplying correctly."
            }
        else:
            options = [correct]
            while len(options) < 4:
                wrong = correct + random.randint(-20, 20)
                if wrong != correct and wrong > 0 and wrong not in options:
                    options.append(wrong)
            
            random.shuffle(options)
            
            return {
                "type": "math",
                "question_type": "multiple_choice",
                "question": question,
                "options": [str(opt) for opt in options],
                "correct": str(correct),
                "explanation": f"{amount} {from_unit} = {correct} {to_unit}",
                "reasoning": f"Multiply by {factor} to convert from {from_unit} to {to_unit}.",
                "hint": f"Remember: 1 {from_unit[:-1] if from_unit.endswith('s') else from_unit} = {factor} {to_unit}",
                "wrong_explanation": "Check the conversion factor and make sure you're multiplying correctly."
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
            },
            {
                "type": "math",
                "question": "What is 10 - 4?",
                "options": ["5", "7", "6", "8"],
                "correct": "6",
                "explanation": "10 - 4 = 6",
                "reasoning": "When we subtract 4 from 10, we get 6.",
                "hint": "Count backwards from 10: 9, 8, 7, 6",
                "wrong_explanation": "Try using your fingers to count backwards."
            },
            {
                "type": "math",
                "question": "What is 3 × 4?",
                "options": ["10", "12", "14", "16"],
                "correct": "12",
                "explanation": "3 × 4 = 12",
                "reasoning": "3 groups of 4 equals 12.",
                "hint": "Think of 3 groups with 4 items each.",
                "wrong_explanation": "Try adding 4 + 4 + 4 = 12."
            }
        ]
