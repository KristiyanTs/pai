#!/usr/bin/env python3
"""
Settings Window - Configuration UI for AI Voice Assistant

Contains the SettingsWindow class for managing AI assistant configuration.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
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
        # Create window
        try:
            if self.parent and hasattr(self.parent, 'winfo_exists') and self.parent.winfo_exists():
                self.window = tk.Toplevel(self.parent)
                # Make window modal if it has a valid parent
                self.window.transient(self.parent)
                self.window.grab_set()
            else:
                self.window = tk.Toplevel()
        except Exception:
            # Fallback to standalone window
            self.window = tk.Toplevel()
        
        self.window.title("🎤 AI Assistant Settings")
        self.window.geometry("800x600")
        self.window.minsize(700, 500)
        self.window.resizable(True, True)
        
        # Configure dark theme
        self.window.configure(bg='#1a1a1a')
        
        # Center the window
        self.center_window()
        
        self.create_widgets()
    
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
        """Create all UI widgets"""
        # Main frame with padding
        main_frame = tk.Frame(self.window, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="🤖 AI Assistant Configuration",
            font=('SF Pro Display', 18, 'bold'),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure notebook style for dark theme
        style.configure('TNotebook', background='#1a1a1a', borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background='#2d2d2d', 
                       foreground='#ffffff',
                       padding=[20, 10],
                       focuscolor='none')
        style.map('TNotebook.Tab',
                 background=[('selected', '#007AFF'), ('active', '#333333')])
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # AI Context Tab
        context_frame = tk.Frame(notebook, bg='#1a1a1a')
        notebook.add(context_frame, text='Context & Knowledge')
        self.create_context_tab(context_frame)
        
        # AI Personality Tab
        personality_frame = tk.Frame(notebook, bg='#1a1a1a')
        notebook.add(personality_frame, text='Personality & Behavior')
        self.create_personality_tab(personality_frame)
        
        # Advanced Tab
        advanced_frame = tk.Frame(notebook, bg='#1a1a1a')
        notebook.add(advanced_frame, text='Advanced Settings')
        self.create_advanced_tab(advanced_frame)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg='#1a1a1a')
        button_frame.pack(fill='x', pady=(20, 0))
        
        # Save button
        save_button = tk.Button(
            button_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            font=('SF Pro Display', 12, 'bold'),
            fg='#ffffff',
            bg='#007AFF',
            activebackground='#0056CC',
            activeforeground='#ffffff',
            bd=0,
            padx=30,
            pady=10
        )
        save_button.pack(side='right', padx=(10, 0))
        
        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel,
            font=('SF Pro Display', 12),
            fg='#ffffff',
            bg='#444444',
            activebackground='#555555',
            activeforeground='#ffffff',
            bd=0,
            padx=30,
            pady=10
        )
        cancel_button.pack(side='right')
        
        # Reset button
        reset_button = tk.Button(
            button_frame,
            text="🔄 Reset to Defaults",
            command=self.reset_to_defaults,
            font=('SF Pro Display', 12),
            fg='#ffffff',
            bg='#666666',
            activebackground='#777777',
            activeforeground='#ffffff',
            bd=0,
            padx=30,
            pady=10
        )
        reset_button.pack(side='left')
    
    def create_context_tab(self, parent):
        """Create the AI context configuration tab"""
        # Scroll frame for context
        canvas = tk.Canvas(parent, bg='#1a1a1a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1a1a1a')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Context label and description
        context_label = tk.Label(
            scrollable_frame,
            text="📚 AI Context & Knowledge",
            font=('SF Pro Display', 14, 'bold'),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        context_label.pack(anchor='w', pady=(10, 5))
        
        context_desc = tk.Label(
            scrollable_frame,
            text="Define what the AI should know and remember in each conversation.",
            font=('SF Pro Display', 10),
            fg='#cccccc',
            bg='#1a1a1a',
            wraplength=550,
            justify='left'
        )
        context_desc.pack(anchor='w', pady=(0, 10))
        
        # Context text area
        self.context_text = scrolledtext.ScrolledText(
            scrollable_frame,
            height=10,
            font=('SF Mono', 11),
            fg='#ffffff',
            bg='#2d2d2d',
            insertbackground='#ffffff',
            selectbackground='#007AFF',
            wrap='word'
        )
        self.context_text.pack(fill='both', expand=True, pady=(0, 20))
        self.context_text.insert('1.0', self.settings_manager.get_setting('ai_context', ''))
        
        # Examples section
        examples_label = tk.Label(
            scrollable_frame,
            text="💡 Context Examples:",
            font=('SF Pro Display', 12, 'bold'),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        examples_label.pack(anchor='w', pady=(0, 5))
        
        examples_text = """• "You are a software developer's assistant. You have expertise in Python, JavaScript, and system administration."
