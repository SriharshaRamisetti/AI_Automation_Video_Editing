"""
main.py

AI Video Automation
-------------------

Main controller for the complete video generation pipeline.

Pipeline:

1. Animation Library
2. Scene Engine
3. Clip Selector
4. Timeline
5. Video Editor
6. Transitions
7. Effects
8. Audio Engine
9. Subtitle Engine
10. Renderer

Usage:

    python main.py "How to manage fear"

The final video will be created inside:

    output/
    └── how_to_manage_fear/
        └── final_video.mp4
"""

import sys
from pathlib import Path


# ============================================================
# PROJECT IMPORTS
# ============================================================

import config

from engine import library
from engine import scene_engine
from engine import clip_selector
from engine import timeline
from engine import video_editor
from engine import transitions
from engine import effects
from engine import audio_engine
from engine import subtitle_engine
from engine import renderer


# ============================================================
# APPLICATION INFORMATION
# ============================================================

APPLICATION_NAME = (
    "AI Video Automation"
)

APPLICATION_VERSION = "1.0"


# ============================================================
# DISPLAY
# ============================================================

def print_header():
    """
    Print application header.
    """

    print()

    print("=" * 70)

    print(
        APPLICATION_NAME
    )

    print(
        f"Version: "
        f"{APPLICATION_VERSION}"
    )

    print("=" * 70)

    print()


# ============================================================
# TOPIC VALIDATION
# ============================================================

def validate_topic(topic):
    """
    Validate user topic.
    """

    if topic is None:

        raise ValueError(
            "Topic is required."
        )

    topic = str(
        topic
    ).strip()

    if not topic:

        raise ValueError(
            "Topic cannot be empty."
        )

    return topic


# ============================================================
# STEP 1
# ============================================================

def run_library_stage():
    """
    Scan the animation library
    and update animations.json.
    """

    print()
    print("=" * 70)
    print("STEP 1/10")
    print("ANIMATION LIBRARY")
    print("=" * 70)

    animations = (
        library.scan_library()
    )

    library.save_database(
        animations
    )

    library.print_library_statistics()

    return animations


# ============================================================
# STEP 2
# ============================================================

def run_scene_stage(topic):
    """
    Generate scene plan.
    """

    print()
    print("=" * 70)
    print("STEP 2/10")
    print("SCENE ENGINE")
    print("=" * 70)

    scene_plan = (
        scene_engine.generate_scene_plan(
            topic
        )
    )

    scene_engine.print_scene_plan(
        scene_plan
    )

    plan_file = (
        scene_engine.save_scene_plan(
            scene_plan
        )
    )

    print(
        f"Scene plan saved to:\n"
        f"{plan_file}"
    )

    return scene_plan


# ============================================================
# STEP 3
# ============================================================

def run_clip_selection_stage(topic):
    """
    Match animations to scenes.
    """

    print()
    print("=" * 70)
    print("STEP 3/10")
    print("CLIP SELECTOR")
    print("=" * 70)

    scene_plan = (
        clip_selector.process_topic(
            topic
        )
    )

    if scene_plan is None:

        raise RuntimeError(
            "Clip selection failed."
        )

    return scene_plan


# ============================================================
# STEP 4
# ============================================================

def run_timeline_stage(topic):
    """
    Create timeline.
    """

    print()
    print("=" * 70)
    print("STEP 4/10")
    print("TIMELINE")
    print("=" * 70)

    project = (
        timeline.process_topic(
            topic
        )
    )

    if project is None:

        raise RuntimeError(
            "Timeline creation failed."
        )

    return project


# ============================================================
# STEP 5
# ============================================================

def run_video_editor_stage(topic):
    """
    Assemble the selected clips.
    """

    print()
    print("=" * 70)
    print("STEP 5/10")
    print("VIDEO EDITOR")
    print("=" * 70)

    output_file = (
        video_editor.process_topic(
            topic
        )
    )

    if output_file is None:

        raise RuntimeError(
            "Video editor failed."
        )

    return output_file


# ============================================================
# STEP 6
# ============================================================

def run_transition_stage(topic):
    """
    Apply transitions.
    """

    print()
    print("=" * 70)
    print("STEP 6/10")
    print("TRANSITIONS")
    print("=" * 70)

    output_file = (
        transitions.process_topic(
            topic
        )
    )

    if output_file is None:

        raise RuntimeError(
            "Transition stage failed."
        )

    return output_file


# ============================================================
# STEP 7
# ============================================================

def run_effect_stage(topic):
    """
    Apply visual effects.
    """

    print()
    print("=" * 70)
    print("STEP 7/10")
    print("EFFECTS")
    print("=" * 70)

    output_file = (
        effects.process_topic(
            topic
        )
    )

    if output_file is None:

        raise RuntimeError(
            "Effects stage failed."
        )

    return output_file


