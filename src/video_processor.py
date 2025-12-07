import logging
import subprocess
from pathlib import Path
from typing import Optional

from config import ProcessingPaths, TextOverlayConfig, TransitionConfig, VideoConfig
from exceptions import FFmpegExecutionError
from ffmpeg_builder import (
    build_concat_command,
    build_dual_video_normalize_command,
    build_normalize_command,
    build_transition_command,
)
from file_handler import (
    discover_input_videos,
    ensure_output_directory,
    temp_directory_manager,
    validate_video_files,
)

logger = logging.getLogger(__name__)


def calculate_foreground_dimensions(
    counter_y_position: int,
    counter_height: int,
    video_config: VideoConfig,
    target_width: int = 1080,
    target_height: int = 1920,
) -> dict:
    """Calculate dimensions and position for foreground video.

    Args:
        counter_y_position: Y position where counter starts
        counter_height: Total height of the counter
        video_config: Video configuration including dual video settings
        target_width: Target canvas width (default: 1080)
        target_height: Target canvas height (default: 1920)

    Returns:
        dict with keys: 'max_width', 'max_height', 'y_pos', 'x_pos'
    """
    dual_config = video_config.dual_video

    counter_end_y = counter_y_position + counter_height

    # Calculate available space
    available_height = (
        target_height
        - counter_end_y
        - dual_config.foreground_top_margin
        - dual_config.foreground_bottom_margin
    )

    available_width = (
        target_width
        - dual_config.foreground_left_margin
        - dual_config.foreground_right_margin
    )

    # Edge case: ensure minimum height
    if available_height < dual_config.min_foreground_height:
        logger.warning(
            f"Counter takes too much space! Available height: {available_height}px, "
            f"minimum required: {dual_config.min_foreground_height}px"
        )
        available_height = dual_config.min_foreground_height

    return {
        'max_width': available_width,
        'max_height': available_height,
        'y_pos': counter_end_y + dual_config.foreground_top_margin,
        'x_pos': dual_config.foreground_left_margin,
    }


