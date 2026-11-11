#!/usr/bin/env python3
"""
==============================================================
  BUNKER BEMONS - UNIFIED MANAGER
  Manage levels, records, and players for your website.
==============================================================

HOW TO USE
  1. Put this file in your website folder (the one with index.html).
  2. Open a terminal / command prompt in that folder.
  3. Run it:    python manage.py
                (if that doesn't work, try:  py manage.py)
  4. Answer the questions. Type  cancel  at any question to stop.

Nothing is saved until you confirm at the very end.
"""

import urllib.request
import urllib.parse
import datetime
import json
import re
import shutil
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

# Picture types the site can show
PFP_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

# ---------------------------------------------------------------
#  FILE LOCATIONS  (no need to touch)
# ---------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
LIST_FILE = DATA_DIR / "_list.json"
PLAYERS_FILE = DATA_DIR / "players.json"
PFP_DIR = ROOT / "assets" / "pfps"

# ---------------------------------------------------------------
#  COUNTRIES  (code -> name, the same names the website shows)
# ---------------------------------------------------------------

COUNTRIES = {
    "ad": "Andorra", "ae": "United Arab Emirates", "af": "Afghanistan",
    "ag": "Antigua & Barbuda", "ai": "Anguilla", "al": "Albania",
    "am": "Armenia", "ao": "Angola", "aq": "Antarctica", "ar": "Argentina",
    "as": "American Samoa", "at": "Austria", "au": "Australia", "aw": "Aruba",
    "ax": "Åland Islands", "az": "Azerbaijan", "ba": "Bosnia & Herzegovina",
    "bb": "Barbados", "bd": "Bangladesh", "be": "Belgium",
    "bf": "Burkina Faso", "bg": "Bulgaria", "bh": "Bahrain", "bi": "Burundi",
    "bj": "Benin", "bl": "St. Barthélemy", "bm": "Bermuda", "bn": "Brunei",
    "bo": "Bolivia", "bq": "Caribbean Netherlands", "br": "Brazil",
    "bs": "Bahamas", "bt": "Bhutan", "bv": "Bouvet Island", "bw": "Botswana",
    "by": "Belarus", "bz": "Belize", "ca": "Canada",
    "cc": "Cocos (Keeling) Islands", "cd": "Congo - Kinshasa",
    "cf": "Central African Republic", "cg": "Congo - Brazzaville",
    "ch": "Switzerland", "ci": "Côte d’Ivoire", "ck": "Cook Islands",
    "cl": "Chile", "cm": "Cameroon", "cn": "China", "co": "Colombia",
    "cp": "Clipperton Island", "cr": "Costa Rica", "cu": "Cuba",
    "cv": "Cape Verde", "cw": "Curaçao", "cx": "Christmas Island",
    "cy": "Cyprus", "cz": "Czechia", "de": "Germany", "dg": "Diego Garcia",
    "dj": "Djibouti", "dk": "Denmark", "dm": "Dominica",
    "do": "Dominican Republic", "dz": "Algeria", "ec": "Ecuador",
    "ee": "Estonia", "eg": "Egypt", "eh": "Western Sahara", "er": "Eritrea",
    "es": "Spain", "es-ct": "Catalonia", "es-ga": "Galicia",
    "es-pv": "Basque Country", "et": "Ethiopia", "eu": "European Union",
    "fi": "Finland", "fj": "Fiji", "fk": "Falkland Islands",
    "fm": "Micronesia", "fo": "Faroe Islands", "fr": "France", "ga": "Gabon",
    "gb": "United Kingdom", "gb-eng": "England", "gb-nir": "Northern Ireland",
    "gb-sct": "Scotland", "gb-wls": "Wales", "gd": "Grenada", "ge": "Georgia",
    "gf": "French Guiana", "gg": "Guernsey", "gh": "Ghana", "gi": "Gibraltar",
    "gl": "Greenland", "gm": "Gambia", "gn": "Guinea", "gp": "Guadeloupe",
    "gq": "Equatorial Guinea", "gr": "Greece",
    "gs": "South Georgia & South Sandwich Islands", "gt": "Guatemala",
    "gu": "Guam", "gw": "Guinea-Bissau", "gy": "Guyana",
    "hk": "Hong Kong SAR China", "hm": "Heard & McDonald Islands",
    "hn": "Honduras", "hr": "Croatia", "ht": "Haiti", "hu": "Hungary",
    "ic": "Canary Islands", "id": "Indonesia", "ie": "Ireland",
    "il": "Israel", "im": "Isle of Man", "in": "India",
    "io": "British Indian Ocean Territory", "iq": "Iraq", "ir": "Iran",
    "is": "Iceland", "it": "Italy", "je": "Jersey", "jm": "Jamaica",
    "jo": "Jordan", "jp": "Japan", "ke": "Kenya", "kg": "Kyrgyzstan",
    "kh": "Cambodia", "ki": "Kiribati", "km": "Comoros",
    "kn": "St. Kitts & Nevis", "kp": "North Korea", "kr": "South Korea",
    "kw": "Kuwait", "ky": "Cayman Islands", "kz": "Kazakhstan", "la": "Laos",
    "lb": "Lebanon", "lc": "St. Lucia", "li": "Liechtenstein",
    "lk": "Sri Lanka", "lr": "Liberia", "ls": "Lesotho", "lt": "Lithuania",
    "lu": "Luxembourg", "lv": "Latvia", "ly": "Libya", "ma": "Morocco",
    "mc": "Monaco", "md": "Moldova", "me": "Montenegro", "mf": "St. Martin",
    "mg": "Madagascar", "mh": "Marshall Islands", "mk": "North Macedonia",
    "ml": "Mali", "mm": "Myanmar (Burma)", "mn": "Mongolia",
    "mo": "Macao SAR China", "mp": "Northern Mariana Islands",
    "mq": "Martinique", "mr": "Mauritania", "ms": "Montserrat", "mt": "Malta",
    "mu": "Mauritius", "mv": "Maldives", "mw": "Malawi", "mx": "Mexico",
    "my": "Malaysia", "mz": "Mozambique", "na": "Namibia",
    "nc": "New Caledonia", "ne": "Niger", "nf": "Norfolk Island",
    "ng": "Nigeria", "ni": "Nicaragua", "nl": "Netherlands", "no": "Norway",
    "np": "Nepal", "nr": "Nauru", "nu": "Niue", "nz": "New Zealand",
    "om": "Oman", "pa": "Panama", "pe": "Peru",
    "pf": "French Polynesia", "pg": "Papua New Guinea", "ph": "Philippines",
    "pk": "Pakistan", "pl": "Poland", "pm": "St. Pierre & Miquelon",
    "pn": "Pitcairn Islands", "pr": "Puerto Rico",
    "ps": "Palestinian Territories", "pt": "Portugal", "pw": "Palau",
    "py": "Paraguay", "qa": "Qatar", "re": "Réunion", "ro": "Romania",
    "rs": "Serbia", "ru": "Russia", "rw": "Rwanda", "sa": "Saudi Arabia",
    "sb": "Solomon Islands", "sc": "Seychelles", "sd": "Sudan",
    "se": "Sweden", "sg": "Singapore", "sh": "St. Helena", "si": "Slovenia",
    "sj": "Svalbard & Jan Mayen", "sk": "Slovakia", "sl": "Sierra Leone",
    "sm": "San Marino", "sn": "Senegal", "so": "Somalia", "sr": "Suriname",
    "ss": "South Sudan", "st": "São Tomé & Príncipe", "sv": "El Salvador",
    "sx": "Sint Maarten", "sy": "Syria", "sz": "Eswatini",
    "tc": "Turks & Caicos Islands", "td": "Chad",
    "tf": "French Southern Territories", "tg": "Togo", "th": "Thailand",
    "tj": "Tajikistan", "tk": "Tokelau", "tl": "Timor-Leste",
    "tm": "Turkmenistan", "tn": "Tunisia", "to": "Tonga", "tr": "Turkey",
    "tt": "Trinidad & Tobago", "tv": "Tuvalu", "tw": "Taiwan",
    "tz": "Tanzania", "ua": "Ukraine", "ug": "Uganda",
    "um": "U.S. Outlying Islands", "un": "United Nations",
    "us": "United States", "uy": "Uruguay", "uz": "Uzbekistan",
    "va": "Vatican City", "vc": "St. Vincent & Grenadines", "ve": "Venezuela",
    "vg": "British Virgin Islands", "vi": "U.S. Virgin Islands",
    "vn": "Vietnam", "vu": "Vanuatu", "wf": "Wallis & Futuna", "ws": "Samoa",
    "xk": "Kosovo", "ye": "Yemen", "yt": "Mayotte", "za": "South Africa",
    "zm": "Zambia", "zw": "Zimbabwe",
}

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


