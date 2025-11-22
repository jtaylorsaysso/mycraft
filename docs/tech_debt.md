# Tech Debt

## World Generation

- [ ] World generation is currently a placeholder. It should be replaced with a proper world generation system.
- [ ] Texture are stretched across chunks. Fine for now, textures need replaced anyhow
- [ ] Texture shopping/creation

## Physics System

- [ ] Add horizontal acceleration and air control for better movement feel
- [ ] Implement slope handling and surface normal projection
- [ ] Add wall sliding with forward raycasts
- [ ] Consider different ground checks for liquids, ladders, etc.

## Performance

- [ ] Profile raycast ground detection performance with many entities
- [ ] Consider spatial partitioning for large numbers of physics objects

## Networking

- [ ] Add player interpolation for smoother remote movement
- [ ] Implement player names above heads
- [ ] Add chat system for player communication
- [ ] Consider UDP for position updates (TCP for important events)
- [ ] Add connection timeout and retry logic
- [ ] Implement player customization (colors, names)
