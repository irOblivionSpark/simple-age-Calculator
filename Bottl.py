#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced CLI Age & Calendar Toolkit (FA/EN)
- Language toggle (فارسی/English) from main menu
- RTL-aware layout for Persian (optional shaping via arabic_reshaper + python-bidi)
- Detects current date from system; falls back to online time if needed
- Age calculation in Gregorian (precise Y/M/D), leap-year aware
- Sections:
  1) Age (Gregorian input)
  2) Age (Jalali/Shamsi input)
  3) Convert Shamsi → Gregorian
  4) Convert Gregorian → Shamsi
  5) Language / تغییر زبان
  0) Exit / خروج
- Pretty CLI with optional colors
"""

import sys
import re
import calendar
from datetime import date, timedelta

# ---------- Optional colors (degrade gracefully) ----------
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    COLOR_OK = True
except Exception:
    COLOR_OK = False
    class Dummy:
        def __getattr__(self, name): return ""
    Fore = Style = Dummy()

# ---------- Optional Jalali backends ----------
JALALI_OK = False
JALALI_BACKEND = None
try:
    from convertdate import jalali as cv_jalali
    JALALI_OK = True
    JALALI_BACKEND = "convertdate"
except Exception:
    try:
        import jdatetime as jd
        JALALI_OK = True
        JALALI_BACKEND = "jdatetime"
    except Exception:
        JALALI_OK = False
        JALALI_BACKEND = None

# ---------- Optional RTL shaping (recommended for Persian) ----------
AR_SHAPE_OK = False
try:
    import arabic_reshaper  # type: ignore
    from bidi.algorithm import get_display  # type: ignore
    AR_SHAPE_OK = True
except Exception:
    AR_SHAPE_OK = False

def fa_shape(s: str) -> str:
    """Apply Arabic/Persian shaping + bidi if libs available."""
    if not s:
        return s
    if AR_SHAPE_OK:
        try:
            return get_display(arabic_reshaper.reshape(s))
        except Exception:
            return s
    return s

# ---------- i18n ----------
LANG = "fa"  # default Persian; set to "en" if you want English by default

# numeral normalization (Persian/Arabic to Latin)
P2L_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def normalize_digits(s: str) -> str:
    return s.translate(P2L_DIGITS)

T = {
    "en": {
        "MAIN_MENU": "MAIN MENU",
        "AGE_G_INPUT": "Calculate Age (Gregorian input)",
        "AGE_J_INPUT": "Calculate Age (Shamsi input)",
        "CONV_J2G": "Convert Shamsi → Gregorian",
        "CONV_G2J": "Convert Gregorian → Shamsi",
        "LANGUAGE": "Language",
        "EXIT": "Exit",
        "SELECT": "Select an option [0-5]: ",
        "ENTER_BD_G": "Enter birthdate (Gregorian) [YYYY-MM-DD] (or 'b' to go back): ",
        "ENTER_BD_J": "Enter birthdate (Jalali) [YYYY-MM-DD] (or 'b' to go back): ",
        "J_DATE": "Jalali date [YYYY-MM-DD] (or 'b' to go back): ",
        "G_DATE": "Gregorian date [YYYY-MM-DD] (or 'b' to go back): ",
        "TRY_ANOTHER": "Try another date? [y/N]: ",
        "GOODBYE": "Goodbye! 👋",
        "INTERRUPTED": "Interrupted. Goodbye!",
        "INVALID": "Invalid choice. Please try again.",
        "AGE_CARD": "AGE CALCULATOR",
        "BIRTH_G": "Birthdate (G)",
        "TODAY_G": "Today (G)",
        "BIRTH_J": "Birthdate (J)",
        "TODAY_J": "Today (J)",
        "AGE": "Age",
        "NEXT_BD_G": "Next BD (G)",
        "NEXT_BD_J": "Next BD (J)",
        "NEXT_BD": "Next BD",
        "IN": "In",
        "YEARS_MONTHS_DAYS": "{y} years, {m} months, {d} days",
        "DAYS": "{n} days",
        "NEED_JALALI": "✖ Jalali features require 'convertdate' or 'jdatetime'. Try:\n   pip install convertdate",
        "FALLBACK_WARN": "⚠ Could not verify a plausible current date. Using fallback 2000-01-01.",
        "ONLINE_INFO": "ℹ Using verified current date (online or adjusted).",
        "ERR": "Error: {e}",
        "LANG_MENU": "LANGUAGE",
        "CUR_LANG": "Current",
        "SWITCH_TO": "Switch to",
        "LANG_FA": "Persian (فارسی)",
        "LANG_EN": "English",
    },
    "fa": {
        "MAIN_MENU": "منوی اصلی",
        "AGE_G_INPUT": "محاسبه سن (ورودی میلادی)",
        "AGE_J_INPUT": "محاسبه سن (ورودی شمسی)",
        "CONV_J2G": "تبدیل شمسی → میلادی",
        "CONV_G2J": "تبدیل میلادی → شمسی",
        "LANGUAGE": "تغییر زبان",
        "EXIT": "خروج",
        "SELECT": "یک گزینه را انتخاب کنید [۰ تا ۵]: ",
        "ENTER_BD_G": "تاریخ تولد (میلادی) را وارد کنید [YYYY-MM-DD] (یا b برای بازگشت): ",
        "ENTER_BD_J": "تاریخ تولد (شمسی) را وارد کنید [YYYY-MM-DD] (یا b برای بازگشت): ",
        "J_DATE": "تاریخ شمسی [YYYY-MM-DD] (یا b برای بازگشت): ",
        "G_DATE": "تاریخ میلادی [YYYY-MM-DD] (یا b برای بازگشت): ",
        "TRY_ANOTHER": "تاریخ دیگری امتحان شود؟ [y/N]: ",
        "GOODBYE": "خدانگهدار! 👋",
        "INTERRUPTED": "عملیات متوقف شد. خدانگهدار!",
        "INVALID": "گزینه نامعتبر است. دوباره امتحان کنید.",
        "AGE_CARD": "محاسبه سن",
        "BIRTH_G": "تولد (میلادی)",
        "TODAY_G": "امروز (میلادی)",
        "BIRTH_J": "تولد (شمسی)",
        "TODAY_J": "امروز (شمسی)",
        "AGE": "سن",
        "NEXT_BD_G": "تولد بعدی (میلادی)",
        "NEXT_BD_J": "تولد بعدی (شمسی)",
        "NEXT_BD": "تولد بعدی",
        "IN": "در",
        "YEARS_MONTHS_DAYS": "{y} سال، {m} ماه، {d} روز",
        "DAYS": "{n} روز",
        "NEED_JALALI": "✖ امکانات شمسی نیازمند 'convertdate' یا 'jdatetime' است. فرمان پیشنهادی:\n   pip install convertdate",
        "FALLBACK_WARN": "⚠ تاریخ جاری قابل اطمینان نبود؛ از 2000-01-01 استفاده شد.",
        "ONLINE_INFO": "ℹ تاریخ امروز از منبع آنلاین/اصلاح‌شده دریافت شد.",
        "ERR": "خطا: {e}",
        "LANG_MENU": "زبان",
        "CUR_LANG": "زبان فعلی",
        "SWITCH_TO": "تغییر به",
        "LANG_FA": "فارسی",
        "LANG_EN": "انگلیسی",
    },
}

def t(key: str, **kwargs) -> str:
    txt = T[LANG].get(key, key)
    return txt.format(**kwargs)

def is_rtl() -> bool:
    return LANG == "fa"

def shape_if_needed(s: str) -> str:
    return fa_shape(s) if is_rtl() else s

# ---------- Optional online time (requests preferred; urllib fallback) ----------
def _fetch_online_date(timeout=3):
    """Try simple public endpoints; return a UTC-based date if possible."""
    urls = [
        "https://worldtimeapi.org/api/ip",
        "https://worldtimeapi.org/api/timezone/Etc/UTC",
    ]
    # requests
    try:
        import requests  # type: ignore
        for u in urls:
            try:
                r = requests.get(u, timeout=timeout)
                if r.ok:
                    data = r.json()
                    if "datetime" in data:
                        dt = data["datetime"]  # e.g. 2025-10-18T14:23:45.123456+00:00
                        y, m, d = map(int, dt[:10].split("-"))
                        return date(y, m, d)
            except Exception:
                continue
    except Exception:
        pass
    # urllib fallback
    try:
        import json, urllib.request
        for u in urls:
            try:
                with urllib.request.urlopen(u, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if "datetime" in data:
                        dt = data["datetime"]
                        y, m, d = map(int, dt[:10].split("-"))
                        return date(y, m, d)
            except Exception:
                continue
    except Exception:
        pass
    return None

def plausible_year(y: int) -> bool:
    return 1970 <= y <= 2100

def get_current_date() -> date:
    """Get today's date from system; if implausible or error, try online."""
    try:
        local_today = date.today()
        if plausible_year(local_today.year):
            return local_today
    except Exception:
        pass
    online = _fetch_online_date()
    if online and plausible_year(online.year):
        return online
    # Final fallback
    return date(2000, 1, 1)

