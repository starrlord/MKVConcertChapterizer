import os
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import logging
import asyncio
import aiohttp
import io
import tempfile
import xml.etree.ElementTree as ET
import subprocess


logging.basicConfig(level=logging.INFO)

async def identify_song(session, audio_data):
    logging.info("Initiating API request to identify song")

    form = aiohttp.FormData()
    form.add_field('file', audio_data, filename='chunk.wav', content_type='audio/wav')
    form.add_field('api_token', 'REPLACEME')

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

async def process_audio_chunks(session, audio, duration, root):
    chunk_duration = 15  # 15 seconds

    for start_time in range(0, duration, 300):  # 300 seconds is 5 minutes
        chunk_start = start_time
        chunk_end = min(chunk_start + chunk_duration, duration)
        audio_chunk = audio[chunk_start * 1000:chunk_end * 1000]
        audio_chunk_data = io.BytesIO()
        audio_chunk.export(audio_chunk_data, format="wav")
        audio_chunk_data.seek(0)

        await handle_audio_chunk(session, audio_chunk_data, chunk_start, root)

async def handle_audio_chunk(session, audio_data, start_time, root):
    title = await identify_song(session, audio_data)

    if title:
        chapter_element = ET.SubElement(root, "ChapterAtom")
        ET.SubElement(chapter_element, "ChapterTimeStart").text = format_time(start_time)
        chapter_display = ET.SubElement(chapter_element, "ChapterDisplay")
        ET.SubElement(chapter_display, "ChapterString").text = title

def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}.000"

async def main(video_path, output_xml):
    logging.info(f"Processing video: {video_path}")
    clip = VideoFileClip(video_path)
    audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    logging.info(f"Extracting audio to temporary file: {audio_path}")
    clip.audio.write_audiofile(audio_path, codec='pcm_s16le')
    audio = AudioSegment.from_wav(audio_path)
    duration = int(clip.duration)
    
    root = ET.Element("Chapters")
    edition_entry = ET.SubElement(root, "EditionEntry")

    async with aiohttp.ClientSession() as session:
        await process_audio_chunks(session, audio, duration, edition_entry)
    
    os.remove(audio_path)
    logging.info(f"Temporary audio file removed: {audio_path}")
    tree = ET.ElementTree(root)
    tree.write(output_xml, encoding='utf-8', xml_declaration=True)
    logging.info(f"Output written to {output_xml}")

    # Add chapters to the MKV file using mkvpropedit
    command = ['mkvpropedit', video_path, '--chapters', output_xml]
    logging.info(f"Running command: {' '.join(command)}")
    subprocess.run(command, check=True)
    logging.info(f"Chapters added to {video_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Identify songs in a video file and output to an XML file.")
    parser.add_argument("video_path", help="Path to the video file (MKV format)")
    parser.add_argument("output_xml", help="Path to the temporary output XML file for chapters")
    args = parser.parse_args()
    
    asyncio.run(main(args.video_path, args.output_xml))
