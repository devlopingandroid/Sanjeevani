"""Sanjeevni AI Domain Scope Guard.

Deterministic backend security guard that restricts Sanjeevni AI strictly to
Health & Wellness domain topics while allowing natural emotional, stress,
sleep, and wellbeing conversations without making unnecessary off-topic LLM calls.
"""
import re
from typing import Tuple, Optional


class DomainGuardStatus:
    ALLOWED = "ALLOWED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


class DomainGuard:
    OFF_TOPIC_REDIRECT_MESSAGE = (
        "I'm Sanjeevni's health and wellness assistant. I can help with topics like "
        "stress, sleep, nutrition, exercise, wellness, and your available health data. "
        "Please ask me a health-related question."
    )

    AMBIGUOUS_CLARIFICATION_MESSAGE = (
        "Of course. Tell me a little more about what you've been experiencing. "
        "Have you been feeling more stressed, tired, worried, low, or having trouble sleeping lately?"
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
        "derivative", "integral", "homework", "math problem", "calculus equation",
        # History & Politics & Geography
        "president", "prime minister", "parliament", "democrat", "republican",
        "capital of", "geography", "world war", "history of",
        # Entertainment, Gaming & Celebrities
        "cinema", "hollywood", "bollywood", "video game", "playstation", "xbox",
        "nintendo", "fortnite", "minecraft", "pop star", "celebrity",
        "sports news", "cricket score", "football match", "nba", "messi", "ronaldo", "match",
        # Creative Writing & Entertainment Requests
        "tell me a joke", "tell a joke", "make me laugh", "write a poem",
        "write a story", "write a song", "write code", "write a script", "write python",
        # Finance & Legal
        "crypto", "bitcoin", "ethereum", "stock market", "investment",
        "lawsuit", "legal advice", "court case", "financial advice",
    ]

    # Explicit Health, Wellness, Stress & Emotional Keywords
    HEALTH_WELLNESS_KEYWORDS = [
        # Stress & Mental Wellness
        "stress", "stressed", "stressing", "anxiety", "anxious", "depressed", "depression",
        "burnout", "overwhelmed", "overwhelming", "panic", "calm", "relax", "relaxation",
        "mindful", "mindfulness", "meditation", "mental", "emotion", "emotional", "wellbeing",
        "wellness", "vagus", "vagal", "somatic", "nervous system", "coping", "tense", "tension",
        "pressure", "pressured",
        # Emotional States & Mood
        "feeling low", "feeling strange", "irritated", "irritating", "irritation", "unmotivated",
        "motivation", "feeling down", "gloomy", "sadness", "mood", "restless", "restlessness",
        "racing thoughts", "worrying", "worried", "worry", "worries",
        # Breathing & Somatic
        "breath", "breathing", "inhale", "exhale", "pranayama", "respiration",
        "diaphragm", "lungs", "hyperventilating",
        # Sleep & Rest & Fatigue
        "sleep", "sleeping", "slept", "insomnia", "tired", "fatigue", "sleepy", "bedtime",
        "nap", "circadian", "rest", "drowsy", "snoring", "apnea", "exhausted", "exhaustion",
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
        "recovery", "habit", "routine", "healthy routine", "energy", "take care",
        "protein", "calorie", "calories", "metabolism",
        # Sanjeevni context
        "sanjeevni", "health", "health data", "stress score", "biometric data"
    ]

    # Conversational Health & Emotion Regex Patterns
    CONVERSATIONAL_HEALTH_PATTERNS = [
        r"feel(ing)?\s+(stressed|overwhelmed|tense|low|strange|tired|anxious|restless|irritated|down|exhausted|sick|unmotivated|unlike\s+myself)",
        r"not\s+feeling\s+like\s+myself",
        r"mind\s+won'?t\s+stop",
        r"thoughts?\s+keep\s+racing",
        r"can'?t\s+(relax|sleep|concentrate|focus)",
        r"cannot\s+(relax|sleep)",
        r"worry(ing)?\s+about",
        r"sleeping\s+(badly|poorly|well)",
        r"waking\s+up\s+at\s+night",
        r"don'?t\s+have\s+much\s+energy",
        r"lack\s+of\s+(energy|motivation|sleep)",
        r"take\s+better\s+care\s+of\s+myself",
        r"healthy\s+routine",
        r"small\s+things\s+are\s+irritating\s+me",
        r"work\s+has\s+been\s+overwhelming",
        r"don'?t\s+know\s+why\s+i\s+feel",
        r"why\s+am\s+i", r"why\s+do\s+i", r"is\s+it\s+normal", r"can\s+stress",
        r"how\s+to\s+(feel|sleep|relax|manage|improve|lower|reduce|boost|heal|treat)",
        r"what\s+is\s+(stress|hrv|bpm|gsr|eda|vagus|vagal|wellness|anxiety|depression|sleep|hygiene|somatic)",
        r"how\s+much\s+(water|sleep|exercise)",
        r"should\s+i\s+(see|go\s+to|consult)\s+a\s+doctor",
    ]

    # Ambiguous Personal Wellbeing Statements (Personal open-ended state expressions)
    AMBIGUOUS_WELLBEING_PATTERNS = [
        r"i\s+don'?t\s+know\s+what'?s\s+(happening|wrong)\s+with\s+me",
        r"something\s+feels?\s+off",
        r"i\s+don'?t\s+feel\s+right",
        r"things?\s+have\s+been\s+different\s+lately",
        r"i\s+just\s+need\s+someone\s+to\s+talk\s+to",
        r"i\s+don'?t\s+know\s+how\s+to\s+explain\s+it",
    ]

    @classmethod
    def evaluate(cls, message: str) -> Tuple[str, Optional[str]]:
        """Evaluates whether a message is within the Health & Wellness domain.

        Returns:
            Tuple[str, Optional[str]]: (status, response_message)
            status can be DomainGuardStatus.ALLOWED, DomainGuardStatus.AMBIGUOUS, or DomainGuardStatus.BLOCKED.
        """
        if not message or not message.strip():
            return DomainGuardStatus.BLOCKED, cls.OFF_TOPIC_REDIRECT_MESSAGE

        lower_msg = message.lower().strip()

        # 1. Check for prompt injection attempts
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, lower_msg):
                return DomainGuardStatus.BLOCKED, cls.OFF_TOPIC_REDIRECT_MESSAGE

        # 2. Check for explicit off-topic phrases & keywords
        has_off_topic_keyword = False
        for kw in cls.OFF_TOPIC_KEYWORDS:
            pattern = r"\b" + re.escape(kw) + r"\b" if len(kw) <= 5 else re.escape(kw)
            if re.search(pattern, lower_msg):
                has_off_topic_keyword = True
                break

        # 3. Check for math equations like "17 x 25", "2+2=4", "solve 5*10"
        if re.search(r"\b\d+\s*[\*\+x×/]\s*\d+\b", lower_msg) or re.search(r"\bwhat\s+is\s+\d+", lower_msg):
            has_off_topic_keyword = True

        # 4. Check for health & wellness keywords
        has_health_keyword = False
        for kw in cls.HEALTH_WELLNESS_KEYWORDS:
            pattern = r"\b" + re.escape(kw) + r"\b" if len(kw) <= 4 else re.escape(kw)
            if re.search(pattern, lower_msg):
                has_health_keyword = True
                break

        # 5. Check for conversational health & emotion patterns
        has_conversational_pattern = any(
            re.search(p, lower_msg) for p in cls.CONVERSATIONAL_HEALTH_PATTERNS
        )

        # 6. Check for ambiguous personal state patterns
        has_ambiguous_pattern = any(
            re.search(p, lower_msg) for p in cls.AMBIGUOUS_WELLBEING_PATTERNS
        )

        # Rule A: If off-topic keyword exists and NO health keyword/pattern -> BLOCKED
        if has_off_topic_keyword and not (has_health_keyword or has_conversational_pattern):
            return DomainGuardStatus.BLOCKED, cls.OFF_TOPIC_REDIRECT_MESSAGE

        # Rule B: If off-topic command dominates even with health words -> BLOCKED
        if has_off_topic_keyword:
            command_patterns = [
                r"write\s+(python|code|script|app|program)",
                r"solve\s+(math|equation)",
                r"tell\s+me\s+a\s+joke",
                r"who\s+won",
                r"how\s+to\s+code",
                r"explain\s+(array|pointer|code|function)",
                r"capital\s+of",
            ]
            if any(re.search(p, lower_msg) for p in command_patterns):
                return DomainGuardStatus.BLOCKED, cls.OFF_TOPIC_REDIRECT_MESSAGE

        # Rule C: Explicit health keyword or conversational health pattern -> ALLOWED
        if has_health_keyword or has_conversational_pattern:
            return DomainGuardStatus.ALLOWED, None

        # Rule D: Ambiguous personal wellbeing state statement -> AMBIGUOUS
        if has_ambiguous_pattern:
            return DomainGuardStatus.AMBIGUOUS, cls.AMBIGUOUS_CLARIFICATION_MESSAGE

        # Rule E: Short general conversational opening (e.g. "hello", "hi sanjeevni") without off-topic terms -> AMBIGUOUS
        if not has_off_topic_keyword and len(lower_msg.split()) <= 4:
            return DomainGuardStatus.AMBIGUOUS, cls.AMBIGUOUS_CLARIFICATION_MESSAGE

        # Default fallback for completely unmatched queries without off-topic terms -> AMBIGUOUS
        if not has_off_topic_keyword:
            return DomainGuardStatus.AMBIGUOUS, cls.AMBIGUOUS_CLARIFICATION_MESSAGE

        return DomainGuardStatus.BLOCKED, cls.OFF_TOPIC_REDIRECT_MESSAGE