def choose_many(question, options):
    print()
    print(question)
    for i, option in enumerate(options, 1):
        print("  {}) {}".format(i, option))

    def parse(text):
        if text.lower() == "all":
            return list(range(len(options)))
        picked = []
        for part in text.replace(" ", "").split(","):
            if not (part.isdigit() and 1 <= int(part) <= len(options)):
                return None
            if int(part) - 1 not in picked:
                picked.append(int(part) - 1)
        return sorted(picked) if picked else None

    answer = ask("Your choice (example: 1,3  or  all)",
                 check=lambda s: None if parse(s) is not None
                 else "Please type numbers from 1 to {} separated by commas, or all."
                 .format(len(options)))
    return parse(answer)


# ===============================================================
#  SMALL HELPERS: reading and saving the website's data files
# ===============================================================

def read_json(path):
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8-sig")), raw


def save_text(path, text, like=None):
    if like is None or like.endswith(b"\n"):
        text += "\n"
    if like is not None and b"\r\n" in like:
        text = text.replace("\n", "\r\n")
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(text.encode("utf-8"))
    temp.replace(path)


def format_json(data):
    text = json.dumps(data, indent=4, ensure_ascii=False)

    def one_line(match):
        items = re.findall(r'"(?:[^"\\]|\\.)*"', match.group(0))
        return "[" + ", ".join(items) + "]"

    return re.sub(
        r'(?<=": )\[\n\s+"(?:[^"\\]|\\.)*"(?:,\n\s+"(?:[^"\\]|\\.)*")*\n\s*\]',
        one_line, text)


