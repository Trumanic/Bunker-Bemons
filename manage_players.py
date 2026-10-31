#!/usr/bin/env python3
"""
==============================================================
  BUNKER BEMONS - PLAYER MANAGER
  Add, remove (ban or fully remove) or update players.
==============================================================

HOW TO USE
  1. Put this file in your website folder (the one with index.html).
  2. Open a terminal / command prompt in that folder.
  3. Run it:    python manage_players.py
                (if that doesn't work, try:  py manage_players.py)
  4. Answer the questions. Type  cancel  at any question to stop.

Nothing is saved until you confirm at the very end.

WHAT IT CHANGES
  data/players.json   - each player's country, profile picture and ban status
  data/<level>.json   - only when a rename / full removal touches a level
  assets/pfps/        - when you give it a picture from your computer
"""

import json
import re
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------
#  SETTINGS  (you can change these)
# ---------------------------------------------------------------

# How many search results to show at once
MAX_SHOWN = 20

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


def choose_many(question, options):
    """
    Like choose(), but you can pick several: type 1,3  or  all.
    Returns a sorted list of positions.
    """
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
    """Returns (data, raw_bytes). raw_bytes is used to keep the file's style."""
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8-sig")), raw


def save_text(path, text, like=None):
    """
    Writes text to a file, keeping the old file's line endings.
    It is written to a temporary file first, so a crash can't corrupt it.
    """
    if like is None or like.endswith(b"\n"):
        text += "\n"
    if like is not None and b"\r\n" in like:
        text = text.replace("\n", "\r\n")
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(text.encode("utf-8"))
    temp.replace(path)


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
    save_text(path, format_json(data), like)


def load_players():
    """Reads data/players.json. Returns (players, raw_bytes_or_None)."""
    if not PLAYERS_FILE.exists():
        return {}, None
    data, raw = read_json(PLAYERS_FILE)
    players = {}
    for name, info in data.items():
        players[name] = dict(info) if isinstance(info, dict) else {}
    return players, raw


def save_players(players, raw):
    """Saves players.json with one player per line (easy to edit by hand)."""
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


def load_order():
    """Reads data/_list.json: the level file names, in rank order."""
    return read_json(LIST_FILE)


def load_levels(order):
    """Reads every level on the list. Each item: rank, file, data, raw."""
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


def level_name(level):
    return level["data"]["name"] if level["data"] else level["file"] + ".json"


# ===============================================================
#  PLAYERS: finding them and seeing what they are connected to
# ===============================================================

def find_key(players, name):
    """The players.json spelling of `name` (ignoring capitals), or None."""
    for key in players:
        if key.lower() == name.lower():
            return key
    return None


def known_names(players, levels):
    """Everyone we know about, as {lowercase: proper spelling}."""
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
    """Everything on the site that belongs to this player."""
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
    """Lets the user search a list of names and pick one. Returns the name."""
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


# ===============================================================
#  QUESTIONS: name, country, picture
# ===============================================================

def ask_name(taken, current=None):
    """Asks for a player name. `taken` = names that can't be used."""
    def check(text):
        if " ".join(text.split()).lower() in taken:
            return "Someone is already called that."
        return None
    return " ".join(ask("Player name", check=check).split())


def store_code(code):
    """'ma' -> 'MA'   (longer codes like gb-eng stay lowercase)"""
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
    """
    Lets the user search for a country by name or 2-letter code.
    Returns the code to save ('' = no country), or None to keep the old one
    (only when keep_text is given).
    """
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
    """A player name that is safe to use as a file name."""
    return re.sub(r'[\\/:*?"<>|]+', "_", name.lower()).strip() or "player"


