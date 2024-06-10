# MKV Song Chapterizer

## Description

MKV Song Chapterizer is a Python application that identifies songs in an MKV video file, creates chapters based on the detected songs, and adds these chapters to the MKV file. Each chapter is based on a 15-second audio chunk sampled every 5 minutes from the video, and the song title is used as the chapter name.

## Requirements

- Python 3.6+
- `moviepy` library
- `pydub` library
- `aiohttp` library
- `ffmpeg` (for audio extraction)
- `MKVToolNix` (for adding chapters to MKV files)

## Installation

1. **Install Python libraries:**

    ```bash
    pip install moviepy pydub aiohttp
    ```

2. **Install FFmpeg:**

    - On Ubuntu:
    
        ```bash
        sudo apt-get install ffmpeg
        ```

    - On macOS:

        ```bash
        brew install ffmpeg
        ```

    - On Windows:
        Download FFmpeg from [FFmpeg.org](https://ffmpeg.org/download.html) and follow the installation instructions.

3. **Install MKVToolNix:**

    - On Ubuntu:
    
        ```bash
        sudo apt-get install mkvtoolnix
        ```

    - On macOS:

        ```bash
        brew install mkvtoolnix
        ```

    - On Windows:
        Download MKVToolNix from [MKVToolNix.download](https://mkvtoolnix.download/downloads.html) and follow the installation instructions.

## Getting an API Key

This application uses the [AudD API](https://audd.io) to identify songs. You will need to obtain an API key from AudD.

1. Go to the [AudD website](https://audd.io).
2. Sign up for an account.
3. Navigate to the API section and generate an API key.

## Usage

1. **Prepare your environment:**
    Ensure you have installed all required dependencies and obtained your AudD API key.

2. **Run the script:**

    ```bash
    python script.py input_video.mkv output_chapters.xml
    ```

    - `input_video.mkv`: Path to the MKV video file.
    - `output_chapters.xml`: Path to the temporary output XML file for chapters.

## Notes

- Ensure that the MKVToolNix binaries (`mkvpropedit`) are in your system's PATH.
- This script extracts audio from the video file to a temporary file, identifies songs, generates an XML file with chapters, and then updates the MKV file with these chapters.
- The script uses a 15-second audio chunk every 5 minutes to identify the song. This interval can be adjusted if needed.

## Example

### Input Video

A video file with multiple songs.

### Output

An MKV file with chapters added at 5-minute intervals, each chapter named after the detected song title.

```xml
<?xml version='1.0' encoding='utf-8'?>
<Chapters>
    <EditionEntry>
        <ChapterAtom>
            <ChapterTimeStart>00:00:00.000</ChapterTimeStart>
            <ChapterDisplay>
                <ChapterString>Sugar Magnolia</ChapterString>
            </ChapterDisplay>
        </ChapterAtom>
        <ChapterAtom>
            <ChapterTimeStart>00:5:00.000</ChapterTimeStart>
            <ChapterDisplay>
                <ChapterString>Deal</ChapterString>
            </ChapterDisplay>
        </ChapterAtom>
        <!-- More ChapterAtom elements as needed -->
    </EditionEntry>
</Chapters>
