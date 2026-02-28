import os
import subprocess
import whisper
from typing import Optional, List
from Services.data_normalization import normalize_transcription, validate_video_file

# Initialize Whisper model (load once, reuse)
_whisper_model = None

def get_whisper_model():
    """Lazy load Whisper model to avoid loading on import."""
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("base")  # Options: tiny, base, small, medium, large
    return _whisper_model

async def extract_text_from_video(video_path: str) -> str:
    """
    Extract text/transcription from a video file using Whisper.
    Video is validated and transcription is normalized before returning.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Normalized transcribed text from the video
    """
    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Validate video file before processing
        validation = validate_video_file(video_path)
        if not validation["valid"]:
            raise ValueError(f"Video validation failed: {', '.join(validation['errors'])}")
        
        # Load Whisper model
        model = get_whisper_model()
        
        # Transcribe video
        result = model.transcribe(video_path)
        
        # Extract text from transcription
        raw_text = result.get("text", "").strip()
        
        # Normalize the transcription
        normalized_text = normalize_transcription(raw_text)
        
        if not normalized_text:
            raise ValueError("No text could be extracted from video after normalization")
        
        return normalized_text
    except Exception as e:
        raise Exception(f"Error extracting text from video: {str(e)}")


def extract_video_chunks(
    video_path: str,
    chunk_duration_sec: float = 120.0,
) -> List[dict]:
    """
    Extract time-based chunks from a video: transcribe with Whisper and group
    segments into chunks by duration. Each chunk has text and start/end times.

    Args:
        video_path: Path to the video file
        chunk_duration_sec: Target duration per chunk in seconds (default 2 min)

    Returns:
        List of dicts: [{"text": str, "start_sec": float, "end_sec": float}, ...]
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    validation = validate_video_file(video_path)
    if not validation["valid"]:
        raise ValueError(f"Video validation failed: {', '.join(validation['errors'])}")

    model = get_whisper_model()
    result = model.transcribe(video_path)

    segments = result.get("segments") or []
    if not segments:
        # Fallback: use full text as single chunk
        raw_text = result.get("text", "").strip()
        if raw_text:
            normalized = normalize_transcription(raw_text)
            if normalized:
                return [{"text": normalized, "start_sec": 0.0, "end_sec": 0.0}]
        return []

    chunks: List[dict] = []
    current_texts: List[str] = []
    chunk_start = 0.0
    chunk_end = 0.0

    for seg in segments:
        start_sec = float(seg.get("start", 0))
        end_sec = float(seg.get("end", 0))
        text = (seg.get("text") or "").strip()
        if not text:
            continue

        normalized = normalize_transcription(text)
        if not normalized:
            continue

        if not current_texts:
            chunk_start = start_sec
        chunk_end = end_sec
        current_texts.append(normalized)

        # Start a new chunk when duration exceeds target
        if chunk_duration_sec > 0 and (chunk_end - chunk_start) >= chunk_duration_sec:
            combined = " ".join(current_texts).strip()
            if combined:
                chunks.append({
                    "text": combined,
                    "start_sec": round(chunk_start, 2),
                    "end_sec": round(chunk_end, 2),
                })
            current_texts = []
            chunk_start = 0.0
            chunk_end = 0.0

    if current_texts:
        combined = " ".join(current_texts).strip()
        if combined:
            chunks.append({
                "text": combined,
                "start_sec": round(chunk_start, 2),
                "end_sec": round(chunk_end, 2),
            })

    return chunks


async def process_video(video_path: str, output_path: Optional[str] = None) -> dict:
    """
    Process a video file: validate, extract metadata, transcribe, etc.
    All data is normalized before returning.
    
    Args:
        video_path: Path to the video file
        output_path: Optional path for processed video output
        
    Returns:
        Dictionary with normalized video metadata and transcription
    """
    try:
        # Validate video file first
        validation = validate_video_file(video_path)
        if not validation["valid"]:
            raise ValueError(f"Video validation failed: {', '.join(validation['errors'])}")
        
        # Extract text/transcription (already normalized in extract_text_from_video)
        transcription = await extract_text_from_video(video_path)
        
        # Get video metadata using ffprobe (if available)
        metadata = validation.get("metadata", {})
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", video_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                import json
                probe_data = json.loads(result.stdout)
                # Add additional metadata
                metadata.update({
                    "duration": probe_data.get("format", {}).get("duration"),
                    "size": probe_data.get("format", {}).get("size"),
                    "bitrate": probe_data.get("format", {}).get("bit_rate"),
                })
        except Exception as e:
            print(f"Could not extract additional video metadata: {str(e)}")
        
        return {
            "transcription": transcription,
            "metadata": metadata
        }
    except Exception as e:
        raise Exception(f"Error processing video: {str(e)}")

