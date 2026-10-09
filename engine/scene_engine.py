"""
scene_engine.py

Scene Planning Engine
---------------------

Converts a topic into a structured video scene plan.

Example:

Input:
    "How to manage fear"

Output:
    [
        {
            "scene_id": 1,
            "title": "What is fear?",
            "description": "...",
            "keywords": [...],
            "emotion": "fear",
            "duration": 5
        },
        ...
    ]
"""

import re
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = BASE_DIR / "projects"


DEFAULT_SCENE_DURATION = 5


# ---------------------------------------------------------
# TEXT UTILITIES
# ---------------------------------------------------------

def normalize_text(text):
    """
    Normalize text for keyword processing.
    """

    text = str(text).lower()

    text = text.replace("-", " ")
    text = text.replace("_", " ")

    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_keywords(topic):
    """
    Extract basic keywords from the topic.

    This is intentionally simple for version 1.
    Later we can replace this with an AI/semantic keyword engine.
    """

    normalized = normalize_text(topic)

    words = normalized.split()

    stop_words = {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "to",
        "of",
        "in",
        "on",
        "for",
        "and",
        "or",
        "with",
        "how",
        "why",
        "what",
        "can",
        "do",
        "does",
        "you",
        "your",
        "we",
        "our",
        "i",
        "me"
    }

    keywords = []

    for word in words:

        if word in stop_words:
            continue

        if len(word) < 3:
            continue

        if word not in keywords:
            keywords.append(word)

    return keywords


# ---------------------------------------------------------
# TOPIC DETECTION
# ---------------------------------------------------------

def detect_topic_type(topic):
    """
    Detect the broad type of topic.

    This helps the scene planner choose an appropriate
    storytelling structure.
    """

    text = normalize_text(topic)

    if any(word in text for word in [
        "fear",
        "anxiety",
        "stress",
        "anger",
        "sadness",
        "emotion",
        "overthinking"
    ]):
        return "psychology"

    if any(word in text for word in [
        "krishna",
        "ram",
        "shiva",
        "buddha",
        "gita",
        "upanishad",
        "mythology",
        "philosophy"
    ]):
        return "philosophy"

    if any(word in text for word in [
        "mind",
        "brain",
        "memory",
        "habit",
        "behavior",
        "psychology"
    ]):
        return "psychology"

    if any(word in text for word in [
        "story",
        "journey",
        "life",
        "lesson"
    ]):
        return "story"

    return "general"


# ---------------------------------------------------------
# EMOTION DETECTION
# ---------------------------------------------------------

def detect_emotion(topic):
    """
    Detect the dominant emotional theme.
    """

    text = normalize_text(topic)

    emotion_map = {

        "fear": [
            "fear",
            "scared",
            "afraid",
            "frightened",
            "phobia"
        ],

        "anxiety": [
            "anxiety",
            "anxious",
            "panic",
            "worry"
        ],

        "anger": [
            "anger",
            "angry",
            "rage",
            "frustration"
        ],

        "sadness": [
            "sad",
            "sadness",
            "grief",
            "lonely",
            "loneliness"
        ],

        "confidence": [
            "confidence",
            "confident",
            "courage",
            "bravery"
        ],

        "motivation": [
            "motivation",
            "discipline",
            "success",
            "growth"
        ],

        "calm": [
            "peace",
            "calm",
            "relax",
            "meditation"
        ]
    }

    for emotion, words in emotion_map.items():

        for word in words:

            if word in text:
                return emotion

    return "neutral"


# ---------------------------------------------------------
# SCENE CREATION
# ---------------------------------------------------------

def create_scene(
    scene_id,
    title,
    description,
    keywords,
    emotion,
    duration=DEFAULT_SCENE_DURATION
):
    """
    Create one standardized scene dictionary.
    """

    return {
        "scene_id": scene_id,
        "title": title,
        "description": description,
        "keywords": keywords,
        "emotion": emotion,
        "duration": duration,
        "clip_id": None,
        "clip_path": None
    }