def ask_pfp(player_name, keep_text=None):
    """
    Asks for a profile picture. Returns (value, copy_job).
      value     - what to write in players.json ('' = none, None = keep old)
      copy_job  - (source, destination) if a picture must be copied, else None
    """
    print()
    print("  You can give:")
    print("   - the file name of an image already in assets/pfps   (example: amine.png)")
    print("   - the path of an image on your computer (you can drag the file")
    print("     into this window). It will be copied into assets/pfps.")
    print("   - a link to an image (https://...)")
    if PFP_DIR.exists():
        images = sorted(p.name for p in PFP_DIR.iterdir()
                        if p.suffix.lower() in PFP_EXTENSIONS)
        if images:
            print("  Images already in assets/pfps: " + ", ".join(images[:15])
                  + (", ..." if len(images) > 15 else ""))
    if keep_text:
        print("  Press Enter to " + keep_text + ", or type  none  to remove the picture.")
    else:
        print("  Press Enter to skip (you can add it later).")

    while True:
        text = ask("Profile picture", required=False).strip("\"'")
        if not text:
            return (None, None) if keep_text else ("", None)
        if text.lower() == "none" and keep_text:
            return "", None
        if re.match(r"^https?://\S+$", text):
            return text, None

        path = Path(text).expanduser()
        if path.is_file():
            if path.suffix.lower() not in PFP_EXTENSIONS:
                print("  ! That file isn't a picture the site can show. Use: "
                      + ", ".join(PFP_EXTENSIONS))
                continue
            if PFP_DIR.exists() and path.resolve().parent == PFP_DIR.resolve():
                return path.name, None
            destination = PFP_DIR / (safe_file_name(player_name) + path.suffix.lower())
            if destination.exists() and not confirm(
                    "  assets/pfps/{} already exists. Replace it?".format(destination.name),
                    default=False):
                continue
            return destination.name, (path, destination)

        if (PFP_DIR / text).is_file():
            return text, None

        if Path(text).suffix.lower() not in PFP_EXTENSIONS:
            print("  ! I can't find that file. Type the picture's file name, its path, or a link.")
            continue
        if confirm("  I can't find assets/pfps/{} yet. Use that name anyway "
                   "(you'll add the picture later)?".format(text), default=False):
            return text, None


def apply_copy(job):
    """Copies a chosen picture into assets/pfps."""
    if job:
        PFP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(job[0]), str(job[1]))


# ===============================================================
#  ADD A PLAYER
# ===============================================================

def add_player():
    heading("ADD A PLAYER")
    players, raw = load_players()
    order, _ = load_order()
    levels = load_levels(order)
    names = known_names(players, levels)

    # ---- 1. Name -------------------------------------------------
    print()
    print("1/3  Player name")
    print("  Type it exactly how it should be shown. Example: Amine")
    taken = {k.lower() for k in players}
    name = ask_name(taken)
    if name.lower() in names and name != names[name.lower()]:
        print("  (The site already writes this name as '{}', so I'll use that.)"
              .format(names[name.lower()]))
        name = names[name.lower()]

    # ---- 2. Country ----------------------------------------------
    print()
    print("2/3  Country")
    country = ask_country()

    # ---- 3. Profile picture --------------------------------------
    print()
    print("3/3  Profile picture")
    pfp, copy_job = ask_pfp(name)

    # ---- Summary + confirmation ----------------------------------
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

    # ---- Save ----------------------------------------------------
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
    print("  They show up on the leaderboard once they have a record or a")
    print("  verification (add one with:  python manage_records.py).")


# ===============================================================
#  REMOVE A PLAYER  -  ban / unban / fully remove
# ===============================================================

