"""
library.py

Animation Library Manager
-------------------------

Responsibilities:
1. Scan the animation_library folder.
2. Find all supported video files.
3. Extract basic video information.
4. Detect category/subcategory from folder structure.
5. Generate useful tags from folder/file names.
6. Save everything into database/animations.json.
7. Search the animation library by keywords/tags.
"""

import json
import re
from pathlib import Path
from datetime import datetime

import cv2


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

LIBRARY_DIR = BASE_DIR / "animation_library"
DATABASE_DIR = BASE_DIR / "database"
DATABASE_FILE = DATABASE_DIR / "animations.json"


# ============================================================
# SUPPORTED VIDEO FORMATS
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
# DEFAULT CATEGORY STRUCTURE
# ============================================================

DEFAULT_LIBRARY_FOLDERS = [
    "psychology",
    "emotions",
    "human_actions",
    "brain",
    "nature",
    "backgrounds",
    "effects",
    "transitions",
    "general"
]


# ============================================================
# BASIC UTILITY FUNCTIONS
# ============================================================

def normalize_text(text):
    """
    Convert text into a clean lowercase format.

    Example:
        "Fear Person Scared"
        ->
        "fear person scared"
    """

    text = str(text)

    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = text.replace(".", " ")

    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip().lower()


def create_project_folders():
    """
    Create the required project folders if they don't exist.
    """

    LIBRARY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for folder in DEFAULT_LIBRARY_FOLDERS:

        folder_path = LIBRARY_DIR / folder

        folder_path.mkdir(
            parents=True,
            exist_ok=True
        )


# ============================================================
# VIDEO FILE DETECTION
# ============================================================

def is_video_file(file_path):
    """
    Check whether a file is a supported video file.
    """

    return (
        file_path.is_file()
        and file_path.suffix.lower()
        in SUPPORTED_VIDEO_EXTENSIONS
    )


# ============================================================
# VIDEO INFORMATION
# ============================================================

