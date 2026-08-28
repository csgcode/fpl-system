"""Decision state: the machine-readable STATE block at the end of
data/decisions/gw{N}/final.md.

The block is machine-written by the finalizer to a fixed schema (documented in
CLAUDE.md), so it is strict-parsed here (no yaml dependency): any line that
deviates refuses loudly with the offending line instead of guessing.
Validation of the parsed values is pydantic's job, exactly as for API payloads.

One scanner backs two projections. `parse_state_picks` extracts only the
`picks:` list — all the write path needs — and tolerates keys it does not
know, so a lineup POST never fails on an unrelated schema addition.
`parse_state` reads the whole block into `DecisionState` and rejects unknown
keys, because that model is the execution plan's sole input.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

MIN_GW = 1
MAX_GW = 38
SQUAD_SIZE = 15
XI_SIZE = 11

_YAML_BLOCK = re.compile(r"```yaml\n(.*?)```", re.DOTALL)
_KEY_LINE = re.compile(r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*):(?P<rest>.*)$")
_PICK_LINE = re.compile(
    r"^\s*-\s*\{\s*id:\s*(?P<id>\d+)\s*,\s*name:\s*(?P<name>.*?)\s*,"
    r"\s*position:\s*(?P<position>\d+)\s*,\s*captain:\s*(?P<captain>true|false)"
    r"\s*,\s*vice:\s*(?P<vice>true|false)\s*\}\s*$"
)
_CHIP_USE_LINE = re.compile(
    r"^-\s*\{\s*chip:\s*(?P<chip>.*?)\s*,\s*gw:\s*(?P<gw>\d+)\s*\}$"
)
_CHIP_PLAN_LINE = re.compile(
    r"^-\s*\{\s*chip:\s*(?P<chip>.*?)\s*,\s*gw:\s*(?P<gw>\d+)\s*"
    r"(?:,\s*status:\s*(?P<status>.*?)\s*)?\}$"
)
_TRANSFER_LINE = re.compile(
    r"^-\s*\{\s*out:\s*(?P<out>.*?)\s*,\s*in:\s*(?P<into>.*?)\s*,"
    r"\s*cost:\s*(?P<cost>-?\d+)\s*\}$"
)

_KNOWN_KEYS = frozenset(
    {
        "gw",
        "team_id",
        "team_value",
        "bank",
        "free_transfers_banked",
        "chips_used",
        "transfers_made",
        "chip",
        "chip_plan",
        "picks",
    }
)
_NULL_SCALARS = frozenset({"null", "~"})
_EMPTY_LIST_SCALARS = frozenset({"", "[]"})
DEFAULT_EARMARK_STATUS = "provisional"

_Item = TypeVar("_Item", bound=BaseModel)


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


class ChipUse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    chip: str
    gw: int = Field(ge=MIN_GW, le=MAX_GW)


class ChipEarmark(BaseModel):
    """A forward-looking chip intention. A forecast, not an activation — only
    DecisionState.chip activates a chip."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    chip: str
    gw: int = Field(ge=MIN_GW, le=MAX_GW)
    status: str = DEFAULT_EARMARK_STATUS


