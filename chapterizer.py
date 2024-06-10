import os
import logging
import asyncio
import aiohttp
import io
import tempfile
import xml.etree.ElementTree as ET
import subprocess
from moviepy.editor import VideoFileClip
from pydub import AudioSegment

# Configure logging
logging.basicConfig(level=logging.INFO)

# API token for AudD
API_TOKEN = 'changeme'

async def identify_song(session, audio_data):
    """Identify the song in the given audio data using the Audd.io API."""
    logging.info("Initiating API request to identify song")

    # Prepare the form data for the API request
    form = aiohttp.FormData()
    form.add_field('file', audio_data, filename='chunk.wav', content_type='audio/wav')
    form.add_field('api_token', API_TOKEN)

    # Make the API request to identify the song
    async with session.post('https://api.audd.io/', data=form) as response:
        logging.info(f"Received response with status code {response.status}")
        if response.status == 200:
            result = await response.json()
            logging.info(f"API response: {result}")
            if result['status'] == 'success' and result['result']:
                return result['result']['title']
        else:
            logging.error(f"Error in API response: {response.status}")
    return None

async def process_audio_chunks(session, audio, clip_length, interval_in_seconds, chunk_duration, root):
    """Process audio chunks and identify songs."""
    consecutive_failures = 0
    for start_time in range(0, clip_length, interval_in_seconds):
        chunk_start = start_time
        chunk_end = min(chunk_start + chunk_duration, clip_length)
        audio_chunk = audio[chunk_start * 1000:chunk_end * 1000]
        audio_chunk_data = io.BytesIO()
        audio_chunk.export(audio_chunk_data, format="wav")
        audio_chunk_data.seek(0)

        # Handle each audio chunk and add chapter info to XML if a song is identified
        title = await handle_audio_chunk(session, audio_chunk_data, chunk_start, root)
        if title is None:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        # Exit if there are 4 consecutive failures
        if consecutive_failures >= 6:
            logging.error("API failed to identify songs for 4 consecutive chunks. Exiting without writing chapters.")
            return False

    return True

async def handle_audio_chunk(session, audio_data, start_time, root):
    """Handle a single audio chunk and add chapter info to XML."""
    title = await identify_song(session, audio_data)
    if title:
        chapter_element = ET.SubElement(root, "ChapterAtom")
        ET.SubElement(chapter_element, "ChapterTimeStart").text = format_time(start_time)
        chapter_display = ET.SubElement(chapter_element, "ChapterDisplay")
        ET.SubElement(chapter_display, "ChapterString").text = title
    return title

def format_time(seconds):
    """Format time in HH:MM:SS.mmm format."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}.000"

async def main(video_path, output_xml=None, output_only=False, clip_interval=5, chunk_duration=15):
    """Main function to process the video file and identify songs."""
    if chunk_duration > 20:
        logging.warning("Chunk duration should be less than 20 seconds. Setting chunk duration to 20 seconds.")
        chunk_duration = 20
    
    interval_in_seconds = clip_interval * 60
    if clip_interval < 1 or clip_interval > 15:
        logging.warning("Duration should be between 1 and 15 minutes. Setting clip_interval to 5 minutes.")
        interval_in_seconds = 5 * 60

    logging.info(f"Processing video: {video_path}")
    clip = VideoFileClip(video_path)
    audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    logging.info(f"Extracting audio to temporary file: {audio_path}")
    clip.audio.write_audiofile(audio_path, codec='pcm_s16le')
    audio = AudioSegment.from_wav(audio_path)
    clip_length = int(clip.duration)
    root = ET.Element("Chapters")
    edition_entry = ET.SubElement(root, "EditionEntry")

    # Process audio chunks and identify songs
    async with aiohttp.ClientSession() as session:
        success = await process_audio_chunks(session, audio, clip_length, interval_in_seconds, chunk_duration, edition_entry)
    
    os.remove(audio_path)
    logging.info(f"Temporary audio file removed: {audio_path}")
    
    if not success:
        logging.error("Chapters have not been written to the file due to consecutive API failures to identify song.")
        return

    tree = ET.ElementTree(root)
    
    if output_xml:
        tree.write(output_xml, encoding='utf-8', xml_declaration=True)
        logging.info(f"Output written to {output_xml}")

        if not output_only:
            # Add chapters to the MKV file using mkvpropedit
            command = ['mkvpropedit', video_path, '--chapters', output_xml]
            logging.info(f"Running command: {' '.join(command)}")
            subprocess.run(command, check=True)
            logging.info(f"Chapters added to {video_path}")
    else:
        logging.error("No output XML file specified. Cannot write chapters.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Identify songs in a video file and output to an XML file.")
    parser.add_argument("video_path", help="Path to the video file (MKV or MP4 format)")
    parser.add_argument("output_xml", nargs='?', help="Path to the temporary output XML file for chapters", default=None)
    parser.add_argument("--output-only", action="store_true", help="Only output the XML content without writing to a file")
    parser.add_argument("--clip-interval", type=int, default=5, help="Take a clip every 5 minutes (1-15 minutes)")
    parser.add_argument("--chunk-duration", type=int, default=15, help="Duration of each audio chunk in seconds (less than 20 seconds)")
    args = parser.parse_args()
    
    asyncio.run(main(args.video_path, args.output_xml, args.output_only, args.clip_interval, args.chunk_duration))