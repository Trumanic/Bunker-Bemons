#!/usr/bin/env python3
"""
==============================================================
  BUNKER BEMONS - RECORD MANAGER
  Add a record to a level, or remove one.
==============================================================

HOW TO USE
  1. Put this file in your website folder (the one with index.html).
  2. Open a terminal / command prompt in that folder.
  3. Run it:    python manage_records.py
                (if that doesn't work, try:  py manage_records.py)
  4. Answer the questions. Type  cancel  at any question to stop.

Every record counts as a 100% completion.
Nothing is saved until you confirm at the very end.
"""

import datetime
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------
#  SETTINGS  (you can change these)
# ---------------------------------------------------------------

# How many search results to show at once
MAX_SHOWN = 20

# ---------------------------------------------------------------
#  FILE LOCATIONS  (no need to touch)
# ---------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
LIST_FILE = DATA_DIR / "_list.json"
PLAYERS_FILE = DATA_DIR / "players.json"


# ===============================================================
#  SMALL HELPERS: talking to the user
# ===============================================================

class Cancelled(Exception):
    """Raised when the user types 'cancel' (or presses Ctrl+C)."""


def heading(text):
    print()
    print("=" * 62)
    print("  " + text)
    print("=" * 62)


def ask(question, hint=None, default=None, required=True, check=None):
    """
    Asks one question and returns the answer.
      hint     - a short help text shown above the question
      default  - used when the user just presses Enter
      required - if False, the user may leave it empty
      check    - a function that returns a problem message, or None if OK
    """
    if hint:
        print("  " + hint)
    shown_default = " [{}]".format(default) if default else ""
    while True:
        try:
            answer = input("> {}{}: ".format(question, shown_default)).strip()
        except (EOFError, KeyboardInterrupt):
            raise Cancelled()
        if answer.lower() == "cancel":
            raise Cancelled()
        if not answer and default is not None:
            answer = default
        if not answer:
            if required:
                print("  ! This can't be empty. Type something, or type cancel.")
                continue
            return ""
        problem = check(answer) if check else None
        if problem:
            print("  ! " + problem)
            continue
        return answer


def confirm(question, default=True):
    """Asks a yes/no question. Returns True for yes."""
    options = "Y/n" if default else "y/N"
    while True:
        answer = ask(question + " (" + options + ")", required=False).lower()
        if answer == "":
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  ! Please answer with y (yes) or n (no).")


def choose(question, options, default=None):
    """
    Shows a numbered menu and returns the position (0, 1, 2...) of the choice.
    default is a position too (or None for no default).
    """
    print()
    print(question)
    for i, option in enumerate(options, 1):
        print("  {}) {}".format(i, option))

    def check(text):
        if text.isdigit() and 1 <= int(text) <= len(options):
            return None
        return "Please type a number from 1 to {}.".format(len(options))

    default_text = str(default + 1) if default is not None else None
    answer = ask("Your choice", default=default_text, check=check)
    return int(answer) - 1


# ===============================================================
#  SMALL HELPERS: reading and saving the website's data files
# ===============================================================

def read_json(path):
    """Returns (data, raw_bytes). raw_bytes is used to keep the file's style."""
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8-sig")), raw

def format_json(data):
    """
    JSON text in the same style as the site's files: indented, with lists of
    names inside a level (creators, tags) kept on one line, like  ["a", "b"].
    (The top-level list in _list.json stays one name per line.)
    """
    text = json.dumps(data, indent=4, ensure_ascii=False)

    def one_line(match):
        items = re.findall(r'"(?:[^"\\]|\\.)*"', match.group(0))
        return "[" + ", ".join(items) + "]"

    return re.sub(
        r'(?<=": )\[\n\s+"(?:[^"\\]|\\.)*"(?:,\n\s+"(?:[^"\\]|\\.)*")*\n\s*\]',
        one_line, text)

def write_json(path, data, like=None):
    """
    Saves data as JSON, in the same style as the site's other files.
    If `like` (the old file's bytes) is given, its line endings are kept.
    The file is written to a temporary file first, so a crash can't corrupt it.
    """
    text = format_json(data)
    if like is None or like.endswith(b"\n"):
        text += "\n"
    if like is not None and b"\r\n" in like:
        text = text.replace("\n", "\r\n")
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(text.encode("utf-8"))
    temp.replace(path)


def load_levels():
    """Reads every level on the list. Each item: rank, file, data, raw."""
    order, _ = read_json(LIST_FILE)
    levels = []
    for rank, file_name in enumerate(order, 1):
        path = DATA_DIR / (file_name + ".json")
        data, raw = None, None
        if path.exists():
            try:
                data, raw = read_json(path)
            except ValueError:
                data, raw = None, None
        levels.append({"rank": rank, "file": file_name, "data": data, "raw": raw})
    return levels


