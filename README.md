# 🎤 AI Voice Assistant

A system-wide AI voice assistant powered by OpenAI's Realtime API. Press a global hotkey to start natural voice conversations with AI from anywhere on your Mac.

## ✨ Features

- **Global Hotkey Activation**: Press `Cmd + Shift + V` from anywhere to start a conversation
- **Real-time Voice Interaction**: Natural speech-to-speech conversations using OpenAI's Realtime API
- **Conversation Memory**: AI remembers previous conversations for context continuity
- **Speech-to-Text Transcription**: All spoken audio is transcribed and printed in the terminal using OpenAI Whisper
- **Minimal UI Overlay**: Transparent, non-intrusive status indicator
- **System-wide Access**: Works from any application or desktop
- **Dark Mode Interface**: Modern, sleek design that matches system aesthetics
- **Auto-termination**: Conversations end automatically when AI finishes speaking

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed on your system
2. **OpenAI API Key** with access to the Realtime API
3. **Microphone and speakers** (built-in or external)

### Installation

1. **Clone or download this repository**
   ```bash
   cd /path/to/pai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Key**
   ```bash
   # Copy the example environment file
   cp env_example.txt .env
   
   # Edit .env and add your OpenAI API key
   nano .env
   ```
   
   Add your API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

4. **Run the assistant**
   ```bash
   python voice_assistant.py
   ```

### Getting Your OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in to your account
3. Create a new API key
4. Copy the key and paste it in your `.env` file

> **Note**: The Realtime API requires a paid OpenAI account and may have usage costs.

## 🎯 Usage

### Starting the Assistant

1. Run the script: `python voice_assistant.py`
2. You'll see: "Global hotkey listener started"
3. The assistant is now ready and listening for the hotkey

### Having a Conversation

1. **Press `Cmd + Shift + V`** from anywhere on your Mac
2. **See the overlay**: A small "🎤 Listening..." indicator appears
3. **Start speaking**: Talk naturally to the AI assistant
4. **See transcription**: Your speech is transcribed and printed in the terminal with "🎤 Transcription: ..."
5. **Wait for response**: The overlay will show "🤔 Thinking..." then "🗣️ Speaking..."
6. **AI response**: The AI's response is also transcribed and shown as "🤖 AI: ..."
7. **Conversation ends**: The overlay disappears when the AI finishes speaking

### Conversation Memory

The AI assistant now remembers your previous conversations to provide better context and continuity:

- **Automatic Memory**: Previous conversations are automatically saved and included as context
- **Smart Context**: The AI receives the most recent conversation history to understand references
- **Configurable**: Memory settings can be adjusted through the settings window (`Cmd + Shift + Z`)
- **Privacy-Safe**: Conversation history is stored locally on your machine
- **Auto-Cleanup**: Old conversations are automatically removed based on age and count limits

**Memory Settings:**
- **Enable/Disable**: Toggle conversation memory on or off
- **Max Messages**: Set how many messages to remember (default: 50)
- **Max Age**: Set how long to keep conversations in hours (default: 24)

### Accessing Settings

Press `Cmd + Shift + Z` from anywhere to open the settings window where you can:
- Configure AI personality and context
- Adjust conversation memory settings
- Change voice speaker
- Toggle voice activation

### Exiting the Assistant

- Press `Cmd + Q` or `Esc` while the terminal is focused
- Or press `Ctrl + C` in the terminal

## 🛠️ Technical Details

### Architecture

The voice assistant consists of several key components:

- **VoiceAssistantOverlay**: Transparent tkinter UI for status display
- **AudioManager**: Handles microphone input and speaker output using sounddevice, includes speech-to-text transcription
- **RealtimeAIClient**: WebSocket client for OpenAI's Realtime API with conversation memory integration
- **ConversationMemory**: Manages persistent conversation history for context continuity
- **SettingsManager**: Handles configuration and settings persistence
- **AIVoiceAssistant**: Main orchestrator that coordinates all components

### Speech-to-Text Transcription

The assistant now includes automatic transcription of all spoken audio using OpenAI's Whisper models:

- **Model**: Uses `gpt-4o-transcribe` for high-quality transcription
- **Real-time Processing**: Audio is transcribed after you stop speaking
- **Terminal Output**: Transcriptions are printed with clear labels
- **Automatic Cleanup**: Temporary audio files are automatically deleted

### Audio Configuration

- **Sample Rate**: 24kHz (required by OpenAI Realtime API)
- **Format**: PCM 16-bit mono
- **Chunk Size**: 1024 samples for low latency

### Threading Model

- **Main Thread**: Runs tkinter UI loop and handles user input
- **Hotkey Listener**: Non-blocking global keyboard listener
- **WebSocket Thread**: Manages real-time communication with OpenAI
- **Audio Threads**: Separate threads for recording and playback

## 🔧 Customization

### Changing the Hotkey

Edit the `hotkey_combination` in the `setup_hotkey_listener` method:

```python
# Current: Cmd+Shift+V
hotkey_combination = {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode.from_char('v')}

# Example: Ctrl+Shift+A
hotkey_combination = {keyboard.Key.ctrl, keyboard.Key.shift, keyboard.KeyCode.from_char('a')}
```

### Modifying AI Instructions

Update the `instructions` in the session configuration:

```python
session_config = {
    "type": "session.update",
    "session": {
        "instructions": "Your custom AI personality and instructions here...",
        # ... other settings
    }
}
```

### Changing the Voice

Modify the `voice` parameter in the session config:

```python
"voice": "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
```

## 🐛 Troubleshooting

### Common Issues

**"OPENAI_API_KEY not found"**
- Ensure your `.env` file exists and contains the API key
- Check that the key starts with `sk-` for regular keys or `org-` for organization keys

**"Failed to connect to OpenAI API"**
- Verify your API key is valid and has Realtime API access
- Check your internet connection
- Ensure you have sufficient OpenAI credits

**"No audio input/output"**
- Check microphone and speaker permissions
- Try running: `python -c "import sounddevice; print(sounddevice.query_devices())"`
- Ensure your default audio devices are working

**Hotkey not working**
- Check that accessibility permissions are granted to your terminal
- Try running with `sudo` (not recommended for security)
- Verify the hotkey combination isn't already used by another app

### Debug Mode

Add debug prints by modifying the logging level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📋 Dependencies

- `openai>=1.52.0` - OpenAI API client
- `pynput>=1.7.6` - Global hotkey detection
- `sounddevice>=0.4.6` - Audio input/output
- `numpy>=1.24.0` - Audio data processing
- `python-dotenv>=1.0.0` - Environment variable loading
- `websocket-client>=1.6.0` - WebSocket communication

## 🔒 Privacy & Security

- **Audio Processing**: All audio is sent to OpenAI's servers for processing
- **API Key**: Stored locally in `.env` file - never share this file
- **No Local Storage**: Conversations are not stored locally
- **Real-time Only**: No conversation history is maintained

## 📄 License

This project is for educational and personal use. Please review OpenAI's usage policies for the Realtime API.

## 🆘 Support

For issues related to:
- **This code**: Check the troubleshooting section above
- **OpenAI API**: Visit [OpenAI Help Center](https://help.openai.com/)
- **Python dependencies**: Check individual package documentation

---

**Made with ❤️ using OpenAI's Realtime API**
