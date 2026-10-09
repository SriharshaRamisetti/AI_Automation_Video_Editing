"""
clip_selector.py

Animation Clip Selection Engine
-------------------------------

Responsibilities:

1. Load the scene plan.
2. Load the animation library database.
3. Compare scene keywords with animation tags.
4. Rank matching animations.
5. Select the best clip for each scene.
6. Save the updated scene plan.

This module does NOT edit videos.

It only decides:

    "Which animation should be used for this scene?"
"""

import json
from pathlib import Path

import config


# ============================================================
# PATHS
# ============================================================

BASE_DIR = config.BASE_DIR

DATABASE_DIR = config.DATABASE_DIR

ANIMATIONS_DATABASE = (
    config.ANIMATIONS_DATABASE
)

PROJECTS_DIR = config.PROJECTS_DIR


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_CLIPS_PER_SCENE = 1

MINIMUM_MATCH_SCORE = 1


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    """
    Normalize text for keyword matching.

    Removes punctuation so:

        "what is Ego?"

    becomes:

        "what is ego"
    """

    if text is None:
        return ""

    text = str(text)

    text = text.lower()

    text = text.replace(
        "_",
        " "
    )

    text = text.replace(
        "-",
        " "
    )

    cleaned_characters = []

    for character in text:

        if (
            character.isalnum()
            or character.isspace()
        ):

            cleaned_characters.append(
                character
            )

    text = "".join(
        cleaned_characters
    )

    return " ".join(
        text.split()
    )


def split_words(text):
    """
    Split normalized text into words.
    """

    normalized = normalize_text(
        text
    )

    if not normalized:
        return []

    return normalized.split()


# ============================================================
# DATABASE
# ============================================================

def load_animation_database():
    """
    Load animations.json.
    """

    if not ANIMATIONS_DATABASE.exists():

        print()

        print(
            "WARNING: Animation database "
            "not found."
        )

        print()

        print(
            f"Expected file:\n"
            f"{ANIMATIONS_DATABASE}"
        )

        return []

    try:

        with open(
            ANIMATIONS_DATABASE,
            "r",
            encoding="utf-8"
        ) as file:

            database = json.load(
                file
            )

        return database.get(
            "animations",
            []
        )

    except Exception as error:

        print()

        print(
            "ERROR: Could not load "
            "animation database."
        )

        print(
            f"Reason: {error}"
        )

        return []


# ============================================================
# SCENE PLAN
# ============================================================

