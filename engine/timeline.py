"""
timeline.py

Timeline Manager
----------------

Responsibilities:
1. Load the scene plan.
2. Read the selected clips.
3. Create the video timeline.
4. Calculate start/end times for every scene.
5. Store transition information.
6. Store effect information.
7. Store audio placeholders.
8. Save the timeline as timeline.json.

This file does NOT render or edit the video.
"""

import json
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROJECTS_DIR = BASE_DIR / "projects"


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_FPS = 30

DEFAULT_WIDTH = 1080

DEFAULT_HEIGHT = 1920

DEFAULT_TRANSITION_DURATION = 0.4


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text):
    """
    Convert text into a normalized format.
    """

    if text is None:
        return ""

    text = str(text)

    text = text.lower()

    text = text.replace("-", " ")

    text = text.replace("_", " ")

    text = " ".join(text.split())

    return text


def topic_to_folder_name(topic):
    """
    Convert a topic into the project folder name.

    Example:

        How to manage fear

    becomes:

        how_to_manage_fear
    """

    topic = normalize_text(topic)

    return topic.replace(" ", "_")


# ============================================================
# FILE HELPERS
# ============================================================

def find_scene_plan(topic):
    """
    Find the scene_plan.json file for a topic.
    """

    folder_name = topic_to_folder_name(topic)

    project_folder = (
        PROJECTS_DIR / folder_name
    )

    scene_plan_file = (
        project_folder / "scene_plan.json"
    )

    return scene_plan_file


