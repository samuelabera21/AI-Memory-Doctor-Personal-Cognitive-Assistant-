from functools import lru_cache
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# NOTE: Continuous learning is planned but not implemented in this version.
# The current classifier is static and trained from the labeled SEED_DATA below.
CATEGORIES = ["activity", "decision", "idea", "mistake", "event", "goal", "habit", "emotion"]

SEED_DATA = [
    ("Today I studied Python for 2 hours", "activity"),
    ("I worked on my AI project", "activity"),
    ("I went to the gym in the morning", "activity"),
    ("I read a book about machine learning", "activity"),
    ("I practiced coding problems", "activity"),
    ("I studied data structures", "activity"),
    ("I learned about APIs", "activity"),
    ("I worked on backend development", "activity"),
    ("I revised my notes", "activity"),
    ("I completed my assignment", "activity"),
    ("I decided to wake up early", "decision"),
    ("I will start learning deep learning", "decision"),
    ("I chose to reduce social media usage", "decision"),
    ("I planned my study schedule", "decision"),
    ("I committed to daily exercise", "decision"),
    ("I decided to focus on AI", "decision"),
    ("I planned to improve my skills", "decision"),
    ("I decided to read every day", "decision"),
    ("I chose to eat healthy", "decision"),
    ("I decided to build a portfolio", "decision"),
    ("I thought about creating a startup", "idea"),
    ("I have an idea for a new app", "idea"),
    ("I imagined building a smart assistant", "idea"),
    ("I brainstormed project ideas", "idea"),
    ("I thought of improving my habits", "idea"),
    ("I came up with a business idea", "idea"),
    ("I thought of automating tasks", "idea"),
    ("I imagined a new feature for my app", "idea"),
    ("I thought about learning blockchain", "idea"),
    ("I had an idea for a chatbot", "idea"),
    ("I wasted time watching YouTube", "mistake"),
    ("I slept too late last night", "mistake"),
    ("I skipped my workout", "mistake"),
    ("I procrastinated on my work", "mistake"),
    ("I forgot to complete my task", "mistake"),
    ("I wasted my time gaming", "mistake"),
    ("I ignored my responsibilities", "mistake"),
    ("I delayed my work", "mistake"),
    ("I missed an important deadline", "mistake"),
    ("I did not follow my plan", "mistake"),
    ("I attended a meeting today", "event"),
    ("I went to my friend's wedding", "event"),
    ("I joined a seminar", "event"),
    ("I participated in a workshop", "event"),
    ("I had a family gathering", "event"),
    ("I attended an online class", "event"),
    ("I went to a conference", "event"),
    ("I attended a tech meetup", "event"),
    ("I joined a webinar", "event"),
    ("I attended a training session", "event"),
    ("I want to become a machine learning expert", "goal"),
    ("My goal is to build an AI startup", "goal"),
    ("I aim to improve my coding skills", "goal"),
    ("I want to get a job in tech", "goal"),
    ("I plan to finish my project this month", "goal"),
    ("I want to learn deep learning", "goal"),
    ("I aim to wake up early daily", "goal"),
    ("I want to improve my health", "goal"),
    ("My goal is to study 4 hours daily", "goal"),
    ("I plan to master Python", "goal"),
    ("I wake up at 6 AM every day", "habit"),
    ("I drink coffee every morning", "habit"),
    ("I check my phone frequently", "habit"),
    ("I study at night regularly", "habit"),
    ("I go for a walk every evening", "habit"),
    ("I exercise daily", "habit"),
    ("I read before sleeping", "habit"),
    ("I use social media a lot", "habit"),
    ("I review my notes daily", "habit"),
    ("I code every day", "habit"),
    ("I felt happy today", "emotion"),
    ("I was stressed about my work", "emotion"),
    ("I felt motivated to study", "emotion"),
    ("I was feeling tired", "emotion"),
    ("I felt excited about my project", "emotion"),
    ("I felt frustrated with coding", "emotion"),
    ("I was anxious about exams", "emotion"),
    ("I felt proud of my progress", "emotion"),
    ("I was feeling lazy today", "emotion"),
    ("I felt confident today", "emotion"),
]


@lru_cache(maxsize=1)
def get_classifier() -> Pipeline:
    # Static model initialization: no automatic runtime retraining is triggered.
    x = [row[0] for row in SEED_DATA]
    y = [row[1] for row in SEED_DATA]

    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, strip_accents="unicode")),
            ("clf", LogisticRegression(max_iter=1200, class_weight="balanced")),
        ]
    )
    model.fit(x, y)
    return model


def predict_memory_type(text: str) -> str:
    model = get_classifier()
    pred = model.predict([text])[0]
    return pred if pred in CATEGORIES else "activity"


def evaluate_seed_accuracy() -> float:
    model = get_classifier()
    x = [row[0] for row in SEED_DATA]
    y = [row[1] for row in SEED_DATA]
    return float(model.score(x, y))


def update_model_with_new_data(new_samples: list):
    """
    Placeholder for future continuous learning.

    This function will:
    - Accept new labeled user data
    - Retrain or fine-tune the classifier
    - Update the model without full restart

    Currently NOT implemented.
    """
    pass
