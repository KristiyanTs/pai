#!/usr/bin/env python3
"""
AI Client - WebSocket client for OpenAI Realtime API

Contains the RealtimeAIClient class for handling real-time communication
with OpenAI's Realtime API for voice conversations.
"""

import json
import base64
import threading
import time
import websocket
from typing import Optional
from queue import Empty

# Import from config module
from config.settings import SettingsManager

# Import from ui module
from ui.overlay import VoiceAssistantOverlay

# Import from audio_manager module
from audio_manager import AudioManager


class RealtimeAIClient:
    """WebSocket client for OpenAI Realtime API"""
    
    def __init__(self, api_key: str, audio_manager: AudioManager, overlay: VoiceAssistantOverlay, settings_manager: SettingsManager):
        self.api_key = api_key
        self.audio_manager = audio_manager
        self.overlay = overlay
        self.settings_manager = settings_manager
        self.ws = None
        self.connected = False
        self.conversation_active = False
        self.conversation_ending = False  # Flag to prevent multiple endings
        
        # WebSocket URL for OpenAI Realtime API
        self.ws_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
    
    def connect(self):
        """Connect to OpenAI Realtime API via WebSocket"""
        try:
            # Create WebSocket with authorization header
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                header=[f"Authorization: Bearer {self.api_key}"],
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Start WebSocket in separate thread
            ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            ws_thread.start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            if not self.connected:
                raise Exception("Failed to connect to OpenAI Realtime API")
                
            return True
            
        except Exception as e:
            print(f"Error connecting to OpenAI API: {e}")
            return False
    
    def _on_open(self, ws):
        """Handle WebSocket connection opened"""
        print("Connected to OpenAI Realtime API")
        self.connected = True
        
        # Get custom instructions from settings
        custom_instructions = self.settings_manager.get_combined_instructions()
        if not custom_instructions.strip():
            # Fallback to default if no custom instructions
            custom_instructions = "You are a helpful AI assistant. Keep responses concise and natural for voice conversation. Be friendly and engaging. Keep your responses brief and to the point."
        
        # Configure the session for voice conversation
        session_config = {
            "type": "session.update",
            "session": {
                "type": "realtime",
                "instructions": custom_instructions
            }
        }
        
        print(f"Using AI instructions: {custom_instructions[:100]}..." if len(custom_instructions) > 100 else f"Using AI instructions: {custom_instructions}")
        print(f"Sending session config: {json.dumps(session_config, indent=2)}")
        self.ws.send(json.dumps(session_config))
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            event = json.loads(message)
            event_type = event.get("type")
            
            # Debug: log unknown events only
            # print(f"DEBUG: Received event: {event_type}")
            
            if event_type == "session.created":
                print("Session created successfully")
                
            elif event_type == "session.updated":
                print("Session updated successfully")
                
            elif event_type == "input_audio_buffer.speech_started":
                print("Speech detected")
                self.overlay.update_status('listening')
                
            elif event_type == "input_audio_buffer.speech_stopped":
                print("Speech ended")
                self.overlay.update_status('processing')
                
            elif event_type == "response.created":
                print("AI response started")
                # Stop recording when AI starts speaking to prevent feedback loop
                self.audio_manager.stop_recording()
                
            elif event_type == "response.audio.delta":
                # Receive audio data from AI
                audio_b64 = event.get("delta", "")
                if audio_b64:
                    try:
                        audio_bytes = base64.b64decode(audio_b64)
                        print(f"DEBUG: Received {len(audio_bytes)} bytes of audio")
                        self.audio_manager.play_audio_data(audio_bytes)
                        self.overlay.update_status('speaking')
                    except Exception as e:
                        print(f"Error processing audio delta: {e}")
                        
            elif event_type == "response.output_audio.delta":
                # Try alternative event name
                audio_b64 = event.get("delta", "")
                if audio_b64:
                    try:
                        audio_bytes = base64.b64decode(audio_b64)
                        self.audio_manager.play_audio_data(audio_bytes)
                        self.overlay.update_status('speaking')
                    except Exception as e:
                        print(f"Error processing output audio delta: {e}")
                        
            elif event_type == "response.audio_transcript.delta":
                # Audio transcript
                transcript = event.get("delta", "")
                if transcript:
                    print(f"AI transcript: {transcript}")
                    
            elif event_type == "response.done":
                print("AI response completed")
                # Mark response as finished and start checking for audio completion
                self.audio_manager.response_finished = True
                if not self.conversation_ending and self.conversation_active:
                    self._check_audio_completion()
                
            elif event_type == "error":
                error_msg = event.get("error", {}).get("message", "Unknown error")
                # Ignore cancellation errors - they're expected when ending conversations
                if "cancellation failed" not in error_msg.lower():
                    print(f"API Error: {error_msg}")
                    self.overlay.update_status('error')
                    if not self.conversation_ending:
                        threading.Timer(2.0, self._end_conversation).start()
            
            else:
                # Silently ignore unknown events for cleaner output
                pass
                
        except Exception as e:
            print(f"Error handling message: {e}")
            print(f"Message was: {message[:200]}...")
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"WebSocket error: {error}")
        self.overlay.update_status('error')
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection closed"""
        print("Disconnected from OpenAI Realtime API")
        self.connected = False
    
    def start_conversation(self):
        """Start a new conversation"""
        if not self.connected:
            print("Not connected to API")
            return False
            
        # Reset flags
        self.conversation_ending = False
        self.conversation_active = True
        
        # Clear any pending audio input from previous conversation
        while not self.audio_manager.input_queue.empty():
            try:
                self.audio_manager.input_queue.get_nowait()
            except Empty:
                break
        
        # Send input_audio_buffer.clear to reset server state
        try:
            clear_event = {"type": "input_audio_buffer.clear"}
            self.ws.send(json.dumps(clear_event))
        except Exception as e:
            print(f"Error clearing input buffer: {e}")
        
        # Start audio recording
        self.audio_manager.start_recording()
        self.audio_manager.start_playback()
        
        # Start sending audio data
        threading.Thread(target=self._send_audio_loop, daemon=True).start()
        
        print("Conversation started")
        return True
    
    def _send_audio_loop(self):
        """Continuously send audio data to API"""
        while self.conversation_active and self.connected:
            # Only send audio if we're actively recording (not when AI is speaking)
            if self.audio_manager.recording:
                audio_data = self.audio_manager.get_audio_data()
                if audio_data:
                    # Send audio data to API
                    audio_event = {
                        "type": "input_audio_buffer.append",
                        "audio": base64.b64encode(audio_data).decode('utf-8')
                    }
                    self.ws.send(json.dumps(audio_event))
            
            time.sleep(0.01)  # Small delay to prevent overwhelming the API
    
    def _check_audio_completion(self):
        """Check if audio has finished playing and end conversation"""
        def check_buffer():
            if not self.conversation_active or self.conversation_ending:
                return
                
            # Check if audio buffer is empty (speech finished)
            with self.audio_manager.buffer_lock:
                buffer_empty = len(self.audio_manager.audio_buffer) == 0
                response_done = self.audio_manager.response_finished
            
            if buffer_empty and response_done:
                # Audio has finished playing
                self._end_conversation()
            else:
                # Check again in 100ms
                threading.Timer(0.1, check_buffer).start()
        
        # Start checking
        check_buffer()
    
    def _end_conversation(self):
        """End the current conversation"""
        if self.conversation_ending:
            return  # Already ending, prevent multiple calls
            
        self.conversation_ending = True
        self.conversation_active = False
        
        print("Ending conversation...")
        
        # Stop audio
        self.audio_manager.stop_recording()
        self.audio_manager.stop_playback()
        
        # Only send cancel if there's actually an active response
        # Skip cancellation since response is already done
        
        # Hide overlay (thread-safe)
        self.overlay.hide_overlay()
        
        print("Conversation ended")
        
        # Reset ending flag after a delay
        threading.Timer(1.0, lambda: setattr(self, 'conversation_ending', False)).start()
    
    def disconnect(self):
        """Disconnect from the API"""
        self.conversation_active = False
        self.connected = False
        if self.ws:
            self.ws.close()
