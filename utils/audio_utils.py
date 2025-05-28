"""
Audio Utilities Module

This module provides audio capabilities for the debate simulator,
including text-to-speech functionality for debate arguments.
"""

import os
import time
import logging
import tempfile
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from gtts import gTTS
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

logger = logging.getLogger(__name__)

# Initialize pygame mixer if available
if AUDIO_AVAILABLE:
    try:
        pygame.mixer.init()
        logger.info("Pygame mixer initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing pygame mixer: {e}")
        AUDIO_AVAILABLE = False


class AudioManager:
    """
    Manages audio generation and playback for debate simulator.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the AudioManager.
        
        Args:
            cache_dir: Directory to cache audio files
        """
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "debate_simulator_audio")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.is_playing = False
        self.should_stop = False
        self.current_audio_thread = None
        self.voice_mapping = {
            "moderator": "en",
            "default": "en"
        }
        
        logger.info(f"AudioManager initialized with cache dir: {self.cache_dir}")
    
    def get_audio_path(self, speaker: str, text: str, message_type: str) -> str:
        """
        Get the path for an audio file based on its content.
        
        Args:
            speaker: Name of the speaker
            text: Text content
            message_type: Type of message
            
        Returns:
            Path to the audio file
        """
        # Create a simple hash of the content to use as filename
        import hashlib
        content_hash = hashlib.md5(f"{speaker}_{text[:100]}".encode()).hexdigest()
        filename = f"{speaker}_{message_type}_{content_hash[:10]}.mp3"
        
        return os.path.join(self.cache_dir, filename)
    
    def text_to_speech(self, text: str, speaker: str = "default", save_path: Optional[str] = None) -> Optional[str]:
        """
        Convert text to speech and save as audio file.
        
        Args:
            text: Text to convert
            speaker: Speaker identifier for voice selection
            save_path: Path to save audio file (optional)
            
        Returns:
            Path to the saved audio file or None if failed
        """
        if not AUDIO_AVAILABLE:
            logger.warning("Audio capabilities not available. Install gTTS and pygame.")
            return None
        
        try:
            # Limit text length to prevent long processing times
            text = text[:500]  # Limit to 500 chars
            
            # Select language/voice based on speaker
            lang = self.voice_mapping.get(speaker, self.voice_mapping["default"])
            
            # Generate speech
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # Save to file
            if save_path is None:
                save_path = os.path.join(self.cache_dir, f"{speaker}_{int(time.time())}.mp3")
            
            tts.save(save_path)
            logger.info(f"Generated audio file: {save_path}")
            
            return save_path
        
        except Exception as e:
            logger.error(f"Error in text_to_speech: {e}")
            return None
    
    def generate_audio_for_message(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Generate audio for a debate message.
        
        Args:
            message: Debate message dictionary
            
        Returns:
            Path to the generated audio file or None if failed
        """
        if not AUDIO_AVAILABLE:
            return None
        
        try:
            speaker = message.get("speaker", "default")
            content = message.get("content", "")
            message_type = message.get("type", "")
            
            # Clean the content - remove markdown and other formatting
            content = self._clean_text_for_speech(content)
            
            # Generate a path for this specific content
            audio_path = self.get_audio_path(speaker, content, message_type)
            
            # Check if we already have this audio file
            if os.path.exists(audio_path):
                logger.info(f"Using cached audio file: {audio_path}")
                return audio_path
            
            # Generate the audio
            return self.text_to_speech(content, speaker, audio_path)
        
        except Exception as e:
            logger.error(f"Error generating audio for message: {e}")
            return None
    
    def play_audio(self, audio_path: str, blocking: bool = False) -> bool:
        """
        Play an audio file.
        
        Args:
            audio_path: Path to the audio file
            blocking: Whether to block until playback completes
            
        Returns:
            True if playback started successfully, False otherwise
        """
        if not AUDIO_AVAILABLE or not os.path.exists(audio_path):
            return False
        
        try:
            if blocking:
                # Play audio and wait for it to complete
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                return True
            else:
                # Play in a separate thread
                self.stop_audio()  # Stop any current playback
                
                def play_thread_func():
                    try:
                        pygame.mixer.music.load(audio_path)
                        pygame.mixer.music.play()
                        self.is_playing = True
                        
                        # Wait for playback to complete or stop signal
                        while pygame.mixer.music.get_busy() and not self.should_stop:
                            pygame.time.Clock().tick(10)
                        
                        self.is_playing = False
                        self.should_stop = False
                    except Exception as e:
                        logger.error(f"Error in audio playback thread: {e}")
                        self.is_playing = False
                
                self.current_audio_thread = threading.Thread(target=play_thread_func)
                self.current_audio_thread.daemon = True
                self.current_audio_thread.start()
                
                return True
        
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False
    
    def stop_audio(self) -> None:
        """
        Stop any currently playing audio.
        """
        if not AUDIO_AVAILABLE:
            return
        
        try:
            if self.is_playing:
                self.should_stop = True
                pygame.mixer.music.stop()
                
                # Wait for thread to finish
                if self.current_audio_thread and self.current_audio_thread.is_alive():
                    self.current_audio_thread.join(timeout=1.0)
                
                self.is_playing = False
                logger.info("Stopped audio playback")
        
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
    
    def generate_audio_for_transcript(self, transcript: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generate audio files for all messages in a transcript.
        
        Args:
            transcript: List of debate transcript messages
            
        Returns:
            Dictionary mapping message IDs to audio file paths
        """
        if not AUDIO_AVAILABLE:
            return {}
        
        audio_paths = {}
        
        for i, message in enumerate(transcript):
            try:
                audio_path = self.generate_audio_for_message(message)
                if audio_path:
                    # Create a unique ID for this message
                    message_id = f"{message.get('speaker', 'unknown')}_{message.get('type', 'message')}_{i}"
                    audio_paths[message_id] = audio_path
            except Exception as e:
                logger.error(f"Error generating audio for transcript item {i}: {e}")
        
        return audio_paths
    
    def _clean_text_for_speech(self, text: str) -> str:
        """
        Clean text for speech generation by removing markdown and other formatting.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Remove markdown headers
        import re
        text = re.sub(r'#+\s+', '', text)
        
        # Remove markdown bold/italic
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        
        # Remove parentheses with actions (common in debate transcripts)
        text = re.sub(r'\(.*?\)', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text


# Create a singleton instance for global use
audio_manager = AudioManager()


def is_audio_available() -> bool:
    """
    Check if audio capabilities are available.
    
    Returns:
        True if audio is available, False otherwise
    """
    return AUDIO_AVAILABLE


def generate_audio_for_message(message: Dict[str, Any]) -> Optional[str]:
    """
    Generate audio for a debate message using the global audio manager.
    
    Args:
        message: Debate message dictionary
        
    Returns:
        Path to the generated audio file or None if failed
    """
    return audio_manager.generate_audio_for_message(message)


def play_audio(audio_path: str, blocking: bool = False) -> bool:
    """
    Play an audio file using the global audio manager.
    
    Args:
        audio_path: Path to the audio file
        blocking: Whether to block until playback completes
        
    Returns:
        True if playback started successfully, False otherwise
    """
    return audio_manager.play_audio(audio_path, blocking)


def stop_audio() -> None:
    """
    Stop any currently playing audio using the global audio manager.
    """
    audio_manager.stop_audio()