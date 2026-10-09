"""
effects.py

Visual Effects Engine
---------------------

Responsibilities:

1. Load timeline.json.
2. Load the transition-processed video clips.
3. Read effects assigned to each scene.
4. Apply visual effects.
5. Apply emotion-based visual styling.
6. Apply zoom effects.
7. Apply camera shake.
8. Apply vignette.
9. Apply brightness / contrast / saturation adjustments.
10. Export the effects-processed video.

This file does NOT handle:

- audio_engine.py
- subtitle_engine.py
- renderer.py

Those modules come later.
"""

from pathlib import Path
import json
import math

import numpy as np
from moviepy import VideoFileClip


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROJECTS_DIR = BASE_DIR / "projects"
OUTPUT_DIR = BASE_DIR / "output"


# ============================================================
# VIDEO SETTINGS
# ============================================================

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text):
    """
    Normalize text.
    """

    if text is None:
        return ""

    text = str(text)

    text = text.lower()

    text = text.replace("-", " ")
    text = text.replace("_", " ")

    return " ".join(text.split())


def topic_to_folder_name(topic):
    """
    Convert:

        How to manage fear

    into:

        how_to_manage_fear
    """

    return normalize_text(topic).replace(
        " ",
        "_"
    )


# ============================================================
# PROJECT PATHS
# ============================================================

def get_project_folder(topic):
    """
    Return the project folder.
    """

    return (
        PROJECTS_DIR
        / topic_to_folder_name(topic)
    )


def find_timeline(topic):
    """
    Locate timeline.json.
    """

    return (
        get_project_folder(topic)
        / "timeline.json"
    )


def find_transition_video(topic):
    """
    Locate the video produced by transitions.py.
    """

    return (
        OUTPUT_DIR
        / topic_to_folder_name(topic)
        / "transition_video.mp4"
    )


# ============================================================
# JSON
# ============================================================

def load_json(file_path):
    """
    Safely load JSON.
    """

    file_path = Path(file_path)

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found:\n{file_path}"
        )

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except json.JSONDecodeError as error:

        raise RuntimeError(
            f"Invalid JSON file:\n{file_path}\n"
            f"Reason: {error}"
        )


def load_timeline(topic):
    """
    Load the project's timeline.
    """

    timeline_file = find_timeline(
        topic
    )

    project = load_json(
        timeline_file
    )

    timeline = project.get(
        "timeline",
        []
    )

    if not timeline:

        raise ValueError(
            "timeline.json contains no scenes."
        )

    return project


# ============================================================
# NUMERIC HELPERS
# ============================================================

def safe_float(
    value,
    default=0.0
):
    """
    Safely convert a value to float.
    """

    try:

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return default


def clamp(
    value,
    minimum,
    maximum
):
    """
    Restrict a value to a range.
    """

    return max(
        minimum,
        min(
            maximum,
            value
        )
    )


# ============================================================
# EFFECT SETTINGS
# ============================================================

def get_effect_intensity(
    effect,
    default=0.05
):
    """
    Read effect intensity.
    """

    if not isinstance(
        effect,
        dict
    ):
        return default

    intensity = safe_float(
        effect.get(
            "intensity",
            default
        ),
        default
    )

    return max(
        0.0,
        intensity
    )


def get_effect_type(effect):
    """
    Read effect type.
    """

    if not isinstance(
        effect,
        dict
    ):
        return ""

    return normalize_text(
        effect.get(
            "type",
            ""
        )
    ).replace(
        " ",
        "_"
    )


# ============================================================
# VIDEO FRAME EFFECTS
# ============================================================

def zoom_frame(
    frame,
    scale
):
    """
    Apply a center zoom to a frame.

    The output maintains the original frame size.
    """

    if frame is None:
        return frame

    if scale <= 0:
        return frame

    height, width = frame.shape[:2]

    zoom_factor = 1.0 + scale

    new_width = int(
        width / zoom_factor
    )

    new_height = int(
        height / zoom_factor
    )

    new_width = max(
        2,
        min(
            width,
            new_width
        )
    )

    new_height = max(
        2,
        min(
            height,
            new_height
        )
    )

    x1 = (
        width - new_width
    ) // 2

    y1 = (
        height - new_height
    ) // 2

    cropped = frame[
        y1:y1 + new_height,
        x1:x1 + new_width
    ]

    # Resize using MoviePy's available
    # image resizing mechanism through
    # a simple nearest-neighbour fallback.

    y_indices = np.linspace(
        0,
        cropped.shape[0] - 1,
        height
    ).astype(int)

    x_indices = np.linspace(
        0,
        cropped.shape[1] - 1,
        width
    ).astype(int)

    resized = cropped[
        y_indices[:, None],
        x_indices[None, :]
    ]

    return resized


