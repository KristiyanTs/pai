#!/usr/bin/env python3
"""
Settings management for AI Voice Assistant

Handles loading, saving, and managing configuration settings for the voice assistant.
"""

import os
import json
from typing import Optional


class SettingsManager:
    """Manages AI assistant settings and configuration"""
    
    def __init__(self):
        self.settings_file = "assistant_settings.json"
        self.default_settings = {
            "ai_context": "You are a helpful AI assistant. Keep responses concise and natural for voice conversation.",
            "ai_personality": "Be friendly, engaging, and professional. Keep your responses brief and to the point.",
            "custom_instructions": "",
            "voice_activation_enabled": True,
            "hotkey_combo": "cmd+shift+v",
            "settings_hotkey_combo": "cmd+shift+z",
            "voice_speaker": "alloy"
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file or create defaults"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_settings = self.default_settings.copy()
                merged_settings.update(settings)
                return merged_settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_setting(self, key, default=None):
        """Get a specific setting value"""
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """Set a specific setting value"""
        self.settings[key] = value
    
    def get_combined_instructions(self):
        """Get combined AI instructions from context, personality, and custom instructions"""
        instructions_parts = []
        
        if self.settings.get("ai_context"):
            instructions_parts.append(self.settings["ai_context"])
        
        if self.settings.get("ai_personality"):
            instructions_parts.append(self.settings["ai_personality"])
        
        if self.settings.get("custom_instructions"):
            instructions_parts.append(self.settings["custom_instructions"])
        
        return " ".join(instructions_parts)
