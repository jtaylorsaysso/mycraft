from ursina import Ursina, camera, Text, Entity, time, window, InputField, color
from engine.world import World
from engine.player import Player
from network.client import get_client
from pathlib import Path
from typing import Optional

# Global references for update loop
_world = None
_player = None
_command_processor = None
_console_output = None
_console_input = None


def _game_update():
    """Called each frame by Ursina to update game state."""
    global _world, _player
    
    if _world and _player:
        # Update chunk loading/unloading based on player position
        _world.update(_player.position)
        
        # Update chunk visibility based on camera frustum
        _world.set_chunk_visibility(camera, _player.position)


def _setup_console(player, input_handler, spawn_pos):
    """Set up the playtest command console."""
    global _console_output, _console_input, _command_processor
    from engine.client_commands import ClientCommandProcessor
    from ursina import mouse
    
    _command_processor = ClientCommandProcessor(player, input_handler, spawn_pos)
    
    # Console output text (shows command results)
    _console_output = Text(
        text='',
        position=(-0.85, -0.3),
        scale=0.8,
        background=True,
        origin=(-0.5, 0),
        color=color.white
    )
    _console_output.visible = False
    
    # Track console state
    console_state = {'active': False, 'output_timer': 0}
    
    def toggle_console():
        console_state['active'] = not console_state['active']
        if console_state['active']:
            _console_output.visible = True
            _console_output.text = "Enter command (type /help for commands):"
            mouse.locked = False
        else:
            _console_output.visible = False
            mouse.locked = True
    
    def handle_console_input(key):
        if key == 't' and not console_state['active']:
            toggle_console()
        elif key == 'escape' and console_state['active']:
            toggle_console()
        elif key == 'enter' and console_state['active']:
            # Get command from a simple approach - show help
            pass  # Will use text input approach
    
    # Use a simpler approach: cycle through preset commands with number keys
    preset_commands = [
        '/help',
        '/info', 
        '/god',
        '/spawn',
        '/speed 2',
        '/speed 1',
    ]
    
    def handle_preset_commands(key):
        if console_state['active']:
            return
        
        # Number keys 1-6 for preset commands
        if key in ['1', '2', '3', '4', '5', '6']:
            idx = int(key) - 1
            if idx < len(preset_commands):
                cmd = preset_commands[idx]
                result = _command_processor.process_command(cmd)
                if result:
                    _console_output.text = '\n'.join(result)
                    _console_output.visible = True
                    console_state['output_timer'] = 3.0  # Show for 3 seconds
    
    def update_console():
        if console_state['output_timer'] > 0:
            console_state['output_timer'] -= time.dt
            if console_state['output_timer'] <= 0:
                _console_output.visible = False
    
    # Console entity for updates
    console_entity = Entity()
    console_entity.input = handle_preset_commands
    console_entity.update = update_console
    
    return _command_processor