• "You work for a marketing company. You understand our products, pricing, and customer base."
• "You are my personal assistant. You know my schedule, preferences, and important contacts."
• "You have access to my company's documentation and internal processes."""
        
        examples_display = tk.Text(
            scrollable_frame,
            height=6,
            font=('SF Pro Display', 10),
            fg='#cccccc',
            bg='#262626',
            bd=0,
            wrap='word',
            state='disabled'
        )
        examples_display.pack(fill='x', pady=(0, 10))
        examples_display.config(state='normal')
        examples_display.insert('1.0', examples_text)
        examples_display.config(state='disabled')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_personality_tab(self, parent):
        """Create the AI personality configuration tab"""
        # Scroll frame for personality
        canvas = tk.Canvas(parent, bg='#1a1a1a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1a1a1a')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Personality label and description
        personality_label = tk.Label(
            scrollable_frame,
            text="🎭 AI Personality & Behavior",
            font=('SF Pro Display', 14, 'bold'),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        personality_label.pack(anchor='w', pady=(10, 5))
        
        personality_desc = tk.Label(
            scrollable_frame,
            text="Configure how the AI should behave and communicate with you.",
            font=('SF Pro Display', 10),
            fg='#cccccc',
            bg='#1a1a1a',
            wraplength=550,
            justify='left'
        )
        personality_desc.pack(anchor='w', pady=(0, 10))
        
        # Personality text area
        self.personality_text = scrolledtext.ScrolledText(
            scrollable_frame,
            height=10,
            font=('SF Mono', 11),
            fg='#ffffff',
            bg='#2d2d2d',
            insertbackground='#ffffff',
            selectbackground='#007AFF',
            wrap='word'
        )
        self.personality_text.pack(fill='both', expand=True, pady=(0, 20))
        self.personality_text.insert('1.0', self.settings_manager.get_setting('ai_personality', ''))
        
        # Personality examples
        examples_label = tk.Label(
            scrollable_frame,
            text="💡 Personality Examples:",
            font=('SF Pro Display', 12, 'bold'),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        examples_label.pack(anchor='w', pady=(0, 5))
        
        examples_text = """• "Be casual, friendly, and use humor when appropriate. Speak like a close colleague."
• "Be formal and professional. Always use proper grammar and avoid slang."
• "Be enthusiastic and energetic. Use emojis and exclamation points frequently."
• "Be concise and direct. Get straight to the point without unnecessary pleasantries."
• "Be patient and educational. Explain things step-by-step for learning purposes."""
        
        examples_display = tk.Text(
            scrollable_frame,
            height=6,
            font=('SF Pro Display', 10),
            fg='#cccccc',
            bg='#262626',
            bd=0,
            wrap='word',
            state='disabled'
        )
        examples_display.pack(fill='x', pady=(0, 10))
        examples_display.config(state='normal')
        examples_display.insert('1.0', examples_text)
        examples_display.config(state='disabled')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_advanced_tab(self, parent):
        """Create the advanced settings tab"""
        # Advanced settings frame
        advanced_frame = tk.Frame(parent, bg='#1a1a1a')
        advanced_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Custom instructions
        custom_label = tk.Label(
            advanced_frame,
            text="⚙️ Custom Instructions",
            font=('SF Pro Display', 14, 'bold'),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        custom_label.pack(anchor='w', pady=(0, 5))
        
        custom_desc = tk.Label(
            advanced_frame,
            text="Additional specific instructions that will be combined with context and personality.",
            font=('SF Pro Display', 10),
            fg='#cccccc',
            bg='#1a1a1a',
            wraplength=550,
            justify='left'
        )
        custom_desc.pack(anchor='w', pady=(0, 10))
        
        self.custom_instructions_text = scrolledtext.ScrolledText(
            advanced_frame,
            height=8,
            font=('SF Mono', 11),
            fg='#ffffff',
            bg='#2d2d2d',
            insertbackground='#ffffff',
            selectbackground='#007AFF',
            wrap='word'
        )
        self.custom_instructions_text.pack(fill='x', pady=(0, 20))
        self.custom_instructions_text.insert('1.0', self.settings_manager.get_setting('custom_instructions', ''))
        
        # Voice activation setting
        activation_frame = tk.Frame(advanced_frame, bg='#1a1a1a')
        activation_frame.pack(fill='x', pady=(0, 10))
        
        self.voice_activation_var = tk.BooleanVar()
        self.voice_activation_var.set(self.settings_manager.get_setting('voice_activation_enabled', True))
        
        activation_check = tk.Checkbutton(
            activation_frame,
            text="Enable voice activation hotkey (Cmd+Shift+V)",
            variable=self.voice_activation_var,
            font=('SF Pro Display', 11),
            fg='#ffffff',
            bg='#1a1a1a',
            selectcolor='#007AFF',
            activebackground='#1a1a1a',
            activeforeground='#ffffff'
        )
        activation_check.pack(anchor='w')
        
        # Preview combined instructions
        preview_label = tk.Label(
            advanced_frame,
            text="🔍 Preview Combined Instructions",
            font=('SF Pro Display', 12, 'bold'),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        preview_label.pack(anchor='w', pady=(20, 5))
        
        self.preview_text = tk.Text(
            advanced_frame,
            height=6,
            font=('SF Pro Display', 10),
            fg='#cccccc',
            bg='#262626',
            bd=0,
            wrap='word',
            state='disabled'
        )
        self.preview_text.pack(fill='x', pady=(0, 10))
        
        # Update preview button
        update_preview_button = tk.Button(
            advanced_frame,
            text="🔄 Update Preview",
            command=self.update_preview,
            font=('SF Pro Display', 10),
            fg='#ffffff',
            bg='#555555',
            activebackground='#666666',
            activeforeground='#ffffff',
            bd=0,
            padx=20,
            pady=5
        )
        update_preview_button.pack(anchor='w')
        
        # Initial preview update
        self.update_preview()
    
    def update_preview(self):
        """Update the preview of combined instructions"""
        # Get current values from text fields
        context = self.context_text.get('1.0', tk.END).strip()
        personality = self.personality_text.get('1.0', tk.END).strip()
        custom = self.custom_instructions_text.get('1.0', tk.END).strip()
        
        # Combine instructions
        parts = [part for part in [context, personality, custom] if part]
        combined = " ".join(parts)
        
        # Update preview
        self.preview_text.config(state='normal')
        self.preview_text.delete('1.0', tk.END)
        if combined:
            self.preview_text.insert('1.0', combined)
        else:
            self.preview_text.insert('1.0', "No instructions configured.")
        self.preview_text.config(state='disabled')
    
    def save_settings(self):
        """Save all settings"""
        try:
            # Update settings from UI
            self.settings_manager.set_setting('ai_context', self.context_text.get('1.0', tk.END).strip())
            self.settings_manager.set_setting('ai_personality', self.personality_text.get('1.0', tk.END).strip())
            self.settings_manager.set_setting('custom_instructions', self.custom_instructions_text.get('1.0', tk.END).strip())
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
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults? This cannot be undone."):
            # Reset text fields
            self.context_text.delete('1.0', tk.END)
            self.context_text.insert('1.0', self.settings_manager.default_settings['ai_context'])
            
            self.personality_text.delete('1.0', tk.END)
            self.personality_text.insert('1.0', self.settings_manager.default_settings['ai_personality'])
            
            self.custom_instructions_text.delete('1.0', tk.END)
            self.custom_instructions_text.insert('1.0', self.settings_manager.default_settings['custom_instructions'])
            
            self.voice_activation_var.set(self.settings_manager.default_settings['voice_activation_enabled'])
            
            # Update preview
            self.update_preview()
    
    def show(self):
        """Show the settings window"""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
