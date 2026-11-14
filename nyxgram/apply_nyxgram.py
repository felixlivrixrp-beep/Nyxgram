#!/usr/bin/env python3
"""Turns a fresh AyuGram Desktop checkout into Nyxgram.

Usage: python apply_nyxgram.py <path-to-AyuGramDesktop-checkout>

Only user-visible things are changed (names, texts, icons). Internal identifiers,
file names and the application id are deliberately left alone, so the code keeps
building exactly like the original.
"""
import re
import shutil
import sys
from pathlib import Path

NEW = "Nyxgram"
HERE = Path(__file__).resolve().parent


def read(path):
    return path.read_text(encoding="utf-8")


def write(path, text):
    path.write_text(text, encoding="utf-8", newline="")


def sub_once(path, old, new):
    text = read(path)
    if old not in text:
        raise SystemExit(f"[!] pattern not found in {path}: {old!r}")
    write(path, text.replace(old, new))
    print(f"[ok] {path.name}: {old!r} -> {new!r}")


def brand_words(text):
    """AyuGram -> Nyxgram in visible text only.

    Never touches identifiers (AyuGramDesktop, ayu_UpdateAyuGram) or URL parts
    (github.com/AyuGram/...)."""
    return re.sub(r"(?<![\w/.])AyuGram(?![\w/])", NEW, text)


def main(src):
    src = Path(src)
    tg = src / "Telegram"
    if not (tg / "SourceFiles" / "core" / "version.h").exists():
        raise SystemExit("not an AyuGram Desktop checkout: " + str(src))

    # 1. Application name (window titles, tray, notifications, data folder name)
    sub_once(tg / "SourceFiles/core/version.h",
             'AppName = "AyuGram Desktop"_cs', f'AppName = "{NEW} Desktop"_cs')

    # 2. Windows file properties
    for rc in ("Telegram.rc", "Updater.rc"):
        p = tg / "Resources/winrc" / rc
        write(p, read(p).replace("AyuGram Desktop", f"{NEW} Desktop"))
        print(f"[ok] {rc}")

    # 3. Interface texts
    langs = tg / "Resources/langs/lang.strings"
    special = {
        "ayu_SettingsWatermark":
            f"{NEW} is based on AyuGram Desktop by Radolyn Labs and Telegram Desktop.",
        "ayu_FirstLaunchAlert":
            f"{NEW} is **free** software and is not affiliated with Telegram. "
            "You assume **full responsibility** for using this application with your account.",
        "ayu_ExteraChatsAlert":
            f"{NEW} is an unofficial mod. Please do not ask questions about it in Telegram or AyuGram support chats.",
    }
    keep = ("ayu_SupporterPopup", "ayu_OfficialResourcePopup")  # describe AyuGram/exteraGram badges
    out, changed = [], 0
    for line in read(langs).split("\n"):
        m = re.match(r'"(ayu_[A-Za-z0-9_]+)"\s*=\s*"', line)
        if m and m.group(1) in special:
            line = f'"{m.group(1)}" = "{special[m.group(1)]}";'
            changed += 1
        elif m and "AyuGram" in line and m.group(1) not in keep:
            key, sep, value = line.partition("=")      # the key must stay untouched
            new_line = key + sep + brand_words(value)
            if new_line != line:
                line = new_line
                changed += 1
        out.append(line)
    write(langs, "\n".join(out))
    print(f"[ok] lang.strings: {changed} lines")

    # 4. A few hard-coded display strings
    sub_once(tg / "SourceFiles/core/application.cpp",
             '.shortAppName = u"AyuGram"_q', f'.shortAppName = u"{NEW}"_q')
    for name in ("crash_report_window.cpp", "crash_reports.cpp"):
        p = tg / "SourceFiles/core" / name
        write(p, brand_words(read(p)))
        print(f"[ok] {name}")

    # 5. Icons (same file names and sizes as the originals)
    art = tg / "Resources/art"
    n = 0
    for icon in sorted((HERE / "icons").iterdir()):
        if (art / icon.name).exists():
            shutil.copyfile(icon, art / icon.name)
            n += 1
        else:
            print(f"[!] no such target icon: {icon.name}")
    print(f"[ok] icons: {n} files")
    print("Nyxgram patch applied.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
