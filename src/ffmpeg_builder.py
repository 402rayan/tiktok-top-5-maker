from pathlib import Path
from typing import Optional

from config import TextOverlayConfig, VideoConfig


def get_crop_filter(anchor: str, target_width: int, target_height: int) -> str:
    crop_formulas = {
        "center": f"crop={target_width}:{target_height}:(iw-{target_width})/2:(ih-{target_height})/2",
        "top": f"crop={target_width}:{target_height}:(iw-{target_width})/2:0",
        "bottom": f"crop={target_width}:{target_height}:(iw-{target_width})/2:ih-{target_height}",
        "left": f"crop={target_width}:{target_height}:0:(ih-{target_height})/2",
        "right": f"crop={target_width}:{target_height}:iw-{target_width}:(ih-{target_height})/2",
        "top_left": f"crop={target_width}:{target_height}:0:0",
        "top_right": f"crop={target_width}:{target_height}:iw-{target_width}:0",
        "bottom_left": f"crop={target_width}:{target_height}:0:ih-{target_height}",
        "bottom_right": f"crop={target_width}:{target_height}:iw-{target_width}:ih-{target_height}",
    }

    return crop_formulas.get(anchor, crop_formulas["center"])


def wrap_text_to_lines(text: str, max_chars_per_line: int = 20) -> list[str]:
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        word_length = len(word)
        if current_length + word_length + len(current_line) <= max_chars_per_line:
            current_line.append(word)
            current_length += word_length
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_length

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def get_text_overlay_filter(text_config: TextOverlayConfig) -> str:
    if not text_config.font_path:
        raise ValueError("Font path is required for text overlay")

    font_path_escaped = str(text_config.font_path).replace("\\", "/").replace(":", "\\:")

    lines = [text_config.text]
    if text_config.text_max_width:
        chars_per_line = int(text_config.text_max_width / (text_config.font_size * 0.6))
        lines = wrap_text_to_lines(text_config.text, chars_per_line)

    filters = []
    line_height = text_config.font_size + text_config.line_spacing

    for i, line in enumerate(lines):
        text_escaped = line.replace("'", "'\\\\\\''").replace(":", "\\:")

        y_offset = i * line_height
        if text_config.y_position.isdigit():
            y_pos = str(int(text_config.y_position) + y_offset)
        else:
            y_pos = f"({text_config.y_position})+{y_offset}" if y_offset > 0 else text_config.y_position

        drawtext_params = [
            f"text='{text_escaped}'",
            f"fontfile='{font_path_escaped}'",
            f"fontsize={text_config.font_size}",
            f"fontcolor={text_config.font_color}",
            f"x={text_config.x_position}",
            f"y={y_pos}",
        ]

        if text_config.box_enabled:
            drawtext_params.extend([
                "box=1",
                f"boxcolor={text_config.box_color}",
                f"boxborderw={text_config.box_border_width}",
            ])

        filters.append("drawtext=" + ":".join(drawtext_params))

    return ",".join(filters)


def build_normalize_command(
    input_path: Path,
    output_path: Path,
    config: VideoConfig,
    crop_anchor: str,
    text_config: Optional[TextOverlayConfig] = None,
) -> list[str]:
    scale_filter = f"scale={config.target_width}:{config.target_height}:force_original_aspect_ratio=increase"
    crop_filter = get_crop_filter(crop_anchor, config.target_width, config.target_height)

    filters = [scale_filter, crop_filter]

    if text_config:
        text_filter = get_text_overlay_filter(text_config)
        filters.append(text_filter)

    video_filter = ",".join(filters)

    command = [
        "ffmpeg",
        "-i", str(input_path),
        "-vf", video_filter,
        "-r", str(config.target_fps),
        "-c:v", config.video_codec,
        "-preset", config.preset,
        "-crf", str(config.crf),
        "-b:v", config.video_bitrate,
        "-c:a", config.audio_codec,
        "-b:a", config.audio_bitrate,
        "-y",
        str(output_path),
    ]

    return command


def build_transition_command(
    duration: float,
    output_path: Path,
    config: VideoConfig,
    sfx_path: Path,
) -> list[str]:
    command = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", f"color=black:s={config.target_width}x{config.target_height}:d={duration}",
        "-i", str(sfx_path),
        "-r", str(config.target_fps),
        "-c:v", config.video_codec,
        "-preset", "ultrafast",
        "-crf", "0",
        "-c:a", config.audio_codec,
        "-shortest",
        "-y",
        str(output_path),
    ]

    return command


def build_concat_command(file_list_path: Path, output_path: Path) -> list[str]:
    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", str(file_list_path),
        "-c", "copy",
        "-y",
        str(output_path),
    ]

    return command