def write_json(path, data, like=None):
    save_text(path, format_json(data), like)


def load_order():
    order, raw = read_json(LIST_FILE)
    return order, raw


def load_levels(order=None):
    if order is None:
        order, _ = load_order()
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


def save_level(level):
    write_json(DATA_DIR / (level["file"] + ".json"), level["data"], like=level["raw"])


def load_players():
    if not PLAYERS_FILE.exists():
        return {}, None
    data, raw = read_json(PLAYERS_FILE)
    players = {}
    for name, info in data.items():
        players[name] = dict(info) if isinstance(info, dict) else {}
    return players, raw


def save_players(players, raw):
    if not players:
        save_text(PLAYERS_FILE, "{}", raw)
        return
    lines = []
    for name, info in players.items():
        inner = ", ".join(
            json.dumps(key, ensure_ascii=False) + ": " + json.dumps(value, ensure_ascii=False)
            for key, value in info.items())
        body = "{ " + inner + " }" if inner else "{}"
        lines.append("    " + json.dumps(name, ensure_ascii=False) + ": " + body)
    save_text(PLAYERS_FILE, "{\n" + ",\n".join(lines) + "\n}", raw)


def known_players(levels):
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


def level_name(level):
    return level["data"]["name"] if level["data"] else level["file"] + ".json"


def level_label(level):
    data = level["data"]
    if not data:
        return "#{}  (missing file: {}.json)".format(level["rank"], level["file"])
    if "records" in data:
        count = len(data.get("records", []))
        return "#{}  {}   ({} record{})".format(
            level["rank"], data["name"], count, "" if count == 1 else "s")
    else:
        return "#{}  {}".format(level["rank"], data["name"])


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


def pick_level(levels, title="Select a level", require_data=False):
    print()
    print(title)
    print("  Type part of the level's name to search (example: ach),")
    print("  or a rank like #12. Press Enter to see the top of the list.")
    while True:
        query = ask("Search", required=False)
        matches = search_levels(levels, query)
        if require_data:
            matches = [lv for lv in matches if lv["data"]]
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
#  SUB-MODULE 1: LEVEL MANAGER
# ===============================================================

def split_list(text):
    items = []
    for part in text.split(","):
        part = part.strip()
        if part and part.lower() not in [i.lower() for i in items]:
            items.append(part)
    return items


def make_file_name(name, order):
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

    print()
    name = " ".join(ask("1/9  Level name", hint="Example: Acheron").split())
    same_name = [lv for lv in levels
                 if lv["data"] and lv["data"]["name"].lower() == name.lower()]
    if same_name and not confirm(
            "  A level called '{}' is already on the list (#{}). Add another one anyway?"
            .format(name, same_name[0]["rank"]), default=False):
        raise Cancelled()

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

    print()
    publisher = ask(
        "3/9  Level publisher",
        hint="The player who uploaded the level. Type - if you don't know.",
    )

    print()
    creators = split_list(ask(
        "4/9  Level creators",
        hint="Separate names with commas. Example: Zoink, Npesta\n"
             "  Leave empty if the publisher is the only creator.",
        required=False,
    ))

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
            verifier = players[verifier.lower()]
            break
        if confirm("  '{}' isn't on the leaderboard yet. Add them as a new player?"
                   .format(verifier), default=False):
            break

    difficulties = list(DIFFICULTIES)
    for lv in levels:
        found = lv["data"] and lv["data"].get("difficulty")
        if found and found not in difficulties:
            difficulties.append(found)
    default_index = (difficulties.index(DEFAULT_DIFFICULTY)
                     if DEFAULT_DIFFICULTY in difficulties else 0)
    difficulty = difficulties[
        choose("6/9  Level difficulty", difficulties, default=default_index)]

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


def remove_level():
    heading("REMOVE A LEVEL")
    order, order_raw = load_order()
    levels = load_levels(order)
    if not levels:
        print("  The list is empty - there is nothing to remove.")
        return

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

    token = str(data["id"]) if data else level["file"]
    what = "level ID" if data else "file name"
    print()
    print("2/2  To make sure this is the right level, type its {}.".format(what))
    ask("Type {} to remove it (or cancel)".format(token),
        check=lambda s: None if s.strip() == token
        else "That doesn't match {}. Try again, or type cancel.".format(token))

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


def points_for(rank, total):
    if total <= 1:
        return MAX_POINTS
    step = (MAX_POINTS - MIN_POINTS) / (total - 1)
    return round(MAX_POINTS - (rank - 1) * step, 3)


def move_level():
    heading("MOVE A LEVEL")
    order, order_raw = load_order()
    levels = load_levels(order)
    total = len(levels)
    if total < 2:
        print("  You need at least 2 levels on the list to move one.")
        return

    level = pick_level(levels, title="1/2  Select the level to move")
    old_rank = level["rank"]
    print()
    print("  Selected: " + level_label(level))

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

    others = [lv for lv in levels if lv is not level]
    above = others[new_rank - 2] if new_rank >= 2 else None
    below = others[new_rank - 1] if new_rank <= len(others) else None

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
#  SUB-MODULE 2: RECORD MANAGER
# ===============================================================

