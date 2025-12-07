import json
import logging
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from exceptions import InvalidInputError

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    file: str
    title: str
    order: int


@dataclass
class VideoMetadataCollection:
    metadata: list[VideoMetadata]

    @classmethod
    def from_json(cls, json_path: Path) -> "VideoMetadataCollection":
        """Load and parse video metadata from JSON file.

        Args:
            json_path: Path to the videos.json file

        Returns:
            VideoMetadataCollection instance

        Raises:
            InvalidInputError: If JSON is malformed or has invalid structure
        """
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidInputError(f"Malformed JSON in {json_path}: {e}")
        except Exception as e:
            raise InvalidInputError(f"Failed to read {json_path}: {e}")

        if not isinstance(data, list):
            raise InvalidInputError(
                f"Invalid JSON structure: expected list, got {type(data).__name__}"
            )

        metadata_list = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise InvalidInputError(
                    f"Invalid item at index {i}: expected object, got {type(item).__name__}"
                )

            if "file" not in item or "title" not in item:
                raise InvalidInputError(
                    f"Invalid item at index {i}: missing 'file' or 'title' field"
                )

            if "order" not in item:
                raise InvalidInputError(
                    f"Invalid item at index {i}: missing 'order' field"
                )

            metadata_list.append(
                VideoMetadata(
                    file=str(item["file"]),
                    title=str(item["title"]),
                    order=int(item["order"])
                )
            )

        return cls(metadata=metadata_list)

    def get_title_for_file(self, filename: str) -> Optional[str]:
        """Get title for a given video filename.

        Args:
            filename: Name of the video file (basename)

        Returns:
            Title string if found, None otherwise
        """
        for meta in self.metadata:
            if meta.file == filename:
                return meta.title
        return None


def load_video_metadata(path: Path) -> Optional[VideoMetadataCollection]:
    """Load video metadata from JSON file with graceful degradation.

    Args:
        path: Path to the videos.json file

    Returns:
        VideoMetadataCollection if file exists and is valid, None if file doesn't exist

    Raises:
        InvalidInputError: If file exists but JSON is malformed
    """
    if not path.exists():
        logger.info(f"Metadata file not found: {path} - will use numbers only")
        return None

    try:
        collection = VideoMetadataCollection.from_json(path)
        logger.info(f"Loaded metadata for {len(collection.metadata)} video(s)")
        return collection
    except InvalidInputError:
        raise


def match_videos_to_metadata(
    videos: list[Path], metadata: Optional[VideoMetadataCollection]
) -> tuple[list[Path], list[Optional[str]]]:
    """Match video files to their titles from metadata and sort by order.

    Args:
        videos: List of video file paths
        metadata: VideoMetadataCollection or None

    Returns:
        Tuple of (sorted videos, list of titles) in order defined by metadata
    """
    if metadata is None:
        return videos, [None] * len(videos)

    # Normalize Unicode strings to NFC for consistent comparison
    # macOS uses NFD (decomposed) for filesystem, but JSON typically uses NFC (composed)
    def normalize(s: str) -> str:
        return unicodedata.normalize('NFC', s)

    # Create a mapping of normalized filename -> (order, title, path)
    video_map = {}
    for video_path in videos:
        filename = video_path.name
        normalized_filename = normalize(filename)
        video_map[normalized_filename] = video_path

    # Match videos to metadata and collect with order
    matched_videos = []
    for meta in metadata.metadata:
        normalized_meta_file = normalize(meta.file)
        if normalized_meta_file in video_map:
            matched_videos.append((meta.order, meta.title, video_map[normalized_meta_file]))
        else:
            logger.warning(f"Video file not found for metadata: {meta.file}")

    # Warn about videos without metadata
    for video_path in videos:
        normalized_filename = normalize(video_path.name)
        if not any(normalize(meta.file) == normalized_filename for meta in metadata.metadata):
            logger.warning(f"No metadata found for video: {video_path.name}")

    # Sort by order (descending: 5, 4, 3, 2, 1)
    matched_videos.sort(key=lambda x: x[0], reverse=True)

    # Extract sorted videos and titles
    sorted_videos = [video for _, _, video in matched_videos]
    titles = [title for _, title, _ in matched_videos]

    return sorted_videos, titles