# ---------- Parsing helpers ----------
def _normalize_sep(s: str) -> str:
    return re.sub(r"[\/\.]", "-", s.strip())

def parse_gregorian(s: str) -> date:
    s = _normalize_sep(s)
    if not re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", s):
        raise ValueError("Use Gregorian YYYY-MM-DD (e.g., 1990-07-15).")
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)

def parse_jalali_tuple(s: str) -> tuple[int, int, int]:
    s = _normalize_sep(s)
    if not re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", s):
        raise ValueError("Use Jalali YYYY-MM-DD (e.g., 1370-04-24).")
    return tuple(map(int, s.split("-")))  # (jy, jm, jd)

# ---------- Jalali conversion wrappers ----------
def gdate_to_jtuple(gd: date) -> tuple[int, int, int]:
    """Gregorian date -> (jy, jm, jd)"""
    if not JALALI_OK:
        raise RuntimeError("Jalali backend not available. Install 'convertdate' or 'jdatetime'.")
    if JALALI_BACKEND == "convertdate":
        return cv_jalali.from_gregorian(gd.year, gd.month, gd.day)
    # jdatetime
    j = jd.date.fromgregorian(date=gd)
    return (j.year, j.month, j.day)

def jtuple_to_gdate(jy: int, jm: int, jd_: int) -> date:
    """(jy, jm, jd) -> Gregorian date"""
    if not JALALI_OK:
        raise RuntimeError("Jalali backend not available. Install 'convertdate' or 'jdatetime'.")
    if JALALI_BACKEND == "convertdate":
        gy, gm, gd = cv_jalali.to_gregorian(jy, jm, jd_)
        return date(gy, gm, gd)
    # jdatetime
    return jd.date(jy, jm, jd_).togregorian()

