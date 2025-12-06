import logging
import subprocess
from pathlib import Path

from config import ProcessingPaths, TransitionConfig, VideoConfig
from exceptions import FFmpegExecutionError
from ffmpeg_builder import (
    build_audio_mix_command,
    build_concat_command,
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


class VideoProcessor:
    def __init__(
        self,
        config: VideoConfig,
        paths: ProcessingPaths,
        transition_config: TransitionConfig,
        sfx_path: Path,
    ):
        self.config = config
        self.paths = paths
        self.transition_config = transition_config
        self.sfx_path = sfx_path

    def process(self, output_filename: str) -> Path:
        logger.info("Starting video processing pipeline")

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

            concatenated_path = temp_dir / "concatenated.mp4"
            self._concatenate_videos(concat_list_path, concatenated_path)
            logger.info("Videos concatenated")

            video_durations = self._get_video_durations(normalized_videos)
            transition_timestamps = self._calculate_transition_timestamps(
                video_durations
            )
            logger.info(f"Calculated {len(transition_timestamps)} transition timestamp(s)")

            output_path = self.paths.output_dir / output_filename
            self._mix_audio_with_sfx(
                concatenated_path, transition_timestamps, output_path
            )
            logger.info("Audio mixing completed")

        logger.info(f"Processing complete: {output_path}")
        return output_path

    def _normalize_videos(
        self, input_videos: list[Path], temp_dir: Path
    ) -> list[Path]:
        normalized_videos = []

        for i, video_path in enumerate(input_videos):
            output_path = temp_dir / f"normalized_{i}.mp4"
            logger.info(f"Normalizing video {i + 1}/{len(input_videos)}: {video_path.name}")

            command = build_normalize_command(
                video_path,
                output_path,
                self.config,
                self.transition_config.crop_anchor,
            )

            self._execute_ffmpeg(command, f"normalize video {i}")
            normalized_videos.append(output_path)

        return normalized_videos

    def _generate_transition_videos(
        self, num_videos: int, temp_dir: Path
    ) -> list[Path]:
        num_transitions = num_videos - 1
        transition_videos = []

        for i in range(num_transitions):
            output_path = temp_dir / f"transition_{i}.mp4"
            logger.info(f"Generating transition {i + 1}/{num_transitions}")

            command = build_transition_command(
                self.transition_config.duration,
                output_path,
                self.config,
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

                if i < len(transition_videos):
                    f.write(f"file '{transition_videos[i]}'\n")

        return concat_list_path

    def _concatenate_videos(
        self, concat_list_path: Path, output_path: Path
    ) -> None:
        logger.info("Concatenating all videos and transitions")

        command = build_concat_command(concat_list_path, output_path)
        self._execute_ffmpeg(command, "concatenate videos")

    def _get_video_durations(self, video_paths: list[Path]) -> list[float]:
        durations = []

        for video_path in video_paths:
            command = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ]

            result = subprocess.run(command, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                raise FFmpegExecutionError(f"Failed to get duration for {video_path}")

            duration = float(result.stdout.strip())
            durations.append(duration)

        return durations

    def _calculate_transition_timestamps(
        self, video_durations: list[float]
    ) -> list[float]:
        timestamps = []
        current_time = 0.0

        for i, duration in enumerate(video_durations[:-1]):
            current_time += duration
            timestamps.append(current_time)
            current_time += self.transition_config.duration

        return timestamps

    def _mix_audio_with_sfx(
        self,
        base_video_path: Path,
        transition_timestamps: list[float],
        output_path: Path,
    ) -> None:
        if not transition_timestamps:
            logger.info("No transitions to mix, copying video as-is")
            import shutil
            shutil.copy(base_video_path, output_path)
            return

        logger.info("Mixing audio with SFX overlays")

        command = build_audio_mix_command(
            base_video_path,
            self.sfx_path,
            transition_timestamps,
            output_path,
            self.config,
        )

        self._execute_ffmpeg(command, "mix audio with SFX")

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
