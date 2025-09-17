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
        
        self.window.title("AI Assistant Settings")
        self.window.geometry("650x750")
        self.window.minsize(600, 700)
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
        # Main scrollable container
        canvas = tk.Canvas(self.window, bg='#0f0f0f', highlightthickness=0)
        
        # Modern scrollbar styling
        style = ttk.Style()
        style.configure("Modern.Vertical.TScrollbar",
                       background='#2c2c2e',
                       troughcolor='#1c1c1e',
                       borderwidth=0,
                       arrowcolor='#8e8e93',
                       darkcolor='#2c2c2e',
                       lightcolor='#2c2c2e')
        
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview, style="Modern.Vertical.TScrollbar")
        self.scrollable_frame = tk.Frame(canvas, bg='#0f0f0f')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Header section
        self.create_header()
        
        # Settings sections
        self.create_context_section()
        self.create_personality_section()
        self.create_advanced_section()
        
        # Action buttons
        self.create_action_buttons()
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def create_header(self):
        """Create modern header section"""
        header_frame = tk.Frame(self.scrollable_frame, bg='#0f0f0f')
        header_frame.pack(fill='x', padx=40, pady=(30, 40))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="AI Assistant",
            font=('SF Pro Display', 24, 'normal'),
            fg='#ffffff',
            bg='#0f0f0f'
        )
        title_label.pack(anchor='w')
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Configure your AI assistant's behavior and knowledge",
            font=('SF Pro Display', 13),
            fg='#8e8e93',
            bg='#0f0f0f'
        )
        subtitle_label.pack(anchor='w', pady=(4, 0))
    
    def create_section_frame(self, title, description):
        """Create a modern section frame with title and description"""
        section_frame = tk.Frame(self.scrollable_frame, bg='#1c1c1e', relief='flat', bd=0)
        section_frame.pack(fill='x', padx=40, pady=(0, 20))
        
        # Section header
        header_frame = tk.Frame(section_frame, bg='#1c1c1e')
        header_frame.pack(fill='x', padx=24, pady=(20, 16))
        
        # Section title
        title_label = tk.Label(
            header_frame,
            text=title,
            font=('SF Pro Display', 17, 'bold'),
            fg='#ffffff',
            bg='#1c1c1e'
        )
        title_label.pack(anchor='w')
        
        # Section description
        if description:
            desc_label = tk.Label(
                header_frame,
                text=description,
                font=('SF Pro Display', 13),
                fg='#8e8e93',
                bg='#1c1c1e',
                wraplength=500,
            justify='left'
        )
            desc_label.pack(anchor='w', pady=(4, 0))
        
        # Content frame
        content_frame = tk.Frame(section_frame, bg='#1c1c1e')
        content_frame.pack(fill='both', expand=True, padx=24, pady=(0, 20))
        
        return content_frame
    
    def create_modern_text_field(self, parent, placeholder, height=6):
        """Create a modern text field with placeholder styling"""
        text_widget = tk.Text(
            parent,
            height=height,
            font=('SF Pro Text', 13),
            fg='#ffffff',
            bg='#2c2c2e',
            insertbackground='#ffffff',
            selectbackground='#0a84ff',
            selectforeground='#ffffff',
            relief='flat',
            bd=0,
            padx=16,
            pady=12,
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
    
    def create_context_section(self):
        """Create the AI context configuration section"""
        content_frame = self.create_section_frame(
            "Context & Knowledge",
            "Define what your AI assistant should know and remember"
        )
        
        self.context_text = self.create_modern_text_field(
            content_frame,
            "Example: You are a software developer's assistant with expertise in Python and JavaScript. You understand our codebase and help with debugging and code reviews.",
            height=8
        )
        self.context_text.pack(fill='x', pady=(0, 16))
        
        # Load existing value
        current_context = self.settings_manager.get_setting('ai_context', '')
        if current_context:
            self.context_text.delete('1.0', tk.END)
            self.context_text.insert('1.0', current_context)
            self.context_text.config(fg='#ffffff')
    
    def create_personality_section(self):
        """Create the AI personality configuration section"""
        content_frame = self.create_section_frame(
            "Personality & Behavior",
            "Configure how your AI assistant communicates and responds"
        )
        
        self.personality_text = self.create_modern_text_field(
            content_frame,
            "Example: Be casual and friendly. Use humor when appropriate. Speak like a close colleague. Be concise but thorough in explanations.",
            height=6
        )
        self.personality_text.pack(fill='x', pady=(0, 16))
        
        # Load existing value
        current_personality = self.settings_manager.get_setting('ai_personality', '')
        if current_personality:
            self.personality_text.delete('1.0', tk.END)
            self.personality_text.insert('1.0', current_personality)
            self.personality_text.config(fg='#ffffff')
    
    def create_advanced_section(self):
        """Create the advanced settings section"""
        content_frame = self.create_section_frame(
            "Advanced Settings",
            "Additional configuration options"
        )
        
        # Custom instructions
        instructions_label = tk.Label(
            content_frame,
            text="Custom Instructions",
            font=('SF Pro Display', 15, 'bold'),
            fg='#ffffff',
            bg='#1c1c1e'
        )
        instructions_label.pack(anchor='w', pady=(0, 8))
        
        self.custom_instructions_text = self.create_modern_text_field(
            content_frame,
            "Additional specific instructions that will be combined with context and personality...",
            height=5
        )
        self.custom_instructions_text.pack(fill='x', pady=(0, 20))
        
        # Load existing value
        current_instructions = self.settings_manager.get_setting('custom_instructions', '')
        if current_instructions:
            self.custom_instructions_text.delete('1.0', tk.END)
            self.custom_instructions_text.insert('1.0', current_instructions)
            self.custom_instructions_text.config(fg='#ffffff')
        
        # Voice activation toggle
        toggle_frame = tk.Frame(content_frame, bg='#1c1c1e')
        toggle_frame.pack(fill='x', pady=(0, 16))
        
        self.voice_activation_var = tk.BooleanVar()
        self.voice_activation_var.set(self.settings_manager.get_setting('voice_activation_enabled', True))
        
        activation_check = tk.Checkbutton(
            toggle_frame,
            text="Enable voice activation hotkey (⌘⇧V)",
            variable=self.voice_activation_var,
            font=('SF Pro Display', 13),
            fg='#ffffff',
            bg='#1c1c1e',
            selectcolor='#0a84ff',
            activebackground='#1c1c1e',
            activeforeground='#ffffff',
            relief='flat',
            bd=0
        )
        activation_check.pack(anchor='w')
    
    def create_action_buttons(self):
        """Create modern action buttons"""
        button_frame = tk.Frame(self.scrollable_frame, bg='#0f0f0f')
        button_frame.pack(fill='x', padx=40, pady=(20, 40))
        
        # Save button (primary)
        save_button = tk.Button(
            button_frame,
            text="Save Settings",
            command=self.save_settings,
            font=('SF Pro Display', 13, 'bold'),
            fg='#ffffff',
            bg='#0a84ff',
            activebackground='#0056b3',
            activeforeground='#ffffff',
            relief='flat',
            bd=0,
            padx=32,
            pady=12,
            cursor='pointinghand'
        )
        save_button.pack(side='right', padx=(12, 0))
        
        # Cancel button (secondary)
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel,
            font=('SF Pro Display', 13),
            fg='#8e8e93',
            bg='#2c2c2e',
            activebackground='#3a3a3c',
            activeforeground='#ffffff',
            relief='flat',
            bd=0,
            padx=32,
            pady=12,
            cursor='pointinghand'
        )
        cancel_button.pack(side='right')
        
        # Reset button (tertiary)
        reset_button = tk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults,
            font=('SF Pro Display', 13),
            fg='#ff453a',
            bg='#0f0f0f',
            activebackground='#1c1c1e',
            activeforeground='#ff453a',
            relief='flat',
            bd=0,
            padx=20,
            pady=12,
            cursor='pointinghand'
        )
        reset_button.pack(side='left')
    
    
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
            
            self.settings_manager.set_setting('ai_context', context_value)
            self.settings_manager.set_setting('ai_personality', personality_value)
            self.settings_manager.set_setting('custom_instructions', instructions_value)
            self.settings_manager.set_setting('voice_activation_enabled', self.voice_activation_var.get())
            
            # Save to file
            if self.settings_manager.save_settings():
                messagebox.showinfo("Settings Saved", "Your AI assistant settings have been saved successfully!")
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
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults? This cannot be undone."):
            # Reset text fields with proper placeholder handling
            self._reset_text_field(self.context_text, self.settings_manager.default_settings['ai_context'])
            self._reset_text_field(self.personality_text, self.settings_manager.default_settings['ai_personality'])
            self._reset_text_field(self.custom_instructions_text, self.settings_manager.default_settings['custom_instructions'])
            
            self.voice_activation_var.set(self.settings_manager.default_settings['voice_activation_enabled'])
    
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
