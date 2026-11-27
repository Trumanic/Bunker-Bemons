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

RATINGS = ["Unrated", "Star", "Featured", "Epic", "Legendary", "Mythic"]

# Common NLW tier options (you can also type any custom/new tier name)
NLW_TIERS = [
    "Beginner",
    "Easy",
    "Medium",
    "Hard",
    "Very Hard",
    "Insane",
    "Extreme",
    "Fuck",
    "Terrifying",
    "Remorseless",
    "Relentless",
    "Insidious",
    "Merciless",
    "Excruciating",
    "Inexorable",
    "Catastrophic",
    "Apocalyptic",
    "Impossible",
]

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
CREATED_FILE = DATA_DIR / "_created.json"
PLAYERS_FILE = DATA_DIR / "players.json"
LEGACY_FILE = DATA_DIR / "_legacy.json"
PACKS_FILE = DATA_DIR / "_packs.json"
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


def load_legacy_order():
    if not LEGACY_FILE.exists():
        return [], None
    data, raw = read_json(LEGACY_FILE)
    return (data if isinstance(data, list) else []), raw

def load_created_order():
    if not CREATED_FILE.exists():
        return [], None
    data, raw = read_json(CREATED_FILE)
    return (data if isinstance(data, list) else []), raw


def target_order(target):
    """(order, raw) of the ranked list or the Created list."""
    return load_created_order() if target == "created" else load_order()


def target_file(target):
    return CREATED_FILE if target == "created" else LIST_FILE


def with_metadata_fields(data, rating=None, nlw=None, gddl=None, created_at=None):
    """Copy of a level's data with rating/nlw/gddl/created_at placed cleanly."""
    updates = {}
    if rating is not None:
        updates["rating"] = rating
    if nlw is not None:
        updates["nlw"] = nlw
    if gddl is not None:
        updates["gddl"] = gddl
    if created_at is not None:
        updates["created_at"] = created_at

    if not updates:
        return dict(data)

    order_after_diff = ["rating", "nlw", "gddl", "created_at"]
    result = {}
    inserted = set()

    for key, value in data.items():
        if key in updates:
            continue
        result[key] = value
        if key == "difficulty":
            for f in order_after_diff:
                if f in updates:
                    result[f] = updates[f]
                    inserted.add(f)

    for f in order_after_diff:
        if f in updates and f not in inserted:
            result[f] = updates[f]

    return result


def with_rating(data, rating):
    """Copy of a level's data with 'rating' placed right after 'difficulty'."""
    return with_metadata_fields(data, rating=rating)


def load_packs():
    if not PACKS_FILE.exists():
        return [], None
    data, raw = read_json(PACKS_FILE)
    return (data if isinstance(data, list) else []), raw


def read_level(file_name, rank, legacy):
    path = DATA_DIR / (file_name + ".json")
    data, raw = None, None
    if path.exists():
        try:
            data, raw = read_json(path)
        except ValueError:
            data, raw = None, None
    return {"rank": rank, "file": file_name, "data": data, "raw": raw, "legacy": legacy}

def read_created_only(file_name):
    level = read_level(file_name, None, False)
    level["created_only"] = True
    return level


def load_levels(order=None, include_legacy=False):
    """Ranked levels, legacy levels, and Created-only levels."""
    if order is None:
        order, _ = load_order()

    levels = [read_level(f, rank, False) for rank, f in enumerate(order, 1)]

    if include_legacy:
        legacy_order, _ = load_legacy_order()
        ranked = set(order)
        levels += [read_level(f, None, True) for f in legacy_order if f not in ranked]
        seen = {lv["file"] for lv in levels}
        created_order, _ = load_created_order()
        levels += [read_created_only(f) for f in created_order if f not in seen]

    return levels


def save_level(level):
    write_json(DATA_DIR / (level["file"] + ".json"), level["data"], like=level["raw"])

def rank_text(level):
    if level["rank"]:
        return "#{}".format(level["rank"])
    return "Created" if level.get("created_only") else "Legacy"


def packs_using(files):
    """[(pack, [level files of that pack that are in `files`])]"""
    files = set(files)
    packs, _ = load_packs()
    found = []
    for pack in packs:
        hit = [f for f in pack.get("levels", []) if f in files]
        if hit:
            found.append((pack, hit))
    return found


def print_pack_impact(files, indent="  "):
    files = set(files)
    affected = packs_using(files)
    if affected:
        print(indent + "Packs affected (the level is removed from them):")
    for pack, _ in affected:
        left = len([f for f in pack.get("levels", []) if f not in files])
        note = ("pack will be DELETED (nothing would be left)" if left == 0
                else "{} level(s) left".format(left))
        print("{}  - {}: {}".format(indent, pack.get("name", pack.get("id")), note))


def strip_from_packs(files):
    """Removes level files from every pack. Packs left empty are deleted.
    Returns (number of packs changed, names of deleted packs)."""
    files = set(files)
    packs, raw = load_packs()
    kept, changed, deleted = [], 0, []
    for pack in packs:
        levels = pack.get("levels", [])
        remaining = [f for f in levels if f not in files]
        if len(remaining) != len(levels):
            changed += 1
            if not remaining:
                deleted.append(pack.get("name", pack.get("id")))
                continue
            pack["levels"] = remaining
        kept.append(pack)
    if changed:
        write_json(PACKS_FILE, kept, like=raw)
    return changed, deleted


