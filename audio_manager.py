#!/usr/bin/env python3
"""
Audio Manager - Handle audio input/output operations

Contains the AudioManager class for managing microphone input and speaker output
for the voice assistant application.
"""

import threading
import time
import numpy as np
import sounddevice as sd
from queue import Queue, Empty


class AudioManager:
    """Handles audio input/output operations"""
    
    def __init__(self):
        self.sample_rate = 24000  # OpenAI Realtime API sample rate
        self.channels = 1
        self.dtype = np.int16
        self.chunk_size = 1024
        
        self.input_queue = Queue()
        self.output_queue = Queue()
        self.recording = False
        self.playing = False
        
        self.input_stream = None
        self.output_stream = None
        
        # Audio buffer for proper sequencing
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_lock = threading.Lock()
        self.response_finished = False
    
    def start_recording(self):
        """Start recording audio from microphone"""
        if self.recording:
            return
            
        self.recording = True
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio input status: {status}")
            if self.recording:
                # Convert float32 to int16 and put in queue
                audio_data = (indata[:, 0] * 32767).astype(np.int16)
                self.input_queue.put(audio_data.tobytes())
        
        try:
            self.input_stream = sd.InputStream(
                callback=audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype='float32',
                blocksize=self.chunk_size
            )
            self.input_stream.start()
            print("Started audio recording")
        except Exception as e:
            print(f"Error starting audio recording: {e}")
            self.recording = False
    
    def stop_recording(self):
        """Stop recording audio"""
        self.recording = False
        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()
            self.input_stream = None
        print("Stopped audio recording")
    
    def start_playback(self):
        """Start audio playback thread"""
        if self.playing:
            return
        
        # Clear any leftover audio from previous sessions
        with self.buffer_lock:
            self.audio_buffer = np.array([], dtype=np.float32)
            self.response_finished = False
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except Empty:
                break
            
        self.playing = True
        
        def playback_thread():
            def audio_callback(outdata, frames, time, status):
                if status:
                    print(f"Audio output status: {status}")
                
                with self.buffer_lock:
                    # Add new audio data to buffer
                    while not self.output_queue.empty():
                        try:
                            audio_bytes = self.output_queue.get_nowait()
                            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                            audio_float = audio_data.astype(np.float32) / 32767.0
                            self.audio_buffer = np.concatenate([self.audio_buffer, audio_float])
                        except Empty:
                            break
                    
                    # Fill output with available buffer data
                    if len(self.audio_buffer) >= frames:
                        outdata[:, 0] = self.audio_buffer[:frames]
                        self.audio_buffer = self.audio_buffer[frames:]
                    elif len(self.audio_buffer) > 0:
                        outdata[:len(self.audio_buffer), 0] = self.audio_buffer
                        outdata[len(self.audio_buffer):, 0] = 0
                        self.audio_buffer = np.array([], dtype=np.float32)
                    else:
                        outdata[:, 0] = 0
        
            try:
                self.output_stream = sd.OutputStream(
                    callback=audio_callback,
                    channels=self.channels,
                    samplerate=self.sample_rate,
                    dtype='float32',
                    blocksize=self.chunk_size
                )
                self.output_stream.start()
                
                # Keep stream alive while playing
                while self.playing:
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"Error in audio playback: {e}")
            finally:
                if self.output_stream:
                    self.output_stream.stop()
                    self.output_stream.close()
                    self.output_stream = None
        
        threading.Thread(target=playback_thread, daemon=True).start()
        print("Started audio playback")
    
    def stop_playback(self):
        """Stop audio playback"""
        self.playing = False
        # Clear audio buffer to prevent leftover audio
        with self.buffer_lock:
            self.audio_buffer = np.array([], dtype=np.float32)
        # Clear output queue
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except Empty:
                break
        print("Stopped audio playback")
    
    def get_audio_data(self):
        """Get recorded audio data from queue"""
        try:
            return self.input_queue.get_nowait()
        except Empty:
            return None
    
    def play_audio_data(self, audio_bytes: bytes):
        """Add audio data to playback queue with proper sequencing"""
        # Ensure audio data is properly queued in order
        self.output_queue.put(audio_bytes)
