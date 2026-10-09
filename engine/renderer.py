"""
renderer.py

Final Video Renderer
--------------------

Responsibilities:

1. Load the project timeline.
2. Locate the latest processed video.
3. Locate subtitles.srt.
4. Optionally burn subtitles into the video.
5. Validate the final video.
6. Render the final upload-ready MP4.
7. Save final_video.mp4.
8. Save project rendering information.

This is the FINAL ENGINE STAGE.

Pipeline:

    video_editor.py
            ↓
    transitions.py
            ↓
    effects.py
            ↓
    audio_engine.py
            ↓
    subtitle_engine.py
            ↓
       renderer.py
            ↓
      final_video.mp4
"""

from pathlib import Path
import json
import shutil
import subprocess


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

VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"

VIDEO_PRESET = "medium"

VIDEO_CRF = 18

PIXEL_FORMAT = "yuv420p"


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
    Convert:

        How to manage fear

    into:

        how_to_manage_fear
    """

    text = normalize_text(
        topic
    )

    return text.replace(
        " ",
        "_"
    )


# ============================================================
# PATH HELPERS
# ============================================================

def get_project_folder(topic):
    """
    Return project folder.
    """

    return (
        PROJECTS_DIR
        / topic_to_folder_name(
            topic
        )
    )


def get_output_folder(topic):
    """
    Return output folder.
    """

    folder = (
        OUTPUT_DIR
        / topic_to_folder_name(
            topic
        )
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return folder


def find_timeline(topic):
    """
    Locate timeline.json.
    """

    return (
        get_project_folder(topic)
        / "timeline.json"
    )


def find_audio_video(topic):
    """
    Locate audio_video.mp4.
    """

    return (
        get_output_folder(topic)
        / "audio_video.mp4"
    )


def find_subtitles(topic):
    """
    Locate subtitles.srt.
    """

    return (
        get_output_folder(topic)
        / "subtitles.srt"
    )


def find_final_video(topic):
    """
    Locate final output.
    """

    return (
        get_output_folder(topic)
        / "final_video.mp4"
    )


# ============================================================
# JSON
# ============================================================

def load_json(file_path):
    """
    Load JSON file.
    """

    file_path = Path(
        file_path
    )

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found:\n"
            f"{file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )


def save_json(
    file_path,
    data
):
    """
    Save JSON file.
    """

    file_path = Path(
        file_path
    )

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# FILE VALIDATION
# ============================================================

def validate_file(
    file_path,
    description
):
    """
    Validate that a file exists.
    """

    file_path = Path(
        file_path
    )

    if not file_path.exists():

        raise FileNotFoundError(
            f"{description} not found:\n"
            f"{file_path}"
        )

    if not file_path.is_file():

        raise ValueError(
            f"{description} is not a file:\n"
            f"{file_path}"
        )

    return True


# ============================================================
# FFMPEG
# ============================================================

def find_ffmpeg():
    """
    Find FFmpeg executable.

    FFmpeg must be installed separately
    and available in PATH.
    """

    ffmpeg = shutil.which(
        "ffmpeg"
    )

    if ffmpeg:

        return ffmpeg

    possible_paths = [
        BASE_DIR / "ffmpeg.exe",
        BASE_DIR / "bin" / "ffmpeg.exe"
    ]

    for path in possible_paths:

        if path.exists():

            return str(
                path
            )

    raise RuntimeError(
        "FFmpeg was not found.\n\n"
        "Install FFmpeg and add it to "
        "your system PATH."
    )


# ============================================================
# SRT PATH FOR FFMPEG
# ============================================================

def escape_subtitle_path(
    subtitle_file
):
    """
    Escape an SRT path for FFmpeg's
    subtitles filter.

    Windows paths require special handling.
    """

    subtitle_file = Path(
        subtitle_file
    ).resolve()

    path = str(
        subtitle_file
    )

    # FFmpeg subtitle filter uses:
    # C\:/folder/file.srt
    # rather than:
    # C:/folder/file.srt

    path = path.replace(
        "\\",
        "/"
    )

    path = path.replace(
        ":",
        "\\:"
    )

    path = path.replace(
        "'",
        "\\'"
    )

    return path


# ============================================================
# SUBTITLE STYLE
# ============================================================

def build_subtitle_filter(
    subtitle_file
):
    """
    Build FFmpeg subtitle filter.

    Designed for vertical 1080x1920 videos.
    """

    escaped_path = (
        escape_subtitle_path(
            subtitle_file
        )
    )

    subtitle_filter = (
        "subtitles="
        f"'{escaped_path}'"
        ":"
        "force_style="
        "'"
        "FontName=Arial,"
        "FontSize=18,"
        "Bold=1,"
        "Alignment=2,"
        "MarginV=120,"
        "Outline=3,"
        "Shadow=1"
        "'"
    )

    return subtitle_filter


# ============================================================
# FFMPEG COMMAND
# ============================================================

def build_render_command(
    input_video,
    output_video,
    subtitle_file=None,
    burn_subtitles=True
):
    """
    Build the FFmpeg rendering command.
    """

    ffmpeg = find_ffmpeg()

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_video)
    ]

    # --------------------------------------------------------
    # VIDEO FILTER
    # --------------------------------------------------------

    video_filter = (
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:"
        "force_original_aspect_ratio=decrease,"
        f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:"
        "(ow-iw)/2:"
        "(oh-ih)/2"
    )

    if (
        burn_subtitles
        and subtitle_file
        and Path(
            subtitle_file
        ).exists()
    ):

        subtitle_filter = (
            build_subtitle_filter(
                subtitle_file
            )
        )

        video_filter = (
            f"{video_filter},"
            f"{subtitle_filter}"
        )

    command.extend([
        "-vf",
        video_filter,

        "-r",
        str(TARGET_FPS),

        "-c:v",
        VIDEO_CODEC,

        "-preset",
        VIDEO_PRESET,

        "-crf",
        str(VIDEO_CRF),

        "-pix_fmt",
        PIXEL_FORMAT,

        "-c:a",
        AUDIO_CODEC,

        "-b:a",
        "192k",

        "-movflags",
        "+faststart",

        str(output_video)
    ])

    return command


# ============================================================
# RUN FFMPEG
# ============================================================

def run_ffmpeg(
    command
):
    """
    Execute FFmpeg.
    """

    print()
    print("=" * 70)
    print("FFMPEG RENDER")
    print("=" * 70)

    print()

    print(
        "Starting final render..."
    )

    print()

    try:

        result = subprocess.run(
            command,
            check=True
        )

    except FileNotFoundError:

        raise RuntimeError(
            "FFmpeg executable could "
            "not be started."
        )

    except subprocess.CalledProcessError as error:

        raise RuntimeError(
            "FFmpeg rendering failed.\n"
            f"Exit code: "
            f"{error.returncode}"
        )

    return result.returncode


# ============================================================
# VIDEO INFORMATION
# ============================================================

def get_video_information(
    video_file
):
    """
    Use FFprobe to inspect the final video.
    """

    video_file = Path(
        video_file
    )

    ffprobe = shutil.which(
        "ffprobe"
    )

    if not ffprobe:

        return {
            "available": False
        }

    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration,size",
        "-show_entries",
        "stream=width,height,r_frame_rate,codec_name",
        "-of",
        "json",
        str(video_file)
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        information = json.loads(
            result.stdout
        )

        return {
            "available": True,
            "data": information
        }

    except Exception as error:

        return {
            "available": False,
            "error": str(
                error
            )
        }


# ============================================================
# OUTPUT VALIDATION
# ============================================================

def validate_rendered_video(
    video_file
):
    """
    Validate final video.
    """

    errors = []

    video_file = Path(
        video_file
    )

    # --------------------------------------------------------
    # EXISTS
    # --------------------------------------------------------

    if not video_file.exists():

        errors.append(
            "Final video does not exist."
        )

        return errors

    # --------------------------------------------------------
    # FILE SIZE
    # --------------------------------------------------------

    file_size = (
        video_file.stat().st_size
    )

    if file_size <= 0:

        errors.append(
            "Final video file is empty."
        )

    # --------------------------------------------------------
    # FFPROBE
    # --------------------------------------------------------

    information = (
        get_video_information(
            video_file
        )
    )

    if not information.get(
        "available",
        False
    ):

        return errors

    data = information.get(
        "data",
        {}
    )

    streams = data.get(
        "streams",
        []
    )

    format_data = data.get(
        "format",
        {}
    )

    # --------------------------------------------------------
    # VIDEO STREAM
    # --------------------------------------------------------

    video_stream = None

    for stream in streams:

        if stream.get(
            "codec_type"
        ) == "video":

            video_stream = stream

            break

    if video_stream is None:

        errors.append(
            "No video stream found."
        )

    else:

        width = int(
            video_stream.get(
                "width",
                0
            )
        )

        height = int(
            video_stream.get(
                "height",
                0
            )
        )

        if width != TARGET_WIDTH:

            errors.append(
                f"Unexpected width: "
                f"{width}"
            )

        if height != TARGET_HEIGHT:

            errors.append(
                f"Unexpected height: "
                f"{height}"
            )

    # --------------------------------------------------------
    # DURATION
    # --------------------------------------------------------

    duration = float(
        format_data.get(
            "duration",
            0
        )
    )

    if duration <= 0:

        errors.append(
            "Invalid video duration."
        )

    return errors


# ============================================================
# RENDER
# ============================================================

def render_video(
    input_video,
    output_video,
    subtitle_file=None,
    burn_subtitles=True
):
    """
    Render final video.
    """

    input_video = Path(
        input_video
    )

    output_video = Path(
        output_video
    )

    validate_file(
        input_video,
        "Input video"
    )

    if (
        burn_subtitles
        and subtitle_file
    ):

        validate_file(
            subtitle_file,
            "Subtitle file"
        )

    output_video.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    command = build_render_command(
        input_video,
        output_video,
        subtitle_file,
        burn_subtitles
    )

    print()
    print(
        "FFmpeg command:"
    )

    print(
        " ".join(
            command
        )
    )

    run_ffmpeg(
        command
    )

    return output_video


# ============================================================
# PROJECT STATUS
# ============================================================

def save_render_status(
    topic,
    project,
    final_video,
    subtitle_file,
    subtitle_enabled
):
    """
    Save renderer information inside
    timeline.json.
    """

    timeline_file = find_timeline(
        topic
    )

    project[
        "render"
    ] = {
        "completed": True,
        "final_video": str(
            final_video.relative_to(
                BASE_DIR
            )
        ),
        "subtitles_burned": bool(
            subtitle_enabled
        ),
        "subtitle_file": (
            str(
                subtitle_file.relative_to(
                    BASE_DIR
                )
            )
            if subtitle_file
            else None
        )
    }

    save_json(
        timeline_file,
        project
    )


# ============================================================
# FINAL REPORT
# ============================================================

def print_final_report(
    topic,
    final_video,
    subtitle_file,
    validation_errors
):
    """
    Print final rendering report.
    """

    print()
    print("=" * 70)
    print("FINAL VIDEO REPORT")
    print("=" * 70)

    print()

    print(
        f"Topic: {topic}"
    )

    print()

    print(
        "Final video:"
    )

    print(
        final_video
    )

    print()

    if subtitle_file:

        print(
            "Subtitles:"
        )

        print(
            subtitle_file
        )

        print()

    if validation_errors:

        print(
            "Validation: FAILED"
        )

        print()

        for error in validation_errors:

            print(
                f"  - {error}"
            )

    else:

        print(
            "Validation: PASSED"
        )

    print()

    print("=" * 70)


# ============================================================
# MAIN PROCESS
# ============================================================

def process_topic(
    topic,
    burn_subtitles=True
):
    """
    Complete final rendering pipeline.

    Input:

        output/
        └── how_to_manage_fear/
            ├── audio_video.mp4
            └── subtitles.srt

    Output:

        output/
        └── how_to_manage_fear/
            └── final_video.mp4
    """

    print()
    print("=" * 70)
    print("AI VIDEO AUTOMATION")
    print("FINAL RENDERER")
    print("=" * 70)

    # --------------------------------------------------------
    # PATHS
    # --------------------------------------------------------

    timeline_file = find_timeline(
        topic
    )

    audio_video = find_audio_video(
        topic
    )

    subtitle_file = find_subtitles(
        topic
    )

    final_video = find_final_video(
        topic
    )

    # --------------------------------------------------------
    # TIMELINE
    # --------------------------------------------------------

    if not timeline_file.exists():

        print()
        print(
            "ERROR: timeline.json not found."
        )

        print()
        print(
            f"Expected:\n"
            f"{timeline_file}"
        )

        return None

    # --------------------------------------------------------
    # AUDIO VIDEO
    # --------------------------------------------------------

    if not audio_video.exists():

        print()
        print(
            "ERROR: audio_video.mp4 "
            "not found."
        )

        print()
        print(
            f"Expected:\n"
            f"{audio_video}"
        )

        print()
        print(
            "Run audio_engine.py first."
        )

        return None

    # --------------------------------------------------------
    # SUBTITLE
    # --------------------------------------------------------

    if (
        burn_subtitles
        and not subtitle_file.exists()
    ):

        print()
        print(
            "WARNING: subtitles.srt "
            "was not found."
        )

        print()
        print(
            "Continuing without "
            "burning subtitles."
        )

        burn_subtitles = False

    try:

        # ----------------------------------------------------
        # LOAD PROJECT
        # ----------------------------------------------------

        project = load_json(
            timeline_file
        )

        # ----------------------------------------------------
        # RENDER
        # ----------------------------------------------------

        rendered_file = render_video(
            audio_video,
            final_video,
            subtitle_file
            if burn_subtitles
            else None,
            burn_subtitles
        )

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        validation_errors = (
            validate_rendered_video(
                rendered_file
            )
        )

        # ----------------------------------------------------
        # SAVE STATUS
        # ----------------------------------------------------

        save_render_status(
            topic,
            project,
            rendered_file,
            subtitle_file
            if burn_subtitles
            else None,
            burn_subtitles
        )

        # ----------------------------------------------------
        # REPORT
        # ----------------------------------------------------

        print_final_report(
            topic,
            rendered_file,
            subtitle_file
            if burn_subtitles
            else None,
            validation_errors
        )

        return rendered_file

    except Exception as error:

        print()
        print("=" * 70)
        print(
            "RENDERER ERROR"
        )
        print("=" * 70)

        print()
        print(
            f"Error: {error}"
        )

        print()

        raise


# ============================================================
# TEST
# ============================================================

def run_renderer_test():
    """
    Standalone renderer test.

    Expected inputs:

        output/
        └── how_to_manage_fear/
            ├── audio_video.mp4
            └── subtitles.srt
    """

    topic = "How to manage fear"

    process_topic(
        topic,
        burn_subtitles=True
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_renderer_test()
