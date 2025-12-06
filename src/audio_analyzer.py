import subprocess
from pathlib import Path

from exceptions import AudioAnalysisError


def validate_audio_file(audio_path: Path) -> None:
    if not audio_path.exists():
        raise AudioAnalysisError(f"Audio file not found: {audio_path}")

    if not audio_path.is_file():
        raise AudioAnalysisError(f"Not a file: {audio_path}")

    if audio_path.stat().st_size == 0:
        raise AudioAnalysisError(f"Empty audio file: {audio_path}")


def get_audio_duration(audio_path: Path) -> float:
    validate_audio_file(audio_path)

    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        raise AudioAnalysisError("ffprobe not found. Please install FFmpeg.")

    if result.returncode != 0:
        raise AudioAnalysisError(f"Failed to analyze audio: {result.stderr}")

    try:
        duration = float(result.stdout.strip())
    except ValueError:
        raise AudioAnalysisError(f"Invalid duration value: {result.stdout}")

    if duration <= 0:
        raise AudioAnalysisError(f"Invalid audio duration: {duration}")

    return duration
