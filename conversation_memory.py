#!/usr/bin/env python3
"""
Conversation Memory - Manage conversation history for AI continuity

Contains the ConversationMemory class for storing and retrieving conversation
history to provide context for ongoing AI interactions.
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationMessage':
        """Create from dictionary"""
        return cls(**data)


class ConversationMemory:
    """Manages conversation history for AI continuity"""
    
    def __init__(self, memory_file: str = "conversation_memory.json", max_messages: int = 50, max_age_hours: int = 24):
        self.memory_file = memory_file
        self.max_messages = max_messages
        self.max_age_hours = max_age_hours
        self.messages: List[ConversationMessage] = []
        self.lock = threading.Lock()
        
        # Load existing memory
        self.load_memory()
    
    def add_message(self, role: str, content: str) -> None:
        """Add a new message to the conversation memory"""
        if not content.strip():
            return
            
        message = ConversationMessage(
            role=role,
            content=content.strip(),
            timestamp=time.time()
        )
        
        with self.lock:
            self.messages.append(message)
            self._cleanup_old_messages()
            self.save_memory()
    
    def get_recent_messages(self, max_count: Optional[int] = None) -> List[ConversationMessage]:
        """Get recent messages for context, optionally limited by count"""
        with self.lock:
            self._cleanup_old_messages()
            
            if max_count is None:
                return self.messages.copy()
            else:
                return self.messages[-max_count:] if self.messages else []
    
    def get_context_string(self, max_count: Optional[int] = None) -> str:
        """Get recent conversation history as a formatted string for AI context"""
        messages = self.get_recent_messages(max_count)
        
        if not messages:
            return ""
        
        context_lines = ["Previous conversation context:"]
        for msg in messages:
            # Format timestamp for readability
            dt = datetime.fromtimestamp(msg.timestamp)
            time_str = dt.strftime("%H:%M")
            
            role_emoji = "👤" if msg.role == "user" else "🤖"
            context_lines.append(f"{role_emoji} ({time_str}) {msg.content}")
        
        context_lines.append("---")
        return "\n".join(context_lines)
    
    def clear_memory(self) -> None:
        """Clear all conversation memory"""
        with self.lock:
            self.messages.clear()
            self.save_memory()
    
    def load_memory(self) -> None:
        """Load conversation memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages = [ConversationMessage.from_dict(msg_data) for msg_data in data.get('messages', [])]
                    # Clean up old messages on load
                    self._cleanup_old_messages()
                    print(f"Loaded {len(self.messages)} messages from conversation memory")
            else:
                self.messages = []
        except Exception as e:
            print(f"Error loading conversation memory: {e}")
            self.messages = []
    
    def save_memory(self) -> None:
        """Save conversation memory to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.memory_file) if os.path.dirname(self.memory_file) else '.', exist_ok=True)
            
            data = {
                'messages': [msg.to_dict() for msg in self.messages],
                'last_updated': time.time()
            }
            
            # Write to temporary file first, then rename for atomic operation
            temp_file = f"{self.memory_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            os.rename(temp_file, self.memory_file)
            
        except Exception as e:
            print(f"Error saving conversation memory: {e}")
    
    def _cleanup_old_messages(self) -> None:
        """Remove old messages based on time and count limits"""
        current_time = time.time()
        max_age_seconds = self.max_age_hours * 3600
        
        # Remove messages older than max_age_hours
        self.messages = [msg for msg in self.messages if (current_time - msg.timestamp) < max_age_seconds]
        
        # Limit number of messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_memory_stats(self) -> Dict[str, any]:
        """Get statistics about the conversation memory"""
        with self.lock:
            if not self.messages:
                return {
                    'total_messages': 0,
                    'user_messages': 0,
                    'assistant_messages': 0,
                    'oldest_message_age_hours': 0,
                    'newest_message_age_hours': 0
                }
            
            current_time = time.time()
            user_count = sum(1 for msg in self.messages if msg.role == 'user')
            assistant_count = sum(1 for msg in self.messages if msg.role == 'assistant')
            
            oldest_age = (current_time - self.messages[0].timestamp) / 3600
            newest_age = (current_time - self.messages[-1].timestamp) / 3600
            
            return {
                'total_messages': len(self.messages),
                'user_messages': user_count,
                'assistant_messages': assistant_count,
                'oldest_message_age_hours': round(oldest_age, 2),
                'newest_message_age_hours': round(newest_age, 2)
            }
    
    def export_conversation(self, output_file: str) -> bool:
        """Export conversation to a readable text file"""
        try:
            messages = self.get_recent_messages()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("AI Voice Assistant Conversation History\n")
                f.write("=" * 50 + "\n\n")
                
                for msg in messages:
                    dt = datetime.fromtimestamp(msg.timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    role_name = "User" if msg.role == "user" else "Assistant"
                    
                    f.write(f"[{time_str}] {role_name}:\n")
                    f.write(f"{msg.content}\n\n")
            
            return True
        except Exception as e:
            print(f"Error exporting conversation: {e}")
            return False
