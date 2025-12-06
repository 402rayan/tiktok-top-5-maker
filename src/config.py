from dataclasses import dataclass
from pathlib import Path
from typing import Optional


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


@dataclass
class TextOverlayConfig:
    text: str = "TEST TEXT"
    font_path: Optional[Path] = None
    font_size: int = 60
    font_color: str = "white"
    x_position: str = "(w-text_w)/2"
    y_position: str = "(h-text_h)/2"
    box_enabled: bool = False
    box_color: str = "black@0.5"
    box_border_width: int = 10
    text_max_width: Optional[int] = None
    line_spacing: int = 0
