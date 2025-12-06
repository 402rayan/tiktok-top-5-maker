class VideoProcessingError(Exception):
    """Base exception for video processing errors."""
    pass


class FFmpegExecutionError(VideoProcessingError):
    """Raised when FFmpeg command execution fails."""
    pass


class InvalidInputError(VideoProcessingError):
    """Raised when input validation fails."""
    pass


class AudioAnalysisError(VideoProcessingError):
    """Raised when audio duration detection fails."""
    pass
