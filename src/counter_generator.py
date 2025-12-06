from typing import Optional


def generate_counter_data(
    current_index: int,
    total_videos: int,
    video_titles: list[Optional[str]],
) -> tuple[list[str], list[Optional[str]]]:
    """Generate counter numbers and titles separately for video overlay.

    Displays numbers 1 to N from top to bottom, reveals titles from bottom to top.
    Returns numbers and titles as separate lists for independent styling.

    Examples:
        current_index=0, total=3, titles=["December", "November", "October"]
        → numbers: ["1.", "2.", "3."]
        → titles: [None, None, "December"]

        current_index=1, total=3, titles=["December", "November", "October"]
        → numbers: ["1.", "2.", "3."]
        → titles: [None, "November", "December"]

    Args:
        current_index: Index of the current video (0-based)
        total_videos: Total number of videos in the compilation
        video_titles: List of titles (or None) for each video, in order

    Returns:
        Tuple of (numbers list, titles list)
    """
    numbers = []
    titles = []

    for display_position in range(total_videos):
        number = display_position + 1  # 1, 2, 3, ..., N
        video_index = total_videos - 1 - display_position  # N-1, N-2, ..., 0

        numbers.append(f"{number}.")

        # Show title if we've reached this video
        if video_index <= current_index and video_titles[video_index]:
            titles.append(video_titles[video_index])
        else:
            titles.append(None)

    return numbers, titles


def calculate_adaptive_font_size(text: str, base_size: int = 70, min_size: int = 45) -> int:
    """Calculate font size based on text length using affine function.

    Longer texts get slightly smaller font size.

    Args:
        text: The text to display
        base_size: Maximum font size for short texts
        min_size: Minimum font size for very long texts

    Returns:
        Calculated font size
    """
    text_length = len(text)

    # Affine penalty: reduce by 1px per character over 15
    if text_length <= 15:
        return base_size

    penalty = text_length - 15
    font_size = base_size - penalty

    # Ensure minimum size
    return max(font_size, min_size)
