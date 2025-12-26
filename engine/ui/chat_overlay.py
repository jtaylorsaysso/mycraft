"""
Chat Overlay UI Component

Provides an in-game chat interface with:
- Message history display (fades after 5 seconds)
- Text input box (activated with T key)
- Support for slash commands (host only)
"""

from direct.gui.DirectGui import DirectEntry, DirectFrame, OnscreenText
from direct.gui.DirectGuiGlobals import FLAT
from panda3d.core import TextNode, TransparencyAttrib
from engine.networking.client import get_client
import time


class ChatOverlay:
    """In-game chat overlay with message history and input."""
    
    def __init__(self, base, on_chat_opened=None, on_chat_closed=None):
        """Initialize chat overlay.
        
        Args:
            base: Panda3D ShowBase instance
            on_chat_opened: Callback when chat input is opened
            on_chat_closed: Callback when chat input is closed
        """
        self.base = base
        self.on_chat_opened = on_chat_opened
        self.on_chat_closed = on_chat_closed
        
        self.visible = False
        self.input_active = False
        
        # Chat message display settings
        self.max_visible_messages = 10
        self.message_fade_time = 5.0  # Seconds before messages fade
        self.message_lifetime = 10.0  # Seconds before messages are removed
        
        # Message history (list of dicts with 'text', 'timestamp', 'node')
        self.displayed_messages = []
        
        # Create chat input box (hidden by default)
        self.input_frame = DirectFrame(
            frameColor=(0, 0, 0, 0.7),
            frameSize=(-0.95, 0.95, -0.05, 0.05),
            pos=(0, 0, -0.85),
            parent=base.aspect2d
        )
        self.input_frame.hide()
        
        self.input_box = DirectEntry(
            text="",
            scale=0.05,
            width=35,
            numLines=1,
            focus=0,
            frameColor=(0.2, 0.2, 0.2, 0.8),
            text_fg=(1, 1, 1, 1),
            pos=(-0.9, 0, -0.015),
            parent=self.input_frame,
            command=self._on_input_submit,
            focusInCommand=self._on_input_focus,
            focusOutCommand=self._on_input_unfocus
        )
        
        # Chat prompt text
        self.prompt_text = OnscreenText(
            text="Chat (T):",
            pos=(-0.92, -0.015),
            scale=0.04,
            fg=(1, 1, 1, 0.7),
            align=TextNode.ALeft,
            parent=self.input_frame,
            mayChange=False
        )
        
        # Message display area (above input)
        self.message_container = base.aspect2d.attachNewNode("chat_messages")
        self.message_container.setPos(0, 0, -0.75)
        
    def open_input(self):
        """Open the chat input box."""
        if self.input_active:
            return
            
        self.input_active = True
        self.input_frame.show()
        self.input_box['focus'] = 1
        self.input_box.enterText('')
        
        if self.on_chat_opened:
            self.on_chat_opened()
    
    def close_input(self, send_message=False):
        """Close the chat input box.
        
        Args:
            send_message: If True, send the message before closing
        """
        if not self.input_active:
            return
        
        if send_message:
            self._send_current_message()
        
        self.input_active = False
        self.input_frame.hide()
        self.input_box['focus'] = 0
        self.input_box.enterText('')
        
        if self.on_chat_closed:
            self.on_chat_closed()
    
    def _on_input_submit(self, text):
        """Called when Enter is pressed in the input box."""
        self.close_input(send_message=True)
    
    def _on_input_focus(self):
        """Called when input box gains focus."""
        pass
    
    def _on_input_unfocus(self):
        """Called when input box loses focus."""
        pass
    
    def _send_current_message(self):
        """Send the current message in the input box."""
        text = self.input_box.get().strip()
        if not text:
            return
        
        client = get_client()
        if client and client.is_connected():
            client.send_chat_message(text)
    
    def add_message(self, player_name: str, message: str, timestamp: float = None):
        """Add a chat message to the display.
        
        Args:
            player_name: Name of the player who sent the message
            message: The message text
            timestamp: Message timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Format message text
        formatted_text = f"{player_name}: {message}"
        
        # Create text node
        y_offset = len(self.displayed_messages) * -0.06
        text_node = OnscreenText(
            text=formatted_text,
            pos=(-0.95, y_offset),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            parent=self.message_container,
            mayChange=True
        )
        text_node.setTransparency(TransparencyAttrib.MAlpha)
        
        # Store message info
        self.displayed_messages.append({
            'text': formatted_text,
            'timestamp': timestamp,
            'node': text_node
        })
        
        # Trim old messages
        while len(self.displayed_messages) > self.max_visible_messages:
            old_msg = self.displayed_messages.pop(0)
            old_msg['node'].removeNode()
        
        # Reposition all messages
        self._reposition_messages()
    
    def _reposition_messages(self):
        """Reposition all visible messages."""
        for i, msg in enumerate(self.displayed_messages):
            y_offset = (len(self.displayed_messages) - i - 1) * -0.06
            msg['node'].setPos(-0.95, y_offset)
    
    def update(self, dt: float):
        """Update chat overlay (fade messages, fetch new messages).
        
        Args:
            dt: Delta time since last update
        """
        current_time = time.time()
        
        # Fetch new messages from client
        client = get_client()
        if client and client.is_connected():
            recent_messages = client.get_recent_chat(count=self.max_visible_messages)
            
            # Check for new messages
            for msg in recent_messages:
                # Simple check: if timestamp is newer than our last message
                if not self.displayed_messages or msg['timestamp'] > self.displayed_messages[-1]['timestamp']:
                    self.add_message(msg['name'], msg['message'], msg['timestamp'])
        
        # Fade old messages
        messages_to_remove = []
        for msg in self.displayed_messages:
            age = current_time - msg['timestamp']
            
            # Remove very old messages
            if age > self.message_lifetime:
                messages_to_remove.append(msg)
                continue
            
            # Fade messages after fade_time
            if age > self.message_fade_time:
                fade_progress = (age - self.message_fade_time) / (self.message_lifetime - self.message_fade_time)
                alpha = max(0.0, 1.0 - fade_progress)
                msg['node'].setAlphaScale(alpha)
            else:
                msg['node'].setAlphaScale(1.0)
        
        # Remove old messages
        for msg in messages_to_remove:
            msg['node'].removeNode()
            self.displayed_messages.remove(msg)
        
        if messages_to_remove:
            self._reposition_messages()
    
    def cleanup(self):
        """Clean up chat overlay."""
        for msg in self.displayed_messages:
            msg['node'].removeNode()
        self.displayed_messages.clear()
        
        self.input_frame.destroy()
        self.message_container.removeNode()