def move_to_legacy(files):
    """Moves level files from the ranked list to the end of the legacy list."""
    files = list(files)
    legacy_order, legacy_raw = load_legacy_order()
    legacy_order += [f for f in files if f not in legacy_order]
    # legacy first: if something fails half-way, no level is lost
    write_json(LEGACY_FILE, legacy_order, like=legacy_raw)
    order, order_raw = load_order()
    write_json(LIST_FILE, [f for f in order if f not in set(files)], like=order_raw)



def remove_level_files(files):
    """Deletes levels everywhere: ranked list, legacy list, packs and disk.
    Returns (number of packs changed, names of deleted packs)."""
    files = set(files)

    # Remove from ranked list
    order, order_raw = load_order()
    if any(f in files for f in order):
        write_json(
            LIST_FILE,
            [f for f in order if f not in files],
            like=order_raw
        )

    # Remove from legacy list
    legacy_order, legacy_raw = load_legacy_order()
    if any(f in files for f in legacy_order):
        write_json(
            LEGACY_FILE,
            [f for f in legacy_order if f not in files],
            like=legacy_raw
        )

    # Remove from created list
    created_order, created_raw = load_created_order()
    if any(f in files for f in created_order):
        write_json(
            CREATED_FILE,
            [f for f in created_order if f not in files],
            like=created_raw
        )

    # Remove levels from packs
    packs_changed, packs_deleted = strip_from_packs(files)

    # Delete actual level files
    for file in files:
        path = DATA_DIR / (file + ".json")
        if path.exists():
            path.unlink()

    return packs_changed, packs_deleted



def unlink_from_list(target, files):
    """Takes levels off ONE list only. The level files and records stay."""
    files = set(files)
    order, raw = target_order(target)
    write_json(target_file(target), [f for f in order if f not in files], like=raw)

    if target == "ranked":
        result = strip_from_packs(files)
        return result

    return 0, []


