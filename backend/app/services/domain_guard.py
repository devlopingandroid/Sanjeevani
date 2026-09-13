"""Sanjeevni AI Domain Scope Guard.

Deterministic backend security guard that restricts Sanjeevni AI strictly to
Health & Wellness domain topics without making external LLM API calls.
"""
import re
from typing import Tuple, Optional


class DomainGuard:
    OFF_TOPIC_REDIRECT_MESSAGE = (
        "I'm Sanjeevni's health and wellness assistant. I can help with topics like "
        "stress, sleep, nutrition, exercise, wellness, and your available health data. "
        "Please ask me a health-related question."
    )

    # Prompt Injection & Bypass keywords
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|system|prior)\s+(instructions|rules|prompts|directives)",
        r"act\s+as\s+(a\s+)?(general|different|other|any|python|code|math|unrestricted)",
        r"forget\s+(that\s+)?(you\s+are|your)\s+(sanjeevni|health|rules|instructions)",
        r"you\s+are\s+now\s+(a|an|free|unrestricted)",
        r"pretend\s+to\s+be",
        r"do\s+anything\s+now",
        r"jailbreak",
        r"override\s+(system|rules|safety|prompt)",
        r"answer\s+anything\s+i\s+ask",
    ]

    # Explicit Off-topic Keywords & Phrases (Blocked unless genuine health context exists)
    OFF_TOPIC_KEYWORDS = [
        # Programming & Computer Science Data Structures
        "array", "arrays", "matrix", "matrices", "pointer", "pointers", "linked list",
        "binary tree", "hashmap", "hashtable", "stack", "queue", "vector", "recursion",
        "loop", "for loop", "while loop", "function", "method", "variable", "class",
        "object", "inheritance", "polymorphic", "algorithm", "sorting", "bubble sort",
        "quick sort", "merge sort", "binary search", "big o", "malloc", "memory leak",
        "boolean", "integer", "string", "float", "double", "char", "null pointer",
        # Coding Languages & Tech Frameworks
        "python", "javascript", "typescript", "java", "c++", "c#", "html", "css",
        "sql", "react", "vue", "angular", "node.js", "docker", "kubernetes",
        "coding", "program", "programming", "compiler", "debugging", "syntax",
        "github", "git", "script", "software development", "api key", "json format",
        "terminal", "command line", "npm", "pip", "repository", "regex",
        # Mathematics & General School Homework
        "algebra", "calculus", "equation", "solve for x", "trigonometry",
        "derivative", "integral", "homework", "math problem",
        # History & Politics & Geography
        "president", "prime minister", "parliament", "democrat", "republican",
        "capital of", "geography", "world war", "history of",
        # Entertainment, Gaming & Celebrities
        "cinema", "hollywood", "bollywood", "video game", "playstation", "xbox",
        "nintendo", "fortnite", "minecraft", "pop star", "celebrity",
        "sports news", "cricket score", "football match", "nba", "messi", "ronaldo",
        # Creative Writing & Entertainment Requests
        "tell me a joke", "tell a joke", "make me laugh", "write a poem",
        "write a story", "write a song", "write code", "write a script", "write python",
        # Finance & Legal
        "crypto", "bitcoin", "ethereum", "stock market", "investment",
        "lawsuit", "legal advice", "court case", "financial advice",
    ]

    # Explicit Health & Wellness Allowed Keywords
    HEALTH_WELLNESS_KEYWORDS = [
        # Stress & Mental Wellness
        "stress", "anxiety", "anxious", "depressed", "depression", "burnout",
        "overwhelmed", "panic", "calm", "relax", "relaxation", "mindful",
        "mindfulness", "meditation", "mental", "emotion", "emotional", "wellbeing",
        "wellness", "vagus", "vagal", "somatic", "nervous system", "coping",
        # Breathing & Somatic
        "breath", "breathing", "inhale", "exhale", "pranayama", "respiration",
        "diaphragm", "lungs", "hyperventilating",
        # Sleep & Rest
        "sleep", "insomnia", "tired", "fatigue", "sleepy", "bedtime", "nap",
        "circadian", "rest", "drowsy", "snoring", "apnea",
        # Biometrics & Sensors & Vitals
        "heart", "pulse", "bpm", "hrv", "rmssd", "temperature", "skin", "gsr",
        "eda", "sweat", "vital", "vitals", "biometric", "sensor", "telemetry",
        "blood pressure", "spo2", "oxygen", "vagal tone", "wearable",
        # Physical Symptoms & Health Concerns
        "headache", "migraine", "pain", "fever", "dizziness", "nausea", "chest",
        "stomach", "cramps", "muscle", "joint", "body", "symptom", "illness",
        "disease", "infection", "sick", "doctor", "physician", "hospital",
        "clinic", "first aid", "emergency", "medicine", "medication", "pill",
        "supplement", "vitamin", "dose", "prescription", "side effect",
        # Lifestyle, Nutrition & Recovery
        "diet", "nutrition", "food", "eating", "meal", "water", "hydration",
        "exercise", "workout", "gym", "cardio", "walk", "running", "jogging",
        "yoga", "stretching", "posture", "weight", "obesity", "fitness",
        "recovery", "habit", "protein", "calorie", "calories", "metabolism",
        # Sanjeevni context
        "sanjeevni", "health", "health data", "stress score", "biometric data"
    ]

    @classmethod
    def evaluate(cls, message: str) -> Tuple[bool, Optional[str]]:
        """Evaluates whether a message is within the Health & Wellness domain.

        Returns:
            Tuple[bool, Optional[str]]: (is_allowed, redirect_message_if_blocked)
        """
        if not message or not message.strip():
            return False, cls.OFF_TOPIC_REDIRECT_MESSAGE

        lower_msg = message.lower().strip()

        # 1. Check for prompt injection attempts
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, lower_msg):
                return False, cls.OFF_TOPIC_REDIRECT_MESSAGE

        # 2. Check for explicit off-topic phrases & keywords
        has_off_topic_keyword = False
        for kw in cls.OFF_TOPIC_KEYWORDS:
            # Word boundary matching for short terms like "array", "c++", "sql"
            pattern = r"\b" + re.escape(kw) + r"\b" if len(kw) <= 5 else re.escape(kw)
            if re.search(pattern, lower_msg):
                has_off_topic_keyword = True
                break

        # 3. Check for health & wellness keywords
        has_health_keyword = False
        for kw in cls.HEALTH_WELLNESS_KEYWORDS:
            if kw in lower_msg:
                has_health_keyword = True
                break

        # 4. If message has explicit off-topic keywords and NO health context -> BLOCK
        if has_off_topic_keyword and not has_health_keyword:
            return False, cls.OFF_TOPIC_REDIRECT_MESSAGE

        # 5. If message has off-topic keyword AND health keyword, check if off-topic command dominates
        if has_off_topic_keyword and has_health_keyword:
            command_patterns = [
                r"write\s+(python|code|script|app|program)",
                r"solve\s+(math|equation)",
                r"tell\s+me\s+a\s+joke",
                r"who\s+won",
                r"how\s+to\s+code",
                r"explain\s+(array|pointer|code|function)",
            ]
            if any(re.search(p, lower_msg) for p in command_patterns):
                return False, cls.OFF_TOPIC_REDIRECT_MESSAGE

        # 6. Check for general health inquiry patterns
        health_inquiry_patterns = [
            r"why\s+am\s+i", r"why\s+do\s+i", r"is\s+it\s+normal", r"can\s+stress",
            r"how\s+to\s+(feel|sleep|relax|manage|improve|lower|reduce|boost|heal|treat)",
            r"what\s+is\s+(stress|hrv|bpm|gsr|eda|vagus|vagal|wellness|anxiety|depression|sleep|hygiene|somatic)",
            r"how\s+much\s+(water|sleep|exercise)",
            r"should\s+i\s+(see|go\s+to|consult)\s+a\s+doctor", r"feeling\s+(sick|tired|stressed|anxious|pain)",
        ]
        has_health_pattern = any(re.search(p, lower_msg) for p in health_inquiry_patterns)

        # 7. Final verdict
        if has_health_keyword:
            return True, None

        if has_health_pattern and not has_off_topic_keyword:
            return True, None

        # Block any query that lacks clear health/wellness context
        return False, cls.OFF_TOPIC_REDIRECT_MESSAGE