def shake_frame(
    frame,
    intensity,
    time_value
):
    """
    Apply a subtle deterministic
    camera shake.

    The movement is generated using
    sine/cosine functions instead of
    randomness so the render remains
    reproducible.
    """

    if frame is None:
        return frame

    height, width = frame.shape[:2]

    max_shift_x = int(
        width * intensity * 0.02
    )

    max_shift_y = int(
        height * intensity * 0.02
    )

    if max_shift_x <= 0 and max_shift_y <= 0:
        return frame

    shift_x = int(
        math.sin(
            time_value * 25
        )
        * max_shift_x
    )

    shift_y = int(
        math.cos(
            time_value * 31
        )
        * max_shift_y
    )

    result = np.zeros_like(
        frame
    )

    source_x1 = max(
        0,
        -shift_x
    )

    source_x2 = min(
        width,
        width - shift_x
    )

    source_y1 = max(
        0,
        -shift_y
    )

    source_y2 = min(
        height,
        height - shift_y
    )

    destination_x1 = max(
        0,
        shift_x
    )

    destination_x2 = (
        destination_x1
        + (
            source_x2
            - source_x1
        )
    )

    destination_y1 = max(
        0,
        shift_y
    )

    destination_y2 = (
        destination_y1
        + (
            source_y2
            - source_y1
        )
    )

    result[
        destination_y1:destination_y2,
        destination_x1:destination_x2
    ] = frame[
        source_y1:source_y2,
        source_x1:source_x2
    ]

    return result


def vignette_frame(
    frame,
    intensity
):
    """
    Apply a cinematic vignette.

    Darkens the corners while keeping
    the center brighter.
    """

    if frame is None:
        return frame

    intensity = clamp(
        intensity,
        0.0,
        1.0
    )

    if intensity <= 0:
        return frame

    height, width = frame.shape[:2]

    y, x = np.ogrid[
        :height,
        :width
    ]

    center_x = width / 2
    center_y = height / 2

    distance_x = (
        x - center_x
    ) / center_x

    distance_y = (
        y - center_y
    ) / center_y

    distance = np.sqrt(
        distance_x ** 2
        +
        distance_y ** 2
    )

    mask = 1.0 - (
        distance * intensity * 0.55
    )

    mask = np.clip(
        mask,
        0.0,
        1.0
    )

    result = (
        frame.astype(
            np.float32
        )
        *
        mask[..., None]
    )

    return np.clip(
        result,
        0,
        255
    ).astype(
        np.uint8
    )


def brightness_frame(
    frame,
    intensity
):
    """
    Adjust brightness.

    Positive values brighten.
    Negative values darken.
    """

    if frame is None:
        return frame

    intensity = clamp(
        intensity,
        -1.0,
        1.0
    )

    if intensity == 0:
        return frame

    adjustment = (
        intensity * 255
    )

    result = (
        frame.astype(
            np.float32
        )
        +
        adjustment
    )

    return np.clip(
        result,
        0,
        255
    ).astype(
        np.uint8
    )


def contrast_frame(
    frame,
    intensity
):
    """
    Adjust contrast.

    intensity:

        0.0 = unchanged
        0.2 = slightly stronger
        -0.2 = slightly flatter
    """

    if frame is None:
        return frame

    intensity = clamp(
        intensity,
        -1.0,
        1.0
    )

    factor = (
        1.0 + intensity
    )

    result = (
        frame.astype(
            np.float32
        )
        - 127.5
    ) * factor + 127.5

    return np.clip(
        result,
        0,
        255
    ).astype(
        np.uint8
    )


def saturation_frame(
    frame,
    intensity
):
    """
    Adjust saturation without requiring
    an additional image-processing library.
    """

    if frame is None:
        return frame

    intensity = clamp(
        intensity,
        -1.0,
        1.0
    )

    if intensity == 0:
        return frame

    image = frame.astype(
        np.float32
    )

    # RGB/BGR channels are treated equally
    # for luminance calculation.

    luminance = (
        0.299 * image[:, :, 0]
        +
        0.587 * image[:, :, 1]
        +
        0.114 * image[:, :, 2]
    )

    luminance = luminance[
        ...,
        None
    ]

    factor = (
        1.0 + intensity
    )

    result = (
        luminance
        +
        (
            image
            - luminance
        )
        * factor
    )

    return np.clip(
        result,
        0,
        255
    ).astype(
        np.uint8
    )


