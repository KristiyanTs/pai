#!/usr/bin/env python3
"""
AI Voice Assistant - System-wide voice assistant using OpenAI's Realtime API

A standalone Python script that provides a global hotkey-activated voice assistant.
Press Cmd+Shift+V to start a conversation with the AI assistant.

Requirements:
- OpenAI API key in .env file
- Python packages: openai, pynput, sounddevice, numpy, python-dotenv, websocket-client

Usage:
1. Copy env_example.txt to .env and add your OpenAI API key
2. Install dependencies: pip install -r requirements.txt
3. Run: python voice_assistant.py
4. Press Cmd+Shift+V to activate voice assistant
5. Press Ctrl+C to exit
"""

import os
import sys
import json
import base64
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
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

class PermissionsHelper:
    """Handle accessibility permissions on macOS"""
    
    @staticmethod
    def check_accessibility_permissions():
        """Check if accessibility permissions are granted using system check"""
        try:
            # Use a more reliable system check
            import subprocess
            result = subprocess.run([
                "osascript", "-e", 
                'tell application "System Events" to get name of every process'
            ], capture_output=True, text=True, timeout=5)
            
            # If this succeeds without permission prompts, we likely have permissions
            return result.returncode == 0
        except Exception:
            # If the system check fails, assume no permissions
            return False
    
    @staticmethod
    def open_accessibility_settings():
        """Open macOS Accessibility settings"""
        try:
            # Open System Preferences to Accessibility settings
            subprocess.run([
                "open", 
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
            ], check=False)
            return True
        except Exception as e:
            print(f"Could not open System Preferences: {e}")
            return False
    
    @staticmethod
    def show_permissions_dialog():
        """Show a dialog asking user to grant accessibility permissions"""
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        # Create custom dialog
        dialog = tk.Toplevel(root)
        dialog.title("🔐 Accessibility Permissions Required")
        dialog.geometry("500x350")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Make dialog modal and on top
        dialog.transient(root)
        dialog.grab_set()
        dialog.attributes('-topmost', True)
        
        # Configure dark theme
        dialog.configure(bg='#1a1a1a')
        
        # Title
        title_label = tk.Label(
            dialog, 
            text="🎤 AI Voice Assistant", 
            font=('SF Pro Display', 18, 'bold'),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        title_label.pack(pady=(20, 10))
        
        # Main message
        message_label = tk.Label(
            dialog,
            text="Accessibility permissions are required for global hotkeys.\n\n"
                 "The hotkey Cmd+Shift+V won't work without these permissions.",
            font=('SF Pro Display', 12),
            fg='#ffffff',
            bg='#1a1a1a',
            justify='center'
        )
        message_label.pack(pady=10)
        
        # Instructions
        instructions = tk.Text(
            dialog,
            height=8,
            width=55,
            font=('SF Mono', 10),
            fg='#ffffff',
            bg='#2d2d2d',
            bd=0,
            wrap='word'
        )
        instructions.pack(pady=10, padx=20)
        
        instructions_text = """Steps to grant permissions:

1. Click "Open Settings" below (or manually open System Preferences)
2. Go to: Security & Privacy → Privacy → Accessibility  
3. Click the lock icon (🔒) and enter your password
4. Find "Terminal" (or your terminal app) in the list
5. Check the box ✅ next to it to grant permission
6. If Terminal isn't listed, click "+" and add it from Applications/Utilities
7. Restart the voice assistant after granting permissions

Hotkey: Cmd+Shift+V (avoiding conflicts with Spotlight)"""
        
        instructions.insert('1.0', instructions_text)
        instructions.config(state='disabled')
        
        # Button frame
        button_frame = tk.Frame(dialog, bg='#1a1a1a')
        button_frame.pack(pady=20)
        
        def open_settings():
            PermissionsHelper.open_accessibility_settings()
            dialog.destroy()
            root.destroy()
        
        def continue_anyway():
            print("⚠️  Continuing without accessibility permissions - global hotkeys will not work")
            dialog.destroy()
            root.destroy()
        
        # Buttons
        open_button = tk.Button(
            button_frame,
            text="🔧 Open Settings",
            command=open_settings,
            font=('SF Pro Display', 12, 'bold'),
            fg='#ffffff',
            bg='#007AFF',
            activebackground='#0056CC',
            activeforeground='#ffffff',
            bd=0,
            padx=20,
            pady=8
        )
        open_button.pack(side='left', padx=10)
        
        continue_button = tk.Button(
            button_frame,
            text="Continue Anyway",
            command=continue_anyway,
            font=('SF Pro Display', 12),
            fg='#ffffff',
            bg='#444444',
            activebackground='#555555',
            activeforeground='#ffffff',
            bd=0,
            padx=20,
            pady=8
        )
        continue_button.pack(side='left', padx=10)
        
        # Wait for dialog to close
        dialog.wait_window()
        root.quit()
        root.destroy()

class VoiceAssistantOverlay:
    """Transparent, borderless overlay UI for showing assistant status"""
    
    def __init__(self):
        self.root = None
        self.label = None
        self.is_visible = False
        self.update_queue = Queue()
        self.action_queue = Queue()  # For show/hide actions
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize the tkinter overlay window"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide initially
        
        # Configure window properties
        self.root.title("AI Assistant")
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes('-topmost', True)  # Always on top
        self.root.attributes('-alpha', 0.8)  # Semi-transparent
        
        # Make window stay on top on macOS
        if sys.platform == 'darwin':
            self.root.call('wm', 'attributes', '.', '-topmost', True)
        
        # Configure window size and position
        self.root.geometry("200x60")
        
        # Center the window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 4  # Position in upper third of screen
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Configure dark theme styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Overlay.TLabel', 
                       background='#1a1a1a', 
                       foreground='#ffffff',
                       font=('SF Pro Display', 14, 'bold'))
        
        # Create main frame with dark background
        frame = tk.Frame(self.root, bg='#1a1a1a', bd=0)
        frame.pack(fill='both', expand=True)
        
        # Create status label
        self.label = ttk.Label(frame, 
                              text="🎤 Listening...", 
                              style='Overlay.TLabel',
                              anchor='center')
        self.label.pack(expand=True, fill='both')
        
        # Round the corners (if supported)
        try:
            self.root.configure(bg='#1a1a1a')
        except:
            pass
    
    def show_overlay(self):
        """Show the overlay window (thread-safe)"""
        self.action_queue.put('show')
    
    def hide_overlay(self):
        """Hide the overlay window (thread-safe)"""
        self.action_queue.put('hide')
    
    def _show_overlay_direct(self):
        """Actually show the overlay (call from main thread only)"""
        if not self.is_visible:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.is_visible = True
    
    def _hide_overlay_direct(self):
        """Actually hide the overlay (call from main thread only)"""
        if self.is_visible:
            self.root.withdraw()
            self.is_visible = False
    
    def update_status(self, status: str):
        """Update the status text in the overlay (thread-safe)"""
        self.update_queue.put(status)
    
    def _process_updates(self):
        """Process pending status updates and actions (call from main thread)"""
        try:
            # Process status updates
            while True:
                status = self.update_queue.get_nowait()
                if self.label:
                    status_icons = {
                        'listening': '🎤 Listening...',
                        'processing': '🤔 Thinking...',
                        'speaking': '🗣️ Speaking...',
                        'error': '❌ Error occurred'
                    }
                    self.label.config(text=status_icons.get(status, status))
        except Empty:
            pass
        
        try:
            # Process show/hide actions
            while True:
                action = self.action_queue.get_nowait()
                if action == 'show':
                    self._show_overlay_direct()
                elif action == 'hide':
                    self._hide_overlay_direct()
        except Empty:
            pass
        
        # Schedule next update check
        self.root.after(50, self._process_updates)


