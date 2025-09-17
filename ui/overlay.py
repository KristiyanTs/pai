#!/usr/bin/env python3
"""
Overlay UI for AI Voice Assistant

Handles the transparent, borderless overlay UI for showing assistant status.
"""

import sys
import tkinter as tk
from tkinter import ttk
from queue import Queue, Empty


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
