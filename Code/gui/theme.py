import customtkinter as ctk

PRIMARY = "#00B4D8"
PRIMARY_DARK = "#0077B6"
PRIMARY_LIGHT = "#48CAE4"

SUCCESS = "#3FB950"
WARNING = "#D29922"
ERROR = "#F85149"

SURFACE = ("#F8F9FA", "#0D1117")
CARD_BG = ("#FFFFFF", "#161B22")
CARD_HOVER = ("#F0F0F0", "#1C2128")
SIDEBAR_BG = ("#F0F2F5", "#0D1117")
BORDER = ("#D0D7DE", "#30363D")
DIVIDER = ("#E8EAED", "#21262D")

TEXT_PRIMARY = ("#1F2328", "#E6EDF3")
TEXT_SECONDARY = ("#656D76", "#8B949E")
TEXT_HINT = ("#8B949E", "#6E7681")

ACCENT_GREEN = "#238636"
ACCENT_PURPLE = "#8957E5"
ACCENT_RED = "#DA3633"
ACCENT_ORANGE = "#F0883E"

SECTION_COLORS = {
    "github": ACCENT_GREEN,
    "evaluation": ACCENT_PURPLE,
    "llm": PRIMARY,
    "output": ACCENT_RED,
    "app": ACCENT_ORANGE,
}

SECTION_ICONS = {
    "github": "\u25C8",
    "evaluation": "\u25C6",
    "llm": "\u2B21",
    "output": "\u25CE",
    "app": "\u2699",
}

FONT_PAGE_TITLE = (20, "bold")
FONT_DIALOG_TITLE = (16, "bold")
FONT_SECTION = (14, "bold")
FONT_LIST_TITLE = (13, "bold")
FONT_NAV = (13, "normal")
FONT_SIDEBAR_TITLE = (13, "bold")
FONT_BODY = (12, "normal")
FONT_BTN = (12, "normal")
FONT_BTN_BOLD = (12, "bold")
FONT_CAPTION = (11, "normal")
FONT_STATUS = (11, "normal")
FONT_STAT_VALUE = (28, "bold")
FONT_STAT_TITLE = (11, "normal")
FONT_ICON_SM = (14, "normal")
FONT_ICON_MD = (16, "bold")
FONT_LOGO = (20, "bold")
FONT_LOGO_SUB = (14, "bold")

_font_cache = {}


def make_font(spec: tuple) -> ctk.CTkFont:
    """根据字体规格创建或获取缓存的CTkFont对象。"""
    if spec not in _font_cache:
        _font_cache[spec] = ctk.CTkFont(size=spec[0], weight=spec[1])
    return _font_cache[spec]


CORNER_RADIUS_CARD = 8
CORNER_RADIUS_BTN = 6
CORNER_RADIUS_ENTRY = 6

PADDING_PAGE = 20
PADDING_CARD = 16
PADDING_SECTION = 12
PADDING_FIELD = 6

SIDEBAR_WIDTH = 180
STATUSBAR_HEIGHT = 30
BTN_HEIGHT = 32
ENTRY_HEIGHT = 32
