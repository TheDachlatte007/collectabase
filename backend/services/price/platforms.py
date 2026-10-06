"""Canonical platform identities shared by catalog scraping and lookup."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformIdentity:
    key: str
    label: str
    scraper_slug: str | None = None


_PLATFORMS = {
    "playstation 5": PlatformIdentity("playstation-5", "PlayStation 5", "playstation-5"),
    "playstation 4": PlatformIdentity("playstation-4", "PlayStation 4", "playstation-4"),
    "playstation 3": PlatformIdentity("playstation-3", "PlayStation 3", "playstation-3"),
    "playstation 2": PlatformIdentity("playstation-2", "PlayStation 2", "playstation-2"),
    "playstation": PlatformIdentity("playstation", "PlayStation", "playstation"),
    "psp": PlatformIdentity("psp", "PSP", "psp"),
    "ps vita": PlatformIdentity("ps-vita", "PS Vita", "ps-vita"),
    "xbox series x s": PlatformIdentity("xbox-series-x-s", "Xbox Series X/S", "xbox-series-x"),
    "xbox one": PlatformIdentity("xbox-one", "Xbox One", "xbox-one"),
    "xbox 360": PlatformIdentity("xbox-360", "Xbox 360", "xbox-360"),
    "xbox": PlatformIdentity("xbox", "Xbox", "xbox"),
    "nintendo switch 2": PlatformIdentity("nintendo-switch-2", "Nintendo Switch 2", "nintendo-switch-2"),
    "nintendo switch": PlatformIdentity("nintendo-switch", "Nintendo Switch", "nintendo-switch"),
    "wii u": PlatformIdentity("wii-u", "Wii U", "wii-u"),
    "wii": PlatformIdentity("wii", "Wii", "wii"),
    "gamecube": PlatformIdentity("gamecube", "GameCube", "gamecube"),
    "nintendo 64": PlatformIdentity("nintendo-64", "Nintendo 64", "nintendo-64"),
    "snes": PlatformIdentity("snes", "SNES", "super-nintendo"),
    "nes": PlatformIdentity("nes", "NES", "nes"),
    "game boy advance": PlatformIdentity("game-boy-advance", "Game Boy Advance", "gameboy-advance"),
    "game boy color": PlatformIdentity("game-boy-color", "Game Boy Color", "gameboy-color"),
    "game boy": PlatformIdentity("game-boy", "Game Boy", "gameboy"),
    "nintendo 3ds": PlatformIdentity("nintendo-3ds", "Nintendo 3DS", "3ds"),
    "nintendo ds": PlatformIdentity("nintendo-ds", "Nintendo DS", "nintendo-ds"),
    "sega dreamcast": PlatformIdentity("sega-dreamcast", "Sega Dreamcast", "sega-dreamcast"),
    "sega saturn": PlatformIdentity("sega-saturn", "Sega Saturn", "sega-saturn"),
    "sega genesis mega drive": PlatformIdentity("sega-genesis-mega-drive", "Sega Genesis/Mega Drive", "sega-genesis"),
    "sega master system": PlatformIdentity("sega-master-system", "Sega Master System", "sega-master-system"),
    "sega game gear": PlatformIdentity("sega-game-gear", "Sega Game Gear", "game-gear"),
}
_ALIASES = {
    "ps5": "playstation 5",
    "ps4": "playstation 4",
    "ps3": "playstation 3",
    "ps2": "playstation 2",
    "xbox series x": "xbox series x s",
    "super nintendo": "snes",
    "genesis": "sega genesis mega drive",
    "mega drive": "sega genesis mega drive",
}
PLATFORM_SLUGS = {identity.label.lower(): identity.scraper_slug for identity in _PLATFORMS.values() if identity.scraper_slug}


def _normalized(value: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())).strip()


def canonicalize_platform(value: str | None) -> PlatformIdentity:
    normalized = _ALIASES.get(_normalized(value), _normalized(value))
    known = _PLATFORMS.get(normalized)
    if known:
        return known
    key = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "unknown"
    label = " ".join(word.capitalize() for word in normalized.split()) or "Unknown"
    return PlatformIdentity(key, label)


def get_known_platforms() -> list[PlatformIdentity]:
    seen: dict[str, PlatformIdentity] = {}
    for identity in _PLATFORMS.values():
        if identity.key not in seen:
            seen[identity.key] = identity
    return sorted(seen.values(), key=lambda p: p.label.lower())
