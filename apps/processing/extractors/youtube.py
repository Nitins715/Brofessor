import re
from typing import Any, Optional
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from .base import BaseExtractor, ExtractionResult, ContentSegment


class YouTubeExtractor(BaseExtractor):
    """Extractor for YouTube video transcripts with segment timestamp preservation."""

    def extract_video_id(self, url: str) -> str:
        """Extract 11-character YouTube video ID from various URL formats."""
        if not url:
            return ""

        # Direct 11-char ID
        if re.fullmatch(r"[0-9A-Za-z_-]{11}", url.strip()):
            return url.strip()

        patterns = [
            r"(?:v=|\/vi\/|\/v\/|youtu\.be\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})",
            r"[?&]v=([0-9A-Za-z_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    def format_timestamp(self, seconds: float) -> str:
        """Convert float seconds to MM:SS or HH:MM:SS format."""
        total_sec = int(seconds)
        hours = total_sec // 3600
        minutes = (total_sec % 3600) // 60
        secs = total_sec % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def fetch_video_metadata(self, url: str) -> dict:
        """Fetch video title and author using YouTube oEmbed (no API key required)."""
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        try:
            resp = requests.get(oembed_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "title": data.get("title", ""),
                    "author": data.get("author_name", ""),
                    "thumbnail_url": data.get("thumbnail_url", ""),
                }
        except Exception:
            pass
        return {}

    def extract(self, source: Any) -> ExtractionResult:
        url = source.uri
        if not url:
            raise ValueError(f"Source '{source.name}' ({source.id}) has no YouTube URL specified.")

        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError(f"Could not extract a valid YouTube video ID from URL: '{url}'")

        # Try to retrieve video title
        oembed_info = self.fetch_video_metadata(url)
        title = oembed_info.get("title") or source.name or f"YouTube Video {video_id}"

        # Fetch transcript
        try:
            # youtube_transcript_api 1.x
            api_instance = YouTubeTranscriptApi()
            if hasattr(api_instance, "fetch"):
                transcript_data = api_instance.fetch(video_id, languages=["en"])
            else:
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        except Exception as e:
            # Fallback attempt without language restriction
            try:
                if hasattr(YouTubeTranscriptApi, "fetch"):
                    transcript_data = YouTubeTranscriptApi().fetch(video_id)
                else:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
            except Exception as inner_e:
                raise ValueError(
                    f"Failed to retrieve transcript for YouTube video '{video_id}': {str(inner_e)}"
                ) from inner_e

        segments = []
        full_text_parts = []

        for item in transcript_data:
            if isinstance(item, dict):
                text = item.get("text", "").strip()
                start = float(item.get("start", 0.0))
                duration = float(item.get("duration", 0.0))
            else:
                text = getattr(item, "text", "").strip()
                start = float(getattr(item, "start", 0.0))
                duration = float(getattr(item, "duration", 0.0))

            if not text:
                continue

            timestamp_str = self.format_timestamp(start)
            full_text_parts.append(f"[{timestamp_str}] {text}")

            segments.append(
                ContentSegment(
                    text=text,
                    metadata={
                        "video_id": video_id,
                        "start_seconds": start,
                        "duration_seconds": duration,
                        "timestamp": timestamp_str,
                    },
                )
            )

        if not full_text_parts:
            raise ValueError(f"YouTube transcript for video '{video_id}' was empty.")

        full_text = "\n".join(full_text_parts)

        return ExtractionResult(
            title=title,
            text=full_text,
            metadata={
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "channel": oembed_info.get("author", ""),
                "segment_count": len(segments),
            },
            segments=segments,
        )
