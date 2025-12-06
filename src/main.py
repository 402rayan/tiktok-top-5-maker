#!/usr/bin/env python3

import argparse
import logging
import sys
from pathlib import Path

from audio_analyzer import get_audio_duration
from config import ProcessingPaths, TransitionConfig, VideoConfig
from exceptions import VideoProcessingError
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

        processor = VideoProcessor(video_config, paths, transition_config, sfx_path)
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
