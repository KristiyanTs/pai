#!/usr/bin/env python3
"""
Settings Window - Configuration UI for AI Voice Assistant

Contains the SettingsWindow class for managing AI assistant configuration.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import subprocess
import threading
from config.settings import SettingsManager


class SettingsWindow:
    """Settings configuration window with dark theme"""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        self.settings_manager = settings_manager
        self.parent = parent
        self.window = None
        self.create_window()
    
    def create_window(self):
        """Create the settings window"""
        # Create window - always create as Toplevel without parent to ensure proper focus
        # This prevents issues when parent window is withdrawn/hidden
        self.window = tk.Toplevel()
        
        self.window.title("Settings")
        self.window.geometry("520x500")
        self.window.minsize(500, 480)
        self.window.resizable(True, True)
        
        # Configure modern dark theme
        self.window.configure(bg='#0f0f0f')
        
        # Center the window
        self.center_window()
        
        self.create_widgets()
        
        # Show window immediately without complex focus logic during creation
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
    
    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """Create modern, minimal UI widgets"""
        # Main container - no scrolling needed
        main_frame = tk.Frame(self.window, bg='#0f0f0f')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header section
        self.create_header(main_frame)
        
        # Settings sections
        self.create_context_section(main_frame)
        self.create_personality_section(main_frame)
        self.create_advanced_section(main_frame)
        
        # Action buttons
        self.create_action_buttons(main_frame)
    
    def create_header(self, parent):
        """Create minimal header section"""
        header_frame = tk.Frame(parent, bg='#0f0f0f')
        header_frame.pack(fill='x', pady=(0, 16))
        
        # Simple title
        title_label = tk.Label(
            header_frame,
            text="Settings",
            font=('Inter', 18, 'bold'),
            fg='#ffffff',
            bg='#0f0f0f'
        )
        title_label.pack(anchor='w')
    
    def create_section_frame(self, parent, title):
        """Create a minimal section frame"""
        section_frame = tk.Frame(parent, bg='#0f0f0f')
        section_frame.pack(fill='x', pady=(0, 12))
        
        # Section title
        title_label = tk.Label(
            section_frame,
            text=title,
            font=('Inter', 14, 'bold'),
            fg='#ffffff',
            bg='#0f0f0f'
        )
        title_label.pack(anchor='w', pady=(0, 6))
        
        return section_frame
    
    def create_modern_text_field(self, parent, placeholder, height=2):
        """Create a compact text field with placeholder styling"""
        text_widget = tk.Text(
            parent,
            height=height,
            font=('JetBrains Mono', 11),
            fg='#ffffff',
            bg='#1c1c1e',
            insertbackground='#ffffff',
            selectbackground='#0a84ff',
            selectforeground='#ffffff',
            relief='flat',
            bd=1,
            padx=10,
            pady=6,
            wrap='word'
        )
        
        # Add placeholder functionality
        text_widget.placeholder = placeholder
        text_widget.insert('1.0', placeholder)
        text_widget.config(fg='#8e8e93')
        
        def on_focus_in(event):
            if text_widget.get('1.0', tk.END).strip() == placeholder:
                text_widget.delete('1.0', tk.END)
                text_widget.config(fg='#ffffff')
        
        def on_focus_out(event):
            if not text_widget.get('1.0', tk.END).strip():
                text_widget.insert('1.0', placeholder)
                text_widget.config(fg='#8e8e93')
        
        text_widget.bind('<FocusIn>', on_focus_in)
        text_widget.bind('<FocusOut>', on_focus_out)
        
        return text_widget
    
    def create_context_section(self, parent):
        """Create the AI context configuration section"""
        section_frame = self.create_section_frame(parent, "Context")
        
        self.context_text = self.create_modern_text_field(
            section_frame,
            "What should the AI know about you and your work?",
            height=2
        )
        self.context_text.pack(fill='x')
        
        # Load existing value
        current_context = self.settings_manager.get_setting('ai_context', '')
        if current_context:
            self.context_text.delete('1.0', tk.END)
            self.context_text.insert('1.0', current_context)
            self.context_text.config(fg='#ffffff')
    
    def create_personality_section(self, parent):
        """Create the AI personality configuration section"""
        section_frame = self.create_section_frame(parent, "Personality")
        
        self.personality_text = self.create_modern_text_field(
            section_frame,
            "How should the AI communicate? (e.g., casual, professional, helpful)",
            height=2
        )
        self.personality_text.pack(fill='x')
        
        # Load existing value
        current_personality = self.settings_manager.get_setting('ai_personality', '')
        if current_personality:
            self.personality_text.delete('1.0', tk.END)
            self.personality_text.insert('1.0', current_personality)
            self.personality_text.config(fg='#ffffff')
    
    def create_advanced_section(self, parent):
        """Create the advanced settings section"""
        section_frame = self.create_section_frame(parent, "Advanced")
        
        # Custom instructions
        self.custom_instructions_text = self.create_modern_text_field(
            section_frame,
            "Additional instructions (optional)",
            height=2
        )
        self.custom_instructions_text.pack(fill='x', pady=(0, 12))
        
        # Load existing value
        current_instructions = self.settings_manager.get_setting('custom_instructions', '')
        if current_instructions:
            self.custom_instructions_text.delete('1.0', tk.END)
            self.custom_instructions_text.insert('1.0', current_instructions)
            self.custom_instructions_text.config(fg='#ffffff')
        
        # Voice speaker selection
        speaker_frame = tk.Frame(section_frame, bg='#0f0f0f')
        speaker_frame.pack(fill='x', pady=(0, 12))
        
        speaker_label = tk.Label(
            speaker_frame,
            text="Voice Speaker:",
            font=('Inter', 11),
            fg='#ffffff',
            bg='#0f0f0f'
        )
        speaker_label.pack(anchor='w', pady=(0, 4))
        
        # Available speakers according to OpenAI documentation
        self.speakers = [
            ("alloy", "Alloy - Neutral and balanced"),
            ("ash", "Ash - Clear and precise"),
            ("ballad", "Ballad - Melodic and smooth"),
            ("coral", "Coral - Warm and friendly"),
            ("echo", "Echo - Resonant and deep"),
            ("sage", "Sage - Calm and thoughtful"),
            ("shimmer", "Shimmer - Bright and energetic"),
            ("verse", "Verse - Versatile and expressive")
        ]
        
        self.speaker_var = tk.StringVar()
        current_speaker = self.settings_manager.get_setting('voice_speaker', 'alloy')
        self.speaker_var.set(current_speaker)
        
        speaker_combo = ttk.Combobox(
            speaker_frame,
            textvariable=self.speaker_var,
            values=[speaker[1] for speaker in self.speakers],
            state="readonly",
            font=('Inter', 10),
            width=40
        )
        
        # Set the current selection properly
        for i, (speaker_id, speaker_name) in enumerate(self.speakers):
            if speaker_id == current_speaker:
                speaker_combo.current(i)
                break
        
        speaker_combo.pack(anchor='w')
        
        # Style the combobox for dark theme
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TCombobox',
                       fieldbackground='#1c1c1e',
                       background='#1c1c1e',
                       foreground='#ffffff',
                       borderwidth=1,
                       relief='flat')
        style.map('TCombobox',
                 fieldbackground=[('readonly', '#1c1c1e')],
                 selectbackground=[('readonly', '#1c1c1e')],
                 selectforeground=[('readonly', '#ffffff')])
        
        # Voice activation toggle
        self.voice_activation_var = tk.BooleanVar()
        self.voice_activation_var.set(self.settings_manager.get_setting('voice_activation_enabled', True))
        
        activation_check = tk.Checkbutton(
            section_frame,
            text="Enable voice hotkey (⌘⇧V)",
            variable=self.voice_activation_var,
            font=('Inter', 11),
            fg='#ffffff',
            bg='#0f0f0f',
            selectcolor='#0a84ff',
            activebackground='#0f0f0f',
            activeforeground='#ffffff',
            relief='flat',
            bd=0
        )
        activation_check.pack(anchor='w')
    
    def create_action_buttons(self, parent):
        """Create minimal action buttons"""
        button_frame = tk.Frame(parent, bg='#0f0f0f')
        button_frame.pack(fill='x', pady=(12, 0))
        
        # Left side buttons
        left_buttons = tk.Frame(button_frame, bg='#0f0f0f')
        left_buttons.pack(side='left')
        
        # Reset to defaults button
        reset_button = tk.Button(
            left_buttons,
            text="🔄 Reset to Defaults",
            command=self.reset_to_defaults,
            font=('Inter', 10),
            fg='#8e8e93',
            bg='#1c1c1e',
            activebackground='#2c2c2e',
            activeforeground='#ffffff',
            relief='flat',
            bd=0,
            padx=12,
            pady=4,
            cursor='pointinghand'
        )
        reset_button.pack(side='left')
        
        # Right side buttons
        right_buttons = tk.Frame(button_frame, bg='#0f0f0f')
        right_buttons.pack(side='right')
        
        # Save button (primary) with emoji
        save_button = tk.Button(
            right_buttons,
            text="💾 Save",
            command=self.save_settings,
            font=('Inter', 10, 'bold'),
            fg='#000000',
            bg='#0a84ff',
            activebackground='#0056b3',
            activeforeground='#000000',
            relief='flat',
            bd=0,
            padx=16,
            pady=4,
            cursor='pointinghand'
        )
        save_button.pack(side='right', padx=(4, 0))
        
        # Cancel button (secondary) - minimal
        cancel_button = tk.Button(
            right_buttons,
            text="Cancel",
            command=self.cancel,
            font=('Inter', 10),
            fg='#8e8e93',
            bg='#0f0f0f',
            activebackground='#1c1c1e',
            activeforeground='#ffffff',
            relief='flat',
            bd=0,
            padx=12,
            pady=4,
            cursor='pointinghand'
        )
        cancel_button.pack(side='right')
    
    
    def _get_text_value(self, text_widget):
        """Get actual value from text widget, ignoring placeholder"""
        content = text_widget.get('1.0', tk.END).strip()
        if content == text_widget.placeholder:
            return ''
        return content
    
    def save_settings(self):
        """Save all settings"""
        try:
            # Update settings from UI (handle placeholders)
            context_value = self._get_text_value(self.context_text)
            personality_value = self._get_text_value(self.personality_text)
            instructions_value = self._get_text_value(self.custom_instructions_text)
            
            # Get selected speaker ID from the combobox
            selected_speaker_name = self.speaker_var.get()
            selected_speaker_id = 'alloy'  # Default fallback
            for speaker_id, speaker_name in self.speakers:
                if speaker_name == selected_speaker_name:
                    selected_speaker_id = speaker_id
                    break
            
            # Update settings (this will trigger change callbacks)
            self.settings_manager.set_setting('ai_context', context_value)
            self.settings_manager.set_setting('ai_personality', personality_value)
            self.settings_manager.set_setting('custom_instructions', instructions_value)
            self.settings_manager.set_setting('voice_activation_enabled', self.voice_activation_var.get())
            self.settings_manager.set_setting('voice_speaker', selected_speaker_id)
            
            # Save to file
            if self.settings_manager.save_settings():
                messagebox.showinfo("Settings Saved", "Your AI assistant settings have been saved and applied immediately!")
                self.window.destroy()
            else:
                messagebox.showerror("Error", "Failed to save settings. Please try again.")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving settings: {str(e)}")
    
    def cancel(self):
        """Cancel without saving"""
        self.window.destroy()
    
    def _reset_text_field(self, text_widget, default_value):
        """Reset a text field to default value or placeholder"""
        text_widget.delete('1.0', tk.END)
        if default_value:
            text_widget.insert('1.0', default_value)
            text_widget.config(fg='#ffffff')
        else:
            text_widget.insert('1.0', text_widget.placeholder)
            text_widget.config(fg='#8e8e93')
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        # Reset text fields with proper placeholder handling
        self._reset_text_field(self.context_text, self.settings_manager.default_settings['ai_context'])
        self._reset_text_field(self.personality_text, self.settings_manager.default_settings['ai_personality'])
        self._reset_text_field(self.custom_instructions_text, self.settings_manager.default_settings['custom_instructions'])
        
        self.voice_activation_var.set(self.settings_manager.default_settings['voice_activation_enabled'])
        
        # Reset speaker to default
        default_speaker = self.settings_manager.default_settings['voice_speaker']
        for i, (speaker_id, speaker_name) in enumerate(self.speakers):
            if speaker_id == default_speaker:
                self.speaker_var.set(speaker_name)
                break
    
    def show(self):
        """Show the settings window"""
        if self.window:
            # Bring to front and focus
            self.window.deiconify()
            self.window.lift()
            self.window.attributes('-topmost', True)
            self.window.focus_force()
            
            # For macOS: Ensure the application is brought to the foreground (async)
            if sys.platform == 'darwin':
                self._activate_app_async()
            
            # Remove topmost after a brief moment so window behaves normally
            self.window.after(100, lambda: self.window.attributes('-topmost', False))
    
    def _activate_app_async(self):
        """Activate the application asynchronously on macOS"""
        def activate():
            try:
                # Use AppleScript to bring the current application to front
                process_name = os.path.basename(sys.executable)
                subprocess.run([
                    'osascript', '-e',
                    f'tell application "{process_name}" to activate'
                ], check=False, capture_output=True, timeout=2)
            except Exception:
                pass
        
        # Run in background thread to avoid blocking UI
        threading.Thread(target=activate, daemon=True).start()
