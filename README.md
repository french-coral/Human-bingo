# Human Bingo Generator

A beginner-friendly Tkinter application for generating Human Bingo grids from a simple JSON proposition list.

## Features

- Any square grid size
- Generate multiple grids at once
- Seeded, reproducible random generation
- Light balancing across a batch
- No duplicates inside a grid when enough propositions exist
- JSON editor and friendly list editor
- Synchronized editing modes
- Faithful PDF preview inside the application
- A4 portrait/landscape PDF export
- Save the generated batch as JSON using the seed as filename
- French/UTF-8 text support
- Minimalist printable design

## Installation

Python 3.10+ is recommended.

```bash
python -m pip install -r requirements.txt
```

On some Linux distributions, Tkinter is a separate system package.

## Run

```bash
python main.py
```

A starter proposition file is included at:

`data/propositions.json`

## Notes

The PDF renderer uses ReportLab. The on-screen preview renders the same PDF drawing logic onto a Tkinter canvas, so the preview closely matches the exported document.
