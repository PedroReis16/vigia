"""Estado do menu de cenários — puro (teclas já traduzidas em nomes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from vigia_lab.catalog import Scenario

Action = Literal["none", "start", "quit"]


@dataclass
class MenuState:
    scenarios: list[Scenario]
    only: str | None = None          # None | "FALL" | "ADL"
    index: int = 0
    _all: list[Scenario] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self._all = list(self.scenarios)

    @property
    def visible(self) -> list[Scenario]:
        if self.only is None:
            return self._all
        return [s for s in self._all if s.label == self.only]

    @property
    def selected(self) -> Scenario:
        return self.visible[self.index]

    def handle(self, key: str) -> Action:
        n = len(self.visible)
        if key in ("up", "left"):
            self.index = (self.index - 1) % n
        elif key in ("down", "right"):
            self.index = (self.index + 1) % n
        elif key == "tab":
            order = [None, "FALL", "ADL"]
            current = self.selected
            self.only = order[(order.index(self.only) + 1) % len(order)]
            vis = self.visible
            self.index = vis.index(current) if current in vis else 0
        elif key == "enter":
            return "start"
        elif key == "esc":
            return "quit"
        return "none"
