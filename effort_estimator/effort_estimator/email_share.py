"""
email_share.py
--------------
Builds the estimate table for e-mail and copies it to the clipboard.

On Windows the table is copied as rich HTML, so Ctrl+V in Outlook / Gmail /
Teams pastes a formatted table (purple header, borders).
On other systems it falls back to tab-separated plain text.
"""

import html
import sys

from calculator import fmt
from config import EXCEL_HEADERS

PURPLE = "#4F2D7F"


def hours_text(hours: float) -> str:
    """8 -> '08', 7.5 -> '07.5', 12 -> '12'"""
    text = fmt(hours)
    return f"0{text}" if hours < 10 else text


def row_values(result, details):
    return [
        details["entity_name"],
        hours_text(result.total_hours),
        details["delivery_date"].strftime("%d-%b-%Y"),
        ", ".join(details["resources"]),
        details["assumptions"],
    ]


# column widths in points - same look as the downloaded Excel sheet
COL_WIDTHS_PT = (130, 105, 105, 170, 320)
CHARS_PER_PT = 0.19           # ~ Arial 10pt characters per point of width
LINE_PT = 14


def _row_height_pt(values) -> int:
    """Estimate wrapped lines so Excel shows the full text (no cut-off rows)."""
    lines = 1
    for value, width in zip(values, COL_WIDTHS_PT):
        per_line = max(1, int(width * CHARS_PER_PT))
        needed = sum(max(1, -(-len(part) // per_line)) for part in value.split("\n"))
        lines = max(lines, needed)
    return lines * LINE_PT + 10


def build_html(result, details) -> str:
    """
    HTML table that pastes correctly in both Outlook and Excel:
      * fixed column widths (<col> + width styles) so columns are not squeezed
      * mso-number-format (text) keeps "08" and the date exactly as text
    """
    base = ("border:.5pt solid #BFBFC8;padding:4pt 7pt;font-family:Arial,sans-serif;"
            "font-size:10pt;vertical-align:middle;white-space:normal;")
    head = base + f"background:{PURPLE};color:#FFFFFF;font-weight:bold;text-align:center;"
    values = row_values(result, details)

    cols = "".join(f'<col width="{round(w * 4 / 3)}" style="width:{w}pt">' for w in COL_WIDTHS_PT)
    ths = "".join(f'<td style="{head}width:{w}pt">{html.escape(h)}</td>'
                  for h, w in zip(EXCEL_HEADERS, COL_WIDTHS_PT))
    tds = []
    for i, (value, w) in enumerate(zip(values, COL_WIDTHS_PT)):
        align = "center" if i in (1, 2) else "left"
        safe = html.escape(value).replace("\n", "<br>")
        tds.append(f'<td style="{base}width:{w}pt;text-align:{align};'
                   f"mso-number-format:'\\@';\">{safe}</td>")
    total_w = sum(COL_WIDTHS_PT)
    return (f'<table border="0" cellspacing="0" cellpadding="0" '
            f'style="border-collapse:collapse;width:{total_w}pt;table-layout:fixed">'
            f"{cols}"
            f'<tr style="height:36pt">{ths}</tr>'
            f'<tr style="height:{_row_height_pt(values)}pt">{"".join(tds)}</tr></table>')


def build_text(result, details) -> str:
    values = [v.replace("\n", " ") for v in row_values(result, details)]
    return "\t".join(EXCEL_HEADERS) + "\r\n" + "\t".join(values)


# ------------------------------------------------------------------ clipboard
def _cf_html(fragment: str) -> bytes:
    """Wrap an HTML fragment in the Windows 'HTML Format' clipboard header."""
    header = ("Version:0.9\r\nStartHTML:{0:010d}\r\nEndHTML:{1:010d}\r\n"
              "StartFragment:{2:010d}\r\nEndFragment:{3:010d}\r\n")
    prefix = ('<html xmlns:o="urn:schemas-microsoft-com:office:office" '
              'xmlns:x="urn:schemas-microsoft-com:office:excel" '
              'xmlns="http://www.w3.org/TR/REC-html40"><head><meta charset="utf-8"></head>'
              "<body>\r\n<!--StartFragment-->")
    suffix = "<!--EndFragment-->\r\n</body></html>"
    dummy = header.format(0, 0, 0, 0)
    start_html = len(dummy.encode("utf-8"))
    start_frag = start_html + len(prefix.encode("utf-8"))
    end_frag = start_frag + len(fragment.encode("utf-8"))
    end_html = end_frag + len(suffix.encode("utf-8"))
    full = header.format(start_html, end_html, start_frag, end_frag) + prefix + fragment + suffix
    return full.encode("utf-8")


def _copy_windows(html_fragment: str, text: str) -> None:
    import ctypes
    import time
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterClipboardFormatW.restype = wintypes.UINT
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]

    GMEM_MOVEABLE = 0x0002
    CF_UNICODETEXT = 13
    CF_HTML = user32.RegisterClipboardFormatW("HTML Format")

    def put(fmt_id, data: bytes):
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not handle:
            raise OSError("GlobalAlloc failed")
        ptr = kernel32.GlobalLock(handle)
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(fmt_id, handle):
            raise OSError("SetClipboardData failed")

    for _ in range(10):                      # clipboard may be busy for a moment
        if user32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        raise OSError("Clipboard is busy - try again")
    try:
        user32.EmptyClipboard()
        put(CF_HTML, _cf_html(html_fragment) + b"\0")
        put(CF_UNICODETEXT, (text + "\0").encode("utf-16-le"))
    finally:
        user32.CloseClipboard()


def copy_for_email(tk_root, result, details) -> bool:
    """Copy the table. Returns True if rich (formatted) copy worked."""
    html_fragment = build_html(result, details)
    text = build_text(result, details)
    if sys.platform.startswith("win"):
        try:
            _copy_windows(html_fragment, text)
            return True
        except Exception:
            pass                              # fall back to plain text below
    tk_root.clipboard_clear()
    tk_root.clipboard_append(text)
    tk_root.update()                          # keep clipboard after dialog closes
    return False
