#!/usr/bin/env python3
"""
==============================================================
  BUNKER BEMONS - LEVEL MANAGER
  Add a new level, remove a level, or move a level to a new rank.
==============================================================

HOW TO USE
  1. Put this file in your website folder (the one with index.html).
  2. Open a terminal / command prompt in that folder.
  3. Run it:    python manage_levels.py
                (if that doesn't work, try:  py manage_levels.py)
  4. Answer the questions. Type  cancel  at any question to stop.

Nothing is saved until you confirm at the very end.
"""

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------
#  SETTINGS  (you can change these)
# ---------------------------------------------------------------

# The choices shown for "Level Difficulty"
DIFFICULTIES = [
    "Easy Demon",
    "Medium Demon",
    "Hard Demon",
    "Insane Demon",
    "Extreme Demon",
]
DEFAULT_DIFFICULTY = "Extreme Demon"

# How many search results to show at once
MAX_SHOWN = 20

# Points for the #1 level and the last level (used to show points when moving
# a level). Keep these the same as in js/score.js.
MAX_POINTS = 100
MIN_POINTS = 1

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


def load_order():
    """Reads data/_list.json: the level file names, in rank order."""
    order, raw = read_json(LIST_FILE)
    return order, raw


def load_levels(order):
    """Reads every level on the list. Each item: rank, file, data."""
    levels = []
    for rank, file_name in enumerate(order, 1):
        path = DATA_DIR / (file_name + ".json")
        data = None
        if path.exists():
            try:
                data = read_json(path)[0]
            except ValueError:
                data = None
        levels.append({"rank": rank, "file": file_name, "data": data})
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
    if level["data"]:
        return "#{}  {}".format(level["rank"], level["data"]["name"])
    return "#{}  (missing file: {}.json)".format(level["rank"], level["file"])


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
        matches = search_levels(levels, query)
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


# ===============================================================
#  ADD A LEVEL
# ===============================================================

def split_list(text):
    """'a, b,  c' -> ['a', 'b', 'c']  (no empty items, no repeats)"""
    items = []
    for part in text.split(","):
        part = part.strip()
        if part and part.lower() not in [i.lower() for i in items]:
            items.append(part)
    return items


def make_file_name(name, order):
    """'Sonic Wave' -> 'sonic_wave' (adds _2, _3... if that name is taken)."""
    base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "level"
    taken = {o.lower() for o in order}
    candidate, number = base, 2
    while candidate in taken or (DATA_DIR / (candidate + ".json")).exists():
        candidate = "{}_{}".format(base, number)
        number += 1
    return candidate