# ---------- Age math ----------
def age_ymd(born: date, today: date):
    """Return (years, months, days) precise difference (Gregorian)."""
    if born > today:
        raise ValueError("Birthdate cannot be in the future.")
    y = today.year - born.year
    m = today.month - born.month
    d = today.day - born.day

    if d < 0:
        # borrow from previous month
        if today.month == 1:
            prev_month, prev_year = 12, today.year - 1
        else:
            prev_month, prev_year = today.month - 1, today.year
        days_in_prev_month = calendar.monthrange(prev_year, prev_month)[1]
        d += days_in_prev_month
        m -= 1
    if m < 0:
        m += 12
        y -= 1
    return y, m, d

def next_birthday_after(born: date, today: date) -> date:
    """Next birthday after 'today' in Gregorian; handles Feb 29."""
    b_month, b_day = born.month, born.day
    def _safe_date(y, m, d):
        last_day = calendar.monthrange(y, m)[1]
        return date(y, m, min(d, last_day))
    candidate = _safe_date(today.year, b_month, b_day)
    if candidate <= today:
        candidate = _safe_date(today.year + 1, b_month, b_day)
    return candidate

def days_until_next_birthday(born: date, today: date) -> int:
    return (next_birthday_after(born, today) - today).days

# ---------- Pretty CLI ----------
WIDTH = 56
BOX_TOP = "╔" + "═" * (WIDTH - 2) + "╗"
BOX_BOTTOM = "╚" + "═" * (WIDTH - 2) + "╝"

def render_box_title(text: str) -> str:
    text = " " + text.strip() + " "
    text = shape_if_needed(text)
    inner_width = WIDTH - 2
    if is_rtl():
        fill = "═" * max(0, inner_width - len(text))
        return "╔" + fill + text + "╗"
    else:
        fill = "═" * max(0, inner_width - len(text))
        return "╔" + text + fill + "╗"

