"""Decision state: the machine-readable STATE block at the end of
data/decisions/gw{N}/final.md, and the planned picks it carries.

The picks section is machine-written by the finalizer to a fixed one-line-per-
pick format, so it is strict-parsed here (no yaml dependency): any line that
deviates refuses loudly instead of guessing. Validation of the parsed picks is
pydantic's job, exactly as for API payloads.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, model_validator

SQUAD_SIZE = 15
XI_SIZE = 11

_YAML_BLOCK = re.compile(r"```yaml\n(.*?)```", re.DOTALL)
_STATE_GW = re.compile(r"^gw:\s*(\d+)\s*$", re.MULTILINE)
_PICK_LINE = re.compile(
    r"^\s*-\s*\{\s*id:\s*(?P<id>\d+)\s*,\s*name:\s*(?P<name>.*?)\s*,"
    r"\s*position:\s*(?P<position>\d+)\s*,\s*captain:\s*(?P<captain>true|false)"
    r"\s*,\s*vice:\s*(?P<vice>true|false)\s*\}\s*$"
)


class PlannedPick(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: int
    name: str
    position: int = Field(ge=1, le=SQUAD_SIZE)
    captain: bool = False
    vice: bool = False

    @property
    def starts(self) -> bool:
        return self.position <= XI_SIZE


class PlannedPicks(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    picks: tuple[PlannedPick, ...]

    @model_validator(mode="after")
    def _squad_shape(self) -> PlannedPicks:
        if len(self.picks) != SQUAD_SIZE:
            raise ValueError(f"expected {SQUAD_SIZE} picks, got {len(self.picks)}")
        positions = sorted(p.position for p in self.picks)
        if positions != list(range(1, SQUAD_SIZE + 1)):
            raise ValueError(f"positions must be exactly 1-{SQUAD_SIZE}, no repeats")
        if len({p.id for p in self.picks}) != SQUAD_SIZE:
            raise ValueError("player ids must be unique")
        captains = [p for p in self.picks if p.captain]
        vices = [p for p in self.picks if p.vice]
        if len(captains) != 1:
            raise ValueError(f"expected exactly one captain, got {len(captains)}")
        if len(vices) != 1:
            raise ValueError(f"expected exactly one vice, got {len(vices)}")
        if captains[0].id == vices[0].id:
            raise ValueError("captain and vice must be different players")
        if not captains[0].starts:
            raise ValueError("captain must start (position 1-11)")
        if not vices[0].starts:
            raise ValueError("vice must start (position 1-11)")
        return self

    def captain(self) -> PlannedPick:
        return next(p for p in self.picks if p.captain)

    def vice(self) -> PlannedPick:
        return next(p for p in self.picks if p.vice)

    def bench(self) -> tuple[PlannedPick, ...]:
        return tuple(
            sorted((p for p in self.picks if not p.starts), key=lambda p: p.position)
        )

    def ids(self) -> frozenset[int]:
        return frozenset(p.id for p in self.picks)

    def in_position_order(self) -> tuple[PlannedPick, ...]:
        return tuple(sorted(self.picks, key=lambda p: p.position))


def parse_state_picks(text: str, *, expected_gw: int) -> PlannedPicks:
    blocks = _YAML_BLOCK.findall(text)
    if not blocks:
        raise ValueError("no yaml block found — final.md must end with a STATE block")
    block = blocks[-1]
    gw_match = _STATE_GW.search(block)
    if gw_match is None:
        raise ValueError("STATE block has no 'gw:' line")
    state_gw = int(gw_match.group(1))
    if state_gw != expected_gw:
        raise ValueError(
            f"STATE block is for gw{state_gw}, not the requested gw{expected_gw} — "
            "refusing to apply a different gameweek's decision"
        )
    return PlannedPicks(picks=_parse_pick_lines(block))


def picks_from_ids(ids: list[int], *, captain: int, vice: int) -> PlannedPicks:
    picks = tuple(
        PlannedPick(
            id=player_id,
            name="",
            position=slot,
            captain=player_id == captain,
            vice=player_id == vice,
        )
        for slot, player_id in enumerate(ids, start=1)
    )
    return PlannedPicks(picks=picks)


def _parse_pick_lines(block: str) -> tuple[PlannedPick, ...]:
    lines = block.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip() == "picks:")
    except StopIteration:
        raise ValueError("STATE block has no 'picks:' section") from None
    picks: list[PlannedPick] = []
    for line in lines[start + 1 :]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        if not line.strip().startswith("- "):
            break
        match = _PICK_LINE.match(line)
        if match is None:
            raise ValueError(f"unparseable pick line in STATE block: {line.strip()!r}")
        picks.append(
            PlannedPick(
                id=int(match["id"]),
                name=_unquote(match["name"]),
                position=int(match["position"]),
                captain=match["captain"] == "true",
                vice=match["vice"] == "true",
            )
        )
    return tuple(picks)


def _unquote(name: str) -> str:
    if len(name) >= 2 and name[0] == name[-1] and name[0] in ("'", '"'):
        return name[1:-1]
    return name