def add_record():
    heading("ADD A RECORD")
    levels = load_levels()
    if not [lv for lv in levels if lv["data"]]:
        print("  There are no levels on the list yet.")
        return
    players = known_players(levels)

    level = pick_level(levels, title="1/4  Select the level", require_data=True)
    data = level["data"]
    print("\n  Level: " + level_label(level))

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
            user = players[user.lower()]
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

    def check_link(text):
        if re.match(r"^https?://\S+$", text):
            return None
        return ("That doesn't look like a link. It should start with "
                "https:// (example: https://www.youtube.com/watch?v=...)")

    print()
    link = ask("3/4  Video link",
               hint="Optional: press Enter to skip (the site will show a '-' instead of 'Watch').",
               required=False, check=check_link)

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

    data.setdefault("records", []).append({"user": user, "link": link, "date": date})
    try:
        save_level(level)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        print("  Nothing was changed. Is the file open in another program?")
        return

    print()
    print("  Done! {}'s record was added to {}.".format(user, data["name"]))


def remove_record():
    heading("REMOVE A RECORD")
    levels = load_levels()
    with_records = [lv for lv in levels if lv["data"] and lv["data"].get("records")]
    if not with_records:
        print("  No level has any records yet - there is nothing to remove.")
        return

    level = pick_level(with_records, title="1/2  Select the level", require_data=True)
    data = level["data"]
    records = data["records"]

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
#  SUB-MODULE 3: PLAYER MANAGER
# ===============================================================

def find_key(players, name):
    for key in players:
        if key.lower() == name.lower():
            return key
    return None


def known_names(players, levels):
    names = {}
    def add(name):
        name = (name or "").strip()
        if name and name.lower() not in names:
            names[name.lower()] = name

    for name in players:
        add(name)
    for level in levels:
        if level["data"]:
            add(level["data"].get("verifier"))
            for record in level["data"].get("records", []):
                add(record.get("user"))
    return names


def find_usage(name, levels):
    target = name.lower()
    usage = {"records": [], "verified": [], "published": [], "created": []}
    for level in levels:
        data = level["data"]
        if not data:
            continue
        for record in data.get("records", []):
            if record.get("user", "").lower() == target:
                usage["records"].append(level)
        if (data.get("verifier") or "").lower() == target:
            usage["verified"].append(level)
        if (data.get("author") or "").lower() == target:
            usage["published"].append(level)
        if any(c.lower() == target for c in data.get("creators", [])):
            usage["created"].append(level)
    return usage


def country_text(code):
    if not code:
        return "(none)"
    return "{} ({})".format(COUNTRIES.get(code.lower(), "unknown"), code)


def player_label(name, players):
    key = find_key(players, name)
    info = players.get(key, {}) if key else {}
    text = name
    if info.get("country"):
        text += "   " + COUNTRIES.get(info["country"].lower(), info["country"])
    if info.get("banned"):
        text += "   [BANNED]"
    return text


def show_usage(name, players, usage):
    key = find_key(players, name)
    info = players.get(key, {}) if key else {}
    print()
    print("-" * 62)
    print("  Player:        " + name + ("   [BANNED]" if info.get("banned") else ""))
    print("  Profile:       " + ("in players.json" if key else "not in players.json"))
    print("  Country:       " + country_text(info.get("country", "")))
    print("  Picture:       " + (info.get("pfp") or "(none)"))
    print("  Records:       {}".format(len(usage["records"])))
    print("  Verified:      {} level(s)".format(len(usage["verified"])))
    print("  Published:     {} level(s)".format(len(usage["published"])))
    print("  Creator of:    {} level(s)".format(len(usage["created"])))
    print("-" * 62)


def pick_player(names, players, title):
    print()
    print(title)
    print("  Type part of the name to search, or press Enter to see everyone.")
    ordered = sorted(names, key=str.lower)
    while True:
        query = ask("Search", required=False).lower()
        matches = [n for n in ordered if query in n.lower()]
        if not matches:
            print("  ! Nobody found. Try fewer letters.")
            continue

        shown = matches[:MAX_SHOWN]
        for i, name in enumerate(shown, 1):
            print("  {:>2}) {}".format(i, player_label(name, players)))
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


def ask_name(taken, current=None):
    def check(text):
        if " ".join(text.split()).lower() in taken:
            return "Someone is already called that."
        return None
    return " ".join(ask("Player name", check=check).split())


def store_code(code):
    return code.upper() if len(code) == 2 else code


def search_countries(text):
    text = text.strip().lower()
    found = []
    if text in COUNTRIES:
        found.append(text)
    starts = sorted(c for c, n in COUNTRIES.items()
                    if n.lower().startswith(text) and c not in found)
    inside = sorted(c for c, n in COUNTRIES.items()
                    if text in n.lower() and c not in found and c not in starts)
    return (found + starts + inside)[:10]


