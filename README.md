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
│   ├── sfx/            # Sound effects for transitions
│   └── effects/        # Effect presets
├── input/              # Drop your MP4 videos here
├── output/             # Final compiled video
├── src/                # Processing scripts
└── temp/               # Temporary processing files (auto-created)
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
- FFmpeg (must be installed and in PATH)

## Installation

1. **Install FFmpeg**
   - macOS: `brew install ffmpeg`
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Linux: `sudo apt install ffmpeg`

2. **Verify installation**
   ```bash
   ffmpeg -version
   ```

## Usage

### Basic Usage

1. Place your MP4 videos in the `input/` directory
2. Run the processor:
   ```bash
   python3 src/main.py
   ```
3. Find your compiled video in `output/top5_compilation.mp4`

### Advanced Options

```bash
python3 src/main.py --help
```

**Available options:**
- `--input-dir PATH` - Custom input directory (default: ./input)
- `--output-dir PATH` - Custom output directory (default: ./output)
- `--output-name NAME` - Output filename (default: top5_compilation.mp4)
- `--resolution WxH` - Target resolution (default: 1080x1920)
- `--fps N` - Target framerate (default: 60)
- `--crop-anchor POSITION` - Crop position: center, top, bottom, left, right (default: center)
- `--verbose` - Enable detailed logging

**Example:**
```bash
python3 src/main.py --resolution 720x1280 --fps 30 --crop-anchor top --verbose
```

## How It Works

1. **Discovery** - Finds all .mp4 files in input/ (sorted alphabetically)
2. **Normalization** - Converts videos to 1080x1920 @ 60fps, center-crops non-matching videos
3. **Transitions** - Generates black screens with SFX (duration auto-detected from buzz_tiktok_sound.mp3)
4. **Concatenation** - Merges videos with transitions between each
5. **Audio Mixing** - Overlays SFX on transitions while keeping original video audio
6. **Output** - Saves final compilation to output/