# ============================================================
# EFFECT APPLICATION
# ============================================================

def apply_single_effect(
    frame,
    effect,
    current_time,
    scene_duration
):
    """
    Apply one effect to one frame.
    """

    if not isinstance(
        effect,
        dict
    ):
        return frame

    effect_type = get_effect_type(
        effect
    )

    intensity = get_effect_intensity(
        effect
    )

    progress = 0.0

    if scene_duration > 0:

        progress = clamp(
            current_time
            / scene_duration,
            0.0,
            1.0
        )

    # --------------------------------------------------------
    # ZOOM
    # --------------------------------------------------------

    if effect_type == "zoom":

        amount = (
            intensity
            * progress
        )

        frame = zoom_frame(
            frame,
            amount
        )

    # --------------------------------------------------------
    # SLOW ZOOM
    # --------------------------------------------------------

    elif effect_type == "slow_zoom":

        amount = (
            intensity
            * progress
        )

        frame = zoom_frame(
            frame,
            amount
        )

    # --------------------------------------------------------
    # SLOW ZOOM IN
    # --------------------------------------------------------

    elif effect_type == "slow_zoom_in":

        amount = (
            intensity
            * progress
        )

        frame = zoom_frame(
            frame,
            amount
        )

    # --------------------------------------------------------
    # CAMERA SHAKE
    # --------------------------------------------------------

    elif effect_type == "camera_shake":

        frame = shake_frame(
            frame,
            intensity,
            current_time
        )

    # --------------------------------------------------------
    # VIGNETTE
    # --------------------------------------------------------

    elif effect_type == "vignette":

        frame = vignette_frame(
            frame,
            intensity
        )

    # --------------------------------------------------------
    # BRIGHTNESS
    # --------------------------------------------------------

    elif effect_type == "brightness":

        frame = brightness_frame(
            frame,
            intensity
        )

    # --------------------------------------------------------
    # CONTRAST
    # --------------------------------------------------------

    elif effect_type == "contrast":

        frame = contrast_frame(
            frame,
            intensity
        )

    # --------------------------------------------------------
    # SATURATION
    # --------------------------------------------------------

    elif effect_type == "saturation":

        frame = saturation_frame(
            frame,
            intensity
        )

    return frame


def apply_effects_to_clip(
    clip,
    effects,
    scene_duration
):
    """
    Apply all effects assigned to a scene.

    MoviePy calls this function for every frame.
    """

    if not effects:

        return clip

    valid_effects = [
        effect
        for effect in effects
        if isinstance(
            effect,
            dict
        )
    ]

    if not valid_effects:

        return clip

    def process_frame(
        get_frame,
        time_value
    ):

        frame = get_frame(
            time_value
        )

        for effect in valid_effects:

            frame = apply_single_effect(
                frame,
                effect,
                time_value,
                scene_duration
            )

        return frame

    return clip.transform(
        process_frame
    )


# ============================================================
# EMOTION EFFECTS
# ============================================================

def get_default_effects_for_emotion(
    emotion
):
    """
    Generate visual effects automatically
    from the scene emotion.

    These are defaults only.

    If timeline.json already contains
    effects, those effects take priority.
    """

    emotion = normalize_text(
        emotion
    )

    if emotion == "fear":

        return [
            {
                "type": "zoom",
                "intensity": 0.05
            },
            {
                "type": "vignette",
                "intensity": 0.20
            }
        ]

    if emotion == "anxiety":

        return [
            {
                "type": "camera_shake",
                "intensity": 0.03
            },
            {
                "type": "zoom",
                "intensity": 0.03
            }
        ]

    if emotion == "anger":

        return [
            {
                "type": "zoom",
                "intensity": 0.08
            },
            {
                "type": "contrast",
                "intensity": 0.10
            }
        ]

    if emotion == "sadness":

        return [
            {
                "type": "slow_zoom",
                "intensity": 0.03
            },
            {
                "type": "saturation",
                "intensity": -0.15
            }
        ]

    if emotion == "confidence":

        return [
            {
                "type": "slow_zoom_in",
                "intensity": 0.04
            },
            {
                "type": "contrast",
                "intensity": 0.05
            }
        ]

    if emotion == "motivation":

        return [
            {
                "type": "slow_zoom_in",
                "intensity": 0.05
            },
            {
                "type": "brightness",
                "intensity": 0.03
            }
        ]

    if emotion == "calm":

        return [
            {
                "type": "slow_zoom",
                "intensity": 0.02
            },
            {
                "type": "saturation",
                "intensity": -0.05
            }
        ]

    return []