class VideoProcessor:
    def __init__(
        self,
        config: VideoConfig,
        paths: ProcessingPaths,
        transition_config: TransitionConfig,
        sfx_path: Path,
        text_config: Optional[TextOverlayConfig] = None,
        per_video_text_configs: Optional[list[list[TextOverlayConfig]]] = None,
        counter_y_position: int = 310,
        input_videos: Optional[list[Path]] = None,
    ):
        self.config = config
        self.paths = paths
        self.transition_config = transition_config
        self.sfx_path = sfx_path
        self.text_config = text_config
        self.per_video_text_configs = per_video_text_configs
        self.counter_y_position = counter_y_position
        self.input_videos = input_videos

    def process(self, output_filename: str) -> Path:
        logger.info("Starting video processing pipeline")

        # Use provided sorted videos or discover them
        if self.input_videos is not None:
            input_videos = self.input_videos
        else:
            input_videos = discover_input_videos(self.paths.input_dir)
        logger.info(f"Found {len(input_videos)} video(s) to process")

        validate_video_files(input_videos)
        logger.info("Input validation completed")

        ensure_output_directory(self.paths.output_dir)

        with temp_directory_manager() as temp_dir:
            logger.info(f"Created temporary directory: {temp_dir}")

            normalized_videos = self._normalize_videos(input_videos, temp_dir)
            logger.info("Video normalization completed")

            transition_videos = self._generate_transition_videos(
                len(input_videos), temp_dir
            )
            logger.info("Transition videos generated")

            concat_list_path = self._create_concat_file_list(
                normalized_videos, transition_videos, temp_dir
            )
            logger.info("Concat file list created")

            # Concatenate to temporary file first
            temp_output = temp_dir / "concat_output.mp4"
            self._concatenate_videos(concat_list_path, temp_output)
            logger.info("Videos concatenated")

            # Trim first 2 frames and save to final output
            output_path = self.paths.output_dir / output_filename
            self._trim_beginning(temp_output, output_path)
            logger.info("Trimmed first frames")

        logger.info(f"Processing complete: {output_path}")
        return output_path

    def _normalize_videos(
        self, input_videos: list[Path], temp_dir: Path
    ) -> list[Path]:
        normalized_videos = []

        # Calculate counter height (same for all videos)
        dual_config = self.config.dual_video
        counter_line_height = dual_config.counter_font_size + dual_config.counter_line_spacing
        counter_height = len(input_videos) * counter_line_height

        for i, video_path in enumerate(input_videos):
            output_path = temp_dir / f"normalized_{i}.mp4"
            logger.info(f"Normalizing video {i + 1}/{len(input_videos)}: {video_path.name}")

            # Get text configs for this specific video
            text_configs = None
            if self.per_video_text_configs and i < len(self.per_video_text_configs):
                text_configs = self.per_video_text_configs[i]
            elif self.text_config:
                text_configs = [self.text_config]

            # Calculate foreground dimensions
            fg_dims = calculate_foreground_dimensions(
                self.counter_y_position,
                counter_height,
                self.config,
            )

            # Use dual video builder
            command = build_dual_video_normalize_command(
                video_path,
                output_path,
                self.config,
                fg_dims,
                text_configs,
            )

            self._execute_ffmpeg(command, f"normalize video {i}")
            normalized_videos.append(output_path)

        return normalized_videos

    def _generate_transition_videos(
        self, num_videos: int, temp_dir: Path
    ) -> list[Path]:
        # Generate transitions between videos + final transition
        num_transitions = num_videos
        transition_videos = []

        for i in range(num_transitions):
            output_path = temp_dir / f"transition_{i}.mp4"
            logger.info(f"Generating transition {i + 1}/{num_transitions}")

            command = build_transition_command(
                self.transition_config.duration,
                output_path,
                self.config,
                self.sfx_path,
            )

            self._execute_ffmpeg(command, f"generate transition {i}")
            transition_videos.append(output_path)

        return transition_videos

    def _create_concat_file_list(
        self,
        normalized_videos: list[Path],
        transition_videos: list[Path],
        temp_dir: Path,
    ) -> Path:
        concat_list_path = temp_dir / "concat_list.txt"

        with open(concat_list_path, "w") as f:
            for i, video_path in enumerate(normalized_videos):
                f.write(f"file '{video_path}'\n")

                # Add transition after each video (including after the last one)
                if i < len(transition_videos):
                    f.write(f"file '{transition_videos[i]}'\n")

        return concat_list_path

    def _concatenate_videos(
        self, concat_list_path: Path, output_path: Path
    ) -> None:
        logger.info("Concatenating all videos and transitions")

        command = build_concat_command(concat_list_path, output_path)
        self._execute_ffmpeg(command, "concatenate videos")

    def _trim_beginning(self, input_path: Path, output_path: Path) -> None:
        """Trim first 2 frames from video to remove black frames."""
        from ffmpeg_builder import build_trim_command

        logger.info("Trimming first 2 frames from video")

        command = build_trim_command(input_path, output_path, frames_to_skip=2, fps=self.config.target_fps)
        self._execute_ffmpeg(command, "trim beginning frames")

    def _execute_ffmpeg(self, command: list[str], description: str) -> None:
        logger.info(f"Executing: {description}")
        logger.debug(f"Command: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=3600,
            )
        except subprocess.TimeoutExpired:
            raise FFmpegExecutionError(f"FFmpeg timeout during: {description}")
        except FileNotFoundError:
            raise FFmpegExecutionError("FFmpeg not found. Please install FFmpeg.")

        if result.returncode != 0:
            error_msg = f"FFmpeg failed during: {description}\n"
            error_msg += f"Return code: {result.returncode}\n"
            error_msg += f"stderr: {result.stderr}"
            logger.error(error_msg)
            raise FFmpegExecutionError(error_msg)

        logger.debug(f"Completed: {description}")
