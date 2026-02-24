Put your local console fallback images in this folder.

Supported formats:
- `.png`
- `.jpg`
- `.jpeg`
- `.webp`

The backend resolves files by slug (first match wins by extension order):
- `nes`
- `snes`
- `nintendo-64`
- `gamecube`
- `wii`
- `wii-u`
- `nintendo-switch`
- `nintendo-switch-2`
- `game-boy`
- `game-boy-color`
- `game-boy-advance`
- `nintendo-ds`
- `nintendo-3ds`
- `playstation`
- `playstation-2`
- `playstation-3`
- `playstation-4`
- `playstation-5`
- `psp`
- `ps-vita`
- `xbox`
- `xbox-360`
- `xbox-one`
- `xbox-series-xs`
- `sega-master-system`
- `sega-genesis`
- `sega-saturn`
- `sega-dreamcast`
- `sega-game-gear`

Examples:
- `playstation-5.png`
- `xbox-one.webp`
- `nintendo-switch.jpg`

Notes:
- Local images are preferred over remote URLs.
- If no local image exists for a slug, the previous remote fallback is used.