def render_box_line(content: str) -> str:
    inner_width = WIDTH - 2
    content = shape_if_needed(content)
    if is_rtl():
        padded = content.rjust(inner_width)
    else:
        padded = content.ljust(inner_width)
    return "║" + padded[:inner_width] + "║"

def title(text: str) -> str:
    return render_box_title(text)

def line(label: str, value: str) -> str:
    label_sh = shape_if_needed(label)
    value_sh = shape_if_needed(value)
    if is_rtl():
        content = f"{value_sh}  {label_sh}"
    else:
        content = f"{label_sh}: {value_sh}"
    return render_box_line(content)

def colorize(s: str, color=Fore.CYAN):
    return (color + s + Style.RESET_ALL) if COLOR_OK else s

def prompt(s: str) -> str:
    msg = shape_if_needed(s)
    return input(colorize(msg, Fore.YELLOW))

def show_age_card(born_g: date, today_g: date, ymd, d2n: int):
    print(title(t("AGE_CARD")))
    # Gregorian lines
    print(line(t("BIRTH_G"), colorize(str(born_g), Fore.GREEN)))
    print(line(t("TODAY_G"), colorize(str(today_g), Fore.GREEN)))
    # Jalali mirrors if available
    if JALALI_OK:
        jb = gdate_to_jtuple(born_g)
        jt = gdate_to_jtuple(today_g)
        print(line(t("BIRTH_J"), colorize(f"{jb[0]:04d}-{jb[1]:02d}-{jb[2]:02d}", Fore.MAGENTA)))
        print(line(t("TODAY_J"), colorize(f"{jt[0]:04d}-{jt[1]:02d}-{jt[2]:02d}", Fore.MAGENTA)))
    y, m, d = ymd
    print(line(t("AGE"), colorize(t("YEARS_MONTHS_DAYS", y=y, m=m, d=d), Fore.CYAN)))
    nb = next_birthday_after(born_g, today_g)
    if JALALI_OK:
        jnb = gdate_to_jtuple(nb)
        nb_j = f"{jnb[0]:04d}-{jnb[1]:02d}-{jnb[2]:02d}"
        print(line(t("NEXT_BD_G"), colorize(str(nb), Fore.BLUE)))
        print(line(t("NEXT_BD_J"), colorize(nb_j, Fore.BLUE)))
    else:
        print(line(t("NEXT_BD"), colorize(str(nb), Fore.BLUE)))
    print(line(t("IN"), colorize(t("DAYS", n=d2n), Fore.CYAN)))
    print(BOX_BOTTOM)

def show_convert_card(title_text: str, g: date, j: tuple[int,int,int]):
    print(title(title_text))
    print(line("Gregorian / میلادی", colorize(str(g), Fore.GREEN)))
    print(line("Jalali / شمسی", colorize(f"{j[0]:04d}-{j[1]:02d}-{j[2]:02d}", Fore.MAGENTA)))
    print(BOX_BOTTOM)

# ---------- Flows ----------
def calculate_age_gregorian_flow():
    today = get_current_date()
    if not plausible_year(today.year):
        print(colorize(t("FALLBACK_WARN"), Fore.RED))
    elif today != date.today():
        print(colorize(t("ONLINE_INFO"), Fore.BLUE))
    while True:
        raw = prompt(t("ENTER_BD_G")).strip()
        raw = normalize_digits(raw)
        if raw.lower() in {"b", "back"}:
            return
        try:
            born = parse_gregorian(raw)
            ymd = age_ymd(born, today)
            d2n = days_until_next_birthday(born, today)
            print()
            show_age_card(born, today, ymd, d2n)
            print()
            again = prompt(t("TRY_ANOTHER")).strip().lower()
            if again not in {"y", "yes", "بله", "آره"}:
                return
        except Exception as e:
            print(colorize(t("ERR", e=e), Fore.RED))

