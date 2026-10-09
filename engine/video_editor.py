"""
video_editor.py

Video Assembly Engine
---------------------

Responsibilities:

1. Load timeline.json.
2. Locate selected animation clips.
3. Prepare clips for the target format.
4. Trim clips to scene duration.
5. Resize clips to 1080x1920.
6. Assemble clips in timeline order.
7. Export a base video.

This file does NOT handle:
- transitions.py
- effects.py
- audio_engine.py
- subtitle_engine.py
- renderer.py

Those modules come later.
"""

from pathlib import Path
import json

from moviepy import (
    VideoFileClip,
    concatenate_videoclips
)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROJECTS_DIR = BASE_DIR / "projects"

OUTPUT_DIR = BASE_DIR / "output"

ANIMATION_LIBRARY_DIR = (
    BASE_DIR / "animation_library"
)


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
    Normalize text for folder names.
    """

    if text is None:

        return ""

    text = str(text)

    text = text.lower()

    text = text.replace(
        "-",
        " "
    )

    text = text.replace(
        "_",
        " "
    )

    return " ".join(
        text.split()
    )


def topic_to_folder_name(topic):
    """
    Convert topic into project folder name.
    """

    return normalize_text(
        topic
    ).replace(
        " ",
        "_"
    )


# ============================================================
# FIND TIMELINE
# ============================================================

def find_timeline(topic):
    """
    Find timeline.json for a topic.
    """

    folder_name = topic_to_folder_name(
        topic
    )

    timeline_file = (
        PROJECTS_DIR
        / folder_name
        / "timeline.json"
    )

    return timeline_file


# ============================================================
# LOAD TIMELINE
# ============================================================

def load_timeline(timeline_file):
    """
    Load timeline.json.
    """

    timeline_file = Path(
        timeline_file
    )

    if not timeline_file.exists():

        raise FileNotFoundError(
            f"Timeline not found:\n"
            f"{timeline_file}"
        )

    with open(
        timeline_file,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# RESOLVE CLIP PATH
# ============================================================

def resolve_clip_path(clip_path):
    """
    Convert the path stored in animations.json
    into an absolute path.

    The library stores paths relative to the
    main project folder.
    """

    if not clip_path:

        return None

    clip_path = Path(
        clip_path
    )

    # --------------------------------------------------------
    # Already absolute
    # --------------------------------------------------------

    if clip_path.is_absolute():

        return clip_path

    # --------------------------------------------------------
    # Relative to project root
    # --------------------------------------------------------

    full_path = (
        BASE_DIR / clip_path
    )

    return full_path


# ============================================================
# VALIDATE CLIP
# ============================================================

def validate_clip_path(clip_path):
    """
    Check whether the animation clip exists.
    """

    if not clip_path:

        return False

    path = resolve_clip_path(
        clip_path
    )

    if path is None:

        return False

    return path.exists()


# ============================================================
# GET SCENE CLIP
# ============================================================

def get_scene_clip_path(scene):
    """
    Extract the animation path from a timeline scene.
    """

    clip = scene.get(
        "clip",
        {}
    )

    if not isinstance(
        clip,
        dict
    ):

        return None

    return clip.get(
        "path"
    )


# ============================================================
# LOAD VIDEO CLIP
# ============================================================

def load_video_clip(
    clip_path,
    scene_duration
):
    """
    Load one animation clip.

    The clip is:

    1. Loaded.
    2. Resized to target resolution.
    3. Trimmed to required duration.
    4. Set to target FPS.
    """

    absolute_path = resolve_clip_path(
        clip_path
    )

    if absolute_path is None:

        raise FileNotFoundError(
            "Clip path is empty."
        )

    if not absolute_path.exists():

        raise FileNotFoundError(
            f"Animation clip not found:\n"
            f"{absolute_path}"
        )

    print(
        f"    Loading: "
        f"{absolute_path.name}"
    )

    clip = VideoFileClip(
        str(absolute_path)
    )

    # --------------------------------------------------------
    # Determine duration
    # --------------------------------------------------------

    original_duration = (
        float(clip.duration)
        if clip.duration
        else 0.0
    )

    required_duration = float(
        scene_duration
    )

    if required_duration <= 0:

        required_duration = (
            original_duration
        )

    # --------------------------------------------------------
    # Trim or loop
    # --------------------------------------------------------

    if original_duration >= required_duration:

        clip = clip.subclipped(
            0,
            required_duration
        )

    else:

        # ----------------------------------------------------
        # The clip is shorter than the scene.
        #
        # For now we use the clip itself.
        # Later we can implement intelligent looping.
        # ----------------------------------------------------

        print(
            "    WARNING: Clip is shorter "
            "than required scene duration."
        )

    # --------------------------------------------------------
    # Resize
    # --------------------------------------------------------

    clip = resize_to_vertical(
        clip
    )

    # --------------------------------------------------------
    # FPS
    # --------------------------------------------------------

    clip = clip.with_fps(
        TARGET_FPS
    )

    return clip


# ============================================================
# RESIZE TO VERTICAL VIDEO
# ============================================================

def resize_to_vertical(clip):
    """
    Convert a clip to 1080x1920.

    The clip keeps its aspect ratio.

    If the source is wider than 9:16,
    the center is cropped.

    If necessary, the clip is resized
    before cropping.
    """

    target_ratio = (
        TARGET_WIDTH /
        TARGET_HEIGHT
    )

    source_width = clip.w

    source_height = clip.h

    if source_width <= 0 or source_height <= 0:

        return clip

    source_ratio = (
        source_width /
        source_height
    )

    # --------------------------------------------------------
    # Source is wider than 9:16
    # --------------------------------------------------------

    if source_ratio > target_ratio:

        # Resize based on height

        clip = clip.resized(
            height=TARGET_HEIGHT
        )

        new_width = clip.w

        crop_width = TARGET_WIDTH

        x_center = new_width / 2

        x1 = max(
            0,
            int(
                x_center -
                crop_width / 2
            )
        )

        x2 = min(
            new_width,
            int(
                x_center +
                crop_width / 2
            )
        )

        clip = clip.cropped(
            x1=x1,
            x2=x2
        )

    # --------------------------------------------------------
    # Source is taller than 9:16
    # --------------------------------------------------------

    else:

        clip = clip.resized(
            width=TARGET_WIDTH
        )

        new_height = clip.h

        crop_height = TARGET_HEIGHT

        y_center = new_height / 2

        y1 = max(
            0,
            int(
                y_center -
                crop_height / 2
            )
        )

        y2 = min(
            new_height,
            int(
                y_center +
                crop_height / 2
            )
        )

        clip = clip.cropped(
            y1=y1,
            y2=y2
        )

    return clip


# ============================================================
# BUILD CLIP COLLECTION
# ============================================================

def build_clip_collection(timeline):
    """
    Load all clips in timeline order.
    """

    clips = []

    scenes = timeline.get(
        "timeline",
        []
    )

    if not scenes:

        raise ValueError(
            "Timeline contains no scenes."
        )

    print()

    print(
        "=" * 70
    )

    print(
        "LOADING VIDEO CLIPS"
    )

    print(
        "=" * 70
    )

    for scene in scenes:

        scene_number = scene.get(
            "scene_number"
        )

        scene_title = scene.get(
            "title",
            f"Scene {scene_number}"
        )

        scene_duration = float(
            scene.get(
                "duration",
                5
            )
        )

        clip_path = get_scene_clip_path(
            scene
        )

        print()

        print(
            f"Scene {scene_number}: "
            f"{scene_title}"
        )

        if not clip_path:

            raise FileNotFoundError(
                f"No clip assigned to "
                f"scene {scene_number}."
            )

        if not validate_clip_path(
            clip_path
        ):

            absolute_path = (
                resolve_clip_path(
                    clip_path
                )
            )

            raise FileNotFoundError(
                f"Clip for scene "
                f"{scene_number} does not exist:\n"
                f"{absolute_path}"
            )

        clip = load_video_clip(
            clip_path,
            scene_duration
        )

        clips.append(
            clip
        )

    return clips


# ============================================================
# CONCATENATE CLIPS
# ============================================================

def concatenate_clips(clips):
    """
    Combine all video clips sequentially.
    """

    if not clips:

        raise ValueError(
            "No video clips available."
        )

    print()

    print(
        "Combining video clips..."
    )

    final_clip = concatenate_videoclips(
        clips,
        method="compose"
    )

    final_clip = final_clip.with_fps(
        TARGET_FPS
    )

    return final_clip


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

def create_output_directory(topic):
    """
    Create output folder for the topic.
    """

    folder_name = topic_to_folder_name(
        topic
    )

    output_folder = (
        OUTPUT_DIR / folder_name
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return output_folder


# ============================================================
# EXPORT BASE VIDEO
# ============================================================

def export_base_video(
    video,
    topic
):
    """
    Export the assembled base video.

    This is not yet the final video.
    """

    output_folder = (
        create_output_directory(
            topic
        )
    )

    output_file = (
        output_folder
        / "base_video.mp4"
    )

    print()

    print(
        "Rendering base video..."
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
# CLOSE CLIPS
# ============================================================

def close_clips(clips):
    """
    Close individual MoviePy clips.
    """

    for clip in clips:

        try:

            clip.close()

        except Exception:

            pass


# ============================================================
# CLOSE VIDEO
# ============================================================

def close_video(video):
    """
    Close final MoviePy video.
    """

    if video is None:

        return

    try:

        video.close()

    except Exception:

        pass


# ============================================================
# PROCESS TOPIC
# ============================================================

def process_topic(topic):
    """
    Complete video assembly process.

    Flow:

        timeline.json
              ↓
        load clips
              ↓
        resize
              ↓
        trim
              ↓
        concatenate
              ↓
        base_video.mp4
    """

    print()

    print(
        "=" * 70
    )

    print(
        "AI VIDEO AUTOMATION"
    )

    print(
        "VIDEO EDITOR"
    )

    print(
        "=" * 70
    )

    timeline_file = find_timeline(
        topic
    )

    if not timeline_file.exists():

        print()

        print(
            "ERROR: timeline.json not found."
        )

        print()

        print(
            f"Expected:"
        )

        print(
            timeline_file
        )

        print()

        print(
            "Run timeline.py first."
        )

        return None

    video = None

    clips = []

    try:

        # ----------------------------------------------------
        # Load timeline
        # ----------------------------------------------------

        timeline = load_timeline(
            timeline_file
        )

        # ----------------------------------------------------
        # Load clips
        # ----------------------------------------------------

        clips = build_clip_collection(
            timeline
        )

        # ----------------------------------------------------
        # Concatenate
        # ----------------------------------------------------

        video = concatenate_clips(
            clips
        )

        # ----------------------------------------------------
        # Export
        # ----------------------------------------------------

        output_file = export_base_video(
            video,
            topic
        )

        print()

        print(
            "=" * 70
        )

        print(
            "VIDEO EDITOR COMPLETED"
        )

        print(
            "=" * 70
        )

        print()

        print(
            f"Base video:"
        )

        print(
            output_file
        )

        print()

        return output_file

    except Exception as error:

        print()

        print(
            "=" * 70
        )

        print(
            "VIDEO EDITOR ERROR"
        )

        print(
            "=" * 70
        )

        print()

        print(
            f"Error: {error}"
        )

        print()

        raise

    finally:

        close_clips(
            clips
        )

        close_video(
            video
        )


# ============================================================
# TEST
# ============================================================

def run_video_editor_test():

    topic = "How to manage fear"

    process_topic(
        topic
    )


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    run_video_editor_test()
