# Infinite Crossy Road

An endless Crossy Road–style game built with Python and Pygame.

Move upward, dodge cars, jump on logs, and collect coins to earn extra lives.

## Requirements
* Python 3.8 or higher
* Pygame 2.1 or higher

Install dependencies with:
```bash
pip install pygame
```

## How to play
Start game with:
```bash
python3 crossyroad.py
```

## Controls

| Action                         | Key                     |
| ------------------------------ | ----------------------- |
| Move up                        | `↑` or `W`              |
| Move down                      | `↓` or `S`              |
| Move left                      | `←` or `A`              |
| Move right                     | `→` or `D`              |
| Quick jump upward              | `Space`                 |
| Pause / Resume                 | `Esc`                   |
| Restart (on pause/game over)   | `R`                     |
| Exit (on game over/pause)      | `Esc` or `Space`        |

## Features
* Infinite, procedurally generated world.
* Obstacles like cars, trucks, and rivers with moving logs.
* Coin collection and extra life system.
* Progressive difficulty scaling.
* Procedurally generated sound effects (no audio files required).
* Built-in start, pause, and game over menus.

## Scoring
* __+10__ points for each forward row.
* __+50__ points per coin collected.
* Every *10 coins* grants __+1 extra life__.
