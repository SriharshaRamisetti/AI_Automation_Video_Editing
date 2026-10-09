"""
subtitle_engine.py

Subtitle Engine
---------------

Responsibilities:

1. Load timeline.json.
2. Read subtitle/script information.
3. Generate subtitle segments.
4. Generate SRT subtitles.
5. Optionally transcribe a voiceover using Whisper.
6. Synchronize subtitles with the project timeline.
7. Validate subtitle timing.
8. Save subtitles.srt.
9. Update timeline.json with subtitle information.

This file does NOT handle:

- renderer.py
"""

from pathlib import Path
import json
import re


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROJECTS_DIR = BASE_DIR / "projects"
OUTPUT_DIR = BASE_DIR / "output"


# ============================================================
# SUBTITLE SETTINGS
# ============================================================

DEFAULT_MAX_CHARS_PER_LINE = 42
DEFAULT_MAX_LINES = 2

MIN_SUBTITLE_DURATION = 0.60
MAX_SUBTITLE_DURATION = 4.50

DEFAULT_GAP = 0.05


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text):
    """
    Normalize text for folder/file matching.
    """

    if text is None:
        return ""

    text = str(text)

    text = text.replace(
        "\n",
        " "
    )

    text = text.replace(
        "\r",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


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

    text = text.lower()

    text = text.replace(
        "-",
        " "
    )

    text = text.replace(
        "_",
        " "
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        "",
        text
    )

    return "_".join(
        text.split()
    )


# ============================================================
# PATH HELPERS
# ============================================================

def get_project_folder(topic):
    """
    Return project directory.
    """

    folder_name = topic_to_folder_name(
        topic
    )

    return (
        PROJECTS_DIR
        / folder_name
    )


def get_output_folder(topic):
    """
    Return output directory.
    """

    folder_name = topic_to_folder_name(
        topic
    )

    folder = (
        OUTPUT_DIR
        / folder_name
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


def find_output_srt(topic):
    """
    Locate subtitles.srt.
    """

    return (
        get_output_folder(topic)
        / "subtitles.srt"
    )


# ============================================================
# JSON
# ============================================================

def load_json(file_path):
    """
    Load a JSON file.
    """

    file_path = Path(
        file_path
    )

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found:\n"
            f"{file_path}"
        )

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    except json.JSONDecodeError as error:

        raise RuntimeError(
            f"Invalid JSON:\n"
            f"{file_path}\n"
            f"Reason: {error}"
        )


def save_json(
    file_path,
    data
):
    """
    Save JSON data.
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
# TIMELINE
# ============================================================

def load_timeline(
    topic
):
    """
    Load the complete timeline project.
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
            "Timeline contains no scenes."
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
    Safely convert to float.
    """

    try:

        return float(
            value
        )

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
    Restrict a number to a range.
    """

    return max(
        minimum,
        min(
            maximum,
            value
        )
    )


# ============================================================
# TEXT SPLITTING
# ============================================================

def split_into_sentences(
    text
):
    """
    Split a script into sentences.

    Example:

        Fear is normal.
        But running from it
        makes it stronger.

    becomes three logical segments.
    """

    text = normalize_text(
        text
    )

    if not text:

        return []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def split_long_sentence(
    sentence,
    max_chars=DEFAULT_MAX_CHARS_PER_LINE
):
    """
    Split very long sentences into
    smaller subtitle units.
    """

    sentence = normalize_text(
        sentence
    )

    if not sentence:

        return []

    words = sentence.split()

    chunks = []

    current_words = []
    current_length = 0

    for word in words:

        word_length = len(
            word
        )

        if not current_words:

            current_words.append(
                word
            )

            current_length = (
                word_length
            )

            continue

        proposed_length = (
            current_length
            + 1
            + word_length
        )

        if proposed_length <= max_chars:

            current_words.append(
                word
            )

            current_length = (
                proposed_length
            )

        else:

            chunks.append(
                " ".join(
                    current_words
                )
            )

            current_words = [
                word
            ]

            current_length = (
                word_length
            )

    if current_words:

        chunks.append(
            " ".join(
                current_words
            )
        )

    return chunks


def prepare_subtitle_text(
    text,
    max_chars=DEFAULT_MAX_CHARS_PER_LINE
):
    """
    Convert arbitrary script text into
    subtitle-sized chunks.
    """

    sentences = split_into_sentences(
        text
    )

    chunks = []

    for sentence in sentences:

        sentence_chunks = (
            split_long_sentence(
                sentence,
                max_chars
            )
        )

        chunks.extend(
            sentence_chunks
        )

    return chunks


# ============================================================
# TEXT TIMING
# ============================================================

def calculate_text_weight(
    text
):
    """
    Calculate approximate speaking weight.

    Longer text gets proportionally more
    subtitle time.
    """

    text = normalize_text(
        text
    )

    if not text:

        return 1.0

    # Characters are used rather than
    # raw words because punctuation and
    # short words still require speaking time.

    return max(
        1.0,
        float(
            len(text)
        )
    )


def distribute_text_timing(
    subtitle_texts,
    start_time,
    end_time
):
    """
    Distribute subtitle timing according
    to text length.
    """

    if not subtitle_texts:

        return []

    start_time = safe_float(
        start_time
    )

    end_time = safe_float(
        end_time
    )

    total_duration = (
        end_time
        - start_time
    )

    if total_duration <= 0:

        return []

    weights = [
        calculate_text_weight(
            text
        )
        for text in subtitle_texts
    ]

    total_weight = sum(
        weights
    )

    if total_weight <= 0:

        total_weight = len(
            subtitle_texts
        )

        weights = [
            1.0
            for _ in subtitle_texts
        ]

    subtitles = []

    current_time = (
        start_time
    )

    for index, (
        text,
        weight
    ) in enumerate(
        zip(
            subtitle_texts,
            weights
        )
    ):

        if index == (
            len(subtitle_texts)
            - 1
        ):

            subtitle_end = (
                end_time
            )

        else:

            duration = (
                total_duration
                * (
                    weight
                    / total_weight
                )
            )

            subtitle_end = (
                current_time
                + duration
            )

        subtitles.append({
            "text": text,
            "start": round(
                current_time,
                3
            ),
            "end": round(
                subtitle_end,
                3
            )
        })

        current_time = (
            subtitle_end
        )

    return subtitles


# ============================================================
# SCENE SCRIPT
# ============================================================

def get_scene_script(
    scene
):
    """
    Look for script/text information
    already present in a scene.

    Supported fields:

        script
        narration
        voiceover_text
        subtitle_text
        text
    """

    possible_fields = [
        "script",
        "narration",
        "voiceover_text",
        "subtitle_text",
        "text"
    ]

    for field in possible_fields:

        value = scene.get(
            field
        )

        if value:

            return normalize_text(
                value
            )

    return ""


def build_scene_script_from_description(
    scene
):
    """
    Fallback script when no explicit
    narration is available.

    This gives the subtitle engine useful
    text during development.

    Later, the final narration generator
    can populate the script field.
    """

    description = normalize_text(
        scene.get(
            "description",
            ""
        )
    )

    if description:

        return description

    title = normalize_text(
        scene.get(
            "title",
            ""
        )
    )

    return title


# ============================================================
# BUILD SUBTITLES FROM TIMELINE
# ============================================================

def generate_subtitles_from_timeline(
    timeline
):
    """
    Generate subtitle entries using
    scene-level text.
    """

    subtitles = []

    subtitle_number = 1

    for scene in timeline:

        scene_number = scene.get(
            "scene_number",
            subtitle_number
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

        if scene_end <= scene_start:

            continue

        script = get_scene_script(
            scene
        )

        if not script:

            script = (
                build_scene_script_from_description(
                    scene
                )
            )

        if not script:

            continue

        text_chunks = (
            prepare_subtitle_text(
                script
            )
        )

        scene_subtitles = (
            distribute_text_timing(
                text_chunks,
                scene_start,
                scene_end
            )
        )

        for item in scene_subtitles:

            item["subtitle_id"] = (
                f"subtitle_"
                f"{subtitle_number:04d}"
            )

            item["scene_number"] = (
                scene_number
            )

            subtitles.append(
                item
            )

            subtitle_number += 1

    return subtitles


# ============================================================
# WHISPER TRANSCRIPTION
# ============================================================

def transcribe_audio_with_whisper(
    audio_file,
    model_name="base"
):
    """
    Transcribe an audio file using
    OpenAI Whisper.

    Whisper is optional.

    If it is not installed, a clear error
    is returned instead of crashing silently.
    """

    audio_file = Path(
        audio_file
    )

    if not audio_file.exists():

        raise FileNotFoundError(
            f"Audio file not found:\n"
            f"{audio_file}"
        )

    try:

        import whisper

    except ImportError:

        raise RuntimeError(
            "Whisper is not installed.\n"
            "Install it with:\n"
            "python -m pip install openai-whisper"
        )

    print()
    print(
        f"Loading Whisper model: "
        f"{model_name}"
    )

    model = whisper.load_model(
        model_name
    )

    print(
        "Transcribing voiceover..."
    )

    result = model.transcribe(
        str(audio_file),
        fp16=False
    )

    return result


def convert_whisper_segments(
    whisper_result
):
    """
    Convert Whisper segments into the
    subtitle format used by this project.
    """

    subtitles = []

    segments = whisper_result.get(
        "segments",
        []
    )

    for index, segment in enumerate(
        segments,
        start=1
    ):

        text = normalize_text(
            segment.get(
                "text",
                ""
            )
        )

        if not text:

            continue

        start = safe_float(
            segment.get(
                "start",
                0
            )
        )

        end = safe_float(
            segment.get(
                "end",
                start
            )
        )

        if end <= start:

            continue

        subtitles.append({
            "subtitle_id": (
                f"subtitle_"
                f"{index:04d}"
            ),
            "scene_number": None,
            "text": text,
            "start": round(
                start,
                3
            ),
            "end": round(
                end,
                3
            )
        })

    return subtitles


# ============================================================
# SRT FORMATTING
# ============================================================

def format_srt_time(
    seconds
):
    """
    Convert seconds into:

        HH:MM:SS,mmm

    SRT format.
    """

    seconds = max(
        0.0,
        safe_float(
            seconds
        )
    )

    total_milliseconds = int(
        round(
            seconds * 1000
        )
    )

    hours = (
        total_milliseconds
        // 3_600_000
    )

    remainder = (
        total_milliseconds
        % 3_600_000
    )

    minutes = (
        remainder
        // 60_000
    )

    remainder = (
        remainder
        % 60_000
    )

    whole_seconds = (
        remainder
        // 1000
    )

    milliseconds = (
        remainder
        % 1000
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{whole_seconds:02d},"
        f"{milliseconds:03d}"
    )


def subtitle_to_srt_block(
    number,
    subtitle
):
    """
    Convert one subtitle into SRT format.
    """

    text = normalize_text(
        subtitle.get(
            "text",
            ""
        )
    )

    start = format_srt_time(
        subtitle.get(
            "start",
            0
        )
    )

    end = format_srt_time(
        subtitle.get(
            "end",
            0
        )
    )

    return (
        f"{number}\n"
        f"{start} --> {end}\n"
        f"{text}\n"
    )


def generate_srt(
    subtitles
):
    """
    Convert subtitle entries into
    complete SRT text.
    """

    blocks = []

    for index, subtitle in enumerate(
        subtitles,
        start=1
    ):

        blocks.append(
            subtitle_to_srt_block(
                index,
                subtitle
            )
        )

    return "\n".join(
        blocks
    )


# ============================================================
# SRT SAVE
# ============================================================

def save_srt(
    subtitles,
    output_file
):
    """
    Save subtitles.srt.
    """

    output_file = Path(
        output_file
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    srt_content = generate_srt(
        subtitles
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            srt_content
        )

    return output_file


# ============================================================
# SUBTITLE VALIDATION
# ============================================================

def validate_subtitles(
    subtitles,
    video_duration
):
    """
    Validate subtitle timing.
    """

    errors = []

    previous_end = 0.0

    video_duration = safe_float(
        video_duration
    )

    for index, subtitle in enumerate(
        subtitles,
        start=1
    ):

        text = normalize_text(
            subtitle.get(
                "text",
                ""
            )
        )

        start = safe_float(
            subtitle.get(
                "start",
                0
            )
        )

        end = safe_float(
            subtitle.get(
                "end",
                0
            )
        )

        # ----------------------------------------------------
        # EMPTY TEXT
        # ----------------------------------------------------

        if not text:

            errors.append(
                f"Subtitle {index}: "
                "empty text."
            )

        # ----------------------------------------------------
        # INVALID TIMING
        # ----------------------------------------------------

        if end <= start:

            errors.append(
                f"Subtitle {index}: "
                "end time is not after "
                "start time."
            )

        # ----------------------------------------------------
        # MINIMUM DURATION
        # ----------------------------------------------------

        duration = (
            end - start
        )

        if duration < MIN_SUBTITLE_DURATION:

            errors.append(
                f"Subtitle {index}: "
                f"duration {duration:.3f}s "
                f"is too short."
            )

        # ----------------------------------------------------
        # MAXIMUM DURATION
        # ----------------------------------------------------

        if duration > MAX_SUBTITLE_DURATION:

            errors.append(
                f"Subtitle {index}: "
                f"duration {duration:.3f}s "
                f"is too long."
            )

        # ----------------------------------------------------
        # OVERLAP
        # ----------------------------------------------------

        if start < previous_end:

            errors.append(
                f"Subtitle {index}: "
                "overlaps previous subtitle."
            )

        # ----------------------------------------------------
        # VIDEO BOUNDS
        # ----------------------------------------------------

        if start < 0:

            errors.append(
                f"Subtitle {index}: "
                "starts before video."
            )

        if end > video_duration + 0.01:

            errors.append(
                f"Subtitle {index}: "
                "ends after video."
            )

        previous_end = end

    return errors


# ============================================================
# ASSIGN SUBTITLES TO TIMELINE
# ============================================================

def attach_subtitles_to_timeline(
    timeline,
    subtitles
):
    """
    Attach generated subtitles to their
    corresponding scenes.
    """

    for scene in timeline:

        scene["subtitles"] = []

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

        scene_number = scene.get(
            "scene_number"
        )

        for subtitle in subtitles:

            subtitle_scene = subtitle.get(
                "scene_number"
            )

            subtitle_start = safe_float(
                subtitle.get(
                    "start",
                    0
                )
            )

            subtitle_end = safe_float(
                subtitle.get(
                    "end",
                    0
                )
            )

            belongs_to_scene = False

            if subtitle_scene == scene_number:

                belongs_to_scene = True

            elif (
                subtitle_start >= scene_start
                and subtitle_end <= scene_end
            ):

                belongs_to_scene = True

            if belongs_to_scene:

                scene["subtitles"].append(
                    subtitle.copy()
                )

    return timeline


# ============================================================
# UPDATE TIMELINE
# ============================================================

def save_subtitle_status(
    topic,
    timeline_project,
    subtitles,
    output_file
):
    """
    Save subtitle information back into
    timeline.json.
    """

    timeline_file = find_timeline(
        topic
    )

    timeline_project[
        "subtitles"
    ] = {
        "completed": True,
        "count": len(
            subtitles
        ),
        "file": str(
            output_file.relative_to(
                BASE_DIR
            )
        )
    }

    timeline_project[
        "timeline"
    ] = attach_subtitles_to_timeline(
        timeline_project[
            "timeline"
        ],
        subtitles
    )

    save_json(
        timeline_file,
        timeline_project
    )


# ============================================================
# OPTIONAL WHISPER MODE
# ============================================================

def generate_subtitles_from_audio(
    audio_file,
    model_name="base"
):
    """
    Generate subtitles directly from
    a voiceover/audio file.

    This is the preferred path when
    accurate speech timing is available.
    """

    result = transcribe_audio_with_whisper(
        audio_file,
        model_name
    )

    return convert_whisper_segments(
        result
    )


# ============================================================
# MAIN PROCESS
# ============================================================

def process_topic(
    topic,
    voiceover_file=None,
    use_whisper=False,
    whisper_model="base"
):
    """
    Complete subtitle pipeline.

    Default behavior:

        Uses script/text from timeline.json.

    Optional behavior:

        If use_whisper=True and a voiceover
        file is supplied, Whisper is used to
        create accurate subtitle timings.
    """

    print()
    print("=" * 70)
    print("AI VIDEO AUTOMATION")
    print("SUBTITLE ENGINE")
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
            f"Expected:\n"
            f"{timeline_file}"
        )

        print()

        return None

    try:

        # ----------------------------------------------------
        # LOAD PROJECT
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
                "Timeline contains no scenes."
            )

        video_duration = safe_float(
            project.get(
                "total_duration",
                0
            )
        )

        # ----------------------------------------------------
        # WHISPER MODE
        # ----------------------------------------------------

        subtitles = []

        if (
            use_whisper
            and voiceover_file
        ):

            print()
            print(
                "Subtitle mode: "
                "Whisper transcription"
            )

            subtitles = (
                generate_subtitles_from_audio(
                    voiceover_file,
                    whisper_model
                )
            )

        # ----------------------------------------------------
        # TIMELINE TEXT MODE
        # ----------------------------------------------------

        else:

            print()
            print(
                "Subtitle mode: "
                "Timeline script"
            )

            subtitles = (
                generate_subtitles_from_timeline(
                    timeline
                )
            )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        validation_errors = (
            validate_subtitles(
                subtitles,
                video_duration
            )
        )

        print()
        print(
            f"Subtitles generated: "
            f"{len(subtitles)}"
        )

        if validation_errors:

            print()
            print(
                "SUBTITLE VALIDATION WARNINGS"
            )

            for error in validation_errors:

                print(
                    f"  - {error}"
                )

        else:

            print(
                "Subtitle validation: PASSED"
            )

        # ----------------------------------------------------
        # SAVE SRT
        # ----------------------------------------------------

        output_file = find_output_srt(
            topic
        )

        save_srt(
            subtitles,
            output_file
        )

        # ----------------------------------------------------
        # SAVE TO TIMELINE
        # ----------------------------------------------------

        save_subtitle_status(
            topic,
            project,
            subtitles,
            output_file
        )

        print()
        print("=" * 70)
        print(
            "SUBTITLE ENGINE COMPLETED"
        )
        print("=" * 70)

        print()
        print(
            "Subtitle file:"
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
            "SUBTITLE ENGINE ERROR"
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

def run_subtitle_test():
    """
    Standalone test.

    Required before running:

        library.py
        scene_engine.py
        clip_selector.py
        timeline.py

    Whisper is NOT required for the
    default timeline-script mode.
    """

    topic = "How to manage fear"

    process_topic(
        topic
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_subtitle_test()
