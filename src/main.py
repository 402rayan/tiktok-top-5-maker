#!/usr/bin/env python3

import argparse
import logging
import sys
from pathlib import Path

from audio_analyzer import get_audio_duration
from config import ProcessingPaths, TextOverlayConfig, TransitionConfig, VideoConfig
from counter_generator import calculate_adaptive_font_size, generate_counter_data
from exceptions import VideoProcessingError
from ffmpeg_builder import wrap_text_to_lines
from file_handler import discover_input_videos
from text_styles import TextStyles
from video_metadata import load_video_metadata, match_videos_to_metadata
from video_processor import VideoProcessor

logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TikTok Top 5 Video Maker - Concatenate videos with transitions"
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(__file__).parent.parent / "input",
        help="Directory containing input MP4 files (default: ./input)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "output",
        help="Directory for output video (default: ./output)",
    )

    parser.add_argument(
        "--output-name",
        type=str,
        default="top5_compilation.mp4",
        help="Output filename (default: top5_compilation.mp4)",
    )

    parser.add_argument(
        "--resolution",
        type=str,
        default="1080x1920",
        help="Target resolution WxH (default: 1080x1920)",
    )

    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="Target framerate (default: 60)",
    )

    parser.add_argument(
        "--crop-anchor",
        type=str,
        choices=["center", "top", "bottom", "left", "right"],
        default="center",
        help="Crop anchor position (default: center)",
    )

    parser.add_argument(
        "--title",
        type=str,
        default="Top 5",
        help="Title text to display at the top of videos (default: Top 5)",
    )

    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Path to videos.json metadata file (default: <input-dir>/videos.json)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("video_processing.log"),
        ],
    )


def main() -> None:
    args = parse_arguments()
    setup_logging(args.verbose)

    try:
        assets_dir = Path(__file__).parent.parent / "assets"
        sfx_path = assets_dir / "sfx" / "buzz_tiktok_sound.mp3"
        font_path = assets_dir / "fonts" / "ProximaNova-Bold.ttf"

        width, height = map(int, args.resolution.split("x"))

        video_config = VideoConfig(
            target_width=width,
            target_height=height,
            target_fps=args.fps,
        )

        paths = ProcessingPaths(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            assets_dir=assets_dir,
        )

        transition_duration = get_audio_duration(sfx_path)
        logger.info(f"Detected transition duration: {transition_duration:.2f}s")

        transition_config = TransitionConfig(
            duration=transition_duration,
            crop_anchor=args.crop_anchor,
        )

        # Load metadata
        metadata_path = args.metadata or (args.input_dir / "videos.json")
        metadata = load_video_metadata(metadata_path)
        logger.info(f"Metadata loaded: {metadata is not None}")

        # Discover videos
        input_videos = discover_input_videos(args.input_dir)
        logger.info(f"Found {len(input_videos)} video(s)")

        # Match videos to titles and sort by order
        input_videos, video_titles = match_videos_to_metadata(input_videos, metadata)

        # Generate per-video text configs
        title_config = TextStyles.get_top5_title(font_path, args.title)

        # Calculate title height to position counter below it
        title_font_size = 70
        title_y_start = video_config.title_y_position
        title_line_spacing = 10
        title_max_width = 1000

        # Calculate how many lines the title will have
        chars_per_line = int(title_max_width / (title_font_size * 0.6))
        title_lines = wrap_text_to_lines(args.title.upper(), chars_per_line)
        num_title_lines = len(title_lines)

        # Calculate title end position
        title_height = num_title_lines * title_font_size + (num_title_lines - 1) * title_line_spacing
        title_end = title_y_start + title_height

        # Counter starts 100px below title
        counter_y_position = title_end + 100

        logger.debug(f"Title has {num_title_lines} line(s), counter starts at y={counter_y_position}")

        per_video_text_configs = []

        for i in range(len(input_videos)):
            # Generate numbers and titles separately
            numbers, titles = generate_counter_data(i, len(input_videos), video_titles)

            # Create configs for this video
            video_configs = [title_config]

            # Numbers config: all numbers with fixed size from config
            numbers_text = "\n".join(numbers)
            numbers_config = TextOverlayConfig(
                text=numbers_text,
                font_path=font_path,
                font_size=video_config.dual_video.counter_font_size,
                font_color="white",
                x_position="100",
                y_position=str(counter_y_position),
                box_enabled=False,
                line_spacing=video_config.dual_video.counter_line_spacing,
                text_border_width=4,
                text_border_color="black",
            )
            video_configs.append(numbers_config)

            # Titles configs: individual titles with adaptive size and baseline alignment
            number_font_size = video_config.dual_video.counter_font_size
            counter_line_height = number_font_size + video_config.dual_video.counter_line_spacing

            for idx, title in enumerate(titles):
                if title:
                    adaptive_size = calculate_adaptive_font_size(title)

                    # Calculate baseline alignment offset
                    # Smaller font needs to be shifted down to align baseline with larger number
                    baseline_offset = number_font_size - adaptive_size - 7.5 # align with counter

                    y_pos = counter_y_position + (idx * counter_line_height) + baseline_offset

                    title_config_item = TextOverlayConfig(
                        text=title,
                        font_path=font_path,
                        font_size=adaptive_size,
                        font_color="white",
                        x_position="200",  # Offset to the right of numbers
                        y_position=str(y_pos),
                        box_enabled=False,
                        text_border_width=3,
                        text_border_color="black",
                    )
                    video_configs.append(title_config_item)

            per_video_text_configs.append(video_configs)
            logger.debug(f"Video {i}: {len(titles) - titles.count(None)} title(s) revealed")

        # Create processor with per-video configs
        processor = VideoProcessor(
            video_config,
            paths,
            transition_config,
            sfx_path,
            text_config=None,
            per_video_text_configs=per_video_text_configs,
            counter_y_position=counter_y_position,
            input_videos=input_videos,
        )
        output_path = processor.process(args.output_name)

        logger.info(f"SUCCESS! Output saved to: {output_path}")

    except VideoProcessingError as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
