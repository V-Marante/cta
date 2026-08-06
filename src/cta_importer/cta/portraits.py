from __future__ import annotations

from dataclasses import dataclass


ELEMENT_CODES = {"Dark": "DA", "Earth": "EA", "Fire": "FI", "Light": "LI", "Water": "WA"}
MAX_ICON_INDEX = {"DA": 30, "EA": 32, "FI": 30, "LI": 30, "WA": 31}


@dataclass(frozen=True)
class PortraitReference:
    element_code: str
    icon_index: int
    frame_name: str
    atlas_name: str

    @property
    def plist_entry(self) -> str:
        return f"assets/{self.atlas_name}.plist"

    @property
    def texture_entry(self) -> str:
        return f"assets/{self.atlas_name}.pvrgz"


def portrait_reference(element: str | None, icon_index: str | int | None) -> PortraitReference | None:
    code = ELEMENT_CODES.get((element or "").strip())
    try:
        index = int(icon_index) if icon_index is not None and str(icon_index).strip() else 0
    except (TypeError, ValueError):
        return None
    if code is None or index < 1 or index > MAX_ICON_INDEX[code]:
        return None
    atlas = "UIGuildMemberIcons1" if code == "WA" and index >= 16 else "UIGuildMemberIcons0"
    return PortraitReference(code, index, f"GMI_{code}_{index:03d}.png", atlas)
