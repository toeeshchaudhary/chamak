from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

_HELP = """
[bold]What Chamak is[/]
  Chamak learns how YOU decide what makes a good investment, draws a flowchart
  of your thinking (your "investing style"), and ranks every stock against it.
  No predictions. No buy/sell signals. Just compatibility, explained.

[bold]Keyboard[/]
  q          Quit
  Esc        Back
  ?          Help (this screen)
  :          Command palette
  /          Search

[bold]Jump to screens[/]
  g          Dashboard
  L          My investing styles
  R          Stocks ranked by fit
  S          Market scanner
  P          My portfolios
  N          News with sentiment
  I          Run the interview to build a style
  D          Demo / autopilot tour
  M          Settings

[bold]Lists & tables[/]
  j / k      Down / up
  Enter      Open / activate
  n          New
  d          Duplicate
  a          Archive

[bold]Style editor[/]
  j / k      Pick a belief
  i          Add a new rule to the selected belief
  x          Delete a rule
  +/-        Make a rule more / less important
  h          Toggle "deal-breaker" (a hard rule)
  n          Add a new belief
  s          Save (creates a new version)
  V          Open the full-screen flowchart view

[bold]Demo autopilot[/]
  Space      Pause / resume
  →  / l     Next scene
  ←  / h     Restart current scene
  q          Quit autopilot

[bold]Tips[/]
  Every save is a new version. The version history screen shows the
  difference between any two versions and lets you roll back.
  When viewing a stock, the flowchart shows the same style with each
  rule colored: [green]green = matches[/], [red]red = doesn't match[/].
  First time? Press [bold]D[/] for the demo tour, or [bold]I[/] for the interview.
"""


class HelpScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Static(_HELP, classes="panel")
        yield Footer()
