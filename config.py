"""
config.py

Central Configuration
---------------------

This file contains the common configuration used by
the AI Video Automation system.

All project/topic folder names should be generated
through the functions in this file so every module
uses the exact same path convention.
"""

from pathlib import Path
import re


# ============================================================
# BASE DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENGINE_DIR = BASE_DIR / "engine"

DATABASE_DIR = BASE_DIR / "database"

PROJECTS_DIR = BASE_DIR / "projects"

OUTPUT_DIR = BASE_DIR / "output"

ANIMATION_LIBRARY_DIR = (
    BASE_DIR / "animation_library"
)


# ============================================================
# DATABASE
# ============================================================

ANIMATIONS_DATABASE = (
    DATABASE_DIR / "animations.json"
)


# ============================================================
# VIDEO SETTINGS
# ============================================================

VIDEO_WIDTH = 1080

VIDEO_HEIGHT = 1920

VIDEO_FPS = 30

VIDEO_ASPECT_RATIO = "9:16"

VIDEO_CODEC = "libx264"

AUDIO_CODEC = "aac"

VIDEO_PRESET = "medium"

VIDEO_CRF = 18

PIXEL_FORMAT = "yuv420p"


# ============================================================
# AUDIO SETTINGS
# ============================================================

VOICEOVER_VOLUME = 1.0

BACKGROUND_MUSIC_VOLUME = 0.20

SOUND_EFFECT_VOLUME = 0.50

AUDIO_BITRATE = "192k"


# ============================================================
# TRANSITIONS
# ============================================================

DEFAULT_TRANSITION = "fade"

DEFAULT_TRANSITION_DURATION = 0.4


# ============================================================
# SUBTITLES
# ============================================================

SUBTITLE_FONT = "Arial"

SUBTITLE_FONT_SIZE = 18

SUBTITLE_BOLD = True

SUBTITLE_OUTLINE = 3

SUBTITLE_SHADOW = 1

SUBTITLE_ALIGNMENT = 2

SUBTITLE_MARGIN_VERTICAL = 120


# ============================================================
# SCENE SETTINGS
# ============================================================

DEFAULT_SCENE_DURATION = 5

MIN_SCENE_DURATION = 2

MAX_SCENE_DURATION = 15


# ============================================================
# SUPPORTED VIDEO FILES
# ============================================================

SUPPORTED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".m4v"
}


# ============================================================
# SUPPORTED AUDIO FILES
# ============================================================

SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
    ".flac"
}


# ============================================================
# OUTPUT FILENAMES
# ============================================================

FINAL_VIDEO_FILENAME = "final_video.mp4"

BASE_VIDEO_FILENAME = "base_video.mp4"

TRANSITION_VIDEO_FILENAME = (
    "transition_video.mp4"
)

EFFECTS_VIDEO_FILENAME = (
    "effects_video.mp4"
)

AUDIO_VIDEO_FILENAME = (
    "audio_video.mp4"
)

SUBTITLE_FILENAME = "subtitles.srt"


# ============================================================
# TOPIC NORMALIZATION
# ============================================================

def normalize_topic(topic):
    """
    Convert a topic into a safe, consistent folder name.

    Examples:

        How to manage fear
        ->
        how_to_manage_fear

        what is Ego?
        ->
        what_is_ego

        How-to-control anger!
        ->
        how_to_control_anger

    IMPORTANT:
    Every module should use this function when
    constructing project/output paths.
    """

    if topic is None:
        return ""

    topic = str(topic).strip().lower()

    # Replace underscores and hyphens with spaces.
    topic = topic.replace("_", " ")
    topic = topic.replace("-", " ")

    # Remove punctuation and special characters.
    topic = re.sub(
        r"[^a-z0-9\s]",
        " ",
        topic
    )

    # Remove duplicate whitespace.
    topic = re.sub(
        r"\s+",
        " ",
        topic
    ).strip()

    # Convert spaces to underscores.
    return topic.replace(
        " ",
        "_"
    )


# ============================================================
# PROJECT DIRECTORY
# ============================================================