# ============================================================
# STEP 8
# ============================================================

def run_audio_stage(topic):
    """
    Add voiceover, music and sound effects.
    """

    print()
    print("=" * 70)
    print("STEP 8/10")
    print("AUDIO ENGINE")
    print("=" * 70)

    output_file = (
        audio_engine.process_topic(
            topic
        )
    )

    if output_file is None:

        raise RuntimeError(
            "Audio stage failed."
        )

    return output_file


# ============================================================
# STEP 9
# ============================================================

def run_subtitle_stage(topic):
    """
    Generate subtitles.
    """

    print()
    print("=" * 70)
    print("STEP 9/10")
    print("SUBTITLE ENGINE")
    print("=" * 70)

    subtitle_file = (
        subtitle_engine.process_topic(
            topic
        )
    )

    if subtitle_file is None:

        raise RuntimeError(
            "Subtitle generation failed."
        )

    return subtitle_file


# ============================================================
# STEP 10
# ============================================================

def run_renderer_stage(topic):
    """
    Render the final video.
    """

    print()
    print("=" * 70)
    print("STEP 10/10")
    print("FINAL RENDERER")
    print("=" * 70)

    final_video = (
        renderer.process_topic(
            topic,
            burn_subtitles=True
        )
    )

    if final_video is None:

        raise RuntimeError(
            "Final rendering failed."
        )

    return final_video


# ============================================================
# COMPLETE PIPELINE
# ============================================================

def generate_video(topic):
    """
    Run the complete AI video pipeline.
    """

    topic = validate_topic(
        topic
    )

    print_header()

    print(
        f"Topic:\n{topic}"
    )

    print()

    print(
        "Starting complete "
        "video generation pipeline..."
    )

    print()

    # --------------------------------------------------------
    # CREATE REQUIRED DIRECTORIES
    # --------------------------------------------------------

    config.create_required_directories()

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    run_library_stage()

    # --------------------------------------------------------
    # STEP 2
    # --------------------------------------------------------

    run_scene_stage(
        topic
    )

    # --------------------------------------------------------
    # STEP 3
    # --------------------------------------------------------

    run_clip_selection_stage(
        topic
    )

    # --------------------------------------------------------
    # STEP 4
    # --------------------------------------------------------

    run_timeline_stage(
        topic
    )

    # --------------------------------------------------------
    # STEP 5
    # --------------------------------------------------------

    run_video_editor_stage(
        topic
    )

    # --------------------------------------------------------
    # STEP 6
    # --------------------------------------------------------

    run_transition_stage(
        topic
    )

    # --------------------------------------------------------
    # STEP 7
    # --------------------------------------------------------

    run_effect_stage(
        topic
    )

    # --------------------------------------------------------
    # STEP 8
    # --------------------------------------------------------

    run_audio_stage(
        topic
    )

    # --------------------------------------------------------
    # STEP 9
    # --------------------------------------------------------

    run_subtitle_stage(
        topic
    )

    # --------------------------------------------------------
    # STEP 10
    # --------------------------------------------------------

    final_video = (
        run_renderer_stage(
            topic
        )
    )

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print()

    print("=" * 70)

    print(
        "VIDEO GENERATION COMPLETED"
    )

    print("=" * 70)

    print()

    print(
        "Topic:"
    )

    print(
        topic
    )

    print()

    print(
        "Final video:"
    )

    print(
        final_video
    )

    print()

    print(
        "Your video is ready."
    )

    print()

    return final_video


# ============================================================
# COMMAND LINE
# ============================================================

def get_topic_from_command_line():
    """
    Read topic from command line.

    Example:

        python main.py "How to manage fear"
    """

    if len(sys.argv) < 2:

        return None

    topic = " ".join(
        sys.argv[1:]
    )

    return topic.strip()


# ============================================================
# INTERACTIVE MODE
# ============================================================

def interactive_mode():
    """
    Ask user for a topic if no command-line
    argument was supplied.
    """

    print()

    print(
        "Enter your video topic."
    )

    print(
        "Example: How to manage fear"
    )

    print()

    topic = input(
        "Topic: "
    ).strip()

    if not topic:

        raise ValueError(
            "No topic entered."
        )

    return topic


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():
    """
    Main application entry point.
    """

    try:

        topic = (
            get_topic_from_command_line()
        )

        if not topic:

            topic = interactive_mode()

        generate_video(
            topic
        )

    except KeyboardInterrupt:

        print()

        print(
            "Process cancelled by user."
        )

        print()

    except Exception as error:

        print()

        print("=" * 70)

        print(
            "VIDEO GENERATION FAILED"
        )

        print("=" * 70)

        print()

        print(
            f"Error:\n{error}"
        )

        print()

        print(
            "Check the previous stage "
            "for the actual problem."
        )

        print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