class NamedTransfer(BaseModel):
    """Transfers as the finalizer writes them: web_names, which are ambiguous
    (two players can share one). `into` spells the STATE block's `in:` key,
    which is a Python keyword."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    out: str
    into: str
    cost: int


class DecisionState(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    gw: int = Field(ge=MIN_GW, le=MAX_GW)
    team_id: int | None
    team_value: float
    bank: float
    free_transfers_banked: int = Field(ge=0)
    chips_used: tuple[ChipUse, ...] = ()
    transfers_made: tuple[NamedTransfer, ...] = ()
    chip: str | None = None
    chip_plan: tuple[ChipEarmark, ...] = ()
    picks: PlannedPicks | None = None


@dataclass(frozen=True)
class _Entry:
    key: str
    value: str
    items: tuple[str, ...]
    line: str


def parse_state(text: str, *, expected_gw: int | None = None) -> DecisionState:
    entries = _scan_block(_state_block(text))
    unknown = [key for key in entries if key not in _KNOWN_KEYS]
    if unknown:
        raise ValueError(
            f"unknown key in STATE block: {unknown[0]!r} — the schema is in "
            "CLAUDE.md; refusing to guess what it means"
        )
    return DecisionState(
        gw=_require_gw(entries, expected_gw),
        team_id=_scalar(entries, "team_id"),
        team_value=_scalar(entries, "team_value"),
        bank=_scalar(entries, "bank"),
        free_transfers_banked=_scalar(entries, "free_transfers_banked"),
        chips_used=[
            _parse_item("chips_used", item, _CHIP_USE_LINE, ChipUse)
            for item in _items(entries, "chips_used")
        ],
        transfers_made=[
            _parse_item("transfers_made", item, _TRANSFER_LINE, NamedTransfer)
            for item in _items(entries, "transfers_made")
        ],
        chip=_scalar(entries, "chip", required=False),
        chip_plan=[
            _parse_item("chip_plan", item, _CHIP_PLAN_LINE, ChipEarmark)
            for item in _items(entries, "chip_plan", required=False)
        ],
        picks=_picks(entries, required=False),
    )


def parse_state_picks(text: str, *, expected_gw: int) -> PlannedPicks:
    entries = _scan_block(_state_block(text))
    _require_gw(entries, expected_gw)
    picks = _picks(entries, required=True)
    assert picks is not None
    return picks


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


def _state_block(text: str) -> str:
    blocks = _YAML_BLOCK.findall(text)
    if not blocks:
        raise ValueError("no yaml block found — final.md must end with a STATE block")
    return blocks[-1]


def _scan_block(block: str) -> dict[str, _Entry]:
    entries: dict[str, _Entry] = {}
    key: str | None = None
    value = ""
    items: list[str] = []
    line = ""

    def close() -> None:
        nonlocal key
        if key is not None:
            entries[key] = _Entry(key, value, tuple(items), line)
            key = None

    for raw_line in block.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if key is None:
                raise ValueError(
                    f"list item before any key in STATE block: {stripped!r}"
                )
            items.append(stripped)
            continue
        match = _KEY_LINE.match(stripped)
        if match is None:
            raise ValueError(f"unparseable line in STATE block: {stripped!r}")
        close()
        if match["key"] in entries:
            raise ValueError(f"duplicate key in STATE block: {match['key']!r}")
        key = match["key"]
        value = match["rest"].strip()
        items = []
        line = stripped
    close()
    return entries


def _require_gw(entries: dict[str, _Entry], expected_gw: int | None) -> int:
    if "gw" not in entries:
        raise ValueError("STATE block has no 'gw:' line")
    raw = _scalar(entries, "gw")
    try:
        gw = int(str(raw))
    except ValueError:
        raise ValueError(f"STATE block has a non-numeric gw: {raw!r}") from None
    if expected_gw is not None and gw != expected_gw:
        raise ValueError(
            f"STATE block is for gw{gw}, not the requested gw{expected_gw} — "
            "refusing to apply a different gameweek's decision"
        )
    return gw


def _scalar(
    entries: dict[str, _Entry], key: str, *, required: bool = True
) -> str | None:
    entry = entries.get(key)
    if entry is None:
        if required:
            raise ValueError(f"STATE block is missing required key {key!r}")
        return None
    if entry.items:
        raise ValueError(
            f"key {key!r} takes a single value, not a list: {entry.line!r}"
        )
    if not entry.value:
        raise ValueError(f"key {key!r} has no value in STATE block: {entry.line!r}")
    if entry.value in _NULL_SCALARS:
        return None
    return _unquote(entry.value)


def _items(
    entries: dict[str, _Entry], key: str, *, required: bool = True
) -> tuple[str, ...]:
    entry = entries.get(key)
    if entry is None:
        if required:
            raise ValueError(f"STATE block is missing required key {key!r}")
        return ()
    if entry.value not in _EMPTY_LIST_SCALARS:
        raise ValueError(
            f"key {key!r} takes '[]' or indented '- {{...}}' item lines, not an "
            f"inline value: {entry.line!r}"
        )
    return entry.items


def _parse_item(
    key: str, item: str, pattern: re.Pattern[str], model: type[_Item]
) -> _Item:
    match = pattern.match(item)
    if match is None:
        raise ValueError(f"unparseable {key} line in STATE block: {item!r}")
    fields = {
        name: _unquote(value)
        for name, value in match.groupdict().items()
        if value is not None
    }
    return model.model_validate(fields)


def _picks(entries: dict[str, _Entry], *, required: bool) -> PlannedPicks | None:
    entry = entries.get("picks")
    if entry is None:
        if required:
            raise ValueError("STATE block has no 'picks:' section")
        return None
    if entry.value not in _EMPTY_LIST_SCALARS:
        raise ValueError(
            f"key 'picks' takes indented '- {{...}}' item lines, not an inline "
            f"value: {entry.line!r}"
        )
    return PlannedPicks(picks=tuple(_parse_pick_line(item) for item in entry.items))


def _parse_pick_line(item: str) -> PlannedPick:
    match = _PICK_LINE.match(item)
    if match is None:
        raise ValueError(f"unparseable pick line in STATE block: {item!r}")
    return PlannedPick(
        id=int(match["id"]),
        name=_unquote(match["name"]),
        position=int(match["position"]),
        captain=match["captain"] == "true",
        vice=match["vice"] == "true",
    )


def _unquote(name: str) -> str:
    if len(name) >= 2 and name[0] == name[-1] and name[0] in ("'", '"'):
        return name[1:-1]
    return name
