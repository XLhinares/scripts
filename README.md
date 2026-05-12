# .scripts

This directory contains a few utility scripts I've coded over time.

## Structure:

- `archiving`:
  - `rsync_script`: (WIP) Synchronizes my home folders to a backup location.
- `apps/`:
  - `vconvert`: Converts videos between different formats with ffmpeg.
  - `weylus`: Sets up and start Weylus.
- `caelestia/`:
  - `livepaper`: Toggles between static and mp4 wallpaper.
  - `scheme_tauon`: (WIP) Generates a color scheme for Tauon based on Caelestia's.
  - `simple_scheme.py`: Generates a color scheme based on user-picked colors.
  - `wallpaper_posthook`: Manages the posthooks triggered on Caelestia WP change.
  - `wallpaper_select`: Opens Caelestia's wallpaper picker.
- `games/`:
  - `palworld_server`: (WIP) Sets up the tools to open a Palworld server without touching router config.
- `system/`:
  - `colors`: Displays common bash colors.
  - `fcitx_switch`: Cycle through set fcitx layouts.
  - `lonely_kitty`: Customizes lonely kitty windows.
  - `system_upgrade`: Offers to run a system upgrade every 48h.
- `tools/`:
  - `script_help`: Shows help for any bash script matching the given structure.
  - `new_version`: Creates a new version of a git project.
