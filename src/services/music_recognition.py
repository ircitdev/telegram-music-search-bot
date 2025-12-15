"""Music recognition service using AudD API."""
import aiohttp
import base64
from typing import Optional, Dict, Any
from dataclasses import dataclass

from src.config import settings
from src.utils.logger import logger


@dataclass
class RecognitionResult:
    """Result of music recognition."""
    success: bool
    artist: Optional[str] = None
    title: Optional[str] = None
    album: Optional[str] = None
    release_date: Optional[str] = None
    label: Optional[str] = None
    timecode: Optional[str] = None
    song_link: Optional[str] = None
    apple_music_url: Optional[str] = None
    spotify_url: Optional[str] = None
    error: Optional[str] = None


class MusicRecognition:
    """AudD API music recognition service."""

    API_URL = "https://api.audd.io/"
    HUMMING_URL = "https://api.audd.io/recognizeWithOffset/"

    def __init__(self):
        self.api_key = settings.AUDD_API_KEY

    async def recognize_audio(self, audio_data: bytes, is_humming: bool = False) -> RecognitionResult:
        """
        Recognize music from audio data.

        Args:
            audio_data: Raw audio bytes
            is_humming: Use humming recognition endpoint

        Returns:
            RecognitionResult with track info or error
        """
        if not self.api_key:
            return RecognitionResult(success=False, error="API ключ не настроен")

        try:
            # Encode audio to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # Prepare request data
            data = {
                'api_token': self.api_key,
                'audio': audio_base64,
                'return': 'apple_music,spotify'
            }

            url = self.HUMMING_URL if is_humming else self.API_URL

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, timeout=30) as response:
                    result = await response.json()

                    logger.info(f"AudD API response: {result.get('status')}")

                    if result.get('status') == 'error':
                        error_msg = result.get('error', {}).get('error_message', 'Неизвестная ошибка')
                        return RecognitionResult(success=False, error=error_msg)

                    if result.get('status') == 'success':
                        track = result.get('result')

                        if not track:
                            return RecognitionResult(
                                success=False,
                                error="Трек не найден. Попробуй записать более четкий фрагмент."
                            )

                        # Extract URLs
                        apple_music_url = None
                        spotify_url = None

                        if track.get('apple_music'):
                            apple_music_url = track['apple_music'].get('url')

                        if track.get('spotify'):
                            spotify_url = track['spotify'].get('external_urls', {}).get('spotify')

                        return RecognitionResult(
                            success=True,
                            artist=track.get('artist'),
                            title=track.get('title'),
                            album=track.get('album'),
                            release_date=track.get('release_date'),
                            label=track.get('label'),
                            timecode=track.get('timecode'),
                            song_link=track.get('song_link'),
                            apple_music_url=apple_music_url,
                            spotify_url=spotify_url
                        )

                    return RecognitionResult(
                        success=False,
                        error="Неожиданный ответ от API"
                    )

        except aiohttp.ClientTimeout:
            logger.error("AudD API timeout")
            return RecognitionResult(success=False, error="Таймаут запроса. Попробуй еще раз.")

        except Exception as e:
            logger.error(f"Music recognition error: {e}")
            return RecognitionResult(success=False, error=f"Ошибка распознавания: {str(e)}")

    async def recognize_from_url(self, url: str) -> RecognitionResult:
        """Recognize music from URL."""
        if not self.api_key:
            return RecognitionResult(success=False, error="API ключ не настроен")

        try:
            data = {
                'api_token': self.api_key,
                'url': url,
                'return': 'apple_music,spotify'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.API_URL, data=data, timeout=30) as response:
                    result = await response.json()

                    if result.get('status') == 'success' and result.get('result'):
                        track = result['result']
                        return RecognitionResult(
                            success=True,
                            artist=track.get('artist'),
                            title=track.get('title'),
                            album=track.get('album'),
                            song_link=track.get('song_link')
                        )

                    return RecognitionResult(success=False, error="Трек не найден")

        except Exception as e:
            logger.error(f"Recognition from URL error: {e}")
            return RecognitionResult(success=False, error=str(e))


# Global instance
music_recognition = MusicRecognition()