class AudioManager:
    """Handles audio input/output operations"""
    
    def __init__(self):
        self.sample_rate = 24000  # OpenAI Realtime API sample rate
        self.channels = 1
        self.dtype = np.int16
        self.chunk_size = 1024
        
        self.input_queue = Queue()
        self.output_queue = Queue()
        self.recording = False
        self.playing = False
        
        self.input_stream = None
        self.output_stream = None
        
        # Audio buffer for proper sequencing
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_lock = threading.Lock()
        self.response_finished = False
    
    def start_recording(self):
        """Start recording audio from microphone"""
        if self.recording:
            return
            
        self.recording = True
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio input status: {status}")
            if self.recording:
                # Convert float32 to int16 and put in queue
                audio_data = (indata[:, 0] * 32767).astype(np.int16)
                self.input_queue.put(audio_data.tobytes())
        
        try:
            self.input_stream = sd.InputStream(
                callback=audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype='float32',
                blocksize=self.chunk_size
            )
            self.input_stream.start()
            print("Started audio recording")
        except Exception as e:
            print(f"Error starting audio recording: {e}")
            self.recording = False
    
    def stop_recording(self):
        """Stop recording audio"""
        self.recording = False
        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()
            self.input_stream = None
        print("Stopped audio recording")
    
    def start_playback(self):
        """Start audio playback thread"""
        if self.playing:
            return
        
        # Clear any leftover audio from previous sessions
        with self.buffer_lock:
            self.audio_buffer = np.array([], dtype=np.float32)
            self.response_finished = False
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except Empty:
                break
            
        self.playing = True
        
        def playback_thread():
            def audio_callback(outdata, frames, time, status):
                if status:
                    print(f"Audio output status: {status}")
                
                with self.buffer_lock:
                    # Add new audio data to buffer
                    while not self.output_queue.empty():
                        try:
                            audio_bytes = self.output_queue.get_nowait()
                            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                            audio_float = audio_data.astype(np.float32) / 32767.0
                            self.audio_buffer = np.concatenate([self.audio_buffer, audio_float])
                        except Empty:
                            break
                    
                    # Fill output with available buffer data
                    if len(self.audio_buffer) >= frames:
                        outdata[:, 0] = self.audio_buffer[:frames]
                        self.audio_buffer = self.audio_buffer[frames:]
                    elif len(self.audio_buffer) > 0:
                        outdata[:len(self.audio_buffer), 0] = self.audio_buffer
                        outdata[len(self.audio_buffer):, 0] = 0
                        self.audio_buffer = np.array([], dtype=np.float32)
                    else:
                        outdata[:, 0] = 0
        
            try:
                self.output_stream = sd.OutputStream(
                    callback=audio_callback,
                    channels=self.channels,
                    samplerate=self.sample_rate,
                    dtype='float32',
                    blocksize=self.chunk_size
                )
                self.output_stream.start()
                
                # Keep stream alive while playing
                while self.playing:
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"Error in audio playback: {e}")
            finally:
                if self.output_stream:
                    self.output_stream.stop()
                    self.output_stream.close()
                    self.output_stream = None
        
        threading.Thread(target=playback_thread, daemon=True).start()
        print("Started audio playback")
    
    def stop_playback(self):
        """Stop audio playback"""
        self.playing = False
        # Clear audio buffer to prevent leftover audio
        with self.buffer_lock:
            self.audio_buffer = np.array([], dtype=np.float32)
        # Clear output queue
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except Empty:
                break
        print("Stopped audio playback")
    
    def get_audio_data(self):
        """Get recorded audio data from queue"""
        try:
            return self.input_queue.get_nowait()
        except Empty:
            return None
    
    def play_audio_data(self, audio_bytes: bytes):
        """Add audio data to playback queue with proper sequencing"""
        # Ensure audio data is properly queued in order
        self.output_queue.put(audio_bytes)