def add_level():
    heading("ADD A LEVEL")
    order, order_raw = load_order()
    levels = load_levels(order)
    players = known_players(levels)

    # ---- 1. Level name -------------------------------------------
    print()
    name = " ".join(ask("1/9  Level name", hint="Example: Acheron").split())
    same_name = [lv for lv in levels
                 if lv["data"] and lv["data"]["name"].lower() == name.lower()]
    if same_name and not confirm(
            "  A level called '{}' is already on the list (#{}). Add another one anyway?"
            .format(name, same_name[0]["rank"]), default=False):
        raise Cancelled()

    # ---- 2. Level ID ---------------------------------------------
    print()
    level_id = ask(
        "2/9  Level ID",
        hint="The number from Geometry Dash. Example: 62214792",
        check=lambda s: None if s.isdigit() else "The ID must be numbers only.",
    )
    same_id = [lv for lv in levels
               if lv["data"] and str(lv["data"]["id"]) == level_id]
    if same_id and not confirm(
            "  The ID {} is already used by '{}' (#{}). Use it anyway?"
            .format(level_id, same_id[0]["data"]["name"], same_id[0]["rank"]),
            default=False):
        raise Cancelled()

    # ---- 3. Publisher --------------------------------------------
    print()
    publisher = ask(
        "3/9  Level publisher",
        hint="The player who uploaded the level. Type - if you don't know.",
    )

    # ---- 4. Creators ---------------------------------------------
    print()
    creators = split_list(ask(
        "4/9  Level creators",
        hint="Separate names with commas. Example: Zoink, Npesta\n"
             "  Leave empty if the publisher is the only creator.",
        required=False,
    ))

    # ---- 5. Verifier ---------------------------------------------
    print()
    verifier = ""
    while True:
        verifier = ask(
            "5/9  Level verifier",
            hint="Only type a name if they are in your friend group (they get\n"
                 "  leaderboard points). Leave empty otherwise.",
            required=False,
        )
        if not verifier:
            break
        if verifier.lower() in players:
            verifier = players[verifier.lower()]  # use the usual spelling
            break
        if confirm("  '{}' isn't on the leaderboard yet. Add them as a new player?"
                   .format(verifier), default=False):
            break

    # ---- 6. Difficulty -------------------------------------------
    difficulties = list(DIFFICULTIES)
    for lv in levels:  # also offer any other difficulty already used on the site
        found = lv["data"] and lv["data"].get("difficulty")
        if found and found not in difficulties:
            difficulties.append(found)
    default_index = (difficulties.index(DEFAULT_DIFFICULTY)
                     if DEFAULT_DIFFICULTY in difficulties else 0)
    difficulty = difficulties[
        choose("6/9  Level difficulty", difficulties, default=default_index)]

    # ---- 7. Verification video -----------------------------------
    def check_link(text):
        if re.match(r"^https?://\S+$", text):
            return None
        return ("That doesn't look like a link. It should start with "
                "https:// (example: https://www.youtube.com/watch?v=...)")

    print()
    while True:
        link = ask("7/9  Verification video link",
                   hint="The YouTube video of the level being verified.",
                   check=check_link)
        if "youtube.com" in link or "youtu.be" in link:
            break
        if confirm("  This isn't a YouTube link, so the video won't play on the "
                   "level page. Use it anyway?", default=False):
            break

    # ---- 8. Tags -------------------------------------------------
    existing_tags = []
    for lv in levels:
        for tag in (lv["data"] or {}).get("tags", []):
            if tag.lower() not in [t.lower() for t in existing_tags]:
                existing_tags.append(tag)
    print()
    tag_hint = "Separate with commas. Example: Wave, Memory. Leave empty for none."
    if existing_tags:
        tag_hint += "\n  Tags already in use: " + ", ".join(sorted(existing_tags))
    tags = split_list(ask("8/9  Level tags", hint=tag_hint, required=False))

    # ---- 9. Position on the list ---------------------------------
    total = len(levels)
    print()
    print("9/9  Position on the list")
    print("  The list has {} levels. Rank 1 is the hardest.".format(total))
    print("  (The level goes wherever you choose, so the ranking is up to you.)")

    def check_rank(text):
        if text.isdigit() and 1 <= int(text) <= total + 1:
            return None
        return "Please type a rank from 1 to {}.".format(total + 1)

    position = int(ask(
        "Rank for this level (press Enter for the very bottom)",
        default=str(total + 1), check=check_rank,
    ))
    above = levels[position - 2] if position >= 2 else None
    below = levels[position - 1] if position <= total else None

    # ---- Summary + confirmation ----------------------------------
    file_name = make_file_name(name, order)
    print()
    print("-" * 62)
    print("  Here is the level you are about to add:")
    print("-" * 62)
    print("  Name:          " + name)
    print("  ID:            " + level_id)
    print("  Publisher:     " + publisher)
    print("  Creators:      " + (", ".join(creators) or "(none)"))
    print("  Verifier:      " + (verifier or "(none)"))
    print("  Difficulty:    " + difficulty)
    print("  Video:         " + link)
    print("  Tags:          " + (", ".join(tags) or "(none)"))
    print("  Rank:          #{}".format(position))
    if above:
        print("                 right below  {}".format(level_label(above)))
    if below:
        print("                 right above  {}".format(level_label(below)))
    print("  File:          data/{}.json".format(file_name))
    if below:
        print()
        print("  Note: every level from #{} down moves one rank lower,".format(position))
        print("  so those levels' points (and the leaderboard) will change a little.")
    print()
    if not confirm("Save this level?"):
        raise Cancelled()

    # ---- Save ----------------------------------------------------
    new_level = {
        "id": int(level_id),
        "name": name,
        "author": publisher,
        "creators": creators,
        "verifier": verifier,
        "difficulty": difficulty,
        "verification": link,
        "tags": tags,
        "records": [],
    }
    level_path = DATA_DIR / (file_name + ".json")
    try:
        write_json(level_path, new_level)
        order.insert(position - 1, file_name)
        write_json(LIST_FILE, order, like=order_raw)
    except OSError as error:
        if level_path.exists() and file_name not in order:
            level_path.unlink()
        print("\n  ! Could not save: {}".format(error))
        print("  Nothing was changed. Is one of the files open in another program?")
        return

    print()
    print("  Done! '{}' was added at #{}.".format(name, position))
    print("  To add records to it, run:  python manage_records.py")


# ===============================================================
#  REMOVE A LEVEL
# ===============================================================

