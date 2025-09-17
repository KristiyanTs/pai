#!/usr/bin/env python3
"""
Permissions Helper - Handle accessibility permissions on macOS

Contains utilities for checking and requesting accessibility permissions
required for global hotkey functionality.
"""

import tkinter as tk
import subprocess


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
