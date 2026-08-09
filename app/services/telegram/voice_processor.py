import logging
import tempfile
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """
    Processes voice messages from Telegram users.
    Transcribes audio to text for AI processing.
    """

    def __init__(self):
        self.supported_formats = [".ogg", ".mp3", ".wav", ".m4a"]

    async def process_voice(self, file_path: str) -> Dict:
        """Process a voice message file."""
        try:
            text = await self._transcribe_audio(file_path)
            if text:
                return {
                    "success": True,
                    "text": text,
                    "language": "en",
                }
            return {"success": False, "error": "Could not transcribe audio"}

        except Exception as e:
            logger.error(f"Voice processing failed: {e}")
            return {"success": False, "error": str(e)}

    async def _transcribe_audio(self, file_path: str) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper API with Ollama fallback."""
        from app.config import settings

        # Try OpenAI Whisper if API key is available
        if settings.openai_api_key:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=settings.openai_api_key)

                with open(file_path, "rb") as audio_file:
                    response = await client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en",
                    )

                return response.text

            except Exception as e:
                logger.error(f"OpenAI Whisper transcription failed: {e}")

        # Fallback: Try local speech recognition if available
        try:
            import speech_recognition as sr
            import tempfile
            import subprocess
            import os

            wav_path = file_path
            if file_path.endswith('.ogg'):
                wav_path = file_path.rsplit('.', 1)[0] + '.wav'
                try:
                    subprocess.run(
                        ['ffmpeg', '-i', file_path, '-ar', '16000', '-ac', '1', wav_path, '-y'],
                        capture_output=True, check=True, timeout=10
                    )
                except (subprocess.CalledProcessError, FileNotFoundError):
                    logger.warning("ffmpeg not available, trying OGG directly")
                    wav_path = file_path

            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)

            if wav_path != file_path and os.path.exists(wav_path):
                os.remove(wav_path)

            return text
        except ImportError:
            logger.warning("speech_recognition not installed, cannot transcribe locally")
        except Exception as e:
            logger.error(f"Local transcription failed: {e}")

        return None

    async def process_image(self, file_path: str) -> Dict:
        """Process an image (OCR and analysis)."""
        try:
            analysis = await self._analyze_image(file_path)
            return {
                "success": True,
                "analysis": analysis,
            }
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_image(self, file_path: str) -> str:
        """Analyze image using GPT-4 Vision with Ollama fallback."""
        from app.config import settings

        # Try OpenAI Vision if API key is available
        if settings.openai_api_key:
            try:
                import base64
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=settings.openai_api_key)

                with open(file_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode("utf-8")

                response = await client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Analyze this financial image (chart, graph, table, or document). Extract key data points, trends, and insights. Be concise and specific with numbers.",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}",
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=1000,
                )

                return response.choices[0].message.content

            except Exception as e:
                logger.error(f"OpenAI Vision analysis failed: {e}")

        # Fallback: Use basic OCR if available
        try:
            import pytesseract
            from PIL import Image
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            if text.strip():
                return f"<b>Extracted text from image:</b>\n\n{text.strip()}\n\n(I can provide better analysis with an OpenAI API key for vision capabilities)"
        except ImportError:
            logger.warning("pytesseract not installed, cannot perform OCR")
        except Exception as e:
            logger.error(f"OCR failed: {e}")

        return "I can't analyze images without an API key. Please describe what you see in the image, and I'll help you analyze it!"


voice_processor = VoiceProcessor()