def remove_menu():
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
    """Levels the player published or created (no repeats)."""
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

    # ---- Levels they published / created -------------------------
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

    # ---- Save ----------------------------------------------------
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
    if legacy:
        print("  {} level(s) were marked as legacy.".format(len(legacy)))


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

    # Levels that were marked legacy because of this player
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
    if restore:
        print("  {} level(s) are no longer marked as legacy.".format(len(restore)))


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

    # ---- 2. What to remove ---------------------------------------
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

    # ---- What should happen to their levels ----------------------
    delete_levels = False
    if "levels" in picked and usage["published"]:
        way = choose(
            "What should happen to the {} level(s) {} published?".format(len(usage["published"]), name),
            ["Keep the levels, just remove the name (publisher becomes '-')",
             "DELETE those levels completely (the levels below move up a rank)"],
            default=0)
        delete_levels = way == 1

    # ---- Summary -------------------------------------------------
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
    if "profile" in picked and ("records" not in picked and "verified" not in picked) \
            and (usage["records"] or usage["verified"]):
        print()
        print("  Note: they still have records or verifications, so they will keep")
        print("  showing on the leaderboard (without a country or picture).")
    if "profile" in picked:
        print("  (Picture files in assets/pfps are never deleted.)")
    print()

    # ---- 3. Confirm by typing the name ---------------------------
    print("3/3  This cannot be undone. To confirm, type the player's name.")
    ask("Type {} to confirm (or cancel)".format(name),
        check=lambda s: None if s.strip().lower() == name.lower()
        else "That doesn't match {}. Try again, or type cancel.".format(name))

    # ---- Do it ---------------------------------------------------
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
        print("  Some changes may already be saved. Is a file open in another program?")
        return

    print()
    print("  Done! The selected parts of {} were removed.".format(name))


# ===============================================================
#  UPDATE A PLAYER
# ===============================================================

def update_player():
    heading("UPDATE A PLAYER")
    players, raw = load_players()
    order, _ = load_order()
    levels = load_levels(order)
    names = known_names(players, levels)
    if not names:
        print("  There are no players yet.")
        return

    # ---- 1. Select the player ------------------------------------
    name = pick_player(names.values(), players, "1/2  Select the player")
    usage = find_usage(name, levels)
    show_usage(name, players, usage)
    key = find_key(players, name)
    info = dict(players.get(key, {})) if key else {"country": "", "pfp": ""}

    # ---- 2. What to update ---------------------------------------
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

    # ---- Summary + confirmation ----------------------------------
    print()
    print("-" * 62)
    print("  Here is what will change:")
    print("-" * 62)
    if renaming:
        print("  Name:     {}  ->  {}".format(name, new_name))
        print("            (updates {} record(s), {} verification(s), {} published, {} creator credit(s))"
              .format(len(usage["records"]), len(usage["verified"]),
                      len(usage["published"]), len(usage["created"])))
    if country_changed:
        print("  Country:  {}  ->  {}".format(country_text(info.get("country", "")),
                                             country_text(new_country)))
    if pfp_changed:
        print("  Picture:  {}  ->  {}".format(info.get("pfp") or "(none)", new_pfp or "(none)"))
        if copy_job:
            print("            (the picture will be copied to assets/pfps)")
    print()
    if not confirm("Save these changes?"):
        raise Cancelled()

    # ---- Save ----------------------------------------------------
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

        # players.json (keeps the player's place in the file)
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

        # A picture named after the player (assets/pfps/<name>.png) follows a rename
        if renaming and not entry["pfp"] and PFP_DIR.exists():
            for ext in PFP_EXTENSIONS:
                old_file = PFP_DIR / (name.lower() + ext)
                new_file = PFP_DIR / (new_name.lower() + ext)
                if old_file.exists() and not new_file.exists():
                    old_file.rename(new_file)
                    print("  (Renamed assets/pfps/{} to {})".format(old_file.name, new_file.name))
        save_players(updated, raw)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        print("  Some changes may already be saved. Is a file open in another program?")
        return

    print()
    print("  Done! {} was updated.".format(new_name))


# ===============================================================
#  MAIN MENU
# ===============================================================

def main():
    if not LIST_FILE.exists():
        print("Couldn't find data/_list.json next to this script.")
        print("Put manage_players.py in your website folder (next to index.html).")
        return

    heading("BUNKER BEMONS - PLAYER MANAGER")
    print("  Tip: type  cancel  at any question to go back without saving.")

    while True:
        try:
            choice = choose("What would you like to do?",
                            ["Add a player", "Remove a player", "Update a player", "Quit"])
        except Cancelled:
            break
        if choice == 3:
            break
        try:
            if choice == 0:
                add_player()
            elif choice == 1:
                remove_menu()
            else:
                update_player()
        except Cancelled:
            print("\n  Cancelled - nothing was changed.")
        except (ValueError, KeyError, TypeError) as error:
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