def remove_level():
    heading("REMOVE A LEVEL")
    order, order_raw = load_order()
    levels = load_levels(order)
    if not levels:
        print("  The list is empty - there is nothing to remove.")
        return

    # ---- 1. Select the level -------------------------------------
    level = pick_level(levels, title="1/2  Select the level to remove")
    data = level["data"]

    print()
    print("-" * 62)
    print("  You selected:  " + level_label(level))
    if data:
        print("  Level ID:      {}".format(data["id"]))
        print("  Publisher:     " + str(data.get("author", "")))
        count = len(data.get("records", []))
        print("  Records:       {}".format(count))
        if count:
            print("  ! Removing this level also deletes its {} record(s)."
                  .format(count))
    print("-" * 62)

    # ---- 2. Confirm by typing its ID -----------------------------
    token = str(data["id"]) if data else level["file"]
    what = "level ID" if data else "file name"
    print()
    print("2/2  To make sure this is the right level, type its {}.".format(what))
    ask("Type {} to remove it (or cancel)".format(token),
        check=lambda s: None if s.strip() == token
        else "That doesn't match {}. Try again, or type cancel.".format(token))

    # ---- Remove --------------------------------------------------
    try:
        order.pop(level["rank"] - 1)
        write_json(LIST_FILE, order, like=order_raw)
        level_file = DATA_DIR / (level["file"] + ".json")
        if level_file.exists():
            level_file.unlink()
    except OSError as error:
        print("\n  ! Could not remove it: {}".format(error))
        print("  Is one of the files open in another program?")
        return

    print()
    print("  Done! {} was removed.".format(level_label(level)))
    if level["rank"] <= len(order):
        print("  Every level below it moved up one rank, so points changed a little.")

# ===============================================================
#  MOVE A LEVEL (change its rank)
# ===============================================================

def points_for(rank, total):
    """Points a level is worth at a given rank (same formula as the site)."""
    if total <= 1:
        return MAX_POINTS
    step = (MAX_POINTS - MIN_POINTS) / (total - 1)
    return round(MAX_POINTS - (rank - 1) * step, 3)


def level_name(level):
    return level["data"]["name"] if level["data"] else level["file"] + ".json"


def move_level():
    heading("MOVE A LEVEL")
    order, order_raw = load_order()
    levels = load_levels(order)
    total = len(levels)
    if total < 2:
        print("  You need at least 2 levels on the list to move one.")
        return

    # ---- 1. Select the level -------------------------------------
    level = pick_level(levels, title="1/2  Select the level to move")
    old_rank = level["rank"]
    print()
    print("  Selected: " + level_label(level))

    # ---- 2. New rank ---------------------------------------------
    print()
    print("2/2  Where should it go?")
    print("  The list has {} levels. Rank 1 is the hardest.".format(total))
    print("  A smaller number = raised (harder).  A bigger number = lowered (easier).")

    def check_rank(text):
        if not (text.isdigit() and 1 <= int(text) <= total):
            return "Please type a rank from 1 to {}.".format(total)
        if int(text) == old_rank:
            return "It is already at #{}. Type a different rank.".format(old_rank)
        return None

    new_rank = int(ask("New rank for {}".format(level_name(level)), check=check_rank))
    steps = abs(new_rank - old_rank)
    raised = new_rank < old_rank

    # What the list will look like around the new spot
    others = [lv for lv in levels if lv is not level]
    above = others[new_rank - 2] if new_rank >= 2 else None
    below = others[new_rank - 1] if new_rank <= len(others) else None

    # ---- Summary + confirmation ----------------------------------
    print()
    print("-" * 62)
    print("  Level:     " + level_name(level))
    if raised:
        print("  Move:      RAISED  #{} -> #{}   ({} spot{} up the list)"
              .format(old_rank, new_rank, steps, "" if steps == 1 else "s"))
        print("  Affects:   levels #{} to #{} each move down one rank."
              .format(new_rank, old_rank - 1))
    else:
        print("  Move:      LOWERED  #{} -> #{}   ({} spot{} down the list)"
              .format(old_rank, new_rank, steps, "" if steps == 1 else "s"))
        print("  Affects:   levels #{} to #{} each move up one rank."
              .format(old_rank + 1, new_rank))
    print("  Points:    {} -> {}".format(points_for(old_rank, total),
                                         points_for(new_rank, total)))
    if above:
        print("  New spot:  right below  " + level_name(above))
    if below:
        print("             right above  " + level_name(below))
    print("-" * 62)
    print("  The other levels' points change a little too, so the leaderboard will shift.")
    print()
    if not confirm("Move this level?"):
        raise Cancelled()

    # ---- Save ----------------------------------------------------
    try:
        order.pop(old_rank - 1)
        order.insert(new_rank - 1, level["file"])
        write_json(LIST_FILE, order, like=order_raw)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        print("  Nothing was changed. Is the file open in another program?")
        return

    print()
    print("  Done! {} was {} from #{} to #{}.".format(
        level_name(level), "raised" if raised else "lowered", old_rank, new_rank))
# ===============================================================
#  MAIN MENU
# ===============================================================

def main():
    if not LIST_FILE.exists():
        print("Couldn't find data/_list.json next to this script.")
        print("Put manage_levels.py in your website folder (next to index.html).")
        return

    heading("BUNKER BEMONS - LEVEL MANAGER")
    print("  Tip: type  cancel  at any question to go back without saving.")

    while True:
        try:
                        choice = choose("What would you like to do?",
                            ["Add a level", "Remove a level",
                             "Move a level (change its rank)", "Quit"])
        except Cancelled:
            break
        if choice == 3:
            break
        try:
            if choice == 0:
                add_level()
            elif choice == 1:
                remove_level()
            else:
                move_level()
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