def load_scene_plan(
    plan_file
):
    """
    Load scene_plan.json.
    """

    plan_file = Path(
        plan_file
    )

    if not plan_file.exists():

        raise FileNotFoundError(
            f"Scene plan not found:\n"
            f"{plan_file}"
        )

    try:

        with open(
            plan_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    except Exception as error:

        raise RuntimeError(
            "Could not read scene plan.\n"
            f"Reason: {error}"
        )


# ============================================================
# ANIMATION SEARCH TEXT
# ============================================================

def get_animation_search_text(
    animation
):
    """
    Build searchable words for an animation.
    """

    words = set()

    fields = [
        animation.get(
            "name",
            ""
        ),
        animation.get(
            "filename",
            ""
        ),
        animation.get(
            "category",
            ""
        ),
        animation.get(
            "subcategory",
            ""
        )
    ]

    for field in fields:

        words.update(
            split_words(field)
        )

    tags = animation.get(
        "tags",
        []
    )

    for tag in tags:

        words.update(
            split_words(tag)
        )

    return words


# ============================================================
# SCENE SEARCH WORDS
# ============================================================

def get_scene_search_words(
    scene
):
    """
    Build searchable words for a scene.
    """

    words = set()

    fields = [
        scene.get(
            "title",
            ""
        ),
        scene.get(
            "description",
            ""
        ),
        scene.get(
            "emotion",
            ""
        )
    ]

    for field in fields:

        words.update(
            split_words(field)
        )

    keywords = scene.get(
        "keywords",
        []
    )

    for keyword in keywords:

        words.update(
            split_words(keyword)
        )

    return words


# ============================================================
# MATCH SCORE
# ============================================================

def calculate_match_score(
    scene,
    animation
):
    """
    Calculate how well an animation matches
    a scene.
    """

    scene_words = (
        get_scene_search_words(
            scene
        )
    )

    animation_words = (
        get_animation_search_text(
            animation
        )
    )

    if (
        not scene_words
        or not animation_words
    ):

        return 0

    score = 0

    matching_words = (
        scene_words.intersection(
            animation_words
        )
    )

    score += len(
        matching_words
    )

    # --------------------------------------------------------
    # CATEGORY MATCH
    # --------------------------------------------------------

    category = normalize_text(
        animation.get(
            "category",
            ""
        )
    )

    topic_type = normalize_text(
        scene.get(
            "topic_type",
            ""
        )
    )

    if (
        category
        and topic_type
        and category == topic_type
    ):

        score += 5

    # --------------------------------------------------------
    # EMOTION MATCH
    # --------------------------------------------------------

    scene_emotion = normalize_text(
        scene.get(
            "emotion",
            ""
        )
    )

    animation_subcategory = (
        normalize_text(
            animation.get(
                "subcategory",
                ""
            )
        )
    )

    animation_category = (
        normalize_text(
            animation.get(
                "category",
                ""
            )
        )
    )

    if scene_emotion:

        if (
            scene_emotion
            == animation_subcategory
        ):

            score += 8

        elif (
            scene_emotion
            == animation_category
        ):

            score += 5

    # --------------------------------------------------------
    # NAME MATCH
    # --------------------------------------------------------

    scene_title_words = set(
        split_words(
            scene.get(
                "title",
                ""
            )
        )
    )

    animation_name_words = set(
        split_words(
            animation.get(
                "name",
                ""
            )
        )
    )

    exact_name_matches = (
        scene_title_words.intersection(
            animation_name_words
        )
    )

    score += (
        len(exact_name_matches)
        * 3
    )

    return score


# ============================================================
# RANK ANIMATIONS
# ============================================================

def rank_animations_for_scene(
    scene,
    animations,
    minimum_score=MINIMUM_MATCH_SCORE
):
    """
    Rank animations for a scene.
    """

    ranked_results = []

    for animation in animations:

        score = (
            calculate_match_score(
                scene,
                animation
            )
        )

        if score < minimum_score:

            continue

        result = animation.copy()

        result[
            "match_score"
        ] = score

        ranked_results.append(
            result
        )

    ranked_results.sort(
        key=lambda item: (
            item.get(
                "match_score",
                0
            ),
            item.get(
                "duration",
                0
            )
        ),
        reverse=True
    )

    return ranked_results


# ============================================================
# DURATION MATCHING
# ============================================================

def calculate_duration_difference(
    clip_duration,
    scene_duration
):
    """
    Calculate duration difference.
    """

    try:

        clip_duration = float(
            clip_duration
        )

        scene_duration = float(
            scene_duration
        )

        return abs(
            clip_duration
            - scene_duration
        )

    except Exception:

        return 999999


def sort_by_duration(
    ranked_clips,
    scene_duration
):
    """
    Sort clips by match score first,
    then duration closeness.
    """

    return sorted(
        ranked_clips,
        key=lambda clip: (
            -clip.get(
                "match_score",
                0
            ),
            calculate_duration_difference(
                clip.get(
                    "duration",
                    0
                ),
                scene_duration
            )
        )
    )


# ============================================================
# BEST CLIP
# ============================================================

def select_best_clip(
    scene,
    animations
):
    """
    Select the best matching clip.
    """

    ranked_clips = (
        rank_animations_for_scene(
            scene,
            animations
        )
    )

    if not ranked_clips:

        return None

    scene_duration = (
        scene.get(
            "duration",
            5
        )
    )

    ranked_clips = (
        sort_by_duration(
            ranked_clips,
            scene_duration
        )
    )

    return ranked_clips[0]


# ============================================================
# MULTIPLE CLIPS
# ============================================================

def select_multiple_clips(
    scene,
    animations,
    number_of_clips=DEFAULT_CLIPS_PER_SCENE
):
    """
    Select multiple matching clips.
    """

    ranked_clips = (
        rank_animations_for_scene(
            scene,
            animations
        )
    )

    if not ranked_clips:

        return []

    scene_duration = float(
        scene.get(
            "duration",
            5
        )
    )

    ranked_clips = (
        sort_by_duration(
            ranked_clips,
            scene_duration
        )
    )

    selected = []

    used_ids = set()

    for clip in ranked_clips:

        clip_id = clip.get(
            "id"
        )

        if clip_id in used_ids:

            continue

        selected.append(
            clip
        )

        used_ids.add(
            clip_id
        )

        if (
            len(selected)
            >= number_of_clips
        ):

            break

    return selected


# ============================================================
# ASSIGN CLIPS
# ============================================================

def assign_clips_to_scenes(
    scene_plan,
    animations
):
    """
    Assign best animation to every scene.
    """

    scenes = scene_plan.get(
        "scenes",
        []
    )

    if not scenes:

        print(
            "WARNING: No scenes found."
        )

        return scene_plan

    print()

    print("=" * 70)

    print(
        "SELECTING ANIMATION CLIPS"
    )

    print("=" * 70)

    for scene in scenes:

        print()

        print(
            f"Scene "
            f"{scene.get('scene_id')}: "
            f"{scene.get('title')}"
        )

        best_clip = (
            select_best_clip(
                scene,
                animations
            )
        )

        if best_clip is None:

            print(
                "  No matching "
                "animation found."
            )

            scene[
                "clip_id"
            ] = None

            scene[
                "clip_path"
            ] = None

            scene[
                "clip_name"
            ] = None

            scene[
                "clip_score"
            ] = 0

            continue

        scene[
            "clip_id"
        ] = best_clip.get(
            "id"
        )

        scene[
            "clip_path"
        ] = best_clip.get(
            "path"
        )

        scene[
            "clip_name"
        ] = best_clip.get(
            "name"
        )

        scene[
            "clip_score"
        ] = best_clip.get(
            "match_score",
            0
        )

        scene[
            "clip_duration"
        ] = best_clip.get(
            "duration",
            0
        )

        print(
            f"  Selected: "
            f"{best_clip.get('filename')}"
        )

        print(
            f"  Score: "
            f"{best_clip.get('match_score', 0)}"
        )

        print(
            f"  Duration: "
            f"{best_clip.get('duration', 0)} sec"
        )

    return scene_plan


# ============================================================
# SAVE
# ============================================================

def save_updated_scene_plan(
    scene_plan,
    original_plan_file
):
    """
    Save updated scene plan.
    """

    original_plan_file = Path(
        original_plan_file
    )

    with open(
        original_plan_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            scene_plan,
            file,
            indent=4,
            ensure_ascii=False
        )

    return original_plan_file


# ============================================================
# REPORT
# ============================================================

def create_selection_report(
    scene_plan
):
    """
    Create selection report.
    """

    report = []

    for scene in scene_plan.get(
        "scenes",
        []
    ):

        report.append({

            "scene_id":
                scene.get(
                    "scene_id"
                ),

            "scene_title":
                scene.get(
                    "title"
                ),

            "duration":
                scene.get(
                    "duration"
                ),

            "emotion":
                scene.get(
                    "emotion"
                ),

            "clip_id":
                scene.get(
                    "clip_id"
                ),

            "clip_name":
                scene.get(
                    "clip_name"
                ),

            "clip_path":
                scene.get(
                    "clip_path"
                ),

            "clip_score":
                scene.get(
                    "clip_score",
                    0
                )
        })

    return report


def print_selection_report(
    scene_plan
):
    """
    Print selection report.
    """

    report = (
        create_selection_report(
            scene_plan
        )
    )

    print()

    print("=" * 70)

    print(
        "CLIP SELECTION REPORT"
    )

    print("=" * 70)

    for item in report:

        print()

        print(
            f"Scene "
            f"{item['scene_id']}: "
            f"{item['scene_title']}"
        )

        print(
            f"  Required duration: "
            f"{item['duration']} sec"
        )

        print(
            f"  Emotion: "
            f"{item['emotion']}"
        )

        print(
            f"  Selected clip: "
            f"{item['clip_name']}"
        )

        print(
            f"  Score: "
            f"{item['clip_score']}"
        )

        print(
            f"  Path: "
            f"{item['clip_path']}"
        )


# ============================================================
# FIND SCENE PLAN
# ============================================================

def find_scene_plan(topic):
    """
    Locate scene_plan.json using the SAME
    normalization logic used by scene_engine.py.
    """

    folder_name = config.normalize_topic(
        topic
    )

    plan_file = (
        PROJECTS_DIR
        / folder_name
        / "scene_plan.json"
    )

    return plan_file


# ============================================================
# PROCESS TOPIC
# ============================================================

def process_topic(topic):
    """
    Complete clip-selection stage.
    """

    print()

    print("=" * 70)

    print(
        "AI VIDEO AUTOMATION"
    )

    print(
        "CLIP SELECTION ENGINE"
    )

    print("=" * 70)

    scene_plan_file = (
        find_scene_plan(
            topic
        )
    )

    print()

    print(
        "Looking for scene plan:"
    )

    print(
        scene_plan_file
    )

    if not scene_plan_file.exists():

        print()

        print(
            "ERROR: Scene plan "
            "does not exist."
        )

        print()

        print(
            f"Expected:\n"
            f"{scene_plan_file}"
        )

        print()

        print(
            "Run scene_engine.py first."
        )

        return None

    scene_plan = (
        load_scene_plan(
            scene_plan_file
        )
    )

    animations = (
        load_animation_database()
    )

    if not animations:

        print()

        print(
            "ERROR: Animation library "
            "is empty."
        )

        print()

        print(
            "Add animation files inside:"
        )

        print(
            f"{config.ANIMATION_LIBRARY_DIR}"
        )

        return None

    print()

    print(
        f"Animations available: "
        f"{len(animations)}"
    )

    scene_plan = (
        assign_clips_to_scenes(
            scene_plan,
            animations
        )
    )

    save_updated_scene_plan(
        scene_plan,
        scene_plan_file
    )

    print_selection_report(
        scene_plan
    )

    print()

    print("=" * 70)

    print(
        "CLIP SELECTION COMPLETED"
    )

    print("=" * 70)

    print()

    print(
        f"Updated file:\n"
        f"{scene_plan_file}"
    )

    print()

    return scene_plan


# ============================================================
# TEST
# ============================================================

def run_clip_selector_test():

    topic = "How to manage fear"

    process_topic(
        topic
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_clip_selector_test()