def known_players(levels):
    """All player names we already know, as {lowercase: proper spelling}."""
    names = {}

    def add(name):
        name = (name or "").strip()
        if name and name.lower() not in names:
            names[name.lower()] = name

    if PLAYERS_FILE.exists():
        try:
            for name in read_json(PLAYERS_FILE)[0]:
                add(name)
        except ValueError:
            pass
    for level in levels:
        if level["data"]:
            add(level["data"].get("verifier"))
            for record in level["data"].get("records", []):
                add(record.get("user"))
    return names


# ===============================================================
#  PICKING A LEVEL FROM THE LIST
# ===============================================================

def level_label(level):
    data = level["data"]
    if not data:
        return "#{}  (missing file: {}.json)".format(level["rank"], level["file"])
    count = len(data.get("records", []))
    return "#{}  {}   ({} record{})".format(
        level["rank"], data["name"], count, "" if count == 1 else "s")


def search_levels(levels, query):
    query = query.strip().lower()
    if not query:
        return levels
    if re.fullmatch(r"#\d+", query):
        return [lv for lv in levels if lv["rank"] == int(query[1:])]
    found = []
    for lv in levels:
        data = lv["data"] or {}
        words = [str(data.get("name", "")), lv["file"], str(data.get("id", ""))]
        if any(query in word.lower() for word in words):
            found.append(lv)
    return found


def pick_level(levels, title="Select a level"):
    """Lets the user search the list and pick one level. Returns that level."""
    print()
    print(title)
    print("  Type part of the level's name to search (example: ach),")
    print("  or a rank like #12. Press Enter to see the top of the list.")
    while True:
        query = ask("Search", required=False)
        matches = [lv for lv in search_levels(levels, query) if lv["data"]]
        if not matches:
            print("  ! Nothing found. Try fewer letters.")
            continue

        shown = matches[:MAX_SHOWN]
        for i, level in enumerate(shown, 1):
            print("  {:>2}) {}".format(i, level_label(level)))
        if len(matches) > MAX_SHOWN:
            print("  ... and {} more. Type more letters to narrow it down."
                  .format(len(matches) - MAX_SHOWN))

        def check(text):
            if text.isdigit() and 1 <= int(text) <= len(shown):
                return None
            return "Please type a number from 1 to {}.".format(len(shown))

        default = "1" if len(shown) == 1 else None
        answer = ask("Number to pick (press Enter to search again)",
                     default=default, required=False, check=check)
        if answer:
            return shown[int(answer) - 1]


def save_level(level):
    """Saves a level's file again (keeping its original style)."""
    write_json(DATA_DIR / (level["file"] + ".json"), level["data"], like=level["raw"])


# ===============================================================
#  ADD A RECORD
# ===============================================================

def add_record():
    heading("ADD A RECORD")
    levels = load_levels()
    if not [lv for lv in levels if lv["data"]]:
        print("  There are no levels on the list yet.")
        return
    players = known_players(levels)

    # ---- 1. Select the level -------------------------------------
    level = pick_level(levels, title="1/4  Select the level")
    data = level["data"]
    print("\n  Level: " + level_label(level))

    # ---- 2. Player -----------------------------------------------
    taken = {r["user"].lower() for r in data.get("records", [])}

    def check_user(text):
        if text.lower() in taken:
            return "{} already has a record on this level.".format(text)
        return None

    print()
    print("  The player who beat the level. Example: Amine")
    if players:
        print("  Players already on the site: "
              + ", ".join(sorted(players.values(), key=str.lower)))
    while True:
        user = ask("2/4  Player", check=check_user)
        if user.lower() in players:
            user = players[user.lower()]  # use the usual spelling
        else:
            if not confirm("  '{}' isn't on the site yet. Add them as a new player?"
                           .format(user), default=False):
                continue
        verifier = (data.get("verifier") or "").strip().lower()
        if verifier and user.lower() == verifier and not confirm(
                "  {} is this level's verifier. Adding a record too would count "
                "the level twice for them. Continue?".format(user), default=False):
            continue
        break

    # ---- 3. Video link -------------------------------------------
    def check_link(text):
        if re.match(r"^https?://\S+$", text):
            return None
        return ("That doesn't look like a link. It should start with "
                "https:// (example: https://www.youtube.com/watch?v=...)")

    print()
    link = ask("3/4  Video link",
               hint="Optional: press Enter to skip (the site will show a '-' instead of 'Watch').",
               required=False, check=check_link)

    
    # ---- 4. Date -------------------------------------------------
    today_dt = datetime.date.today()
    today = "{}/{}/{}".format(today_dt.day, today_dt.month, today_dt.year)

    def parse_user_date(text):
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.datetime.strptime(text, fmt).date()
            except ValueError:
                pass
        return None

    def check_date(text):
        if parse_user_date(text) is None:
            return "Please use the format D/M/YYYY (example: 28/4/2026)."
        return None


    print()
    print("4/4  Date of the record")
    while True:
        way = choose("How do you want to set the date?",
                     ["Use today's date ({})".format(today), "Type a date"],
                     default=0)
        if way == 0:
            date = today
            break
        dt = parse_user_date(
            ask("Date (D/M/YYYY)", hint="Example: 28/4/2026", check=check_date))
        date = "{}/{}/{}".format(dt.day, dt.month, dt.year)
        if dt > today_dt and not confirm(
                "  {} is in the future. Use it anyway?".format(date), default=False):
            continue
        break

    # ---- Summary + confirmation ----------------------------------
    print()
    print("-" * 62)
    print("  Here is the record you are about to add:")
    print("-" * 62)
    print("  Level:   " + level_label(level))
    print("  Player:  " + user)
    print("  Video:   " + (link or "(none)"))
    print("  Date:    " + date)
    print()
    if not confirm("Save this record?"):
        raise Cancelled()

    # ---- Save ----------------------------------------------------
    data.setdefault("records", []).append({"user": user, "link": link, "date": date})
    try:
        save_level(level)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        print("  Nothing was changed. Is the file open in another program?")
        return

    print()
    print("  Done! {}'s record was added to {}.".format(user, data["name"]))