def get_project_directory(topic):
    """
    Return the project directory for a topic.

    Example:

        projects/what_is_ego/
    """

    folder_name = normalize_topic(
        topic
    )

    directory = (
        PROJECTS_DIR / folder_name
    )

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    return directory


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

def get_output_directory(topic):
    """
    Return the output directory for a topic.

    Example:

        output/what_is_ego/
    """

    folder_name = normalize_topic(
        topic
    )

    directory = (
        OUTPUT_DIR / folder_name
    )

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    return directory


# ============================================================
# PROJECT FILE HELPERS
# ============================================================

def get_scene_plan_file(topic):
    """
    Return scene_plan.json path.
    """

    return (
        get_project_directory(topic)
        / "scene_plan.json"
    )


def get_timeline_file(topic):
    """
    Return timeline.json path.
    """

    return (
        get_project_directory(topic)
        / "timeline.json"
    )


# ============================================================
# OUTPUT FILE HELPERS
# ============================================================

def get_base_video_file(topic):
    """
    Return base_video.mp4 path.
    """

    return (
        get_output_directory(topic)
        / BASE_VIDEO_FILENAME
    )


def get_transition_video_file(topic):
    """
    Return transition video path.
    """

    return (
        get_output_directory(topic)
        / TRANSITION_VIDEO_FILENAME
    )


def get_effects_video_file(topic):
    """
    Return effects video path.
    """

    return (
        get_output_directory(topic)
        / EFFECTS_VIDEO_FILENAME
    )


def get_audio_video_file(topic):
    """
    Return audio video path.
    """

    return (
        get_output_directory(topic)
        / AUDIO_VIDEO_FILENAME
    )


def get_subtitle_file(topic):
    """
    Return subtitles.srt path.
    """

    return (
        get_output_directory(topic)
        / SUBTITLE_FILENAME
    )


def get_final_video_file(topic):
    """
    Return final_video.mp4 path.
    """

    return (
        get_output_directory(topic)
        / FINAL_VIDEO_FILENAME
    )


# ============================================================
# DIRECTORY CREATION
# ============================================================

def create_required_directories():
    """
    Create all required project directories.
    """

    directories = [
        ENGINE_DIR,
        DATABASE_DIR,
        PROJECTS_DIR,
        OUTPUT_DIR,
        ANIMATION_LIBRARY_DIR
    ]

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True
        )


# ============================================================
# CONFIGURATION DISPLAY
# ============================================================

def print_configuration():

    print()

    print("=" * 70)

    print(
        "AI VIDEO AUTOMATION"
    )

    print(
        "CONFIGURATION"
    )

    print("=" * 70)

    print()

    print(
        f"Base directory: "
        f"{BASE_DIR}"
    )

    print(
        f"Animation library: "
        f"{ANIMATION_LIBRARY_DIR}"
    )

    print(
        f"Database: "
        f"{ANIMATIONS_DATABASE}"
    )

    print(
        f"Projects: "
        f"{PROJECTS_DIR}"
    )

    print(
        f"Output: "
        f"{OUTPUT_DIR}"
    )

    print()

    print(
        f"Video resolution: "
        f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}"
    )

    print(
        f"FPS: "
        f"{VIDEO_FPS}"
    )

    print(
        f"Aspect ratio: "
        f"{VIDEO_ASPECT_RATIO}"
    )

    print()

    print(
        f"Video codec: "
        f"{VIDEO_CODEC}"
    )

    print(
        f"Audio codec: "
        f"{AUDIO_CODEC}"
    )

    print()

    print("=" * 70)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    create_required_directories()

    print_configuration()

    test_topics = [
        "How to manage fear",
        "what is Ego?",
        "How-to-control anger!"
    ]

    print()

    print("TOPIC NORMALIZATION TEST")
    print("-" * 70)

    for topic in test_topics:

        print()

        print(
            f"Original: "
            f"{topic}"
        )

        print(
            f"Normalized: "
            f"{normalize_topic(topic)}"
        )

        print(
            f"Project: "
            f"{get_project_directory(topic)}"
        )

        print(
            f"Output: "
            f"{get_output_directory(topic)}"
        )

    print()
