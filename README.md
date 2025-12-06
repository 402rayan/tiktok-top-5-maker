# TikTok Top 5 Maker

Automate the creation of TikTok "Top 5" compilation videos.

## Overview

**Input:** 5 MP4 videos
**Output:** 1 concatenated MP4 video with transitions, effects, and text overlays

## Tech Stack

- **Python 3.x** - Core scripting language
- **FFmpeg** - Video processing engine
- **PyInstaller** - Executable bundling (future)
- **Tkinter/CustomTkinter** - GUI interface (future)

## Project Structure

```
tiktok-top-5-maker/
├── assets/
│   ├── fonts/          # Custom fonts for text overlays
│   ├── transitions/    # Transition templates/configs
│   └── effects/        # Effect presets
├── input/              # Drop your 5 videos here
├── output/             # Final compiled video
├── src/                # Processing scripts
└── ffmpeg/             # FFmpeg binaries (bundled)
```

## Development Phases

1. **Phase 1:** CLI script with FFmpeg - Core video processing
2. **Phase 2:** GUI with Tkinter - User-friendly interface
3. **Phase 3:** Executable packaging - Standalone app for distribution

## Features (Planned)

- Video concatenation with smooth transitions
- Custom text overlays with font customization
- Special effects between clips
- Progress tracking
- Drag & drop interface
- One-click export

## Requirements

- Python 3.8+
- FFmpeg (will be bundled in final executable)