# ===============================================================
#  REMOVE A RECORD
# ===============================================================

def remove_record():
    heading("REMOVE A RECORD")
    levels = load_levels()
    with_records = [lv for lv in levels if lv["data"] and lv["data"].get("records")]
    if not with_records:
        print("  No level has any records yet - there is nothing to remove.")
        return

    # ---- 1. Select the level (only levels that have records) -----
    level = pick_level(with_records, title="1/2  Select the level")
    data = level["data"]
    records = data["records"]

    # ---- 2. Select the player ------------------------------------
    print("\n  Level: " + level_label(level))
    print()
    print("2/2  Whose record do you want to remove?")
    for i, record in enumerate(records, 1):
        print("  {:>2}) {}   ({})".format(i, record["user"], record.get("date", "no date")))

    def find(text):
        if text.isdigit() and 1 <= int(text) <= len(records):
            return int(text) - 1
        for i, record in enumerate(records):
            if record["user"].lower() == text.lower():
                return i
        return None

    answer = ask("Player (type their number or their name)",
                 check=lambda s: None if find(s) is not None
                 else "Please type a number from 1 to {}, or a name from the list."
                 .format(len(records)))
    record = records[find(answer)]

    # ---- Summary + confirmation ----------------------------------
    print()
    print("-" * 62)
    print("  You are about to remove this record:")
    print("-" * 62)
    print("  Level:   " + level_label(level))
    print("  Player:  " + record["user"])
    print("  Video:   " + (record.get("link") or "(none)"))
    print("  Date:    " + str(record.get("date", "")))
    print()
    if not confirm("Remove this record?", default=False):
        raise Cancelled()

    # ---- Save ----------------------------------------------------
    records.remove(record)
    try:
        save_level(level)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        print("  Nothing was changed. Is the file open in another program?")
        return

    print()
    print("  Done! {}'s record was removed from {}.".format(record["user"], data["name"]))


# ===============================================================
#  MAIN MENU
# ===============================================================

def main():
    if not LIST_FILE.exists():
        print("Couldn't find data/_list.json next to this script.")
        print("Put manage_records.py in your website folder (next to index.html).")
        return

    heading("BUNKER BEMONS - RECORD MANAGER")
    print("  Tip: type  cancel  at any question to go back without saving.")

    while True:
        try:
            choice = choose("What would you like to do?",
                            ["Add a record", "Remove a record", "Quit"])
        except Cancelled:
            break
        if choice == 2:
            break
        try:
            add_record() if choice == 0 else remove_record()
        except Cancelled:
            print("\n  Cancelled - nothing was changed.")
        except (ValueError, KeyError) as error:
            print("\n  ! A data file looks broken: {}".format(error))
            print("  Nothing was changed.")

    print("\nBye!")


if __name__ == "__main__":
    try:
        main()
    finally:
        # Keeps the window open if you started this by double-clicking it
        if sys.stdin and sys.stdin.isatty():
            try:
                input("\nPress Enter to close...")
            except (EOFError, KeyboardInterrupt):
                pass