def ask_country(keep_text=None):
    print()
    print("  Type a country name or its 2-letter code. Examples: Morocco, MA, Saudi Arabia")
    if keep_text:
        print("  Press Enter to " + keep_text + ", or type  none  to remove the country.")
    else:
        print("  Press Enter to skip (you can add it later).")
    while True:
        text = ask("Country", required=False)
        if not text:
            return None if keep_text else ""
        if text.lower() == "none" and keep_text:
            return ""
        matches = search_countries(text)
        if not matches:
            print("  ! No country found. Try a different spelling or fewer letters.")
            continue
        for i, code in enumerate(matches, 1):
            print("  {:>2}) {}   ({})".format(i, COUNTRIES[code], store_code(code)))

        def check(answer):
            if answer.isdigit() and 1 <= int(answer) <= len(matches):
                return None
            return "Please type a number from 1 to {}.".format(len(matches))

        default = "1" if len(matches) == 1 else None
        answer = ask("Number to pick (press Enter to search again)",
                     default=default, required=False, check=check)
        if answer:
            return store_code(matches[int(answer) - 1])


def safe_file_name(name):
    return re.sub(r'[\\/:*?"<>|]+', "_", name.lower()).strip() or "player"




def ask_pfp(player_name, keep_text=None):
    print()
    print("  You can give:")
    print("   - the file name of an image already in assets/pfps")
    print("   - a website-relative path (assets/pfps/Amine.png)")
    print("   - the path of an image on your computer")
    print("   - a link to an image (the image will be downloaded automatically)")

    if PFP_DIR.exists():
        images = sorted(
            p.name for p in PFP_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in PFP_EXTENSIONS
        )
        if images:
            print("  Images already in assets/pfps: " + ", ".join(images[:15])
                  + (", ..." if len(images) > 15 else ""))

    if keep_text:
        print("  Press Enter to " + keep_text + ", or type none to remove the picture.")
    else:
        print("  Press Enter to skip (you can add it later).")

    while True:
        text = ask("Profile picture", required=False).strip().strip("\"'")

        if not text:
            return (None, None) if keep_text else ("", None)

        if text.lower() == "none" and keep_text:
            return "", None

        # External image URL
        if re.match(r"^https?://\S+$", text, re.IGNORECASE):
            parsed = urllib.parse.urlparse(text)
            extension = Path(parsed.path).suffix.lower()

            if extension not in PFP_EXTENSIONS:
                print("  ! The URL doesn't have a supported image extension.")
                print("  Supported formats: " + ", ".join(PFP_EXTENSIONS))
                continue

            destination = PFP_DIR / (
                safe_file_name(player_name) + extension
            )

            if destination.exists():
                if not confirm(
                    "  assets/pfps/{} already exists. Replace it?".format(
                        destination.name
                    ),
                    default=False
                ):
                    continue

            print("  Downloading profile picture...")

            try:
                request = urllib.request.Request(
                    text,
                    headers={"User-Agent": "Mozilla/5.0"}
                )

                with urllib.request.urlopen(request, timeout=20) as response:
                    content_type = response.headers.get("Content-Type", "")
                    image_data = response.read()

                if not content_type.lower().startswith("image/"):
                    print("  ! The URL didn't return an image.")
                    continue

                if not image_data:
                    print("  ! The downloaded image is empty.")
                    continue

                return (
                    "assets/pfps/" + destination.name,
                    (image_data, destination)
                )

            except Exception as error:
                print("  ! Could not download the image: {}".format(error))
                print("  Check the URL and try again.")
                continue

        # Normalize website-relative paths
        normalized = text.replace("\\", "/")

        prefix = "assets/pfps/"
        if normalized.lower().startswith(prefix.lower()):
            normalized = normalized[len(prefix):]

        # Existing image inside assets/pfps
        existing = PFP_DIR / normalized
        if existing.is_file():
            if existing.suffix.lower() not in PFP_EXTENSIONS:
                print("  ! Unsupported image format.")
                continue
            return prefix + existing.name, None

        # Image path on the user's computer
        path = Path(text).expanduser()

        if path.is_file():
            if path.suffix.lower() not in PFP_EXTENSIONS:
                print("  ! That file isn't a supported image. Use: "
                      + ", ".join(PFP_EXTENSIONS))
                continue

            if PFP_DIR.exists() and path.resolve().parent == PFP_DIR.resolve():
                return prefix + path.name, None

            destination = PFP_DIR / (
                safe_file_name(player_name) + path.suffix.lower()
            )

            if destination.exists():
                if not confirm(
                    "  assets/pfps/{} already exists. Replace it?".format(
                        destination.name
                    ),
                    default=False
                ):
                    continue

            return prefix + destination.name, (path, destination)

        # Allow entering a filename that will be added later
        if Path(normalized).suffix.lower() not in PFP_EXTENSIONS:
            print("  ! I can't find that image. Enter a filename, path, or URL.")
            continue

        if confirm(
            "  I can't find assets/pfps/{} yet. Use that name anyway "
            "(you'll add the picture later)?".format(normalized),
            default=False
        ):
            return prefix + Path(normalized).name, None






def apply_copy(job):
    if job:
        PFP_DIR.mkdir(parents=True, exist_ok=True)

        # Downloaded image data
        if isinstance(job[0], bytes):
            job[1].write_bytes(job[0])

        # Local image file
        else:
            shutil.copy2(str(job[0]), str(job[1]))




