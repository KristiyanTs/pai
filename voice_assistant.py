#!/usr/bin/env python3
"""
AI Voice Assistant - Core voice assistant functionality

Contains the main AIVoiceAssistant class and supporting components.
"""

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional
from queue import Queue, Empty
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

# Import from ai_client module
from ai_client import RealtimeAIClient

# Import from hotkey_manager module
from hotkey_manager import HotkeyManager
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
        
        # Initialize hotkey manager
        self.hotkey_manager = HotkeyManager(
            voice_callback=self.on_hotkey_pressed,
            settings_callback=self.on_settings_hotkey_pressed,
            exit_callback=self._on_exit_requested
        )
        
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
        print("Settings hotkey pressed - opening settings")
        # Queue the settings window opening for the main thread
        self.gui_queue.put('show_settings')
    
    def _on_exit_requested(self):
        """Handle exit request from hotkey"""
        self.running = False
    
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
    
    
    def run(self):
        """Main application loop"""
        try:
            # Setup hotkey listener
            listener = self.hotkey_manager.setup_hotkey_listener()
            
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
        
        # Stop hotkey listener
        self.hotkey_manager.stop_listener()
        
        # Disconnect from API
        self.ai_client.disconnect()
        
        # Stop audio
        self.audio_manager.stop_recording()
        self.audio_manager.stop_playback()
        
        # Hide overlay
        self.overlay.hide_overlay()
        
        print("Cleanup complete")