def get_video_information(file_path):
    """
    Extract technical information from a video.

    Returns:
        dictionary containing:
        - duration
        - width
        - height
        - fps
        - frame count
        - file size
    """

    information = {
        "duration": 0.0,
        "width": 0,
        "height": 0,
        "fps": 0.0,
        "frame_count": 0,
        "file_size_mb": 0.0
    }

    try:

        capture = cv2.VideoCapture(str(file_path))

        if not capture.isOpened():
            return information

        width = int(
            capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        fps = float(
            capture.get(
                cv2.CAP_PROP_FPS
            )
        )

        frame_count = int(
            capture.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        duration = 0.0

        if fps > 0:
            duration = frame_count / fps

        capture.release()

        file_size_mb = (
            file_path.stat().st_size
            / (1024 * 1024)
        )

        information = {
            "duration": round(
                duration,
                3
            ),
            "width": width,
            "height": height,
            "fps": round(
                fps,
                3
            ),
            "frame_count": frame_count,
            "file_size_mb": round(
                file_size_mb,
                3
            )
        }

    except Exception as error:

        print(
            f"WARNING: Could not read video information "
            f"for {file_path.name}"
        )

        print(
            f"Reason: {error}"
        )

    return information


# ============================================================
# CATEGORY DETECTION
# ============================================================

def detect_category(relative_path):
    """
    Determine category and subcategory from the folder structure.

    Example:

        animation_library/
            psychology/
                fear/
                    scared_person.mp4

    Returns:

        category = psychology
        subcategory = fear
    """

    parts = relative_path.parts

    if len(parts) >= 2:

        category = normalize_text(
            parts[0]
        )

        subcategory = normalize_text(
            parts[1]
        )

    elif len(parts) == 1:

        category = "general"
        subcategory = "general"

    else:

        category = "general"
        subcategory = "general"

    return category, subcategory


# ============================================================
# TAG GENERATION
# ============================================================

def generate_tags(file_path, category, subcategory):
    """
    Generate searchable tags using:

    1. Category
    2. Subcategory
    3. Filename
    4. Parent folders
    """

    tags = set()

    # --------------------------------------------------------
    # Category
    # --------------------------------------------------------

    if category:
        tags.add(
            normalize_text(category)
        )

    # --------------------------------------------------------
    # Subcategory
    # --------------------------------------------------------

    if subcategory:
        tags.add(
            normalize_text(subcategory)
        )

    # --------------------------------------------------------
    # Filename
    # --------------------------------------------------------

    filename = normalize_text(
        file_path.stem
    )

    filename_words = filename.split()

    for word in filename_words:

        if len(word) > 1:

            tags.add(word)

    # --------------------------------------------------------
    # Parent folders
    # --------------------------------------------------------

    for parent in file_path.parents:

        if parent == LIBRARY_DIR:
            break

        parent_name = normalize_text(
            parent.name
        )

        if parent_name:
            tags.add(parent_name)

    return sorted(tags)


# ============================================================
# CREATE ANIMATION RECORD
# ============================================================

def create_animation_record(file_path):
    """
    Create a complete database record for one animation.
    """

    relative_path = file_path.relative_to(
        LIBRARY_DIR
    )

    category, subcategory = detect_category(
        relative_path
    )

    video_information = get_video_information(
        file_path
    )

    tags = generate_tags(
        file_path,
        category,
        subcategory
    )

    record = {

        "id": None,

        "name": file_path.stem,

        "filename": file_path.name,

        "path": str(
            file_path.relative_to(
                BASE_DIR
            )
        ),

        "category": category,

        "subcategory": subcategory,

        "tags": tags,

        "duration": video_information[
            "duration"
        ],

        "width": video_information[
            "width"
        ],

        "height": video_information[
            "height"
        ],

        "fps": video_information[
            "fps"
        ],

        "frame_count": video_information[
            "frame_count"
        ],

        "file_size_mb": video_information[
            "file_size_mb"
        ],

        "orientation": detect_orientation(
            video_information["width"],
            video_information["height"]
        ),

        "created_at": datetime.now().isoformat(
            timespec="seconds"
        )
    }

    return record


# ============================================================
# ORIENTATION DETECTION
# ============================================================

def detect_orientation(width, height):
    """
    Determine whether the video is:

        portrait
        landscape
        square
        unknown
    """

    if width <= 0 or height <= 0:

        return "unknown"

    if height > width:

        return "portrait"

    if width > height:

        return "landscape"

    return "square"


# ============================================================
# SCAN LIBRARY
# ============================================================

def scan_library():
    """
    Scan the entire animation library.

    Returns:
        list of animation records.
    """

    create_project_folders()

    animations = []

    print()
    print("=" * 70)
    print("SCANNING ANIMATION LIBRARY")
    print("=" * 70)

    video_files = []

    for file_path in LIBRARY_DIR.rglob("*"):

        if is_video_file(file_path):

            video_files.append(
                file_path
            )

    video_files.sort()

    print(
        f"\nFound {len(video_files)} video files.\n"
    )

    for index, file_path in enumerate(
        video_files,
        start=1
    ):

        print(
            f"[{index}/{len(video_files)}] "
            f"Processing: {file_path.name}"
        )

        record = create_animation_record(
            file_path
        )

        # Unique ID
        record["id"] = (
            f"animation_{index:05d}"
        )

        animations.append(
            record
        )

    print()
    print(
        f"✓ Library scan completed."
    )

    print(
        f"✓ Total animations: "
        f"{len(animations)}"
    )

    return animations


# ============================================================
# SAVE DATABASE
# ============================================================

def save_database(animations):
    """
    Save animation records into animations.json.
    """

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    database = {

        "version": "1.0",

        "updated_at": datetime.now().isoformat(
            timespec="seconds"
        ),

        "total_animations": len(
            animations
        ),

        "animations": animations
    }

    with open(
        DATABASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            database,
            file,
            indent=4,
            ensure_ascii=False
        )

    print()
    print(
        f"✓ Database saved:"
    )

    print(
        f"  {DATABASE_FILE}"
    )


# ============================================================
# LOAD DATABASE
# ============================================================

def load_database():
    """
    Load animations.json.

    Returns:
        list of animations
    """

    if not DATABASE_FILE.exists():

        return []

    try:

        with open(
            DATABASE_FILE,
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

        print(
            f"ERROR: Could not load database."
        )

        print(
            f"Reason: {error}"
        )

        return []


# ============================================================
# SEARCH LIBRARY
# ============================================================

def search_animations(
    query,
    category=None,
    subcategory=None,
    orientation=None,
    minimum_duration=None,
    maximum_duration=None
):
    """
    Search animations using tags and metadata.

    Example:

        search_animations("fear")

    or:

        search_animations(
            "fear",
            category="psychology"
        )
    """

    animations = load_database()

    if not animations:

        return []

    query_words = set(
        normalize_text(query).split()
    )

    results = []

    for animation in animations:

        # ----------------------------------------------------
        # Category filter
        # ----------------------------------------------------

        if category:

            if normalize_text(
                animation.get(
                    "category",
                    ""
                )
            ) != normalize_text(category):

                continue

        # ----------------------------------------------------
        # Subcategory filter
        # ----------------------------------------------------

        if subcategory:

            if normalize_text(
                animation.get(
                    "subcategory",
                    ""
                )
            ) != normalize_text(
                subcategory
            ):

                continue

        # ----------------------------------------------------
        # Orientation filter
        # ----------------------------------------------------

        if orientation:

            if animation.get(
                "orientation"
            ) != orientation:

                continue

        # ----------------------------------------------------
        # Duration filter
        # ----------------------------------------------------

        duration = float(
            animation.get(
                "duration",
                0
            )
        )

        if minimum_duration is not None:

            if duration < minimum_duration:

                continue

        if maximum_duration is not None:

            if duration > maximum_duration:

                continue

        # ----------------------------------------------------
        # Search text
        # ----------------------------------------------------

        searchable_text = set()

        searchable_text.update(
            normalize_text(
                animation.get(
                    "name",
                    ""
                )
            ).split()
        )

        searchable_text.update(
            animation.get(
                "tags",
                []
            )
        )

        searchable_text.add(
            normalize_text(
                animation.get(
                    "category",
                    ""
                )
            )
        )

        searchable_text.add(
            normalize_text(
                animation.get(
                    "subcategory",
                    ""
                )
            )
        )

        # ----------------------------------------------------
        # Calculate relevance score
        # ----------------------------------------------------

        score = len(
            query_words.intersection(
                searchable_text
            )
        )

        if score > 0:

            result = animation.copy()

            result["match_score"] = score

            results.append(
                result
            )

    # Highest relevance first
    results.sort(
        key=lambda item: (
            item["match_score"],
            item.get("duration", 0)
        ),
        reverse=True
    )

    return results


# ============================================================
# LIBRARY STATISTICS
# ============================================================

def get_library_statistics():
    """
    Return basic statistics about the animation library.
    """

    animations = load_database()

    statistics = {

        "total": len(
            animations
        ),

        "categories": {},

        "subcategories": {},

        "orientations": {},

        "total_duration": 0.0
    }

    for animation in animations:

        category = animation.get(
            "category",
            "unknown"
        )

        subcategory = animation.get(
            "subcategory",
            "unknown"
        )

        orientation = animation.get(
            "orientation",
            "unknown"
        )

        duration = float(
            animation.get(
                "duration",
                0
            )
        )

        statistics[
            "categories"
        ][category] = (
            statistics[
                "categories"
            ].get(
                category,
                0
            ) + 1
        )

        statistics[
            "subcategories"
        ][subcategory] = (
            statistics[
                "subcategories"
            ].get(
                subcategory,
                0
            ) + 1
        )

        statistics[
            "orientations"
        ][orientation] = (
            statistics[
                "orientations"
            ].get(
                orientation,
                0
            ) + 1
        )

        statistics[
            "total_duration"
        ] += duration

    statistics[
        "total_duration"
    ] = round(
        statistics[
            "total_duration"
        ],
        2
    )

    return statistics


# ============================================================
# PRINT LIBRARY STATISTICS
# ============================================================

def print_library_statistics():
    """
    Print a readable summary of the library.
    """

    statistics = get_library_statistics()

    print()
    print("=" * 70)
    print("ANIMATION LIBRARY STATISTICS")
    print("=" * 70)

    print(
        f"\nTotal animations: "
        f"{statistics['total']}"
    )

    print(
        f"Total duration: "
        f"{statistics['total_duration']} seconds"
    )

    print("\nCategories:")

    for category, count in sorted(
        statistics["categories"].items()
    ):

        print(
            f"  {category}: {count}"
        )

    print("\nOrientations:")

    for orientation, count in sorted(
        statistics["orientations"].items()
    ):

        print(
            f"  {orientation}: {count}"
        )


# ============================================================
# COMMAND-LINE TEST
# ============================================================

def run_library_test():
    """
    Test the library system.
    """

    print()
    print("=" * 70)
    print("AI VIDEO AUTOMATION")
    print("ANIMATION LIBRARY SYSTEM")
    print("=" * 70)

    animations = scan_library()

    save_database(
        animations
    )

    print_library_statistics()

    print()
    print("=" * 70)
    print("LIBRARY TEST COMPLETED")
    print("=" * 70)


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    run_library_test()
