"""
transitions.py

Transition Engine
-----------------

Responsibilities:

1. Load timeline.json.
2. Read transition settings for every scene.
3. Load the selected animation clips.
4. Apply transitions between scenes.
5. Apply fade-in/fade-out transitions.
6. Apply crossfade transitions when requested.
7. Preserve the target video format.
8. Export the transition-processed video.

This file does NOT handle:
- effects.py
- audio_engine.py
- subtitle_engine.py
- renderer.py

Those modules come later.
"""

from pathlib import Path
import json

from moviepy import VideoFileClip, concatenate_videoclips


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

DEFAULT_TRANSITION_DURATION = 0.4


# ============================================================
# TEXT / TOPIC HELPERS
# ============================================================

def normalize_text(text):
    """
    Normalize text so topic names can safely be converted
    into project folder names.
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

    return normalize_text(topic).replace(" ", "_")


# ============================================================
# TIMELINE
# ============================================================

def find_timeline(topic):
    """
    Locate the timeline.json file for a topic.
    """

    folder_name = topic_to_folder_name(topic)

    timeline_file = (
        PROJECTS_DIR
        / folder_name
        / "timeline.json"
    )

    return timeline_file


def load_timeline(timeline_file):
    """
    Load timeline.json.
    """

    timeline_file = Path(timeline_file)

    if not timeline_file.exists():
        raise FileNotFoundError(
            f"Timeline not found:\n{timeline_file}"
        )

    try:

        with open(
            timeline_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except json.JSONDecodeError as error:

        raise RuntimeError(
            "timeline.json contains invalid JSON.\n"
            f"Reason: {error}"
        )


# ============================================================
# PATH RESOLUTION
# ============================================================

def resolve_clip_path(clip_path):
    """
    Convert the relative animation path stored inside
    timeline.json into an absolute filesystem path.
    """

    if not clip_path:
        return None

    clip_path = Path(clip_path)

    if clip_path.is_absolute():
        return clip_path

    return BASE_DIR / clip_path


def validate_clip_path(clip_path):
    """
    Check whether an animation clip exists.
    """

    path = resolve_clip_path(clip_path)

    if path is None:
        return False

    return path.exists()


# ============================================================
# VIDEO RESIZING
# ============================================================

def resize_to_vertical(clip):
    """
    Convert any source video into:

        1080 x 1920

    while preserving the center of the original video.

    Landscape videos are center-cropped.

    Portrait videos are center-cropped if necessary.
    """

    target_ratio = TARGET_WIDTH / TARGET_HEIGHT

    source_width = clip.w
    source_height = clip.h

    if source_width <= 0 or source_height <= 0:
        return clip

    source_ratio = source_width / source_height

    # --------------------------------------------------------
    # LANDSCAPE / WIDER VIDEO
    # --------------------------------------------------------

    if source_ratio > target_ratio:

        clip = clip.resized(
            height=TARGET_HEIGHT
        )

        new_width = clip.w

        x_center = new_width / 2

        x1 = max(
            0,
            int(x_center - TARGET_WIDTH / 2)
        )

        x2 = min(
            new_width,
            int(x_center + TARGET_WIDTH / 2)
        )

        clip = clip.cropped(
            x1=x1,
            x2=x2
        )

    # --------------------------------------------------------
    # PORTRAIT / TALLER VIDEO
    # --------------------------------------------------------

    else:

        clip = clip.resized(
            width=TARGET_WIDTH
        )

        new_height = clip.h

        y_center = new_height / 2

        y1 = max(
            0,
            int(y_center - TARGET_HEIGHT / 2)
        )

        y2 = min(
            new_height,
            int(y_center + TARGET_HEIGHT / 2)
        )

        clip = clip.cropped(
            y1=y1,
            y2=y2
        )

    return clip


# ============================================================
# SCENE DURATION
# ============================================================

def get_scene_duration(scene):
    """
    Safely read scene duration.
    """

    try:

        duration = float(
            scene.get("duration", 5)
        )

    except (
        TypeError,
        ValueError
    ):

        duration = 5.0

    if duration <= 0:
        duration = 5.0

    return duration


# ============================================================
# TRANSITION DURATION
# ============================================================

def get_transition_duration(
    transition,
    scene_duration
):
    """
    Get a safe transition duration.

    Prevents a transition from becoming longer
    than the actual scene.
    """

    if not isinstance(transition, dict):
        return 0.0

    try:

        duration = float(
            transition.get(
                "duration",
                DEFAULT_TRANSITION_DURATION
            )
        )

    except (
        TypeError,
        ValueError
    ):

        duration = DEFAULT_TRANSITION_DURATION

    if duration <= 0:
        return 0.0

    # Never allow a transition to consume
    # the complete scene.

    maximum_duration = scene_duration / 2

    duration = min(
        duration,
        maximum_duration
    )

    return duration


# ============================================================
# LOAD SCENE CLIP
# ============================================================

def load_scene_clip(scene):
    """
    Load one scene's animation clip.

    The clip is:

    1. Validated.
    2. Trimmed to scene duration.
    3. Resized to 1080x1920.
    4. Converted to 30 FPS.
    """

    scene_number = scene.get(
        "scene_number",
        "unknown"
    )

    scene_title = scene.get(
        "title",
        f"Scene {scene_number}"
    )

    duration = get_scene_duration(scene)

    clip_information = scene.get(
        "clip",
        {}
    )

    if not isinstance(
        clip_information,
        dict
    ):
        raise ValueError(
            f"Invalid clip information "
            f"for scene {scene_number}."
        )

    clip_path = clip_information.get(
        "path"
    )

    if not clip_path:

        raise FileNotFoundError(
            f"No animation clip assigned "
            f"to scene {scene_number}."
        )

    absolute_path = resolve_clip_path(
        clip_path
    )

    if not absolute_path.exists():

        raise FileNotFoundError(
            f"Animation clip for scene "
            f"{scene_number} does not exist:\n"
            f"{absolute_path}"
        )

    print()
    print(
        f"Loading Scene {scene_number}: "
        f"{scene_title}"
    )

    print(
        f"  File: {absolute_path.name}"
    )

    clip = VideoFileClip(
        str(absolute_path)
    )

    original_duration = (
        float(clip.duration)
        if clip.duration
        else 0.0
    )

    # --------------------------------------------------------
    # TRIM
    # --------------------------------------------------------

    if original_duration >= duration:

        clip = clip.subclipped(
            0,
            duration
        )

    else:

        print(
            "  WARNING: Source clip is shorter "
            "than the requested scene duration."
        )

        # We cannot manufacture additional
        # animation here. Keep the original clip.

    # --------------------------------------------------------
    # RESIZE
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
# TRANSITION FUNCTIONS
# ============================================================

def apply_fade_in(
    clip,
    duration
):
    """
    Fade the beginning of a clip from black.
    """

    if duration <= 0:
        return clip

    duration = min(
        duration,
        clip.duration / 2
    )

    return clip.with_effects([
        __import__(
            "moviepy"
        ).video.fx.all.FadeIn(
            duration
        )
    ])


def apply_fade_out(
    clip,
    duration
):
    """
    Fade the end of a clip to black.
    """

    if duration <= 0:
        return clip

    duration = min(
        duration,
        clip.duration / 2
    )

    return clip.with_effects([
        __import__(
            "moviepy"
        ).video.fx.all.FadeOut(
            duration
        )
    ])


def apply_crossfade_out(
    clip,
    duration
):
    """
    Prepare a clip for a crossfade.

    MoviePy handles the actual overlap during
    concatenation.
    """

    if duration <= 0:
        return clip

    duration = min(
        duration,
        clip.duration / 2
    )

    return clip


# ============================================================
# TRANSITION TYPE NORMALIZATION
# ============================================================

def normalize_transition_type(
    transition
):
    """
    Normalize transition names.

    Supported:

        none
        fade
        fade_from_black
        fade_to_black
        crossfade
    """

    if not isinstance(
        transition,
        dict
    ):
        return "none"

    transition_type = transition.get(
        "type",
        "none"
    )

    if transition_type is None:
        return "none"

    transition_type = normalize_text(
        transition_type
    )

    transition_type = transition_type.replace(
        " ",
        "_"
    )

    return transition_type


# ============================================================
# APPLY SCENE TRANSITIONS
# ============================================================

def apply_scene_transitions(
    clips,
    timeline
):
    """
    Apply transitions to a collection of clips.

    The first scene can receive:

        fade_from_black

    The last scene can receive:

        fade_to_black

    Intermediate scenes can use:

        crossfade
        fade
        none
    """

    if not clips:
        raise ValueError(
            "No clips available."
        )

    if not timeline:
        raise ValueError(
            "Timeline is empty."
        )

    if len(clips) != len(timeline):

        raise ValueError(
            "Number of clips does not match "
            "number of timeline scenes."
        )

    processed_clips = []

    print()
    print("=" * 70)
    print("APPLYING TRANSITIONS")
    print("=" * 70)

    for index, (
        clip,
        scene
    ) in enumerate(
        zip(clips, timeline)
    ):

        scene_number = scene.get(
            "scene_number",
            index + 1
        )

        transition_in = scene.get(
            "transition_in",
            {}
        )

        transition_out = scene.get(
            "transition_out",
            {}
        )

        transition_in_type = (
            normalize_transition_type(
                transition_in
            )
        )

        transition_out_type = (
            normalize_transition_type(
                transition_out
            )
        )

        transition_in_duration = (
            get_transition_duration(
                transition_in,
                clip.duration
            )
        )

        transition_out_duration = (
            get_transition_duration(
                transition_out,
                clip.duration
            )
        )

        print()
        print(
            f"Scene {scene_number}"
        )

        print(
            f"  In: "
            f"{transition_in_type} "
            f"({transition_in_duration}s)"
        )

        print(
            f"  Out: "
            f"{transition_out_type} "
            f"({transition_out_duration}s)"
        )

        # ----------------------------------------------------
        # FADE IN
        # ----------------------------------------------------

        if transition_in_type in {
            "fade",
            "fade_from_black"
        }:

            clip = apply_fade_in(
                clip,
                transition_in_duration
            )

        # ----------------------------------------------------
        # FADE OUT
        # ----------------------------------------------------

        if transition_out_type in {
            "fade",
            "fade_to_black"
        }:

            clip = apply_fade_out(
                clip,
                transition_out_duration
            )

        # ----------------------------------------------------
        # CROSSFADE
        # ----------------------------------------------------

        if transition_in_type == "crossfade":

            clip = apply_crossfade_out(
                clip,
                transition_in_duration
            )

        processed_clips.append(
            clip
        )

    return processed_clips


# ============================================================
# BUILD FINAL TRANSITION VIDEO
# ============================================================

def concatenate_with_transitions(
    clips,
    timeline
):
    """
    Combine clips into one transition-processed video.

    For normal fade transitions:

        clip 1 -> clip 2 -> clip 3

    For crossfade:

        clip 1
             \\ 
              clip 2

    MoviePy's composition system is used to
    maintain video dimensions.
    """

    if not clips:
        raise ValueError(
            "No clips available."
        )

    transition_clips = []

    for index, (
        clip,
        scene
    ) in enumerate(
        zip(clips, timeline)
    ):

        transition_in = scene.get(
            "transition_in",
            {}
        )

        transition_type = (
            normalize_transition_type(
                transition_in
            )
        )

        duration = get_transition_duration(
            transition_in,
            clip.duration
        )

        # ----------------------------------------------------
        # CROSSFADE
        # ----------------------------------------------------

        if (
            transition_type == "crossfade"
            and index > 0
            and duration > 0
        ):

            clip = clip.with_start(
                -duration
            )

            transition_clips.append(
                clip
            )

        else:

            transition_clips.append(
                clip
            )

    # --------------------------------------------------------
    # NORMAL CONCATENATION
    # --------------------------------------------------------

    final_video = concatenate_videoclips(
        transition_clips,
        method="compose"
    )

    final_video = final_video.with_fps(
        TARGET_FPS
    )

    return final_video


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

def create_output_directory(
    topic
):
    """
    Create:

        output/how_to_manage_fear/
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
# EXPORT
# ============================================================

