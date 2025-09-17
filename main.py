#!/usr/bin/env python3
"""
Main entry point for AI Voice Assistant

A standalone Python script that provides a global hotkey-activated voice assistant.
Press Cmd+Shift+V to start a conversation with the AI assistant.

Requirements:
- OpenAI API key in .env file
- Python packages: openai, pynput, sounddevice, numpy, python-dotenv, websocket-client

Usage:
1. Copy env_example.txt to .env and add your OpenAI API key
2. Install dependencies: pip install -r requirements.txt
3. Run: python main.py
4. Press Cmd+Shift+V to activate voice assistant
5. Press Ctrl+C to exit
"""

import sys
from voice_assistant import AIVoiceAssistant


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