# ============================================================
# EFFECT VALIDATION
# ============================================================

SUPPORTED_EFFECTS = {
    "zoom",
    "slow_zoom",
    "slow_zoom_in",
    "camera_shake",
    "vignette",
    "brightness",
    "contrast",
    "saturation"
}


def validate_effect(
    effect
):
    """
    Validate an effect dictionary.
    """

    if not isinstance(
        effect,
        dict
    ):

        return False

    effect_type = get_effect_type(
        effect
    )

    return effect_type in (
        SUPPORTED_EFFECTS
    )


def validate_scene_effects(
    scene
):
    """
    Return validation errors for a scene.
    """

    errors = []

    effects = scene.get(
        "effects",
        []
    )

    if effects is None:

        return errors

    if not isinstance(
        effects,
        list
    ):

        errors.append(
            "Effects must be a list."
        )

        return errors

    for effect in effects:

        if not validate_effect(
            effect
        ):

            errors.append(
                f"Unsupported effect: "
                f"{effect}"
            )

    return errors


# ============================================================
# SCENE EFFECT PLAN
# ============================================================

def get_scene_effects(
    scene
):
    """
    Get effects for a scene.

    Priority:

    1. Effects explicitly stored in
       timeline.json.
    2. Emotion-based defaults.
    """

    effects = scene.get(
        "effects"
    )

    if isinstance(
        effects,
        list
    ) and effects:

        return effects

    emotion = scene.get(
        "emotion",
        "neutral"
    )

    return get_default_effects_for_emotion(
        emotion
    )


# ============================================================
# APPLY EFFECTS TO VIDEO
# ============================================================

def apply_effects_to_video(
    video,
    timeline
):
    """
    Apply scene-specific effects.

    Because the complete video is already
    assembled, each scene's time range is
    processed independently.
    """

    if video is None:

        raise ValueError(
            "Video cannot be None."
        )

    if not timeline:

        return video

    processed_video = video

    print()
    print("=" * 70)
    print("APPLYING VISUAL EFFECTS")
    print("=" * 70)

    for scene in timeline:

        scene_number = scene.get(
            "scene_number",
            "unknown"
        )

        scene_start = safe_float(
            scene.get(
                "start",
                0
            )
        )

        scene_end = safe_float(
            scene.get(
                "end",
                scene_start
            )
        )

        scene_duration = (
            scene_end
            - scene_start
        )

        if scene_duration <= 0:

            continue

        effects = get_scene_effects(
            scene
        )

        print()
        print(
            f"Scene {scene_number}"
        )

        if not effects:

            print(
                "  Effects: none"
            )

            continue

        effect_names = []

        for effect in effects:

            effect_type = get_effect_type(
                effect
            )

            effect_names.append(
                effect_type
            )

        print(
            "  Effects: "
            +
            ", ".join(
                effect_names
            )
        )

        # ----------------------------------------------------
        # Extract scene
        # ----------------------------------------------------

        scene_clip = (
            processed_video.subclipped(
                scene_start,
                scene_end
            )
        )

        # ----------------------------------------------------
        # Apply effects
        # ----------------------------------------------------

        scene_clip = (
            apply_effects_to_clip(
                scene_clip,
                effects,
                scene_duration
            )
        )

        # ----------------------------------------------------
        # Replace the scene in the
        # complete video.
        # ----------------------------------------------------

        processed_video = (
            replace_video_segment(
                processed_video,
                scene_clip,
                scene_start,
                scene_end
            )
        )

    return processed_video


# ============================================================
# REPLACE VIDEO SEGMENT
# ============================================================

def replace_video_segment(
    original_video,
    replacement_clip,
    start_time,
    end_time
):
    """
    Replace a section of the original
    video with a processed clip.

    The timeline remains unchanged.
    """

    before = None
    after = None

    try:

        if start_time > 0:

            before = (
                original_video.subclipped(
                    0,
                    start_time
                )
            )

        if end_time < original_video.duration:

            after = (
                original_video.subclipped(
                    end_time,
                    original_video.duration
                )
            )

        parts = []

        if before is not None:

            parts.append(
                before
            )

        parts.append(
            replacement_clip
        )

        if after is not None:

            parts.append(
                after
            )

        from moviepy import (
            concatenate_videoclips
        )

        new_video = concatenate_videoclips(
            parts,
            method="compose"
        )

        new_video = new_video.with_fps(
            TARGET_FPS
        )

        return new_video

    except Exception:

        if before is not None:

            try:
                before.close()
            except Exception:
                pass

        if after is not None:

            try:
                after.close()
            except Exception:
                pass

        raise


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

