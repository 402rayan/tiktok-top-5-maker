from pathlib import Path

from config import VideoConfig


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


def build_normalize_command(
    input_path: Path,
    output_path: Path,
    config: VideoConfig,
    crop_anchor: str,
) -> list[str]:
    scale_filter = f"scale={config.target_width}:{config.target_height}:force_original_aspect_ratio=increase"
    crop_filter = get_crop_filter(crop_anchor, config.target_width, config.target_height)
    video_filter = f"{scale_filter},{crop_filter}"

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
) -> list[str]:
    command = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", f"color=black:s={config.target_width}x{config.target_height}:d={duration}",
        "-f", "lavfi",
        "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100:duration={duration}",
        "-r", str(config.target_fps),
        "-c:v", config.video_codec,
        "-preset", "ultrafast",
        "-crf", "0",
        "-c:a", config.audio_codec,
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


def build_audio_mix_command(
    base_video_path: Path,
    sfx_audio_path: Path,
    transition_timestamps: list[float],
    output_path: Path,
    config: VideoConfig,
) -> list[str]:
    command = ["ffmpeg", "-i", str(base_video_path)]

    for _ in transition_timestamps:
        command.extend(["-i", str(sfx_audio_path)])

    filters = []
    audio_inputs = ["0:a"]

    for i, timestamp in enumerate(transition_timestamps):
        delay_ms = int(timestamp * 1000)
        filters.append(f"[{i + 1}:a]adelay=delays={delay_ms}:all=1[sfx{i}]")
        audio_inputs.append(f"[sfx{i}]")

    num_inputs = len(audio_inputs)
    amix_filter = f"{''.join(audio_inputs)}amix=inputs={num_inputs}:duration=first[aout]"
    filters.append(amix_filter)

    filter_complex = ";".join(filters)

    command.extend([
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", config.audio_codec,
        "-b:a", config.audio_bitrate,
        "-y",
        str(output_path),
    ])

    return command