def add_player():
    heading("ADD A PLAYER")
    players, raw = load_players()
    order, _ = load_order()
    levels = load_levels(order)
    names = known_names(players, levels)

    print()
    print("1/3  Player name")
    print("  Type it exactly how it should be shown. Example: Amine")
    taken = {k.lower() for k in players}
    name = ask_name(taken)
    if name.lower() in names and name != names[name.lower()]:
        print("  (The site already writes this name as '{}', so I'll use that.)"
              .format(names[name.lower()]))
        name = names[name.lower()]

    print()
    print("2/3  Country")
    country = ask_country()

    print()
    print("3/3  Profile picture")
    pfp, copy_job = ask_pfp(name)

    print()
    print("-" * 62)
    print("  Here is the player you are about to add:")
    print("-" * 62)
    print("  Name:     " + name)
    print("  Country:  " + country_text(country))
    print("  Picture:  " + (pfp or "(none)") + ("   (will be copied to assets/pfps)" if copy_job else ""))
    print()
    if not confirm("Save this player?"):
        raise Cancelled()

    players[name] = {"country": country, "pfp": pfp}
    try:
        apply_copy(copy_job)
        save_players(players, raw)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        print("  Nothing was changed. Is a file open in another program?")
        return

    print()
    print("  Done! {} was added.".format(name))


def remove_player_menu():
    heading("REMOVE A PLAYER")
    print("  Ban        = hide the player on the website. Nothing is deleted,")
    print("               and you can unban them any time.")
    print("  Fully remove = really delete parts of the player (you choose which).")
    choice = choose("Which kind of removal?", [
        "Ban a player (hide them)",
        "Unban a player (show them again)",
        "Fully remove a player",
    ])
    if choice == 0:
        ban_player()
    elif choice == 1:
        unban_player()
    else:
        full_remove()


def credited_levels(usage):
    seen, result = set(), []
    for level in usage["published"] + usage["created"]:
        if level["file"] not in seen:
            seen.add(level["file"])
            result.append(level)
    return sorted(result, key=lambda lv: lv["rank"])


def ban_player():
    heading("BAN A PLAYER")
    players, raw = load_players()
    order, _ = load_order()
    levels = load_levels(order)
    names = known_names(players, levels)
    candidates = {k: v for k, v in names.items()
                  if not players.get(find_key(players, v) or "", {}).get("banned")}
    if not candidates:
        print("  There is nobody to ban.")
        return

    name = pick_player(candidates.values(), players, "1/2  Select the player to ban")
    usage = find_usage(name, levels)
    show_usage(name, players, usage)
    print("  Banning hides {} from the leaderboards and hides their records on".format(name))
    print("  the level pages. Nothing is deleted, and you can unban them later.")

    legacy = []
    credited = credited_levels(usage)
    if credited:
        print()
        print("2/2  {} published or created these levels:".format(name))
        for level in credited:
            print("   - #{}  {}".format(level["rank"], level_name(level)))
        print("  They can be marked as LEGACY levels. (For now this only adds a")
        print("  'legacy' mark to the level - the site doesn't use it yet.)")
        if confirm("Mark these levels as LEGACY?", default=False):
            legacy = credited
    else:
        print("\n  (They haven't published or created any levels.)")

    print()
    if not confirm("Ban {}?".format(name)):
        raise Cancelled()

    try:
        for level in legacy:
            level["data"]["legacy"] = True
            save_level(level)
        key = find_key(players, name)
        if key is None:
            key = name
            players[key] = {"country": "", "pfp": ""}
        players[key]["banned"] = True
        save_players(players, raw)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        print("  Is a file open in another program?")
        return

    print()
    print("  Done! {} is now banned (hidden).".format(name))


def unban_player():
    heading("UNBAN A PLAYER")
    players, raw = load_players()
    order, _ = load_order()
    levels = load_levels(order)
    banned = {k.lower(): k for k, info in players.items() if info.get("banned")}
    if not banned:
        print("  Nobody is banned right now.")
        return

    name = pick_player(banned.values(), players, "1/1  Select the player to unban")
    usage = find_usage(name, levels)
    show_usage(name, players, usage)

    restore = []
    legacy_levels = [lv for lv in credited_levels(usage) if lv["data"].get("legacy")]
    if legacy_levels:
        print()
        print("  These levels they published or created are marked LEGACY:")
        for level in legacy_levels:
            print("   - #{}  {}".format(level["rank"], level_name(level)))
        if confirm("Remove the LEGACY mark from these levels?"):
            restore = legacy_levels

    print()
    if not confirm("Unban {}?".format(name)):
        raise Cancelled()

    try:
        for level in restore:
            del level["data"]["legacy"]
            save_level(level)
        key = find_key(players, name)
        players[key].pop("banned", None)
        save_players(players, raw)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        print("  Is a file open in another program?")
        return

    print()
    print("  Done! {} is visible again.".format(name))