def calculate_age_jalali_flow():
    if not JALALI_OK:
        print(colorize(t("NEED_JALALI"), Fore.RED))
        return
    today = get_current_date()
    if not plausible_year(today.year):
        print(colorize(t("FALLBACK_WARN"), Fore.RED))
    elif today != date.today():
        print(colorize(t("ONLINE_INFO"), Fore.BLUE))
    while True:
        raw = prompt(t("ENTER_BD_J")).strip()
        raw = normalize_digits(raw)
        if raw.lower() in {"b", "back"}:
            return
        try:
            jy, jm, jd_ = parse_jalali_tuple(raw)
            born_g = jtuple_to_gdate(jy, jm, jd_)
            ymd = age_ymd(born_g, today)
            d2n = days_until_next_birthday(born_g, today)
            print()
            show_age_card(born_g, today, ymd, d2n)
            print()
            again = prompt(t("TRY_ANOTHER")).strip().lower()
            if again not in {"y", "yes", "بله", "آره"}:
                return
        except Exception as e:
            print(colorize(t("ERR", e=e), Fore.RED))

def convert_jalali_to_gregorian_flow():
    if not JALALI_OK:
        print(colorize(t("NEED_JALALI"), Fore.RED))
        return
    while True:
        raw = prompt(t("J_DATE")).strip()
        raw = normalize_digits(raw)
        if raw.lower() in {"b", "back"}:
            return
        try:
            jy, jm, jd_ = parse_jalali_tuple(raw)
            g = jtuple_to_gregorian_safe(jy, jm, jd_)
            j = (jy, jm, jd_)
            print()
            show_convert_card(shape_if_needed(t("CONV_J2G")), g, j)
            print()
        except Exception as e:
            print(colorize(t("ERR", e=e), Fore.RED))

def convert_gregorian_to_jalali_flow():
    if not JALALI_OK:
        print(colorize(t("NEED_JALALI"), Fore.RED))
        return
    while True:
        raw = prompt(t("G_DATE")).strip()
        raw = normalize_digits(raw)
        if raw.lower() in {"b", "back"}:
            return
        try:
            g = parse_gregorian(raw)
            j = gdate_to_jtuple(g)
            print()
            show_convert_card(shape_if_needed(t("CONV_G2J")), g, j)
            print()
        except Exception as e:
            print(colorize(t("ERR", e=e), Fore.RED))

def jtuple_to_gregorian_safe(jy, jm, jd_):
    return jtuple_to_gdate(jy, jm, jd_)

# ---------- Language toggle ----------
def language_menu():
    global LANG
    print()
    print(title(t("LANG_MENU")))
    cur = t("LANG_FA") if LANG == "fa" else t("LANG_EN")
    alt = t("LANG_EN") if LANG == "fa" else t("LANG_FA")
    print(line(t("CUR_LANG"), colorize(cur, Fore.CYAN)))
    print(line(t("SWITCH_TO"), colorize(alt, Fore.GREEN)))
    print(BOX_BOTTOM)
    choice = prompt(("-> " if not is_rtl() else shape_if_needed("← ")) + "[1] " + (t("SWITCH_TO") + " " + alt) + " | [0] " + (t("EXIT") if LANG=="en" else t("EXIT")) + ": ")
    choice = normalize_digits(choice).strip()
    if choice == "1":
        LANG = "en" if LANG == "fa" else "fa"

# ---------- Main menu ----------
def main_menu():
    while True:
        print()
        print(title(t("MAIN_MENU")))
        # order reversed for RTL looks nicer: we print lines already right-justified
        print(line("1)", t("AGE_G_INPUT")))
        print(line("2)", t("AGE_J_INPUT")))
        print(line("3)", t("CONV_J2G")))
        print(line("4)", t("CONV_G2J")))
        print(line("5)", t("LANGUAGE") + " / Language"))
        print(line("0)", t("EXIT") + " / Exit"))
        print(BOX_BOTTOM)
        choice = prompt(t("SELECT"))
        choice = normalize_digits(choice).strip()
        if choice == "1":
            calculate_age_gregorian_flow()
        elif choice == "2":
            calculate_age_jalali_flow()
        elif choice == "3":
            convert_jalali_to_gregorian_flow()
        elif choice == "4":
            convert_gregorian_to_jalali_flow()
        elif choice == "5":
            language_menu()
        elif choice == "0":
            print(colorize(t("GOODBYE"), Fore.GREEN)); break
        else:
            print(colorize(t("INVALID"), Fore.RED))

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n" + colorize(t("INTERRUPTED"), Fore.GREEN))
        sys.exit(0)
