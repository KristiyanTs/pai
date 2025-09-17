#!/usr/bin/env python3
"""
AI Voice Assistant - Core voice assistant functionality

Contains the main AIVoiceAssistant class and supporting components.
"""

import os
import sys
import json
import base64
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional
import asyncio
import websocket
import numpy as np
import sounddevice as sd
from queue import Queue, Empty
from pynput import keyboard
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv()

# Import from config module
from config.settings import SettingsManager

# Import from ui module
from ui.overlay import VoiceAssistantOverlay
from ui.settings_window import SettingsWindow

# Import from permissions module
from permissions import PermissionsHelper

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


class AIVoiceAssistant:
    """Main voice assistant application"""
    
    def __init__(self):
        # Load API key
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
        
        # Check accessibility permissions first
        print("🔐 Checking accessibility permissions...")
        if not PermissionsHelper.check_accessibility_permissions():
            print("❌ Accessibility permissions not granted")
            print("📋 Opening permissions setup dialog...")
            PermissionsHelper.show_permissions_dialog()
            print("ℹ️  You can continue, but global hotkeys won't work until permissions are granted")
        else:
            print("✅ Accessibility permissions granted")
        
        # Initialize components
        self.settings_manager = SettingsManager()
        self.overlay = VoiceAssistantOverlay()
        self.audio_manager = AudioManager()
        self.ai_client = RealtimeAIClient(self.api_key, self.audio_manager, self.overlay, self.settings_manager)
        self.settings_window = None
        
        # Queue for thread-safe GUI operations
        self.gui_queue = Queue()
        
        # State
        self.running = True
        self.conversation_in_progress = False
        self.has_permissions = PermissionsHelper.check_accessibility_permissions()
        
        # Debouncing for hotkeys
        self.last_settings_hotkey_time = 0
        self.settings_hotkey_debounce = 0.5  # 500ms debounce
        
        # Connect to API
        print("Connecting to OpenAI Realtime API...")
        if not self.ai_client.connect():
            raise Exception("Failed to connect to OpenAI API")
        print("Connected successfully!")
    
    def on_hotkey_pressed(self):
        """Handle global hotkey press (Cmd+Shift+V)"""
        if self.conversation_in_progress:
            print("Conversation already in progress")
            return
        
        print("Hotkey pressed - starting conversation")
        self.conversation_in_progress = True
        
        # Run conversation in separate thread
        threading.Thread(target=self._handle_conversation, daemon=True).start()
    
    def on_settings_hotkey_pressed(self):
        """Handle settings hotkey press (Cmd+Shift+Z)"""
        current_time = time.time()
        if current_time - self.last_settings_hotkey_time < self.settings_hotkey_debounce:
            return  # Ignore if too soon after last press
        
        self.last_settings_hotkey_time = current_time
        print("Settings hotkey pressed - opening settings")
        # Queue the settings window opening for the main thread
        self.gui_queue.put('show_settings')
    
    def show_settings(self):
        """Show the settings window"""
        try:
            if self.settings_window is None or not hasattr(self.settings_window, 'window') or not self.settings_window.window.winfo_exists():
                # Create new settings window
                self.settings_window = SettingsWindow(self.settings_manager, self.overlay.root)
            else:
                # Show existing window
                self.settings_window.show()
        except Exception as e:
            print(f"Error opening settings window: {e}")
    
    def _process_gui_queue(self):
        """Process GUI operations from background threads (call from main thread only)"""
        try:
            while True:
                action = self.gui_queue.get_nowait()
                if action == 'show_settings':
                    self.show_settings()
        except Empty:
            pass
    
    def _handle_conversation(self):
        """Handle a complete conversation cycle"""
        try:
            # Show overlay and set status (thread-safe)
            self.overlay.show_overlay()
            self.overlay.update_status('listening')
            
            # Start conversation
            if self.ai_client.start_conversation():
                # Conversation will be handled by WebSocket events
                # The conversation will end automatically when AI response is complete
                pass
            else:
                print("Failed to start conversation")
                self.overlay.update_status('error')
                time.sleep(2)
                self.overlay.hide_overlay()
                
        except Exception as e:
            print(f"Error in conversation: {e}")
            self.overlay.update_status('error')
            time.sleep(2)
            self.overlay.hide_overlay()
        finally:
            self.conversation_in_progress = False
    
    def setup_hotkey_listener(self):
        """Setup global hotkey listener"""
        # Define hotkey combinations
        voice_hotkey = {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode.from_char('v')}
        settings_hotkey = {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode.from_char('z')}  # Z for Settings
        current_keys = set()
        
        def on_press(key):
            current_keys.add(key)
            if voice_hotkey.issubset(current_keys):
                self.on_hotkey_pressed()
            elif settings_hotkey.issubset(current_keys):
                self.on_settings_hotkey_pressed()
        
        def on_release(key):
            current_keys.discard(key)
            
            # Exit on Ctrl+C or Cmd+Q
            if key == keyboard.Key.esc or (key == keyboard.KeyCode.from_char('q') and keyboard.Key.cmd in current_keys):
                print("Exit hotkey detected")
                self.running = False
                return False
        
        try:
            # Start listener
            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.start()
            
            print("Global hotkey listener started")
            if self.has_permissions:
                print("✅ Press Cmd+Shift+V to activate voice assistant")
                print("⚙️  Press Cmd+Shift+Z to open preferences/settings")
            else:
                print("⚠️  Cmd+Shift+V and Cmd+Shift+Z hotkeys will not work without accessibility permissions")
                print("💡 Grant permissions to enable global hotkey activation")
            print("Press Cmd+Q or Esc to exit")
            
            return listener
            
        except Exception as e:
            print(f"❌ Could not start hotkey listener: {e}")
            print("⚠️  Global hotkeys will not work. You may need to grant accessibility permissions.")
            return None
    
    def run(self):
        """Main application loop"""
        try:
            # Setup hotkey listener
            listener = self.setup_hotkey_listener()
            
            # Start GUI update processing
            self.overlay._process_updates()
            
            # Keep application running
            while self.running:
                # Update tkinter
                self.overlay.root.update()
                
                # Process GUI queue for thread-safe operations
                self._process_gui_queue()
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up...")
        
        # Disconnect from API
        self.ai_client.disconnect()
        
        # Stop audio
        self.audio_manager.stop_recording()
        self.audio_manager.stop_playback()
        
        # Hide overlay
        self.overlay.hide_overlay()
        
        print("Cleanup complete")