def full_remove():
    heading("FULLY REMOVE A PLAYER")
    players, raw = load_players()
    order, order_raw = load_order()
    levels = load_levels(order)
    names = known_names(players, levels)
    if not names:
        print("  There are no players.")
        return

    name = pick_player(names.values(), players, "1/3  Select the player")
    usage = find_usage(name, levels)
    key = find_key(players, name)
    show_usage(name, players, usage)

    options, kinds = [], []
    if key:
        options.append("Their profile (country, picture, ban) in players.json")
        kinds.append("profile")
    if usage["records"]:
        options.append("Their records ({})".format(len(usage["records"])))
        kinds.append("records")
    if usage["verified"]:
        options.append("Their verifications ({}) - the levels stay, the verifier is left blank"
                       .format(len(usage["verified"])))
        kinds.append("verified")
    if usage["published"] or usage["created"]:
        options.append("Their levels ({} published, {} created)"
                       .format(len(usage["published"]), len(usage["created"])))
        kinds.append("levels")
    if not options:
        print("  There is nothing to remove for {}.".format(name))
        return

    print()
    print("2/3  What do you want to remove? You can pick more than one.")
    picked = [kinds[i] for i in choose_many("Parts of {} to remove:".format(name), options)]

    delete_levels = False
    if "levels" in picked and usage["published"]:
        way = choose(
            "What should happen to the {} level(s) {} published?".format(len(usage["published"]), name),
            ["Keep the levels, just remove the name (publisher becomes '-')",
             "DELETE those levels completely (the levels below move up a rank)"],
            default=0)
        delete_levels = way == 1

    deleting = usage["published"] if delete_levels else []
    deleting_files = {lv["file"] for lv in deleting}
    print()
    print("-" * 62)
    print("  This will happen to {}:".format(name))
    print("-" * 62)
    if "profile" in picked:
        print("  - Remove their profile from players.json")
    if "records" in picked:
        print("  - Delete {} record(s)".format(len(usage["records"])))
    if "verified" in picked:
        print("  - Clear the verifier on {} level(s)".format(len(usage["verified"])))
    if "levels" in picked:
        if delete_levels:
            print("  - DELETE {} level(s):".format(len(deleting)))
            for level in deleting:
                print("      #{}  {}".format(level["rank"], level_name(level)))
        elif usage["published"]:
            print("  - Replace them as publisher on {} level(s) with '-'".format(len(usage["published"])))
        others = [lv for lv in usage["created"] if lv["file"] not in deleting_files]
        if others:
            print("  - Remove their name from the creators of {} level(s)".format(len(others)))
    print()

    print("3/3  This cannot be undone. To confirm, type the player's name.")
    ask("Type {} to confirm (or cancel)".format(name),
        check=lambda s: None if s.strip().lower() == name.lower()
        else "That doesn't match {}. Try again, or type cancel.".format(name))

    target = name.lower()
    changed = {}
    for level in levels:
        data = level["data"]
        if not data or level["file"] in deleting_files:
            continue
        before = json.dumps(data, sort_keys=True)
        if "records" in picked:
            data["records"] = [r for r in data.get("records", [])
                               if r.get("user", "").lower() != target]
        if "verified" in picked and (data.get("verifier") or "").lower() == target:
            data["verifier"] = ""
        if "levels" in picked:
            if not delete_levels and (data.get("author") or "").lower() == target:
                data["author"] = "-"
            data["creators"] = [c for c in data.get("creators", [])
                                if c.lower() != target]
        if json.dumps(data, sort_keys=True) != before:
            changed[level["file"]] = level

    try:
        for level in changed.values():
            save_level(level)
        if deleting_files:
            order = [f for f in order if f not in deleting_files]
            write_json(LIST_FILE, order, like=order_raw)
            for file_name in deleting_files:
                path = DATA_DIR / (file_name + ".json")
                if path.exists():
                    path.unlink()
        if "profile" in picked and key:
            del players[key]
            save_players(players, raw)
    except OSError as error:
        print("\n  ! Something went wrong while saving: {}".format(error))
        return

    print()
    print("  Done! The selected parts of {} were removed.".format(name))