def load_scene_plan(scene_plan_file):
    """
    Load scene_plan.json.
    """

    scene_plan_file = Path(scene_plan_file)

    if not scene_plan_file.exists():

        raise FileNotFoundError(
            f"Scene plan not found:\n{scene_plan_file}"
        )

    with open(
        scene_plan_file,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# TIME HELPERS
# ============================================================

def format_time(seconds):
    """
    Convert seconds into HH:MM:SS.mmm format.

    Example:

        5.25

    becomes:

        00:00:05.250
    """

    seconds = float(seconds)

    hours = int(seconds // 3600)

    minutes = int(
        (seconds % 3600) // 60
    )

    remaining_seconds = (
        seconds % 60
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{remaining_seconds:06.3f}"
    )


# ============================================================
# SCENE DURATION
# ============================================================

def get_scene_duration(scene):
    """
    Get the required duration of a scene.
    """

    duration = scene.get(
        "duration",
        5
    )

    try:

        duration = float(duration)

    except (
        TypeError,
        ValueError
    ):

        duration = 5.0

    if duration <= 0:

        duration = 5.0

    return duration


# ============================================================
# CREATE TIMELINE SCENE
# ============================================================

def create_timeline_scene(
    scene,
    scene_number,
    start_time
):
    """
    Create one timeline entry.
    """

    duration = get_scene_duration(
        scene
    )

    end_time = (
        start_time + duration
    )

    timeline_scene = {

        "timeline_id": (
            f"timeline_scene_{scene_number:03d}"
        ),

        "scene_id": scene.get(
            "scene_id",
            scene_number
        ),

        "scene_number": scene_number,

        "title": scene.get(
            "title",
            f"Scene {scene_number}"
        ),

        "description": scene.get(
            "description",
            ""
        ),

        "keywords": scene.get(
            "keywords",
            []
        ),

        "emotion": scene.get(
            "emotion",
            "neutral"
        ),

        # ----------------------------------------------------
        # TIMING
        # ----------------------------------------------------

        "start": round(
            start_time,
            3
        ),

        "end": round(
            end_time,
            3
        ),

        "duration": round(
            duration,
            3
        ),

        "start_timecode": format_time(
            start_time
        ),

        "end_timecode": format_time(
            end_time
        ),

        # ----------------------------------------------------
        # SELECTED ANIMATION
        # ----------------------------------------------------

        "clip": {

            "id": scene.get(
                "clip_id"
            ),

            "name": scene.get(
                "clip_name"
            ),

            "path": scene.get(
                "clip_path"
            ),

            "original_duration": scene.get(
                "clip_duration",
                0
            ),

            "start": 0.0,

            "end": round(
                duration,
                3
            )

        },

        # ----------------------------------------------------
        # TRANSITIONS
        # ----------------------------------------------------

        "transition_in": {

            "type": "fade",

            "duration": (
                DEFAULT_TRANSITION_DURATION
            )

        },

        "transition_out": {

            "type": "fade",

            "duration": (
                DEFAULT_TRANSITION_DURATION
            )

        },

        # ----------------------------------------------------
        # EFFECTS
        # ----------------------------------------------------

        "effects": [],

        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        "audio": {

            "voiceover": None,

            "music": None,

            "sound_effects": []

        },

        # ----------------------------------------------------
        # SUBTITLES
        # ----------------------------------------------------

        "subtitles": []

    }

    return timeline_scene


# ============================================================
# BUILD TIMELINE
# ============================================================

def build_timeline(scene_plan):
    """
    Convert the scene plan into a complete timeline.
    """

    scenes = scene_plan.get(
        "scenes",
        []
    )

    if not scenes:

        raise ValueError(
            "No scenes found in scene plan."
        )

    timeline = []

    current_time = 0.0

    for scene_number, scene in enumerate(
        scenes,
        start=1
    ):

        timeline_scene = create_timeline_scene(
            scene,
            scene_number,
            current_time
        )

        timeline.append(
            timeline_scene
        )

        current_time = (
            timeline_scene["end"]
        )

    return timeline, current_time


# ============================================================
# SET FIRST/LAST TRANSITIONS
# ============================================================

def configure_transitions(timeline):
    """
    Configure transitions.

    First scene:
        Fade from black.

    Middle scenes:
        Fade in/out.

    Last scene:
        Fade to black.
    """

    if not timeline:

        return timeline

    # First scene

    timeline[0]["transition_in"] = {

        "type": "fade_from_black",

        "duration": DEFAULT_TRANSITION_DURATION

    }

    # Last scene

    timeline[-1]["transition_out"] = {

        "type": "fade_to_black",

        "duration": DEFAULT_TRANSITION_DURATION

    }

    return timeline


# ============================================================
# ADD DEFAULT EFFECTS
# ============================================================

def add_default_effects(timeline):
    """
    Add basic effect instructions according to emotion.

    The actual effects will be processed later by
    effects.py.
    """

    for scene in timeline:

        emotion = normalize_text(
            scene.get(
                "emotion",
                "neutral"
            )
        )

        effects = []

        if emotion == "fear":

            effects.append({
                "type": "zoom",
                "intensity": 0.05
            })

            effects.append({
                "type": "vignette",
                "intensity": 0.20
            })

        elif emotion == "anxiety":

            effects.append({
                "type": "camera_shake",
                "intensity": 0.03
            })

        elif emotion == "anger":

            effects.append({
                "type": "zoom",
                "intensity": 0.08
            })

        elif emotion == "sadness":

            effects.append({
                "type": "slow_zoom",
                "intensity": 0.03
            })

        elif emotion == "confidence":

            effects.append({
                "type": "slow_zoom_in",
                "intensity": 0.04
            })

        elif emotion == "motivation":

            effects.append({
                "type": "slow_zoom_in",
                "intensity": 0.05
            })

        elif emotion == "calm":

            effects.append({
                "type": "slow_zoom",
                "intensity": 0.02
            })

        scene["effects"] = effects

    return timeline


# ============================================================
# ADD AUDIO STRUCTURE
# ============================================================

def add_audio_structure(timeline):
    """
    Create placeholders for the audio engine.

    Actual audio files will be assigned later.
    """

    for scene in timeline:

        scene["audio"] = {

            "voiceover": {

                "file": None,

                "start": scene["start"],

                "end": scene["end"]

            },

            "music": {

                "file": None,

                "start": scene["start"],

                "end": scene["end"],

                "volume": 0.20

            },

            "sound_effects": []

        }

    return timeline


# ============================================================
# ADD SUBTITLE STRUCTURE
# ============================================================

def add_subtitle_structure(timeline):
    """
    Create an empty subtitle structure.

    subtitle_engine.py will populate this later.
    """

    for scene in timeline:

        scene["subtitles"] = []

    return timeline


# ============================================================
# VALIDATE TIMELINE
# ============================================================

def validate_timeline(timeline):
    """
    Check whether scenes are sequential and valid.
    """

    errors = []

    if not timeline:

        errors.append(
            "Timeline is empty."
        )

        return errors

    previous_end = 0.0

    for scene in timeline:

        start = float(
            scene["start"]
        )

        end = float(
            scene["end"]
        )

        duration = float(
            scene["duration"]
        )

        # Invalid duration

        if duration <= 0:

            errors.append(
                f"Scene {scene['scene_number']} "
                f"has invalid duration."
            )

        # Invalid timing

        if end <= start:

            errors.append(
                f"Scene {scene['scene_number']} "
                f"has invalid timing."
            )

        # Gap

        if start > previous_end + 0.001:

            errors.append(
                f"Gap detected before "
                f"scene {scene['scene_number']}."
            )

        # Overlap

        if start < previous_end - 0.001:

            errors.append(
                f"Overlap detected at "
                f"scene {scene['scene_number']}."
            )

        previous_end = end

    return errors


# ============================================================
# CREATE TIMELINE PROJECT
# ============================================================

def create_timeline_project(scene_plan):
    """
    Create the complete timeline project.
    """

    timeline, total_duration = build_timeline(
        scene_plan
    )

    timeline = configure_transitions(
        timeline
    )

    timeline = add_default_effects(
        timeline
    )

    timeline = add_audio_structure(
        timeline
    )

    timeline = add_subtitle_structure(
        timeline
    )

    errors = validate_timeline(
        timeline
    )

    project = {

        "version": "1.0",

        "topic": scene_plan.get(
            "topic",
            ""
        ),

        "topic_type": scene_plan.get(
            "topic_type",
            "general"
        ),

        "primary_emotion": scene_plan.get(
            "primary_emotion",
            "neutral"
        ),

        "video": {

            "width": DEFAULT_WIDTH,

            "height": DEFAULT_HEIGHT,

            "fps": DEFAULT_FPS,

            "aspect_ratio": "9:16"

        },

        "total_duration": round(
            total_duration,
            3
        ),

        "total_duration_timecode": format_time(
            total_duration
        ),

        "scene_count": len(
            timeline
        ),

        "timeline": timeline,

        "validation": {

            "valid": len(errors) == 0,

            "errors": errors

        }

    }

    return project


# ============================================================
# SAVE TIMELINE
# ============================================================

def save_timeline(
    project,
    topic
):
    """
    Save timeline.json inside the project folder.
    """

    folder_name = topic_to_folder_name(
        topic
    )

    project_folder = (
        PROJECTS_DIR / folder_name
    )

    project_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    timeline_file = (
        project_folder / "timeline.json"
    )

    with open(
        timeline_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            project,
            file,
            indent=4,
            ensure_ascii=False
        )

    return timeline_file


# ============================================================
# PRINT TIMELINE
# ============================================================

def print_timeline(project):
    """
    Display the generated timeline.
    """

    print()

    print("=" * 70)

    print("VIDEO TIMELINE")

    print("=" * 70)

    print()

    print(
        f"Topic: {project['topic']}"
    )

    print(
        f"Resolution: "
        f"{project['video']['width']}x"
        f"{project['video']['height']}"
    )

    print(
        f"FPS: "
        f"{project['video']['fps']}"
    )

    print(
        f"Total duration: "
        f"{project['total_duration']} seconds"
    )

    print()

    for scene in project["timeline"]:

        print(
            f"Scene {scene['scene_number']}: "
            f"{scene['title']}"
        )

        print(
            f"  "
            f"{scene['start_timecode']}"
            f" → "
            f"{scene['end_timecode']}"
        )

        print(
            f"  Duration: "
            f"{scene['duration']} sec"
        )

        print(
            f"  Clip: "
            f"{scene['clip']['name']}"
        )

        print(
            f"  Emotion: "
            f"{scene['emotion']}"
        )

        print()


# ============================================================
# PROCESS TOPIC
# ============================================================

def process_topic(topic):
    """
    Generate timeline for a topic.
    """

    scene_plan_file = find_scene_plan(
        topic
    )

    if not scene_plan_file.exists():

        print()
        print(
            "ERROR: scene_plan.json was not found."
        )

        print()

        print(
            f"Expected file:"
        )

        print(
            scene_plan_file
        )

        print()

        print(
            "Run scene_engine.py first."
        )

        return None

    scene_plan = load_scene_plan(
        scene_plan_file
    )

    project = create_timeline_project(
        scene_plan
    )

    timeline_file = save_timeline(
        project,
        topic
    )

    print_timeline(
        project
    )

    print("=" * 70)

    print(
        "TIMELINE CREATED SUCCESSFULLY"
    )

    print("=" * 70)

    print()

    print(
        f"Saved to:"
    )

    print(
        timeline_file
    )

    print()

    if project["validation"]["valid"]:

        print(
            "Timeline validation: PASSED"
        )

    else:

        print(
            "Timeline validation: FAILED"
        )

        for error in project[
            "validation"
        ]["errors"]:

            print(
                f"  - {error}"
            )

    return project


# ============================================================
# TEST
# ============================================================

def run_timeline_test():

    topic = "How to manage fear"

    process_topic(
        topic
    )


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    run_timeline_test()
