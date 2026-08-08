import requests
import os

class TelegramBot:
    """
    A flexible Telegram bot client for sending messages, photos, videos, documents, and audio.
    """
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, text: str) -> bool:
        """Sends a text message."""
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Telegram Message Error: {e}")
            return False

    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """Sends a photo file."""
        return self._send_media(photo_path, caption, endpoint="sendPhoto", file_field="photo")

    def send_video(self, video_path: str, caption: str = "") -> bool:
        """Sends a video file."""
        return self._send_media(video_path, caption, endpoint="sendVideo", file_field="video")

    def send_document(self, document_path: str, caption: str = "") -> bool:
        """Sends a document (e.g. PDF, TXT) file."""
        return self._send_media(document_path, caption, endpoint="sendDocument", file_field="document")

    def send_audio(self, audio_path: str, caption: str = "") -> bool:
        """Sends an audio file."""
        return self._send_media(audio_path, caption, endpoint="sendAudio", file_field="audio")

    def _send_media(self, file_path: str, caption: str, endpoint: str, file_field: str) -> bool:
        """Internal helper to send files."""
        if not os.path.exists(file_path):
            print(f"Error: File not found - {file_path}")
            return False
            
        url = f"{self.base_url}/{endpoint}"
        payload = {"chat_id": self.chat_id, "caption": caption}
        
        try:
            with open(file_path, "rb") as f:
                files = {file_field: f}
                response = requests.post(url, data=payload, files=files)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Telegram {endpoint} Error: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"Response: {response.text}")
            return False