# ---------------------------------------------------------
# PSYCHOLOGY STRUCTURE
# ---------------------------------------------------------

def create_psychology_scenes(topic, keywords, emotion):
    """
    Create a psychology-focused storytelling structure.
    """

    topic_text = topic.strip()

    scenes = []

    scenes.append(
        create_scene(
            1,
            "The Problem",
            f"Introduce the problem of {topic_text}.",
            keywords + [emotion, "problem"],
            emotion,
            5
        )
    )

    scenes.append(
        create_scene(
            2,
            "What Is Happening?",
            f"Explain what is actually happening when someone experiences {topic_text}.",
            keywords + [emotion, "mind", "thinking"],
            emotion,
            6
        )
    )

    scenes.append(
        create_scene(
            3,
            "The Brain",
            f"Explain how the brain responds to {topic_text}.",
            keywords + [emotion, "brain", "stress"],
            emotion,
            6
        )
    )

    scenes.append(
        create_scene(
            4,
            "The Hidden Effect",
            f"Show how {topic_text} can affect everyday behavior.",
            keywords + [emotion, "behavior", "human"],
            emotion,
            6
        )
    )

    scenes.append(
        create_scene(
            5,
            "What To Do",
            f"Give practical steps for dealing with {topic_text}.",
            keywords + [emotion, "solution", "calm", "confidence"],
            "confidence",
            7
        )
    )

    scenes.append(
        create_scene(
            6,
            "The Takeaway",
            f"End with a memorable message about {topic_text}.",
            keywords + ["ending", "hope", "confidence", "motivation"],
            "motivation",
            5
        )
    )

    return scenes


# ---------------------------------------------------------
# PHILOSOPHY STRUCTURE
# ---------------------------------------------------------

def create_philosophy_scenes(topic, keywords, emotion):
    """
    Create a philosophy/mythology storytelling structure.
    """

    scenes = []

    scenes.append(
        create_scene(
            1,
            "The Question",
            f"Introduce the philosophical question behind {topic}.",
            keywords + ["question", "thinking"],
            emotion,
            6
        )
    )

    scenes.append(
        create_scene(
            2,
            "The Ancient Perspective",
            f"Introduce the philosophical perspective related to {topic}.",
            keywords + ["ancient", "philosophy", "wisdom"],
            emotion,
            7
        )
    )

    scenes.append(
        create_scene(
            3,
            "The Story",
            f"Use a story or philosophical example to explain {topic}.",
            keywords + ["story", "ancient", "wisdom"],
            emotion,
            8
        )
    )

    scenes.append(
        create_scene(
            4,
            "The Meaning",
            f"Explain the deeper meaning behind the teaching.",
            keywords + ["meaning", "truth", "wisdom"],
            "calm",
            7
        )
    )

    scenes.append(
        create_scene(
            5,
            "Modern Life",
            f"Connect the ancient idea to modern life.",
            keywords + ["modern", "life", "human"],
            emotion,
            7
        )
    )

    scenes.append(
        create_scene(
            6,
            "The Lesson",
            f"End with the central lesson of {topic}.",
            keywords + ["lesson", "wisdom", "motivation"],
            "calm",
            6
        )
    )

    return scenes


# ---------------------------------------------------------
# GENERAL STRUCTURE
# ---------------------------------------------------------

