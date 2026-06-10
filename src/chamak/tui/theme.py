"""Grayscale-leaning theme with selective accent colors.

Keeps the user's i3 aesthetic (no flashy colors in chrome), but uses
muted greens/ambers for score-encoded data so demo recordings read at a
glance.
"""

from __future__ import annotations

DEFAULT_CSS = """
Screen { background: #0c0c0e; color: #d4d4d4; }
Header { background: #16161a; color: #e6e6e6; text-style: bold; }
Footer { background: #16161a; color: #909090; }

.title { text-style: bold; color: #f0f0f0; }
.subtitle { color: #8a8a8a; }
.dim { color: #6b6b6b; }
.muted { color: #707070; }
.ok { color: #98c379; }
.warn { color: #e5c07b; }
.err { color: #e06c75; }
.accent { color: #88c0d0; }

.panel { border: round #2a2a2c; padding: 1 2; background: #111114; }
.panel-title { text-style: bold; color: #d4d4d4; }
.kbd { color: #88c0d0; text-style: bold; }

.score-hi { color: #98c379; text-style: bold; }
.score-mid { color: #e5c07b; }
.score-lo { color: #6b6b6b; }

DataTable { background: #0f0f12; }
DataTable > .datatable--header { background: #1c1c1f; color: #d0d0d0; text-style: bold; }
DataTable > .datatable--cursor { background: #2f2f33; }
DataTable > .datatable--hover { background: #1a1a1d; }

Tree { background: #0f0f12; padding: 0 1; }
Tree > .tree--cursor { background: #2c2c2e; }
Tree > .tree--guides { color: #303034; }

Input { background: #1a1a1d; border: tall #2a2a2c; color: #e8e8e8; }
Input:focus { border: tall #5e81ac; }

ListView { background: #0f0f12; }
ListItem { background: #0f0f12; padding: 0 1; height: auto; }
ListItem.--highlight { background: #2a2a2d; }
ListItem:hover { background: #1a1a1d; }

Button { background: #1c1c1f; color: #d4d4d4; border: tall #2a2a2c; min-width: 14; }
Button:hover { background: #25252a; }
Button.-primary { background: #2c2c34; color: #ffffff; border: tall #5e81ac; }
Button.-warning { background: #3c2a1a; color: #f0e0c0; }

/* demo overlay */
#demo-overlay {
    background: #1a1a1f;
    color: #e0e0e0;
    border: round #5e81ac;
    padding: 0 1;
    width: auto;
    height: auto;
    dock: top;
}
#demo-step { color: #88c0d0; text-style: bold; }
"""