def update_player():
    heading("UPDATE A PLAYER")
    players, raw = load_players()
    order, _ = load_order()
    levels = load_levels(order)
    names = known_names(players, levels)
    if not names:
        print("  There are no players yet.")
        return

    name = pick_player(names.values(), players, "1/2  Select the player")
    usage = find_usage(name, levels)
    show_usage(name, players, usage)
    key = find_key(players, name)
    info = dict(players.get(key, {})) if key else {"country": "", "pfp": ""}

    print()
    print("2/2  What do you want to update? You can pick more than one.")
    picked = choose_many("Options:", ["Player's name", "Country", "Profile picture"])

    new_name, new_country, new_pfp, copy_job = name, None, None, None

    if 0 in picked:
        print()
        print("  New name (it will be changed on every record, verification and credit).")
        taken = {n for n in names if n != name.lower()}
        new_name = ask_name(taken)
        if new_name == name:
            print("  (That is the same name - nothing to rename.)")

    if 1 in picked:
        print()
        print("  Country (now: {})".format(country_text(info.get("country", ""))))
        new_country = ask_country(keep_text="keep it as it is")

    if 2 in picked:
        print()
        print("  Profile picture (now: {})".format(info.get("pfp") or "(none)"))
        new_pfp, copy_job = ask_pfp(new_name, keep_text="keep it as it is")

    renaming = new_name != name
    country_changed = new_country is not None and new_country != info.get("country", "")
    pfp_changed = new_pfp is not None and new_pfp != info.get("pfp", "")

    if not (renaming or country_changed or pfp_changed):
        print("\n  Nothing to change.")
        return

    print()
    print("-" * 62)
    print("  Here is what will change:")
    print("-" * 62)

    if renaming:
        print("  Name:     {}  ->  {}".format(name, new_name))
    if country_changed:
        print("  Country:  {}  ->  {}".format(
            country_text(info.get("country", "")),
            country_text(new_country)
        ))
    if pfp_changed:
        print("  Picture:  {}  ->  {}".format(
            info.get("pfp") or "(none)",
            new_pfp or "(none)"
        ))

    print()
    if not confirm("Save these changes?"):
        raise Cancelled()

    try:
        if renaming:
            old, new = name.lower(), new_name
            changed = []

            for level in levels:
                data = level["data"]
                if not data:
                    continue

                touched = False

                for record in data.get("records", []):
                    if record.get("user", "").lower() == old:
                        record["user"] = new
                        touched = True

                if (data.get("verifier") or "").lower() == old:
                    data["verifier"] = new
                    touched = True

                if (data.get("author") or "").lower() == old:
                    data["author"] = new
                    touched = True

                creators = data.get("creators", [])
                for i, creator in enumerate(creators):
                    if creator.lower() == old:
                        creators[i] = new
                        touched = True

                if touched:
                    changed.append(level)

            for level in changed:
                save_level(level)

        updated = {}
        placed = False

        for k, v in players.items():
            if key is not None and k == key:
                updated[new_name] = dict(info)
                placed = True
            else:
                updated[k] = v

        if not placed:
            updated[new_name] = dict(info)

        entry = updated[new_name]
        entry.setdefault("country", "")
        entry.setdefault("pfp", "")

        if country_changed:
            entry["country"] = new_country

        if pfp_changed:
            entry["pfp"] = new_pfp
            apply_copy(copy_job)

        # Automatically rename an old image if no explicit picture is assigned.
        if renaming and not entry["pfp"] and PFP_DIR.exists():
            for ext in PFP_EXTENSIONS:
                old_file = PFP_DIR / (name.lower() + ext)
                new_file = PFP_DIR / (new_name.lower() + ext)

                if old_file.exists() and not new_file.exists():
                    old_file.rename(new_file)
                    entry["pfp"] = "assets/pfps/" + new_file.name
                    break

        save_players(updated, raw)

    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        return

    print()
    print("  Done! {} was updated.".format(new_name))


# ===============================================================
#  MAIN MENU & ROUTING
# ===============================================================

def run_levels_menu():
    while True:
        try:
            choice = choose("Level Manager - What would you like to do?",
                            ["Add a level", "Remove a level", "Move a level (change its rank)", "Back to Main Menu"])
            if choice == 3:
                break
            if choice == 0:
                add_level()
            elif choice == 1:
                remove_level()
            elif choice == 2:
                move_level()
        except Cancelled:
            print("\n  Cancelled - nothing was changed.")
        except (ValueError, KeyError) as error:
            print("\n  ! A data file looks broken: {}".format(error))
            print("  Nothing was changed.")


def run_records_menu():
    while True:
        try:
            choice = choose("Record Manager - What would you like to do?",
                            ["Add a record", "Remove a record", "Back to Main Menu"])
            if choice == 2:
                break
            if choice == 0:
                add_record()
            elif choice == 1:
                remove_record()
        except Cancelled:
            print("\n  Cancelled - nothing was changed.")
        except (ValueError, KeyError) as error:
            print("\n  ! A data file looks broken: {}".format(error))
            print("  Nothing was changed.")


def run_players_menu():
    while True:
        try:
            choice = choose("Player Manager - What would you like to do?",
                            ["Add a player", "Remove / Ban a player", "Update a player", "Back to Main Menu"])
            if choice == 3:
                break
            if choice == 0:
                add_player()
            elif choice == 1:
                remove_player_menu()
            elif choice == 2:
                update_player()
        except Cancelled:
            print("\n  Cancelled - nothing was changed.")
        except (ValueError, KeyError, TypeError) as error:
            print("\n  ! A data file looks broken: {}".format(error))
            print("  Nothing was changed.")


def main():
    if not LIST_FILE.exists():
        print("Couldn't find data/_list.json next to this script.")
        print("Put manage.py in your website folder (next to index.html).")
        return

    heading("BUNKER BEMONS - UNIFIED MANAGER")
    print("  Tip: type  cancel  at any question to go back without saving.")

    while True:
        try:
            choice = choose("What do you want to manage?",
                            ["Levels (Add, Remove, Move)",
                             "Records (Add, Remove)",
                             "Players (Add, Remove/Ban, Update)",
                             "Quit"])
        except Cancelled:
            break

        if choice == 0:
            run_levels_menu()
        elif choice == 1:
            run_records_menu()
        elif choice == 2:
            run_players_menu()
        elif choice == 3:
            break

    print("\nBye!")


if __name__ == "__main__":
    try:
        main()
    finally:
        if sys.stdin and sys.stdin.isatty():
            try:
                input("\nPress Enter to close...")
            except (EOFError, KeyboardInterrupt):
                pass