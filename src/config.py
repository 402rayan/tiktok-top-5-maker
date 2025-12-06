from dataclasses import dataclass
from pathlib import Path


@dataclass
class VideoConfig:
    target_width: int = 1080
    target_height: int = 1920
    target_fps: int = 60
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    video_bitrate: str = "5M"
    audio_bitrate: str = "192k"
    preset: str = "medium"
    crf: int = 23


@dataclass
class ProcessingPaths:
    input_dir: Path
    output_dir: Path
    assets_dir: Path


@dataclass
class TransitionConfig:
    duration: float
    crop_anchor: str = "center"
    transition_audio_volume: float = 1.0
    video_audio_volume: float = 1.0
