"""
title: Chat Video
author: liemkg1234
date: 2025-05
description: A pipeline for Chat Video, using yt-dlp, Whisper, SmolVLM2
requirements: openai, imageio[ffmpeg]
"""

import json
import os
import sys
import tempfile
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import re
import requests
from typing import Optional
from textwrap import dedent
from PIL import Image
from io import BytesIO
import threading

import imageio
import base64
from openai import OpenAI

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger.setLevel(logging.INFO)

logger.propagate = True
logger.info("✅ Logger is working")


class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]
        priority: int = 0

        # yt-dlp server URL
        yt_dlp_url: str = "http://yt-dlp-server:8000"

        # Whisper
        whisper_url: str = "http://asr:8000/v1/"
        whisper_model: str = "Systran/faster-whisper-medium"

        # VLM
        vlm_url: str = "http://llm:8000/v1/"
        vlm_model: str = "ggml-org_InternVL3-8B-Instruct-GGUF_InternVL3-8B-Instruct-Q4_K_M.gguf"
        # vlm_model: str = "ggml-org_Qwen2.5-VL-7B-Instruct-GGUF_Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf",
        video_max_duration: float = 300.0

    def __init__(self):
        self.type = "filter"
        self.name = "Chat Video RAG Filter"
        self.name = "Chat Video RAG Filter"
        self.context = None
        self.valves = self.Valves(
            **{
                "pipelines": ["*"],
            }
        )

    async def on_startup(self):
        pass

    async def on_shutdown(self):
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        if isinstance(body, str):
            body = json.loads(body)
        if body.get("task") or body.get("metadata", {}).get("task"):
            return body

        logger.info(" START----------------------------------------------------------------------------------")

        messages = body.get("messages", [])

        # Extract YouTube URL from the user message
        urls, user_content = self.extract_youtube_urls(messages[-1]["content"])
        if urls:
            url = urls[0]

            # # Download video and audio
            logger.info(" ===== Download Video =====:")
            video_path = self.download_video(url)
            audio_path = self.download_audio(url)
            logger.info(f" === Video: {video_path}, Audio: {audio_path}")

            # Transcribe audio
            logger.info(" ===== Transcribe audio =====:")
            segments = self.transcription(audio_path)
            logger.info(f" === Audio Segments: {segments}")

            # VLM
            logger.info(" ===== VLM =====:")
            threads = []

            def process_segment(i, segment, segments, video_path, vlm_func):
                start = segment["start"]
                end = segment["end"]
                segments[i]["video_text"] = vlm_func(video_path, start, end)

            for i, segment in enumerate(segments):
                t = threading.Thread(
                    target=process_segment,
                    args=(i, segment, segments, video_path, self.vlm)  # assuming inside a class
                )
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # Build context after all threads are done
            context = "Context of video: \n"
            for i, segment in enumerate(segments):
                start = segment["start"]
                end = segment["end"]
                context += dedent(f"""
                Segment {i}:
                Start Time: {start} seconds
                End Time: {end} seconds
                Audio Transcript: {segment["audio_text"]}
                Video Context: {segment["video_text"]}
                """)

            self.context = context

        if self.context is not None:
            # System Prompt
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": dedent(f"""
        You are a helpful assistant that analyzes video content based on segmented data. Each segment contains:
        - Start and end time (in seconds),
        - Audio transcript,
        - Visual context description.
        
        Use this information to answer the user's questions accurately, even if the questions are about specific moments, topics, people, or actions in the video.
        Always respond in Vietnamese.
        Be concise, clear, and refer to the most relevant segments to support your answer.
        """),
                },
            )

            # User Prompt
            messages[-1]["content"] = dedent(f"""
        This is segments of video:
        {self.context}
        
        This is the user message:
        {user_content}
        """)

            body["messages"] = messages
            logger.info(f" Messages before chat: {messages}")

        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        logger.info(" ----------------------------------------------------------------------------------END")
        return body

    @staticmethod
    def extract_youtube_urls(text: str) -> list:
        pattern = r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w\-]+)"
        cleaned_text = re.sub(pattern, "", text)
        return re.findall(pattern, text), cleaned_text.strip()

    def download_video(self, url: str, quality: int = 360) -> str:
        try:
            response = requests.get(
                f"{self.valves.yt_dlp_url}/download/video",
                params={"url": url, "quality": quality},
            )
            response.raise_for_status()
            data = response.json()
            if data["status"] == "success":
                return data["path"]
            raise Exception(data["message"])
        except Exception as e:
            raise RuntimeError(f"Video download failed: {str(e)}")

    def download_audio(self, url: str) -> str:
        try:
            response = requests.get(f"{self.valves.yt_dlp_url}/download/audio", params={"url": url})
            response.raise_for_status()
            data = response.json()
            if data["status"] == "success":
                return data["path"]
            raise Exception(data["message"])
        except Exception as e:
            raise RuntimeError(f"Audio download failed: {str(e)}")

    def transcription(self, audio_path: str):
        try:
            client = OpenAI(api_key="abc", base_url=self.valves.whisper_url)

            transcript = client.audio.transcriptions.create(
                model=self.valves.whisper_model,
                temperature=0,
                include=["logprobs"],
                file=open(audio_path, "rb"),
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

            segments_chunked = chunk_transcript_by_duration(transcript.segments, max_duration=self.valves.video_max_duration)
            return segments_chunked
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

    def vlm(self, video_path: str, start: float, end: float) -> str:
        try:
            # Get image in video
            reader = imageio.get_reader(video_path)
            fps = reader.get_meta_data()["fps"]
            frame_number = int(fps * 1)
            frame = reader.get_data(frame_number)
            reader.close()

            img = Image.fromarray(frame)

            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            img.save(temp_file.name, format="PNG")
            with open(temp_file.name, "rb") as image_file:
                b64_image = base64.b64encode(image_file.read()).decode("utf-8")

            system_prompt = dedent("""
        You are a vision model analyzing a frame from a video. Please extract the following structured information from the image:
    
        1. **Caption** – A short description of what is happening in the frame.
        2. **Objects** – A list of recognizable objects or entities (e.g., "person", "car", "laptop").
        3. **OCR** – Any visible and readable text in the image.
        4. **Activity** – What action(s) are taking place in the frame? (e.g., "a person is typing on a laptop").
        5. **Scene** – Describe the environment or setting (e.g., "office", "kitchen", "outdoor park").
        6. **Lighting** – Describe the lighting condition (e.g., "bright natural light", "dim indoor light", "night with street lights").
    
        Respond in list, clearly labeled. Be concise and accurate.
        
        Example:
        - Caption: ...
        - Objects: ...
        - OCR: ...
        - Activity: ...
        - Scene: ...
        - Lighting: ...
      """)

            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                        },
                        {"type": "text", "text": "Describe this image."},
                    ],
                },
            ]

            client = OpenAI(api_key="abc", base_url=self.valves.vlm_url)
            response = client.chat.completions.create(
                model=self.valves.vlm_model,
                messages=messages,
                max_tokens=256,
            )

            content = response.choices[0].message.content
            logger.info(f" Content when VLM: {content}")

            return content

        except Exception as e:
            raise RuntimeError(f"VLM Error: {str(e)}")


def chunk_transcript_by_duration(segments, max_duration=60.0):
    if not segments:
        return []

    chunks = []
    current_chunk = {
        "start": segments[0].start,
        "end": segments[0].end,
        "audio_text": segments[0].text.strip(),
    }

    for i in range(1, len(segments)):
        segment = segments[i]
        proposed_end = segment.end
        chunk_duration = proposed_end - current_chunk["start"]

        if chunk_duration <= max_duration:
            current_chunk["end"] = segment.end
            current_chunk["audio_text"] += ". " + segment.text.strip()
        else:
            chunks.append(current_chunk)
            current_chunk = {
                "start": segment.start,
                "end": segment.end,
                "audio_text": segment.text.strip(),
            }

    chunks.append(current_chunk)
    return chunks