def export_transition_video(
    video,
    topic
):
    """
    Export the transition-processed video.
    """

    output_folder = (
        create_output_directory(
            topic
        )
    )

    output_file = (
        output_folder
        / "transition_video.mp4"
    )

    print()
    print(
        "Rendering transition video..."
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

def close_clips(clips):
    """
    Safely close source clips.
    """

    for clip in clips:

        try:
            clip.close()

        except Exception:
            pass


def close_video(video):
    """
    Safely close generated video.
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

def process_topic(topic):
    """
    Complete transition-processing pipeline.

    Input:

        "How to manage fear"

    Reads:

        projects/
        └── how_to_manage_fear/
            └── timeline.json

    Produces:

        output/
        └── how_to_manage_fear/
            └── transition_video.mp4
    """

    print()
    print("=" * 70)
    print("AI VIDEO AUTOMATION")
    print("TRANSITION ENGINE")
    print("=" * 70)

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
            f"Expected:\n{timeline_file}"
        )

        print()
        print(
            "Run timeline.py first."
        )

        return None

    source_clips = []
    processed_clips = []
    final_video = None

    try:

        # ----------------------------------------------------
        # LOAD TIMELINE
        # ----------------------------------------------------

        timeline_project = (
            load_timeline(
                timeline_file
            )
        )

        timeline = (
            timeline_project.get(
                "timeline",
                []
            )
        )

        if not timeline:

            raise ValueError(
                "timeline.json contains "
                "no timeline scenes."
            )

        # ----------------------------------------------------
        # LOAD CLIPS
        # ----------------------------------------------------

        print()
        print(
            f"Scenes found: "
            f"{len(timeline)}"
        )

        for scene in timeline:

            clip = load_scene_clip(
                scene
            )

            source_clips.append(
                clip
            )

        # ----------------------------------------------------
        # APPLY TRANSITIONS
        # ----------------------------------------------------

        processed_clips = (
            apply_scene_transitions(
                source_clips,
                timeline
            )
        )

        # ----------------------------------------------------
        # COMBINE
        # ----------------------------------------------------

        final_video = (
            concatenate_with_transitions(
                processed_clips,
                timeline
            )
        )

        # ----------------------------------------------------
        # EXPORT
        # ----------------------------------------------------

        output_file = (
            export_transition_video(
                final_video,
                topic
            )
        )

        print()
        print("=" * 70)
        print(
            "TRANSITION ENGINE COMPLETED"
        )
        print("=" * 70)

        print()
        print(
            "Transition video:"
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
            "TRANSITION ENGINE ERROR"
        )
        print("=" * 70)

        print()
        print(
            f"Error: {error}"
        )

        print()

        raise

    finally:

        close_clips(
            source_clips
        )

        close_clips(
            processed_clips
        )

        close_video(
            final_video
        )


# ============================================================
# TEST
# ============================================================

def run_transition_test():
    """
    Standalone test.

    Before running this:

    1. animation_library must contain videos.
    2. library.py should have been run.
    3. scene_engine.py should have been run.
    4. clip_selector.py should have been run.
    5. timeline.py should have been run.
    """

    topic = "How to manage fear"

    process_topic(
        topic
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_transition_test()
