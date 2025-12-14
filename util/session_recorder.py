"""
Session Recorder for MyCraft Playtesting

Captures player input events with timestamps for replay and debugging.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class InputEvent:
    """A single input event with timestamp."""
    t: float  # Time since recording started (seconds)
    type: str  # "key_down", "key_up", "mouse_move", "mouse_click"
    data: Dict[str, Any] = field(default_factory=dict)


class SessionRecorder:
    """Records input events to a JSON file for later replay."""
    
    def __init__(self):
        self.events: List[InputEvent] = []
        self._recording = False
        self._start_time: float = 0.0
        self._metadata: Dict[str, Any] = {}
    
    def start(self, spawn_pos: tuple = None, metadata: Dict[str, Any] = None) -> None:
        """Start recording a new session."""
        self.events = []
        self._recording = True
        self._start_time = time.perf_counter()
        self._metadata = {
            "recorded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "spawn_pos": list(spawn_pos) if spawn_pos else [0, 0, 0],
            **(metadata or {})
        }
    
    def stop(self) -> None:
        """Stop recording."""
        self._recording = False
        if self.events:
            self._metadata["duration"] = self.events[-1].t
            self._metadata["event_count"] = len(self.events)
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording
    
    def record_key(self, key: str, pressed: bool) -> None:
        """Record a key press or release event."""
        if not self._recording:
            return
        
        event_type = "key_down" if pressed else "key_up"
        self._add_event(event_type, {"key": key})
    
    def record_mouse_move(self, dx: float, dy: float) -> None:
        """Record mouse movement delta."""
        if not self._recording:
            return
        
        # Skip zero movements
        if dx == 0 and dy == 0:
            return
            
        self._add_event("mouse_move", {"dx": dx, "dy": dy})
    
    def record_mouse_click(self, button: str, pressed: bool) -> None:
        """Record mouse button click."""
        if not self._recording:
            return
        
        event_type = "mouse_down" if pressed else "mouse_up"
        self._add_event(event_type, {"button": button})
    
    def record_state_snapshot(self, pos: tuple, rot_y: float) -> None:
        """Record current player state (for verification during replay)."""
        if not self._recording:
            return
        
        self._add_event("state_snapshot", {
            "pos": list(pos),
            "rot_y": rot_y
        })
    
    def _add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Add an event with current timestamp."""
        t = time.perf_counter() - self._start_time
        self.events.append(InputEvent(t=round(t, 4), type=event_type, data=data))
    
    def save(self, path: Path) -> None:
        """Save the recorded session to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        session_data = {
            "version": "1.0",
            "metadata": self._metadata,
            "events": [asdict(e) for e in self.events]
        }
        
        with path.open("w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get recording statistics."""
        if not self.events:
            return {"event_count": 0, "duration": 0}
        
        return {
            "event_count": len(self.events),
            "duration": self.events[-1].t if self.events else 0,
            "recording": self._recording
        }


class SessionPlayer:
    """Replays a recorded session by feeding events at correct timestamps."""
    
    def __init__(self):
        self.events: List[InputEvent] = []
        self.metadata: Dict[str, Any] = {}
        self._playing = False
        self._start_time: float = 0.0
        self._event_index: int = 0
        self._speed: float = 1.0
    
    def load(self, path: Path) -> bool:
        """Load a session file. Returns True if successful."""
        path = Path(path)
        if not path.exists():
            return False
        
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.metadata = data.get("metadata", {})
            self.events = [
                InputEvent(t=e["t"], type=e["type"], data=e.get("data", {}))
                for e in data.get("events", [])
            ]
            return True
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to load session: {e}")
            return False
    
    def start(self, speed: float = 1.0) -> None:
        """Start playback."""
        self._playing = True
        self._start_time = time.perf_counter()
        self._event_index = 0
        self._speed = max(0.1, min(10.0, speed))  # Clamp to reasonable range
    
    def stop(self) -> None:
        """Stop playback."""
        self._playing = False
    
    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._playing
    
    def is_finished(self) -> bool:
        """Check if playback has completed."""
        return self._event_index >= len(self.events)
    
    def get_spawn_pos(self) -> Optional[tuple]:
        """Get the spawn position from metadata."""
        pos = self.metadata.get("spawn_pos")
        return tuple(pos) if pos else None
    
    def update(self) -> List[InputEvent]:
        """Get any events that should fire now. Call each frame."""
        if not self._playing or self.is_finished():
            return []
        
        current_time = (time.perf_counter() - self._start_time) * self._speed
        ready_events = []
        
        while self._event_index < len(self.events):
            event = self.events[self._event_index]
            if event.t <= current_time:
                ready_events.append(event)
                self._event_index += 1
            else:
                break
        
        # Auto-stop at end
        if self.is_finished():
            self._playing = False
        
        return ready_events
    
    def get_progress(self) -> Dict[str, Any]:
        """Get playback progress info."""
        total_duration = self.events[-1].t if self.events else 0
        current_time = (time.perf_counter() - self._start_time) * self._speed if self._playing else 0
        
        return {
            "playing": self._playing,
            "progress": self._event_index / len(self.events) if self.events else 0,
            "current_time": min(current_time, total_duration),
            "total_duration": total_duration,
            "events_played": self._event_index,
            "total_events": len(self.events)
        }
