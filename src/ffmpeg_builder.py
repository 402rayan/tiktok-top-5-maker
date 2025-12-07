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

    # First split by explicit newlines, then wrap each segment if needed
    segments = text_config.text.split('\n')
    lines = []

    if text_config.text_max_width:
        chars_per_line = int(text_config.text_max_width / (text_config.font_size * 0.6))
        for segment in segments:
            wrapped = wrap_text_to_lines(segment, chars_per_line)
            lines.extend(wrapped)
    else:
        lines = segments

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

        if text_config.text_border_width > 0:
            drawtext_params.extend([
                f"borderw={text_config.text_border_width}",
                f"bordercolor={text_config.text_border_color}",
            ])

        filters.append("drawtext=" + ":".join(drawtext_params))

    return ",".join(filters)


def build_normalize_command(
    input_path: Path,
    output_path: Path,
    config: VideoConfig,
    crop_anchor: str,
    text_config: Optional[TextOverlayConfig] = None,
    text_configs: Optional[list[TextOverlayConfig]] = None,
) -> list[str]:
    scale_filter = f"scale={config.target_width}:{config.target_height}:force_original_aspect_ratio=increase"
    crop_filter = get_crop_filter(crop_anchor, config.target_width, config.target_height)

    filters = [scale_filter, crop_filter]

    # Support both single and multiple text configs
    if text_config and not text_configs:
        text_configs = [text_config]

    if text_configs:
        for tc in text_configs:
            text_filter = get_text_overlay_filter(tc)
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


def build_dual_video_normalize_command(
    input_path: Path,
    output_path: Path,
    config: VideoConfig,
    foreground_dimensions: dict,
    text_configs: Optional[list[TextOverlayConfig]] = None,
) -> list[str]:
    """Build FFmpeg command for dual video display with blurred background.

    Creates two synchronized video streams from the same input:
    - Background: Blurred video scaled to fill entire frame
    - Foreground: Original video scaled to fit available space

    Args:
        input_path: Path to input video file
        output_path: Path where output will be saved
        config: Video configuration including dual video settings
        foreground_dimensions: Dict with 'max_width', 'max_height', 'y_pos'
        text_configs: Optional list of text overlay configurations

    Returns:
        List of FFmpeg command arguments
    """
    blur_sigma = config.dual_video.blur_sigma
    fg_width = foreground_dimensions['max_width']
    fg_height = foreground_dimensions['max_height']
    fg_x_pos = foreground_dimensions['x_pos']
    fg_y_pos = foreground_dimensions['y_pos']

    # Build filter_complex
    filter_parts = [
        # Split into two streams
        "[0:v]split=2[original][blur_source]",

        # Background: scale to cover, crop, blur
        f"[blur_source]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920:(iw-1080)/2:(ih-1920)/2,"
        f"gblur=sigma={blur_sigma}[blurred_bg]",

        # Foreground: scale to fit available space with margins
        f"[original]scale=w='min({fg_width},iw)':h='min({fg_height},ih)':force_original_aspect_ratio=decrease[scaled_fg]",

        # Overlay foreground on background, centered within available space
        f"[blurred_bg][scaled_fg]overlay=x={fg_x_pos}+(({fg_width}-w)/2):y={fg_y_pos}+(({fg_height}-h)/2)[composed]",
    ]

    # Add text overlays
    if text_configs:
        text_filters = []
        for tc in text_configs:
            text_filter = get_text_overlay_filter(tc)
            text_filters.append(text_filter)

        # Apply text overlays to composed video
        text_chain = ",".join(text_filters)
        filter_parts.append(f"[composed]{text_chain}[final]")
    else:
        filter_parts.append("[composed]null[final]")

    filter_complex = ";".join(filter_parts)

    command = [
        "ffmpeg",
        "-i", str(input_path),
        "-filter_complex", filter_complex,
        "-map", "[final]",
        "-map", "0:a?",  # Include audio if present
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


def build_trim_command(input_path: Path, output_path: Path, frames_to_skip: int = 2, fps: int = 60) -> list[str]:
    """Build FFmpeg command to trim first N frames from video.

    Args:
        input_path: Input video file
        output_path: Output video file
        frames_to_skip: Number of frames to skip at the beginning
        fps: Video framerate

    Returns:
        FFmpeg command list
    """
    command = [
        "ffmpeg",
        "-i", str(input_path),
        "-vf", f"select='gte(n,{frames_to_skip})',setpts=PTS-STARTPTS",
        "-af", "asetpts=PTS-STARTPTS",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-y",
        str(output_path),
    ]

    return command
