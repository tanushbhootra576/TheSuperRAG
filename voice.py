import os
import hashlib
import time
import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import tempfile

voice_router = APIRouter(prefix="/api/voice", tags=["Voice"])

# Load Whisper model lazily to avoid blocking startup
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            # Using 'tiny' model for speed on CPU
            _whisper_model = whisper.load_model("tiny")
        except Exception as e:
            print(f"Failed to load Whisper: {e}")
            raise HTTPException(status_code=500, detail="Speech-to-Text model unavailable")
    return _whisper_model

@voice_router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # Validate file size (max 25MB approx)
    file.file.seek(0, os.SEEK_END)
    if file.file.tell() > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 25MB)")
    file.file.seek(0)
    
    # Save to temp file since Whisper needs a file path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        model = get_whisper_model()
        # Transcribe
        result = model.transcribe(tmp_path)
        
        # Determine confidence (approximate from segments)
        segments = result.get("segments", [])
        avg_confidence = sum(s.get("no_speech_prob", 0.0) for s in segments) / max(len(segments), 1)
        # Invert no_speech_prob as a rough confidence measure
        confidence = 1.0 - avg_confidence
        
        return {
            "transcript": result.get("text", "").strip(),
            "language": result.get("language", "en"),
            "confidence": round(confidence, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

class TTSRequest(BaseModel):
    text: str
    voice: str = "neutral"
    speed: float = 1.0

def get_cache_path(text: str, voice: str) -> str:
    hash_str = hashlib.md5((text + voice).encode()).hexdigest()
    # Cache in temp dir
    cache_dir = os.path.join(tempfile.gettempdir(), "thesuperrag_tts_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{hash_str}.mp3")

def cleanup_cache():
    # Simple TTL cleanup: remove files older than 24h
    cache_dir = os.path.join(tempfile.gettempdir(), "thesuperrag_tts_cache")
    if not os.path.exists(cache_dir): return
    now = time.time()
    for f in os.listdir(cache_dir):
        path = os.path.join(cache_dir, f)
        if now - os.path.getmtime(path) > 86400: # 24h
            try: os.remove(path)
            except: pass

@voice_router.post("/synthesize")
async def synthesize_speech(req: TTSRequest):
    cleanup_cache()
    cache_path = get_cache_path(req.text, req.voice)
    
    if os.path.exists(cache_path):
        return FileResponse(cache_path, media_type="audio/mpeg")
        
    try:
        if req.voice in ["professional", "friendly"] and os.environ.get("ELEVENLABS_API_KEY"):
            # ElevenLabs logic (placeholder using httpx)
            import httpx
            voice_id = "pNInz6obpgDQGcFmaJcg" if req.voice == "professional" else "EXAVITQu4vr4xnSDxMaL"
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": os.environ.get("ELEVENLABS_API_KEY")
            }
            data = {"text": req.text, "model_id": "eleven_monolingual_v1"}
            async with httpx.AsyncClient() as client:
                res = await client.post(url, json=data, headers=headers, timeout=30.0)
                res.raise_for_status()
                with open(cache_path, "wb") as f:
                    f.write(res.content)
        else:
            # Fallback to gTTS
            from gtts import gTTS
            tts = gTTS(text=req.text, lang='en', slow=(req.speed < 1.0))
            tts.save(cache_path)
            
        return FileResponse(cache_path, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
