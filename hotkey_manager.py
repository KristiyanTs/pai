#!/usr/bin/env python3
"""
Hotkey Manager - Handle global hotkey detection and management

Contains the HotkeyManager class for managing global hotkeys,
permissions checking, and hotkey event handling.
"""

import time
from typing import Optional, Callable
from pynput import keyboard

# Import from permissions module
from permissions import PermissionsHelper


class HotkeyManager:
    """Manages global hotkeys and their event handling"""
    
    def __init__(self, voice_callback: Callable, settings_callback: Callable, exit_callback: Callable, settings_manager=None):
        """
        Initialize the hotkey manager
        
        Args:
            voice_callback: Function to call when voice hotkey is pressed
            settings_callback: Function to call when settings hotkey is pressed
            exit_callback: Function to call when exit hotkey is pressed
            settings_manager: SettingsManager instance for hotkey configuration
        """
        self.voice_callback = voice_callback
        self.settings_callback = settings_callback
        self.exit_callback = exit_callback
        self.settings_manager = settings_manager
        
        # State
        self.has_permissions = PermissionsHelper.check_accessibility_permissions()
        self.listener = None
        
        # Debouncing for hotkeys
        self.last_settings_hotkey_time = 0
        self.settings_hotkey_debounce = 0.5  # 500ms debounce
        
        # Define hotkey combinations (will be updated from settings)
        self.voice_hotkey = {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode.from_char('v')}
        self.settings_hotkey = {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode.from_char('z')}
        self.current_keys = set()
        
        # Register for settings changes if settings manager is provided
        if self.settings_manager:
            self.settings_manager.add_change_callback(self._on_settings_changed)
            self._update_hotkeys_from_settings()
    
    def _on_settings_changed(self, key: str, value):
        """Handle settings changes"""
        if key in ["hotkey_combo", "settings_hotkey_combo"]:
            print(f"Hotkey combination changed: {key} = {value}")
            self._update_hotkeys_from_settings()
    
    def _update_hotkeys_from_settings(self):
        """Update hotkey combinations from settings"""
        if not self.settings_manager:
            return
            
        # Update voice hotkey
        voice_combo = self.settings_manager.get_setting('hotkey_combo', 'cmd+shift+v')
        self.voice_hotkey = self._parse_hotkey_combo(voice_combo)
        
        # Update settings hotkey
        settings_combo = self.settings_manager.get_setting('settings_hotkey_combo', 'cmd+shift+z')
        self.settings_hotkey = self._parse_hotkey_combo(settings_combo)
        
        print(f"Updated hotkeys - Voice: {voice_combo}, Settings: {settings_combo}")
    
    def _parse_hotkey_combo(self, combo: str):
        """Parse hotkey combination string into key set"""
        keys = set()
        combo_lower = combo.lower().replace('+', ' ')
        
        if 'cmd' in combo_lower or 'command' in combo_lower:
            keys.add(keyboard.Key.cmd)
        if 'ctrl' in combo_lower or 'control' in combo_lower:
            keys.add(keyboard.Key.ctrl)
        if 'alt' in combo_lower:
            keys.add(keyboard.Key.alt)
        if 'shift' in combo_lower:
            keys.add(keyboard.Key.shift)
        
        # Extract the main key (last part)
        parts = combo_lower.split()
        if parts:
            main_key = parts[-1]
            if main_key in ['v', 'z', 'q', 'esc']:
                keys.add(keyboard.KeyCode.from_char(main_key))
            elif main_key == 'space':
                keys.add(keyboard.Key.space)
            elif main_key == 'enter':
                keys.add(keyboard.Key.enter)
        
        return keys
    
    def check_permissions(self) -> bool:
        """Check if accessibility permissions are granted"""
        self.has_permissions = PermissionsHelper.check_accessibility_permissions()
        return self.has_permissions
    
    def setup_hotkey_listener(self) -> Optional[keyboard.Listener]:
        """Setup global hotkey listener"""
        def on_press(key):
            self.current_keys.add(key)
            if self.voice_hotkey.issubset(self.current_keys):
                self._on_voice_hotkey_pressed()
            elif self.settings_hotkey.issubset(self.current_keys):
                self._on_settings_hotkey_pressed()
        
        def on_release(key):
            self.current_keys.discard(key)
            
            # Exit on Ctrl+C or Cmd+Q
            if key == keyboard.Key.esc or (key == keyboard.KeyCode.from_char('q') and keyboard.Key.cmd in self.current_keys):
                print("Exit hotkey detected")
                self.exit_callback()
                return False
        
        try:
            # Start listener
            self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self.listener.start()
            
            print("Global hotkey listener started")
            if self.has_permissions:
                print("✅ Press Cmd+Shift+V to activate voice assistant")
                print("⚙️  Press Cmd+Shift+Z to open preferences/settings")
            else:
                print("⚠️  Cmd+Shift+V and Cmd+Shift+Z hotkeys will not work without accessibility permissions")
                print("💡 Grant permissions to enable global hotkey activation")
            print("Press Cmd+Q or Esc to exit")
            
            return self.listener
            
        except Exception as e:
            print(f"❌ Could not start hotkey listener: {e}")
            print("⚠️  Global hotkeys will not work. You may need to grant accessibility permissions.")
            return None
    
    def _on_voice_hotkey_pressed(self):
        """Handle voice hotkey press (Cmd+Shift+V)"""
        self.voice_callback()
    
    def _on_settings_hotkey_pressed(self):
        """Handle settings hotkey press (Cmd+Shift+Z)"""
        current_time = time.time()
        if current_time - self.last_settings_hotkey_time < self.settings_hotkey_debounce:
            return  # Ignore if too soon after last press
        
        self.last_settings_hotkey_time = current_time
        self.settings_callback()
    
    def stop_listener(self):
        """Stop the hotkey listener"""
        if self.listener:
            self.listener.stop()
            self.listener = None
    
    def is_listener_running(self) -> bool:
        """Check if the listener is currently running"""
        return self.listener is not None and self.listener.running
