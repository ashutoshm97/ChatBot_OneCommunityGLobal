import os
import subprocess
import whisper
from typing import Optional
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

