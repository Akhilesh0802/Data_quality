"""
theme.py
--------
Purple & grey colour palette + font helper. Change colours here only.
"""

# Purple family
PURPLE = "#4F2D7F"
PURPLE_DARK = "#3A1F5E"
PURPLE_MID = "#7B5BA6"
PURPLE_LIGHT = "#EDE7F6"
PURPLE_SOFT = "#DCD0EE"

# Grey family
GREY_BG = "#F2F2F5"
GREY_BORDER = "#DCDCE3"
GREY_TRACK = "#ECECF1"
GREY_TEXT = "#6B6B78"
GREY_DARK = "#2E2E38"
GREY_CHARCOAL = "#45454F"
WHITE = "#FFFFFF"

FONT_FAMILY = "Segoe UI"


def font(size: int, weight: str = "normal"):
    return (FONT_FAMILY, size, weight)