def run(
    networking: bool = False,
    sensitivity: float = 40.0,
    god_mode: bool = False,
    debug: bool = False,
    spawn_point: tuple = None,
    config_path: str = None,
    record_session: str = None,
    replay_session: str = None
):
    global _world, _player
    
    # Initialize hot-config if path provided
    hot_config = None
    if config_path:
        from util.hot_config import init_config
        hot_config = init_config(Path(config_path))
        # Override settings from config
        if hot_config:
            sensitivity = hot_config.get("mouse_sensitivity", sensitivity)
            god_mode = hot_config.get("god_mode", god_mode)
            debug = hot_config.get("debug_overlay", debug)
    
    # Initialize session recorder if recording
    recorder = None
    if record_session:
        from util.session_recorder import SessionRecorder
        recorder = SessionRecorder()
    
    # Initialize session player if replaying
    session_player = None
    if replay_session:
        from util.session_recorder import SessionPlayer
        session_player = SessionPlayer()
        if not session_player.load(Path(replay_session)):
            print(f"Failed to load replay: {replay_session}")
            session_player = None
    
    app = Ursina()
    
    # Determine spawn position first (needed for chunk preloading)
    if replay_session and session_player:
        # Use spawn from recording
        spawn_pos = session_player.get_spawn_pos() or (10, 2, 10)
    elif spawn_point:
        spawn_pos = spawn_point
    elif networking:
        client = get_client()
        if client and client.is_connected():
            spawn_pos = tuple(client.spawn_pos) if hasattr(client, 'spawn_pos') else (10, 2, 10)
        else:
            spawn_pos = (10, 2, 10)
    else:
        spawn_pos = (10, 2, 10)
    
    # Create the world (now with dynamic chunk loading)
    _world = World()
    
    # Pre-load chunks around spawn to prevent falling through empty world
    spawn_chunk = _world.get_player_chunk_coords(spawn_pos)
    for cx in range(spawn_chunk[0] - 2, spawn_chunk[0] + 3):
        for cz in range(spawn_chunk[1] - 2, spawn_chunk[1] + 3):
            if (cx, cz) not in _world.chunks:
                _world.create_chunk(cx, cz)
    
    # Ensure safe spawn height (prevent spawning underground)
    # We query the world generation directly for the ground truth height
    if hasattr(spawn_pos, 'x'):
        sx, sz = spawn_pos.x, spawn_pos.z
        current_y = spawn_pos.y
    else:
        sx, sz = spawn_pos[0], spawn_pos[2]
        current_y = spawn_pos[1]
        
    terrain_height = _world.get_height(int(sx), int(sz))
    safe_y = max(current_y, terrain_height + 2.5)  # Add 2.5m buffer
    
    if safe_y != current_y:
        print(f"⚠️  Adjusting spawn height: {current_y:.1f} -> {safe_y:.1f} (Terrain is {terrain_height})")
        spawn_pos = (sx, safe_y, sz)

    
    _player = Player(
        start_pos=spawn_pos,
        networking=networking,
        sensitivity=sensitivity,
        god_mode=god_mode,
        config=hot_config
    )
    
    # Set up session recording/replay on input handler
    if hasattr(_player, 'input_handler'):
        if recorder:
            _player.input_handler.set_recorder(recorder)
            recorder.start(spawn_pos=spawn_pos)
            print(f"🎬 Recording session: {record_session}")
        if session_player:
            _player.input_handler.set_session_player(session_player)
            session_player.start()
            print(f"▶️ Replaying session: {replay_session}")
    
    # Set up playtest console
    if hasattr(_player, 'input_handler'):
        cmd_processor = _setup_console(_player, _player.input_handler, spawn_pos)
        if recorder:
            cmd_processor.set_recorder(recorder)
        if session_player:
            cmd_processor.set_session_player(session_player)

    # Register the game update loop
    update_entity = Entity()
    update_entity.update = _game_update

    if debug:
        debug_text = Text(position=(-0.85, 0.45), text='DEBUG INFO', scale=1, background=True)
        
        def update_debug():
            if _player:
                p = _player.position
                c = _world.get_player_chunk_coords(p) if _world else (0,0)
                fps = int(1/time.dt) if time.dt > 0 else 0
                god_status = 'ON' if (hasattr(_player, 'input_handler') and _player.input_handler.god_mode) else 'OFF'
                debug_text.text = (
                    f"FPS: {fps}\n"
                    f"Pos: ({p.x:.1f}, {p.y:.1f}, {p.z:.1f})\n"
                    f"Chunk: {c}\n"
                    f"God Mode: {god_status}\n"
                    f"[1-6] Quick Commands"
                )
        
        # Create an entity to handle debug updates
        d_ent = Entity()
        d_ent.update = update_debug
    
    # Handle cleanup on exit
    def on_exit():
        if recorder and recorder.is_recording():
            recorder.stop()
            path = Path("recordings") / f"{record_session}.json"
            recorder.save(path)
            print(f"💾 Session saved: {path}")
    
    import atexit
    atexit.register(on_exit)

    app.run()