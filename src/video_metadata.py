import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from exceptions import InvalidInputError

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    file: str
    title: str


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

            metadata_list.append(
                VideoMetadata(file=str(item["file"]), title=str(item["title"]))
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
) -> list[Optional[str]]:
    """Match video files to their titles from metadata.

    Args:
        videos: List of video file paths
        metadata: VideoMetadataCollection or None

    Returns:
        List of titles (or None) in the same order as videos
    """
    if metadata is None:
        return [None] * len(videos)

    titles = []
    for video_path in videos:
        filename = video_path.name
        title = metadata.get_title_for_file(filename)

        if title is None:
            logger.warning(f"No metadata found for video: {filename}")

        titles.append(title)

    return titles