def create_general_scenes(topic, keywords, emotion):
    """
    Generic structure for topics that don't fall into
    psychology or philosophy.
    """

    scenes = []

    scenes.append(
        create_scene(
            1,
            "Introduction",
            f"Introduce the topic: {topic}.",
            keywords,
            emotion,
            5
        )
    )

    scenes.append(
        create_scene(
            2,
            "Understanding",
            f"Explain the basic idea behind {topic}.",
            keywords + ["understanding"],
            emotion,
            6
        )
    )

    scenes.append(
        create_scene(
            3,
            "Why It Matters",
            f"Explain why {topic} matters.",
            keywords + ["importance"],
            emotion,
            6
        )
    )

    scenes.append(
        create_scene(
            4,
            "Example",
            f"Give an example related to {topic}.",
            keywords + ["example", "human"],
            emotion,
            6
        )
    )

    scenes.append(
        create_scene(
            5,
            "Solution",
            f"Explain what someone can do about {topic}.",
            keywords + ["solution", "action"],
            "confidence",
            7
        )
    )

    scenes.append(
        create_scene(
            6,
            "Conclusion",
            f"End with the main lesson about {topic}.",
            keywords + ["ending", "lesson"],
            "motivation",
            5
        )
    )

    return scenes


# ---------------------------------------------------------
# MAIN SCENE PLANNER
# ---------------------------------------------------------

def generate_scene_plan(topic):
    """
    Generate a complete scene plan for a topic.
    """

    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty.")

    topic = topic.strip()

    keywords = extract_keywords(topic)

    topic_type = detect_topic_type(topic)

    emotion = detect_emotion(topic)

    if topic_type == "psychology":

        scenes = create_psychology_scenes(
            topic,
            keywords,
            emotion
        )

    elif topic_type == "philosophy":

        scenes = create_philosophy_scenes(
            topic,
            keywords,
            emotion
        )

    else:

        scenes = create_general_scenes(
            topic,
            keywords,
            emotion
        )

    total_duration = sum(
        scene["duration"]
        for scene in scenes
    )

    plan = {
        "topic": topic,
        "topic_type": topic_type,
        "primary_emotion": emotion,
        "keywords": keywords,
        "total_duration": total_duration,
        "scene_count": len(scenes),
        "scenes": scenes
    }

    return plan


# ---------------------------------------------------------
# SAVE PLAN
# ---------------------------------------------------------

def create_project_directory(topic):
    """
    Create a project folder for the topic.
    """

    safe_name = normalize_text(topic)

    safe_name = safe_name.replace(" ", "_")

    project_directory = PROJECTS_DIR / safe_name

    project_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    return project_directory


def save_scene_plan(plan):
    """
    Save the generated scene plan as JSON.
    """

    topic = plan["topic"]

    project_directory = create_project_directory(topic)

    plan_file = project_directory / "scene_plan.json"

    with open(
        plan_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            plan,
            file,
            indent=4,
            ensure_ascii=False
        )

    return plan_file


# ---------------------------------------------------------
# DISPLAY PLAN
# ---------------------------------------------------------

def print_scene_plan(plan):
    """
    Print the scene plan in a readable format.
    """

    print()
    print("=" * 70)
    print("SCENE PLAN")
    print("=" * 70)

    print()
    print(f"Topic: {plan['topic']}")
    print(f"Type: {plan['topic_type']}")
    print(f"Emotion: {plan['primary_emotion']}")
    print(f"Scenes: {plan['scene_count']}")
    print(f"Duration: {plan['total_duration']} seconds")

    print()

    for scene in plan["scenes"]:

        print(
            f"Scene {scene['scene_id']}: "
            f"{scene['title']}"
        )

        print(
            f"  Duration: "
            f"{scene['duration']} sec"
        )

        print(
            f"  Emotion: "
            f"{scene['emotion']}"
        )

        print(
            f"  Keywords: "
            f"{', '.join(scene['keywords'])}"
        )

        print(
            f"  Description: "
            f"{scene['description']}"
        )

        print()


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

def run_scene_engine_test():

    print()
    print("=" * 70)
    print("AI VIDEO AUTOMATION")
    print("SCENE ENGINE TEST")
    print("=" * 70)

    topic = "How to manage fear"

    plan = generate_scene_plan(topic)

    print_scene_plan(plan)

    plan_file = save_scene_plan(plan)

    print("=" * 70)
    print("SCENE PLAN SAVED")
    print("=" * 70)

    print()
    print(f"File: {plan_file}")
    print()


if __name__ == "__main__":
    run_scene_engine_test()
