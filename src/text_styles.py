from pathlib import Path

from config import TextOverlayConfig, VideoConfig


class TextStyles:
    @staticmethod
    def get_top5_title(font_path: Path, title_text: str, y_position: int = VideoConfig.title_y_position) -> TextOverlayConfig:
        return TextOverlayConfig(
            text=title_text.upper(),
            font_path=font_path,
            font_size=70,
            font_color="black",
            x_position="(w-text_w)/2",
            y_position=str(y_position),
            box_enabled=True,
            box_color="white",
            box_border_width=25,
            text_max_width=1000,
            line_spacing=10,
        )

    @staticmethod
    def get_subtitle_style(font_path: Path, subtitle_text: str) -> TextOverlayConfig:
        return TextOverlayConfig(
            text=subtitle_text,
            font_path=font_path,
            font_size=50,
            font_color="white",
            x_position="(w-text_w)/2",
            y_position="h-100",
            box_enabled=True,
            box_color="black@0.7",
            box_border_width=15,
        )

    @staticmethod
    def get_countdown_style(font_path: Path, number: str) -> TextOverlayConfig:
        return TextOverlayConfig(
            text=number,
            font_path=font_path,
            font_size=120,
            font_color="yellow",
            x_position="(w-text_w)/2",
            y_position="(h-text_h)/2",
            box_enabled=True,
            box_color="black@0.8",
            box_border_width=25,
        )

    @staticmethod
    def get_counter_style(font_path: Path, counter_text: str, y_position: int = 240) -> TextOverlayConfig:
        return TextOverlayConfig(
            text=counter_text,
            font_path=font_path,
            font_size=80,
            font_color="white",
            x_position="100",
            y_position=str(y_position),
            box_enabled=False,
            text_max_width=1000,
            line_spacing=10,
            text_border_width=4,
            text_border_color="black",
        )