def refresh_packs():
    """Recalculates every pack's average rank, tier and multiplier after the
    list order changed. Uses manage_packs.py so both scripts stay in sync."""
    try:
        import manage_packs
    except ImportError:
        print("  ! manage_packs.py not found, so pack tiers were NOT updated.")
        return
    try:
        packs, raw = manage_packs.load_packs()
        if not packs:
            return
        before = json.dumps(packs, sort_keys=True)
        manage_packs.recalculate_all_packs(packs, manage_packs.load_list())
        if json.dumps(packs, sort_keys=True) != before:
            manage_packs.save_packs(packs, raw)
            print("  Pack tiers and multipliers were refreshed.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("  ! Could not refresh pack tiers: {}".format(error))


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
        return "{}  (missing file: {}.json)".format(rank_text(level), level["file"])
    if "records" in data:
        count = len(data.get("records", []))
        return "{}  {}   ({} record{})".format(
            rank_text(level), data["name"], count, "" if count == 1 else "s")
    else:
        return "{}  {}".format(rank_text(level), data["name"])


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
#  METADATA INPUT HELPERS (rating, nlw, gddl, created_at)
# ===============================================================

def collect_known_nlw_tiers(levels):
    tiers = list(NLW_TIERS)
    for lv in levels:
        val = (lv.get("data") or {}).get("nlw")
        if isinstance(val, str):
            cleaned = re.sub(r"\s+", " ", val).strip()
            if cleaned and cleaned.lower() not in {t.lower() for t in tiers}:
                tiers.append(cleaned)
    return tiers


def prompt_rating(current=None):
    default_idx = RATINGS.index(current) if current in RATINGS else 0
    return RATINGS[choose("Level rating (in-game)", RATINGS, default=default_idx)]


def prompt_nlw(levels, current=None):
    known = collect_known_nlw_tiers(levels)
    options = known + ["Other / custom tier name", "None / leave empty"]
    default_idx = len(options) - 1
    if current:
        for idx, t in enumerate(known):
            if t.lower() == str(current).strip().lower():
                default_idx = idx
                break
        else:
            default_idx = len(known)  # custom tier

    picked = choose("NLW tier", options, default=default_idx)
    if picked < len(known):
        return known[picked]
    if picked == len(known):
        prefill = current if (current and current not in known) else None
        custom = ask(
            "Custom NLW tier name",
            hint="Type any tier name (example: Remorseless or a new tier name).",
            default=prefill,
            required=True,
        )
        return re.sub(r"\s+", " ", custom).strip()
    return ""


def parse_gddl_value(raw_text):
    """Returns a float (e.g. 22.08) for valid GDDL input, None for empty/cleared,
    or raises ValueError if invalid."""
    text = raw_text.strip()
    if not text or text.lower() in ("none", "null", "n/a", "-"):
        return None

    # Support legacy strings like "Tier 23 | 22.52" if pasted or defaulted
    m = re.match(r"^tier\s*\d+\s*\|\s*([+-]?\d+(?:\.\d+)?)$", text, re.IGNORECASE)
    if m:
        val = float(m.group(1))
    else:
        val = float(text)

    if val < 0:
        raise ValueError("GDDL rating cannot be negative.")
    return round(val, 2)


def prompt_gddl(current=None):
    print()
    hint = (
        "Enter the exact GDDL number (e.g. 22.08). "
        "Press Enter to leave empty (or keep current)."
    )
    default_val = str(current) if current not in (None, "") else None
    while True:
        ans = ask(
            "GDDL tier",
            hint=hint,
            default=default_val,
            required=False,
        )
        if not ans:
            return None
        try:
            return parse_gddl_value(ans)
        except ValueError:
            print("  ! Enter a valid non-negative number like 22.08.")


def parse_dmy_date(text):
    s = text.strip()
    if not s:
        return ""
    if s.lower() == "today":
        dt = datetime.date.today()
        return "{}/{}/{}".format(dt.day, dt.month, dt.year)
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(s, fmt).date()
            return "{}/{}/{}".format(dt.day, dt.month, dt.year)
        except ValueError:
            pass
    return None


def prompt_created_at(current=None):
    print()
    default_val = current if current else None
    while True:
        ans = ask(
            "Created / achieved date (D/M/YYYY)",
            hint="Format: D/M/YYYY (example: 3/7/2017) or 'today'. Press Enter to leave empty.",
            default=default_val,
            required=False,
        )
        if not ans:
            return ""
        parsed = parse_dmy_date(ans)
        if parsed is not None:
            return parsed
        print("  ! Please use D/M/YYYY (example: 3/7/2017) or type 'today'.")

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


def add_level(target="ranked"):
    created = target == "created"
    heading("ADD A LEVEL TO THE CREATED LIST" if created else "ADD A LEVEL")
    order, order_raw = target_order(target)
    levels = load_levels(include_legacy=True)   # every level on the site
    target_levels = load_levels(order)          # only the list we add to
    players = known_players(levels)
    steps = 14 if created else 13
    counter = iter(range(1, steps + 1))

    def step(text):
        return "{}/{}  {}".format(next(counter), steps, text)

    print()
    name = " ".join(ask(step("Level name"), hint="Example: Acheron").split())
    same_name = [lv for lv in levels
                 if lv["data"] and lv["data"]["name"].lower() == name.lower()]
    if same_name and not confirm(
            "  A level called '{}' is already on the site ({}). Add another one anyway?"
            .format(name, rank_text(same_name[0])), default=False):
        raise Cancelled()

    print()
    level_id = ask(
        step("Level ID"),
        hint="The number from Geometry Dash. Example: 62214792",
        check=lambda s: None if s.isdigit() else "The ID must be numbers only.",
    )
    same_id = [lv for lv in levels
               if lv["data"] and str(lv["data"]["id"]) == level_id]
    if same_id:
        if created:
            print("  Tip: to put a level that is already on the site on the Created list,")
            print("  cancel and use 'Add an EXISTING level' instead.")
        if not confirm(
                "  The ID {} is already used by '{}' ({}). Use it anyway?"
                .format(level_id, same_id[0]["data"]["name"], rank_text(same_id[0])),
                default=False):
            raise Cancelled()

    print()
    publisher = ask(
        step("Level publisher"),
        hint="The player who uploaded the level. Type - if you don't know.",
    )

    print()
    if created:
        creators_hint = ("Separate names with commas. Example: Zoink, Npesta\n"
                         "  Required here: only people listed as creators earn Creator Points.\n"
                         "  Include the publisher too if they helped make it.")
    else:
        creators_hint = ("Separate names with commas. Example: Zoink, Npesta\n"
                         "  Leave empty if the publisher is the only creator.")
    creators = split_list(ask(step("Level creators"), hint=creators_hint, required=created))

    print()
    verifier = ""
    while True:
        verifier = ask(
            step("Level verifier"),
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
        choose(step("Level difficulty"), difficulties, default=default_index)]

    print()
    print(step("Rating (in-game)"))
    rating = prompt_rating("Unrated" if created else None)

    print()
    print(step("NLW tier"))
    nlw = prompt_nlw(levels)

    print()
    print(step("GDDL tier"))
    gddl = prompt_gddl()

    print()
    print(step("Created date (D/M/YYYY)"))
    created_at = prompt_created_at()

    def check_link(text):
        if re.match(r"^https?://\S+$", text):
            return None
        return ("That doesn't look like a link. It should start with "
                "https:// (example: https://www.youtube.com/watch?v=...)")

    print()
    while True:
        link = ask(step("Verification video link"),
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
    tags = split_list(ask(step("Level tags"), hint=tag_hint, required=False))

    total = len(target_levels)
    print()
    print(step("Position on the Created list" if created else "Position on the list"))
    print("  The list has {} levels. Rank 1 is the top.".format(total))

    def check_rank(text):
        if text.isdigit() and 1 <= int(text) <= total + 1:
            return None
        return "Please type a rank from 1 to {}.".format(total + 1)

    position = int(ask(
        "Rank for this level (press Enter for the very bottom)",
        default=str(total + 1), check=check_rank,
    ))
    above = target_levels[position - 2] if position >= 2 else None
    below = target_levels[position - 1] if position <= total else None

    file_name = make_file_name(name, order)
    print()
    print("-" * 62)
    print("  Here is the level you are about to add:")
    print("-" * 62)
    print("  List:          " + ("Created" if created else "Ranked"))
    print("  Name:          " + name)
    print("  ID:            " + level_id)
    print("  Publisher:     " + publisher)
    print("  Creators:      " + (", ".join(creators) or "(none)"))
    print("  Verifier:      " + (verifier or "(none)"))
    print("  Difficulty:    " + difficulty)
    print("  Rating:        " + (rating or "(none)"))
    print("  NLW:           " + (nlw or "(none)"))
    print("  GDDL:          " + (str(gddl) if gddl is not None else "(none)"))
    print("  Created At:    " + (created_at or "(none)"))
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
        "rating": rating or "",
        "nlw": nlw or "",
        "gddl": gddl,
        "created_at": created_at or "",
        "verification": link,
        "tags": tags,
        "records": [],
    }

    level_path = DATA_DIR / (file_name + ".json")
    try:
        write_json(level_path, new_level)
        order.insert(position - 1, file_name)
        write_json(target_file(target), order, like=order_raw)
    except OSError as error:
        if level_path.exists() and file_name not in order:
            level_path.unlink()
        print("\n  ! Could not save: {}".format(error))
        print("  Nothing was changed. Is one of the files open in another program?")
        return

    print()
    print("  Done! '{}' was added at #{}.".format(name, position))

    if not created:
        refresh_packs()


def edit_level():
    heading("EDIT A LEVEL'S INFO")
    levels = [lv for lv in load_levels(include_legacy=True) if lv["data"]]
    if not levels:
        print("  There are no levels on the site.")
        return

    level = pick_level(levels, title="1/3  Select the level to edit", require_data=True)
    data = dict(level["data"])
    print("\n  Selected: " + level_label(level))

    options = [
        "Name (now: {!r})".format(data.get("name", "")),
        "Publisher (now: {!r})".format(data.get("author", "")),
        "Creators (now: {})".format(", ".join(data.get("creators", [])) or "(none)"),
        "Verifier (now: {!r})".format(data.get("verifier", "")),
        "Difficulty (now: {!r})".format(data.get("difficulty", "")),
        "Rating (now: {!r})".format(data.get("rating", "")),
        "NLW tier (now: {!r})".format(data.get("nlw", "")),
        "GDDL tier (now: {!r})".format(data.get("gddl", "")),
        "Created date D/M/YYYY (now: {!r})".format(data.get("created_at", "")),
        "Verification link (now: {!r})".format(data.get("verification", "")),
        "Tags (now: {})".format(", ".join(data.get("tags", [])) or "(none)"),
    ]

    print()
    print("2/3  Which fields do you want to edit?")
    picked = choose_many("Select one or more fields:", options)

    new_rating = data.get("rating")
    new_nlw = data.get("nlw")
    new_gddl = data.get("gddl")
    new_created_at = data.get("created_at")

    def check_link(text):
        if re.match(r"^https?://\S+$", text):
            return None
        return "That doesn't look like a link. It should start with https://."

    for idx in picked:
        if idx == 0:
            data["name"] = " ".join(ask("New level name", default=data.get("name", "")).split())
        elif idx == 1:
            data["author"] = ask("New publisher", default=data.get("author", ""))
        elif idx == 2:
            data["creators"] = split_list(ask(
                "New creators (comma-separated)",
                default=", ".join(data.get("creators", [])),
                required=False,
            ))
        elif idx == 3:
            data["verifier"] = ask("New verifier", default=data.get("verifier", ""), required=False)
        elif idx == 4:
            diffs = list(DIFFICULTIES)
            cur_d = data.get("difficulty")
            if cur_d and cur_d not in diffs:
                diffs.append(cur_d)
            d_idx = diffs.index(cur_d) if cur_d in diffs else 0
            data["difficulty"] = diffs[choose("New difficulty", diffs, default=d_idx)]
        elif idx == 5:
            new_rating = prompt_rating(data.get("rating"))
        elif idx == 6:
            new_nlw = prompt_nlw(levels, data.get("nlw"))
        elif idx == 7:
            new_gddl = prompt_gddl(data.get("gddl"))
        elif idx == 8:
            new_created_at = prompt_created_at(data.get("created_at"))
        elif idx == 9:
            data["verification"] = ask("New verification link", default=data.get("verification", ""), check=check_link)
        elif idx == 10:
            data["tags"] = split_list(ask(
                "New tags (comma-separated)",
                default=", ".join(data.get("tags", [])),
                required=False,
            ))

    updated_data = with_metadata_fields(
        data,
        rating=new_rating if 5 in picked else None,
        nlw=new_nlw if 6 in picked else None,
        gddl=new_gddl if 7 in picked else None,
        created_at=new_created_at if 8 in picked else None,
    )

    print()
    print("-" * 62)
    print("  3/3  Review updated values for {}:".format(updated_data.get("name", level["file"])))
    print("-" * 62)
    print("  Rating:     " + (str(updated_data.get("rating")) or "(none)"))
    print("  NLW:        " + (str(updated_data.get("nlw")) or "(none)"))
    print("  GDDL:       " + (str(updated_data.get("gddl")) or "(none)"))
    print("  Created At: " + (str(updated_data.get("created_at")) or "(none)"))
    print()
    if not confirm("Save changes to data/{}.json?".format(level["file"])):
        raise Cancelled()

    level["data"] = updated_data
    try:
        save_level(level)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        return

    print("\n  Done! Updated data/{}.json.".format(level["file"]))


def remove_level(target="ranked"):
    created = target == "created"
    heading("REMOVE A LEVEL FROM THE CREATED LIST" if created else "REMOVE A LEVEL")
    order, order_raw = target_order(target)
    levels = load_levels(order)
    if not levels:
        print("  The list is empty - there is nothing to remove.")
        return

    level = pick_level(levels, title="1/2  Select the level to remove")
    data = level["data"]

    if created:
        ranked_order, _ = load_order()
        legacy_order, _ = load_legacy_order()
        elsewhere = level["file"] in ranked_order or level["file"] in legacy_order
        other_name = "ranked or legacy list"
    else:
        created_order, _ = load_created_order()
        elsewhere = level["file"] in created_order
        other_name = "Created list"

    print()
    print("-" * 62)
    print("  You selected:  " + level_label(level))
    if elsewhere:
        print("  This level is also on the {}.".format(other_name))
        print("  It is only taken off THIS list; the level file and its records are kept.")
        if not created:
            print_pack_impact({level["file"]})
        print("-" * 62)
        print()
        if not confirm("Take it off this list?", default=False):
            raise Cancelled()
        try:
            unlink_from_list(target, {level["file"]})
        except OSError as error:
            print("\n  ! Could not save: {}".format(error))
            print("  Is one of the files open in another program?")
            return
        print()
        print("  Done! {} was taken off the {} list.".format(
            level_label(level), "Created" if created else "ranked"))
        if not created:
            refresh_packs()
        return

    if data:
        print("  Level ID:      {}".format(data["id"]))
        print("  Publisher:     " + str(data.get("author", "")))
        count = len(data.get("records", []))
        print("  Records:       {}".format(count))
        if count:
            print("  ! Removing this level also deletes its {} record(s)."
                  .format(count))
    print("-" * 62)

    print_pack_impact({level["file"]})

    token = str(data["id"]) if data else level["file"]
    what = "level ID" if data else "file name"
    print()
    print("2/2  To make sure this is the right level, type its {}.".format(what))
    ask("Type {} to remove it (or cancel)".format(token),
        check=lambda s: None if s.strip() == token
        else "That doesn't match {}. Try again, or type cancel.".format(token))

    try:
        packs_changed, packs_deleted = remove_level_files({level["file"]})
    except OSError as error:
        print("\n  ! Could not remove it: {}".format(error))
        print("  Is one of the files open in another program?")
        return

    print()
    print("  Done! {} was removed.".format(level_label(level)))
    if level["rank"] < len(order):
        print("  Every level below it moved up one rank, so points changed a little.")
    if packs_changed:
        print("  Removed from {} pack(s).".format(packs_changed))
    for pack_name in packs_deleted:
        print("  Pack '{}' had nothing left and was deleted.".format(pack_name))

    if not created:
        refresh_packs()


def points_for(rank, total):
    if total <= 1:
        return MAX_POINTS
    step = (MAX_POINTS - MIN_POINTS) / (total - 1)
    return round(MAX_POINTS - (rank - 1) * step, 3)


def move_level(target="ranked"):
    heading("MOVE A LEVEL IN THE CREATED LIST" if target == "created" else "MOVE A LEVEL")
    order, order_raw = target_order(target)
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
        write_json(target_file(target), order, like=order_raw)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        print("  Nothing was changed. Is the file open in another program?")
        return

    print()
    print("  Done! {} was {} from #{} to #{}.".format(
        level_name(level), "raised" if raised else "lowered", old_rank, new_rank))

    if target == "ranked":
        refresh_packs()


def add_existing_to_created():
    heading("ADD AN EXISTING LEVEL TO THE CREATED LIST")
    created_order, created_raw = load_created_order()
    levels = [lv for lv in load_levels(include_legacy=True)
              if lv["data"] and lv["file"] not in created_order]
    if not levels:
        print("  Every level on the site is already on the Created list.")
        return

    level = pick_level(levels, title="1/4  Select the level", require_data=True)
    data = level["data"]
    print("\n  Level: " + level_label(level))

    creators = list(data.get("creators", []))
    print()
    if creators:
        print("  Creators: " + ", ".join(creators))
    else:
        print("  ! This level has no creators listed. Only creators earn Creator Points.")
    if not creators or confirm("2/4  Change the creators list?", default=False):
        creators = split_list(ask(
            "2/4  Level creators",
            hint="Separate names with commas. Include the publisher if they helped make it."))

    
    current = data.get("rating")

    if current in RATINGS:
        rating = current
        print("3/4  Level rating (in-game)")
        print("  Keeping existing rating: {}".format(rating))
    else:
        rating = RATINGS[choose(
            "3/4  Level rating (in-game)",
            RATINGS,
            default=RATINGS.index("Unrated")
    )]


    total = len(created_order)
    print()
    print("4/4  Position on the Created list")
    print("  The Created list has {} levels. Rank 1 is the top.".format(total))

    def check_rank(text):
        if text.isdigit() and 1 <= int(text) <= total + 1:
            return None
        return "Please type a rank from 1 to {}.".format(total + 1)

    position = int(ask("Rank for this level (press Enter for the very bottom)",
                       default=str(total + 1), check=check_rank))

    print()
    print("-" * 62)
    print("  Level:     " + level_name(level))
    print("  Creators:  " + ", ".join(creators))
    print("  Rating:    " + rating)
    print("  Rank:      #{} on the Created list".format(position))
    print("-" * 62)
    if not confirm("Add it to the Created list?"):
        raise Cancelled()

    data["creators"] = creators
    level["data"] = with_rating(data, rating)
    created_order.insert(position - 1, level["file"])
    try:
        save_level(level)
        write_json(CREATED_FILE, created_order, like=created_raw)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        print("  Is a file open in another program?")
        return

    print()
    print("  Done! {} was added to the Created list at #{}.".format(level_name(level), position))


def set_rating():
    heading("CHANGE A LEVEL'S RATING")
    created_order, _ = load_created_order()
    levels = [lv for lv in load_levels(created_order) if lv["data"]]
    if not levels:
        print("  The Created list is empty.")
        return

    level = pick_level(levels, title="1/2  Select the level", require_data=True)
    data = level["data"]
    current = data.get("rating") if data.get("rating") in RATINGS else "Unrated"
    print("\n  Current rating: " + current)
    new = RATINGS[choose("2/2  New rating", RATINGS, default=RATINGS.index(current))]
    if new == current:
        print("\n  Nothing to change.")
        return
    if not confirm("Change {} from {} to {}?".format(level_name(level), current, new)):
        raise Cancelled()

    level["data"] = with_rating(data, new)
    try:
        save_level(level)
    except OSError as error:
        print("\n  ! Could not save: {}".format(error))
        return
    print("\n  Done! {} is now {}.".format(level_name(level), new))


# ===============================================================
#  SUB-MODULE 2: RECORD MANAGER
# ===============================================================

def add_record():
    heading("ADD A RECORD")
    levels = load_levels(include_legacy=True)
    if not [lv for lv in levels if lv["data"]]:
        print("  There are no levels on the list yet.")
        return
    players = known_players(levels)

    level = pick_level(levels, title="1/4  Select the level", require_data=True)
    data = level["data"]
    print("\n  Level: " + level_label(level))
    if level["legacy"]:
        print("  Note: this is a legacy level. It has no points, but counts toward packs.")

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


def bulk_add_records():
    heading("BULK ADD RECORDS")

    levels = [lv for lv in load_levels(include_legacy=True) if lv["data"]]
    if not levels:
        print("  There are no levels available.")
        return

    players = known_players(levels)

    print()
    if players:
        print("  Players already on the site: " +
              ", ".join(sorted(players.values(), key=str.lower)))

    user = ask("Player name")

    if user.lower() in players:
        user = players[user.lower()]
    elif not confirm(
        "  '{}' isn't on the site yet. Add records for them anyway?"
        .format(user), default=False
    ):
        raise Cancelled()

    selected = {}
    unmatched = []

    print()
    print("PASTE LEVEL NAMES")
    print("  Paste one level name per line.")
    print("  You can also separate names with commas.")
    print("  Press Enter on an empty line when finished.")

    while True:
        line = ask("Level name", required=False)
        if not line:
            break

        for name in line.split(","):
            name = name.strip()
            if not name:
                continue

            matches = [
                lv for lv in levels
                if name.lower() in (
                    str(lv["data"].get("name", "")).lower(),
                    lv["file"].lower(),
                    str(lv["data"].get("id", "")).lower()
                )
            ]

            if len(matches) == 1:
                selected[matches[0]["file"]] = matches[0]
            elif not matches:
                unmatched.append(name)
            else:
                unmatched.append(name + " (ambiguous - multiple matches)")

    if confirm("Would you also like to search and select levels?",
               default=True):
        while True:
            available = [
                lv for lv in levels
                if lv["file"] not in selected
            ]

            if not available:
                print("  All available levels have been selected.")
                break

            if not confirm("Add another level?", default=True):
                break

            level = pick_level(
                available,
                title="Search for a level to add"
            )
            selected[level["file"]] = level

    if unmatched:
        print()
        print("  Names that couldn't be matched:")
        for name in unmatched:
            print("   - " + name)

    if not selected:
        print("\n  No levels were selected.")
        return

    eligible = []
    duplicates = []

    for level in selected.values():
        data = level["data"]
        taken = {
            r.get("user", "").lower()
            for r in data.get("records", [])
        }

        if user.lower() in taken:
            duplicates.append(level)
        else:
            eligible.append(level)

    if duplicates:
        print()
        print("  These levels already have a record for {}:".format(user))
        for level in duplicates:
            print("   - " + level_name(level))
        print("  They will be skipped.")

    if not eligible:
        print("\n  No new records to add.")
        return

    verifier_levels = [
        lv for lv in eligible
        if (lv["data"].get("verifier") or "").strip().lower() == user.lower()
    ]

    if verifier_levels:
        print()
        print("  {} is also the verifier of {} selected level(s)."
              .format(user, len(verifier_levels)))
        if not confirm("Continue adding these records?", default=False):
            raise Cancelled()

    today_dt = datetime.date.today()
    today = "{}/{}/{}".format(
        today_dt.day, today_dt.month, today_dt.year
    )

    def parse_bulk_date(value):
        if value.lower() == "today":
            return today

        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                dt = datetime.datetime.strptime(value, fmt).date()
                return "{}/{}/{}".format(dt.day, dt.month, dt.year)
            except ValueError:
                pass

        return None

    def ask_bulk_date(question, default=None):
        while True:
            value = ask(
                question,
                hint="Use D/M/YYYY (example: 28/4/2026), or type today.",
                default=default
            )
            result = parse_bulk_date(value)
            if result:
                return result
            print("  ! Invalid date. Please try again.")

    print()
    date_method = choose(
        "How would you like to assign record dates?",
        [
            "Same date for every record",
            "Enter dates individually",
            "Default date + individual overrides"
        ],
        default=2
    )

    dates = {}

    if date_method == 0:
        shared_date = ask_bulk_date("Date for all records", default=today)
        dates = {lv["file"]: shared_date for lv in eligible}

    elif date_method == 1:
        for i, level in enumerate(eligible, 1):
            print()
            print("{}/{}  {}".format(
                i, len(eligible), level_name(level)
            ))
            dates[level["file"]] = ask_bulk_date("Record date")

    else:
        default_date = ask_bulk_date(
            "Default date for all records", default=today
        )

        for i, level in enumerate(eligible, 1):
            print()
            print("{}/{}  {}".format(
                i, len(eligible), level_name(level)
            ))
            print("  Current date: {}".format(default_date))

            change = ask(
                "Change this date? (y/N)",
                required=False
            ).lower()

            if change in ("y", "yes"):
                dates[level["file"]] = ask_bulk_date("New date")
            else:
                dates[level["file"]] = default_date

    print()
    link_method = choose(
        "How would you like to handle video links?",
        [
            "No video links",
            "Use one shared video link",
            "Enter individual video links"
        ],
        default=0
    )

    links = {}

    def check_bulk_link(value):
        if not value or re.match(r"^https?://\S+$", value):
            return None
        return "The link must start with https:// or http://."

    if link_method == 1:
        shared_link = ask(
            "Shared video link",
            required=False,
            check=check_bulk_link
        )
        links = {lv["file"]: shared_link for lv in eligible}

    elif link_method == 2:
        for i, level in enumerate(eligible, 1):
            print()
            print("{}/{}  {}".format(
                i, len(eligible), level_name(level)
            ))
            links[level["file"]] = ask(
                "Video link (Enter to skip)",
                required=False,
                check=check_bulk_link
            )

    else:
        links = {lv["file"]: "" for lv in eligible}

    print()
    print("=" * 62)
    print("  BULK RECORDS SUMMARY")
    print("=" * 62)
    print("  Player: {}".format(user))
    print("  New records: {}".format(len(eligible)))
    print("  Skipped duplicates: {}".format(len(duplicates)))
    print()

    for i, level in enumerate(eligible, 1):
        print("  {}. {}".format(i, level_name(level)))
        print("     Date: {}".format(dates[level["file"]]))
        print("     Video: {}".format(
            links[level["file"]] or "(none)"
        ))

    print()
    if not confirm("Save all {} records?".format(len(eligible))):
        raise Cancelled()

    for level in eligible:
        level["data"].setdefault("records", []).append({
            "user": user,
            "link": links[level["file"]],
            "date": dates[level["file"]]
        })

    try:
        for level in eligible:
            save_level(level)
    except OSError as error:
        print("\n  ! Could not save all records: {}".format(error))
        print("  Some earlier files may already have been saved.")
        return

    print()
    print("  Done! Added {} records for {}.".format(
        len(eligible), user
    ))
    if duplicates:
        print("  Skipped {} duplicate records.".format(len(duplicates)))
    if unmatched:
        print("  Could not match {} pasted name(s).".format(len(unmatched)))


def remove_record():
    heading("REMOVE A RECORD")
    levels = load_levels(include_legacy=True)
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

        normalized = text.replace("\\", "/")

        prefix = "assets/pfps/"
        if normalized.lower().startswith(prefix.lower()):
            normalized = normalized[len(prefix):]

        existing = PFP_DIR / normalized
        if existing.is_file():
            if existing.suffix.lower() not in PFP_EXTENSIONS:
                print("  ! Unsupported image format.")
                continue
            return prefix + existing.name, None

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

        if isinstance(job[0], bytes):
            job[1].write_bytes(job[0])
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
    return sorted(result, key=lambda lv: lv["rank"] or 10**9)


def ban_player():
    heading("BAN A PLAYER")
    players, raw = load_players()
    order, _ = load_order()
    levels = load_levels(order, include_legacy=True)
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

    to_legacy = []
    ranked = [lv for lv in credited_levels(usage) if lv["rank"]]
    if ranked:
        print()
        print("2/2  {} published or created these ranked levels:".format(name))
        for level in ranked:
            print("   - {}  {}".format(rank_text(level), level_name(level)))
        print("  They can be MOVED TO LEGACY: taken off the ranked list and added to the")
        print("  legacy list (no rank, no points). Every level below a moved level goes up")
        print("  one rank, so points and the leaderboard change. Unbanning does not move")
        print("  them back.")
        if confirm("Move some of these levels to legacy?", default=False):
            picked = choose_many(
                "Levels to move to legacy:",
                ["{}  {}".format(rank_text(lv), level_name(lv)) for lv in ranked])
            to_legacy = [ranked[i] for i in picked]
    else:
        print("\n  (They haven't published or created any ranked levels.)")

    print()
    if to_legacy:
        print("  Moving to legacy: " + ", ".join(level_name(lv) for lv in to_legacy))
    if not confirm("Ban {}?".format(name)):
        raise Cancelled()

    try:
        if to_legacy:
            move_to_legacy(lv["file"] for lv in to_legacy)
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
    if to_legacy:
        print("  {} level(s) moved to legacy.".format(len(to_legacy)))

        refresh_packs()


def unban_player():
    heading("UNBAN A PLAYER")
    players, raw = load_players()
    order, _ = load_order()
    levels = load_levels(order, include_legacy=True)
    banned = {k.lower(): k for k, info in players.items() if info.get("banned")}
    if not banned:
        print("  Nobody is banned right now.")
        return

    name = pick_player(banned.values(), players, "1/1  Select the player to unban")
    usage = find_usage(name, levels)
    show_usage(name, players, usage)

    in_legacy = [lv for lv in credited_levels(usage) if lv["legacy"]]
    if in_legacy:
        print()
        print("  These levels they published or created are in the legacy list:")
        for level in in_legacy:
            print("   - {}".format(level_name(level)))
        print("  Unbanning does NOT move them back to the ranked list.")

    print()
    if not confirm("Unban {}?".format(name)):
        raise Cancelled()

    try:
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
    levels = load_levels(order, include_legacy=True)
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
                print("      {}  {}".format(rank_text(level), level_name(level)))
            print_pack_impact(deleting_files, indent="      ")
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
            remove_level_files(deleting_files)
        if "profile" in picked and key:
            del players[key]
            save_players(players, raw)
    except OSError as error:
        print("\n  ! Something went wrong while saving: {}".format(error))
        return

    print()
    print("  Done! The selected parts of {} were removed.".format(name))

    refresh_packs()


def update_player():
    heading("UPDATE A PLAYER")
    players, raw = load_players()
    order, _ = load_order()
    levels = load_levels(order, include_legacy=True)
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

def run_created_menu():
    while True:
        try:
            choice = choose("Created List - What would you like to do?", [
                "Add a NEW level to the Created list",
                "Add an EXISTING level to the Created list",
                "Remove a level from the Created list",
                "Move a level (change its rank)",
                "Change a level's rating",
                "Back to Main Menu",
            ])
            if choice == 5:
                break
            if choice == 0:
                add_level("created")
            elif choice == 1:
                add_existing_to_created()
            elif choice == 2:
                remove_level("created")
            elif choice == 3:
                move_level("created")
            elif choice == 4:
                set_rating()
        except Cancelled:
            print("\n  Cancelled - nothing was changed.")
        except (ValueError, KeyError, TypeError) as error:
            print("\n  ! A data file looks broken: {}".format(error))
            print("  Nothing was changed.")


def run_levels_menu():
    while True:
        try:
            choice = choose("Level Manager - What would you like to do?", [
                "Add a level",
                "Edit a level",
                "Remove a level",
                "Move a level (change its rank)",
                "Back to Main Menu",
            ])
            if choice == 4:
                break
            if choice == 0:
                add_level()
            elif choice == 1:
                edit_level()
            elif choice == 2:
                remove_level()
            elif choice == 3:
                move_level()
        except Cancelled:
            print("\n  Cancelled - nothing was changed.")
        except (ValueError, KeyError) as error:
            print("\n  ! A data file looks broken: {}".format(error))
            print("  Nothing was changed.")


def run_records_menu():
    while True:
        try:
            choice = choose(
                "Record Manager - What would you like to do?",
                [
                    "Add a record",
                    "Remove a record",
                    "Bulk add records",
                    "Back to Main Menu"
                ]
            )

            if choice == 3:
                break
            if choice == 0:
                add_record()
            elif choice == 1:
                remove_record()
            elif choice == 2:
                bulk_add_records()

        except Cancelled:
            print("\n  Cancelled - nothing was changed.")
        except (ValueError, KeyError, TypeError) as error:
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
                            ["Levels (Add, Edit, Remove, Move)",
                             "Records (Add, Remove)",
                             "Players (Add, Remove/Ban, Update)",
                             "Created List (Add, Remove, Move, Rating)",
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
            run_created_menu()
        elif choice == 4:
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