def create_output_directory(
    topic
):
    """
    Create output/topic folder.
    """

    output_folder = (
        OUTPUT_DIR
        / topic_to_folder_name(
            topic
        )
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return output_folder


# ============================================================
# EXPORT
# ============================================================

def export_effects_video(
    video,
    topic
):
    """
    Export effects-processed video.
    """

    output_folder = (
        create_output_directory(
            topic
        )
    )

    output_file = (
        output_folder
        / "effects_video.mp4"
    )

    print()
    print(
        "Rendering effects video..."
    )

    video.write_videofile(
        str(output_file),
        fps=TARGET_FPS,
        codec="libx264",
        audio=False,
        preset="medium"
    )

    return output_file


# ============================================================
# RESOURCE CLEANUP
# ============================================================

def close_video(
    video
):
    """
    Safely close a MoviePy video.
    """

    if video is None:
        return

    try:

        video.close()

    except Exception:

        pass


# ============================================================
# MAIN PROCESS
# ============================================================

def process_topic(
    topic
):
    """
    Complete effects pipeline.

    Input:

        How to manage fear

    Reads:

        output/
        └── how_to_manage_fear/
            └── transition_video.mp4

    and:

        projects/
        └── how_to_manage_fear/
            └── timeline.json

    Produces:

        output/
        └── how_to_manage_fear/
            └── effects_video.mp4
    """

    print()
    print("=" * 70)
    print("AI VIDEO AUTOMATION")
    print("EFFECTS ENGINE")
    print("=" * 70)

    timeline_file = find_timeline(
        topic
    )

    transition_video = (
        find_transition_video(
            topic
        )
    )

    # --------------------------------------------------------
    # CHECK TIMELINE
    # --------------------------------------------------------

    if not timeline_file.exists():

        print()
        print(
            "ERROR: timeline.json not found."
        )

        print()
        print(
            f"Expected:\n{timeline_file}"
        )

        print()
        print(
            "Run timeline.py first."
        )

        return None

    # --------------------------------------------------------
    # CHECK TRANSITION VIDEO
    # --------------------------------------------------------

    if not transition_video.exists():

        print()
        print(
            "ERROR: transition_video.mp4 "
            "not found."
        )

        print()
        print(
            f"Expected:\n{transition_video}"
        )

        print()
        print(
            "Run transitions.py first."
        )

        return None

    video = None

    try:

        # ----------------------------------------------------
        # LOAD TIMELINE
        # ----------------------------------------------------

        project = load_timeline(
            topic
        )

        timeline = project.get(
            "timeline",
            []
        )

        if not timeline:

            raise ValueError(
                "No scenes found in timeline."
            )

        # ----------------------------------------------------
        # LOAD VIDEO
        # ----------------------------------------------------

        print()
        print(
            "Loading transition video:"
        )

        print(
            transition_video
        )

        video = VideoFileClip(
            str(
                transition_video
            )
        )

        video = video.with_fps(
            TARGET_FPS
        )

        # ----------------------------------------------------
        # APPLY EFFECTS
        # ----------------------------------------------------

        processed_video = (
            apply_effects_to_video(
                video,
                timeline
            )
        )

        # ----------------------------------------------------
        # EXPORT
        # ----------------------------------------------------

        output_file = (
            export_effects_video(
                processed_video,
                topic
            )
        )

        print()
        print("=" * 70)
        print(
            "EFFECTS ENGINE COMPLETED"
        )
        print("=" * 70)

        print()
        print(
            "Effects video:"
        )

        print(
            output_file
        )

        print()

        return output_file

    except Exception as error:

        print()
        print("=" * 70)
        print(
            "EFFECTS ENGINE ERROR"
        )
        print("=" * 70)

        print()
        print(
            f"Error: {error}"
        )

        print()

        raise

    finally:

        close_video(
            video
        )


# ============================================================
# TEST
# ============================================================

def run_effects_test():
    """
    Standalone test.

    Required before running:

        library.py
        scene_engine.py
        clip_selector.py
        timeline.py
        video_editor.py
        transitions.py
    """

    topic = "How to manage fear"

    process_topic(
        topic
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_effects_test()