class RealtimeAIClient:
    """WebSocket client for OpenAI Realtime API"""
    
    def __init__(self, api_key: str, audio_manager: AudioManager, overlay: VoiceAssistantOverlay):
        self.api_key = api_key
        self.audio_manager = audio_manager
        self.overlay = overlay
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
        
        # Configure the session for voice conversation
        session_config = {
            "type": "session.update",
            "session": {
                "type": "realtime",
                "instructions": "You are a helpful AI assistant. Keep responses concise and natural for voice conversation. Be friendly and engaging. Keep your responses brief and to the point."
            }
        }
        
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
        self.overlay = VoiceAssistantOverlay()
        self.audio_manager = AudioManager()
        self.ai_client = RealtimeAIClient(self.api_key, self.audio_manager, self.overlay)
        
        # State
        self.running = True
        self.conversation_in_progress = False
        self.has_permissions = PermissionsHelper.check_accessibility_permissions()
        
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
        # Define hotkey combination: Cmd+Shift+V (V for Voice)
        hotkey_combination = {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode.from_char('v')}
        current_keys = set()
        
        def on_press(key):
            current_keys.add(key)
            if hotkey_combination.issubset(current_keys):
                self.on_hotkey_pressed()
        
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
            else:
                print("⚠️  Cmd+Shift+V hotkey will not work without accessibility permissions")
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


def main():
    """Main entry point"""
    print("🎤 AI Voice Assistant")
    print("=" * 50)
    
    try:
        # Create and run assistant
        assistant = AIVoiceAssistant()
        assistant.run()
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease ensure:")
        print("1. You have a .env file with your OPENAI_API_KEY")
        print("2. Your API key is valid and has access to the Realtime API")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error starting voice assistant: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
