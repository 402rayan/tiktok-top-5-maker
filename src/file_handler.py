import shutil
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from exceptions import InvalidInputError


def discover_input_videos(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        raise InvalidInputError(f"Input directory does not exist: {input_dir}")

    if not input_dir.is_dir():
        raise InvalidInputError(f"Input path is not a directory: {input_dir}")

    video_files = sorted(input_dir.glob("*.mp4"))

    return video_files


def validate_video_files(video_paths: list[Path]) -> None:
    if not video_paths:
        raise InvalidInputError("No MP4 files found in input directory")

    for path in video_paths:
        if not path.exists():
            raise InvalidInputError(f"Video file not found: {path}")

        if not path.is_file():
            raise InvalidInputError(f"Not a file: {path}")

        if path.stat().st_size == 0:
            raise InvalidInputError(f"Empty video file: {path}")


def create_temp_directory(base_dir: Optional[Path] = None) -> Path:
    if base_dir is None:
        base_dir = Path(__file__).parent.parent / "temp"

    base_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = base_dir / f"session_{int(time.time())}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    return temp_dir


def cleanup_temp_files(temp_dir: Path) -> None:
    if temp_dir.exists() and temp_dir.is_dir():
        shutil.rmtree(temp_dir, ignore_errors=True)


def ensure_output_directory(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


@contextmanager
def temp_directory_manager(base_dir: Optional[Path] = None):
    temp_dir = create_temp_directory(base_dir)
    try:
        yield temp_dir
    finally:
        cleanup_temp_files(temp_dir)
