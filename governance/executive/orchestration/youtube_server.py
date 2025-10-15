#!/usr/bin/env python3
"""
YouTube MCP Server (FastMCP)
Provides YouTube transcript and video tools using yt-dlp-transcript
"""
import json

from mcp.server.fastmcp import FastMCP, tool
from yt_dlp_transcript import yt_dlp_transcript

mcp = FastMCP("youtube")

@tool()
def get_transcript(url: str, language: str = "en"):
    """
    Get transcript from a YouTube video.
    
    Args:
        url: YouTube video URL
        language: Subtitle language code (default: en)
    
    Returns:
        str: Full video transcript
    """
    try:
        transcript = yt_dlp_transcript(url, language=language)
        return {
            "status": "success",
            "transcript": transcript,
            "url": url,
            "language": language,
            "length": len(transcript)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": url
        }

@tool()
def get_timed_transcript(url: str, language: str = "en"):
    """
    Get transcript with timestamps from a YouTube video.
    
    Args:
        url: YouTube video URL
        language: Subtitle language code (default: en)
    
    Returns:
        dict: Transcript with timing information
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # Extract video ID
        video_id = url.split("v=")[-1].split("&")[0] if "v=" in url else url.split("/")[-1]

        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])

        return {
            "status": "success",
            "transcript": transcript_list,
            "url": url,
            "segments": len(transcript_list)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": url
        }

@tool()
def get_video_info(url: str):
    """
    Get metadata for a YouTube video.
    
    Args:
        url: YouTube video URL
    
    Returns:
        dict: Video title, duration, uploader, etc.
    """
    try:
        import subprocess
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            info = json.loads(result.stdout)
            return {
                "status": "success",
                "title": info.get("title"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "view_count": info.get("view_count"),
                "upload_date": info.get("upload_date"),
                "url": url
            }
        return {"status": "error", "error": result.stderr}
    except Exception as e:
        return {"status": "error", "error": str(e), "url": url}

@tool()
def batch_transcripts(urls: str, language: str = "en"):
    """
    Fetch transcripts from multiple YouTube videos.
    
    Args:
        urls: Comma-separated YouTube URLs
        language: Subtitle language (default: en)
    
    Returns:
        list: Transcripts for all videos
    """
    url_list = [u.strip() for u in urls.split(",")]
    results = []

    for url in url_list:
        result = get_transcript(url, language)
        results.append(result)

    return {
        "results": results,
        "total": len(url_list),
        "successful": sum(1 for r in results if r.get("status") == "success")
    }

if __name__ == "__main__":
    mcp.run()

