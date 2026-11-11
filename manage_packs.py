#!/usr/bin/env python3
"""
==============================================================
  BUNKER DEMONS - PACK MANAGER
  Create, edit, and delete packs for your website.
==============================================================

HOW TO USE
  1. Put this file in your website folder (the one with index.html).
  2. Open a terminal / command prompt in that folder.
  3. Run it:    python manage_packs.py
               (if that doesn't work, try:  py manage_packs.py)
  4. Answer the questions. Type  cancel  at any question to stop.

Nothing is saved until you confirm at the very end.

Packs are stored in data/_packs.json.
Each pack has a name, description, thumbnail, tier, multiplier,
and a list of level file names (from data/_list.json).
"""

import json
import re
import shutil
import sys
import math
from pathlib import Path

def valid_multiplier(text):
    try:
        value = float(text)
        if not math.isfinite(value) or value < 0:
            return "Please type a valid number (0 or more)."
        return None
    except ValueError:
        return "Please type a valid number (0 or more)."


def parse_multiplier(text):
    value = float(text)
    return int(value) if value.is_integer() else value


def get_multiplier(pack):
    return pack.get("multiplier", pack.get("multiplier_points", 0))

# ---------------------------------------------------------------
#  FILE LOCATIONS
# ---------------------------------------------------------------

ROOT        = Path(__file__).resolve().parent
DATA_DIR    = ROOT / "data"
LIST_FILE   = DATA_DIR / "_list.json"
PACKS_FILE  = DATA_DIR / "_packs.json"
THUMBS_DIR  = ROOT / "assets" / "pack-thumbs"

IMG_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
MAX_SHOWN = 20

# ---------------------------------------------------------------
#  USER INTERACTION HELPERS
# ---------------------------------------------------------------

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
                print("  ! This field cannot be empty. Type something, or type 'cancel' to go back.")
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
        print("  ! Please answer with 'y' (yes) or 'n' (no).")


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
                 else "Please type numbers from 1 to {} separated by commas, or 'all'."
                 .format(len(options)))
    return parse(answer)


# ---------------------------------------------------------------
#  JSON HELPERS
# ---------------------------------------------------------------

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


def load_packs():
    if not PACKS_FILE.exists():
        PACKS_FILE.write_bytes(b"[]\n")
    data, raw = read_json(PACKS_FILE)
    if not isinstance(data, list):
        data = []
    return data, raw


def save_packs(packs, raw):
    write_json(PACKS_FILE, packs, like=raw)


def load_list():
    levels = []
    if LIST_FILE.exists():
        data, _ = read_json(LIST_FILE)
        if isinstance(data, list):
            levels.extend(data)
    legacy_file = DATA_DIR / "_legacy.json"
    if legacy_file.exists():
        legacy_data, _ = read_json(legacy_file)
        if isinstance(legacy_data, list):
            for f in legacy_data:
                if f not in levels:
                    levels.append(f)
    return levels


def load_level_names(order):
    names = {}
    for file_name in order:
        path = DATA_DIR / (file_name + ".json")
        try:
            data, _ = read_json(path)
            names[file_name] = data.get("name", file_name)
        except Exception:
            names[file_name] = file_name
    return names


def make_pack_id(name, existing_ids):
    base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "pack"
    taken = {i.lower() for i in existing_ids}
    candidate, number = base, 2
    while candidate in taken:
        candidate = "{}_{}".format(base, number)
        number += 1
    return candidate


def pack_label(pack, index):
    tier = pack.get("tier", "")
    pts = get_multiplier(pack)
    lvls = len(pack.get("levels", []))
    return "{}. {}  [{}]  ({} levels, {}x multiplier)".format(
        index + 1, pack.get("name", "(unnamed)"),
        tier, lvls, pts)


def existing_tiers(packs):
    # Mandatory standard tiers always come first
    base_tiers = ["Bronze", "Silver", "Gold", "Diamond"]
    seen = set(base_tiers)
    result = list(base_tiers)
    
    for p in packs:
        t = p.get("tier", "").strip()
        if t and t not in seen:
            seen.add(t)
            result.append(t)
    return result


# ---------------------------------------------------------------
#  THUMBNAIL HELPER
# ---------------------------------------------------------------

def ask_thumbnail(keep_text=None):
    print()
    print("  Thumbnail options:")
    print("   - Direct image URL (https://...)")
    print("   - Image file name already inside assets/pack-thumbs/")
    print("   - Path to an image on your computer (it will be copied automatically)")
    print("   - CSS gradient string (e.g. linear-gradient(...))")
    print("   - Solid color (e.g. #ff4500, blue)")
    if THUMBS_DIR.exists():
        images = sorted(p.name for p in THUMBS_DIR.iterdir()
                        if p.suffix.lower() in IMG_EXTENSIONS)
        if images:
            print("  Available in pack-thumbs/: " + ", ".join(images[:10])
                  + (", ..." if len(images) > 10 else ""))
    if keep_text:
        print("  Press Enter to {}, or type 'none' to remove it.".format(keep_text))
    else:
        print("  Press Enter to skip (you can add one later).")

    while True:
        text = ask("Thumbnail", required=False).strip("\"'")
        if not text:
            return (None, None) if keep_text else ("", None)
        if text.lower() == "none" and keep_text:
            return "", None
        if re.match(r"^https?://\S+$", text):
            return text, None
        if "-gradient(" in text.lower():
            return text, None
        if text.startswith("#") or text.lower().startswith("rgb") or text.lower().startswith("hsl"):
            return text, None

        path = Path(text).expanduser()
        if path.is_file():
            if path.suffix.lower() not in IMG_EXTENSIONS:
                print("  ! Unsupported image format. Use: " + ", ".join(IMG_EXTENSIONS))
                continue
            safe_name = re.sub(r"[^\w.\-]", "_", path.name.lower())
            destination = THUMBS_DIR / safe_name
            if destination.exists() and not confirm(
                    "  assets/pack-thumbs/{} already exists. Overwrite it?".format(safe_name),
                    default=False):
                continue
            return "assets/pack-thumbs/" + safe_name, (path, destination)

        if (THUMBS_DIR / text).is_file():
            return "assets/pack-thumbs/" + text, None

        if Path(text).suffix.lower() not in IMG_EXTENSIONS:
            if not any(c in text for c in ("/\\")):
                if confirm("  '{}' is not a file or URL. Treat it as a solid color?".format(text), default=True):
                    return text, None
            print("  ! Could not find that file. Please enter a valid URL, file path, gradient, or color.")
            continue
        if confirm("  assets/pack-thumbs/{} not found yet. Use that file name anyway?".format(text), default=False):
            return "assets/pack-thumbs/" + text, None


def apply_copy(job):
    if job:
        THUMBS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(job[0]), str(job[1]))


# ---------------------------------------------------------------
#  LEVEL PICKER
# ---------------------------------------------------------------

def search_levels(order, level_names, query):
    q = query.strip().lower()
    if not q:
        return order
    return [f for f in order
            if q in f.lower() or q in level_names.get(f, "").lower()]


def pick_levels(order, level_names, already_picked=None):
    picked = list(already_picked or [])

    print()
    print("  Pick the demons for this pack.")
    print("  Type part of a demon's name to search, or press Enter to view all.")
    print("  Type 'done' when you are finished selecting.")
    if picked:
        print("  Currently selected: " + ", ".join(
            level_names.get(f, f) for f in picked))

    while True:
        try:
            query = input("> Search level (or type 'done'): ").strip()
        except (EOFError, KeyboardInterrupt):
            raise Cancelled()
        if query.lower() == "cancel":
            raise Cancelled()
        if query.lower() == "done":
            if not picked:
                print("  ! A pack must contain at least one demon.")
                continue
            return picked

        matches = search_levels(order, level_names, query)
        if not matches:
            print("  ! No levels found matching that search.")
            continue

        shown = matches[:MAX_SHOWN]
        for i, file_name in enumerate(shown, 1):
            marker = "[x]" if file_name in picked else "[ ]"
            display = level_names.get(file_name, file_name)
            print("  {:>2}) {} {}".format(i, marker, display))
        if len(matches) > MAX_SHOWN:
            print("  ... and {} more results. Type more letters to refine your search."
                  .format(len(matches) - MAX_SHOWN))

        print("  Type a number to toggle selection (or search again):")
        try:
            answer = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            raise Cancelled()
        if answer.lower() == "cancel":
            raise Cancelled()
        if answer.lower() == "done":
            if not picked:
                print("  ! A pack must contain at least one demon.")
                continue
            return picked
        if not answer:
            continue

        parts = answer.replace(" ", "").split(",")
        for part in parts:
            if part.isdigit() and 1 <= int(part) <= len(shown):
                file_name = shown[int(part) - 1]
                if file_name in picked:
                    picked.remove(file_name)
                    print("  Removed: " + level_names.get(file_name, file_name))
                else:
                    picked.append(file_name)
                    print("  Added:   " + level_names.get(file_name, file_name))
            else:
                print("  ! '{}' is not a valid number on this list.".format(part))

        if picked:
            print("  Selection updated ({} demon{}): {}".format(
                len(picked), "" if len(picked) == 1 else "s",
                ", ".join(level_names.get(f, f) for f in picked)))


# ---------------------------------------------------------------
#  PACK ACTIONS
# ---------------------------------------------------------------

def pick_pack(packs, title="Select a pack"):
    if not packs:
        print("  There are no packs available.")
        return None

    print()
    print(title)

    for i, pack in enumerate(packs):
        print("  {:>2}) {}".format(i + 1, pack_label(pack, i)))

    def check(text):
        if text.isdigit() and 1 <= int(text) <= len(packs):
            return None
        return "Please type a number from 1 to {}.".format(len(packs))

    default = "1" if len(packs) == 1 else None
    answer = ask("Pack number", default=default, check=check)
    return int(answer) - 1


def create_pack():
    heading("CREATE A PACK")
    packs, raw = load_packs()
    order = load_list()

    if not order:
        print("  The demon list is empty. Add levels before creating packs.")
        return

    level_names = load_level_names(order)

    # 1. Name
    print()
    name = " ".join(ask(
        "1/5 Pack Name",
        hint="Example: Egyptian Hell Level Pack"
    ).split())

    taken_names = [p.get("name", "").lower() for p in packs]
    if name.lower() in taken_names:
        if not confirm(
            "A pack named '{}' already exists. Create another?".format(name),
            default=False
        ):
            raise Cancelled()

    # 2. Tier (Bronze, Silver, Gold, Diamond mandatory + custom)
    print()
    tiers = existing_tiers(packs)
    print("  Available Tiers:")
    for i, t in enumerate(tiers, 1):
        print("    {}. {}".format(i, t))
    print("    (You can type one of these numbers, or type a brand new tier name)")

    tier_input = ask("2/5 Tier", hint="Type a tier name or select from above")
    if tier_input.isdigit() and 1 <= int(tier_input) <= len(tiers):
        tier = tiers[int(tier_input) - 1]
    else:
        tier = " ".join(tier_input.split())

    # 3. Multiplier
    print()
    multiplier_raw = ask(
        "3/5 Multiplier Points",
        hint="Bonus points awarded upon completion. Example: 0.5, 1, 2, 5.5",
        check=valid_multiplier
    )
    multiplier = parse_multiplier(multiplier_raw)

    # 4. Description
    print()
    description = ask(
        "4/5 Description",
        hint="A brief sentence describing the pack (optional).",
        required=False
    )

    # 5. Thumbnail
    print()
    print("5/5 Pack Thumbnail")
    thumbnail, copy_job = ask_thumbnail()

    # 6. Demons
    print()
    print("--- Select Demons for this Pack ---")
    levels = pick_levels(order, level_names)

    pack_id = make_pack_id(name, [p.get("id", "") for p in packs])

    print()
    print("-" * 62)
    print("  Summary of the new pack:")
    print("-" * 62)
    print("  Name:         " + name)
    print("  ID:           " + pack_id)
    print("  Tier:         " + tier)
    print("  Multiplier:   " + str(multiplier))
    print("  Description:  " + (description or "(none)"))
    print("  Thumbnail:    " + (thumbnail or "(none)"))
    print("  Demons ({})".format(len(levels)))
    for f in levels:
        print("    - " + level_names.get(f, f))

    print()
    if not confirm("Save this pack?"):
        raise Cancelled()

    new_pack = {
        "id": pack_id,
        "name": name,
        "description": description,
        "thumbnail": thumbnail,
        "tier": tier,
        "multiplier": multiplier,
        "levels": levels,
    }

    packs.append(new_pack)

    try:
        apply_copy(copy_job)
        save_packs(packs, raw)
    except OSError as error:
        print("\n  ! Could not save file: {}".format(error))
        return

    print()
    print("  Success! Pack '{}' was created.".format(name))


def edit_pack():
    heading("EDIT A PACK")
    packs, raw = load_packs()
    if not packs:
        print("  There are no packs to edit.")
        return
    order       = load_list()
    level_names = load_level_names(order)

    idx = pick_pack(packs, "1/2  Choose the pack you want to modify")
    if idx is None:
        return
    pack = packs[idx]

    print()
    print("  Selected Pack: " + pack.get("name", "(unnamed)"))
    print()
    print("2/2  What would you like to change? (You can select multiple items)")
    picked = choose_many("Options:", [
        "Pack Name",
        "Tier",
        "Multiplier Points",
        "Description",
        "Thumbnail",
        "Demons (levels in the pack)",
    ])

    new_name       = pack.get("name", "")
    new_tier       = pack.get("tier", "")
    new_multiplier = get_multiplier(pack)
    new_desc       = pack.get("description", "")
    new_thumb      = pack.get("thumbnail", "")
    new_levels     = list(pack.get("levels", []))
    copy_job       = None

    if 0 in picked:
        print()
        taken = {
            p.get("name", "").lower()
            for i, p in enumerate(packs) if i != idx
        }
        while True:
            new_name = " ".join(ask("New pack name", default=pack.get("name", "")).split())
            if new_name.lower() in taken:
                if not confirm("A pack named '{}' already exists. Use this name anyway?".format(new_name), default=False):
                    continue
            break

    if 1 in picked:
        print()
        tiers = existing_tiers(packs)
        print("  Available Tiers:")
        for i, t in enumerate(tiers, 1):
            print("    {}. {}".format(i, t))
        
        tier_input = ask("New tier", default=pack.get("tier", ""))
        if tier_input.isdigit() and 1 <= int(tier_input) <= len(tiers):
            new_tier = tiers[int(tier_input) - 1]
        else:
            new_tier = " ".join(tier_input.split())

    if 2 in picked:
        print()
        new_multiplier = parse_multiplier(ask(
            "New multiplier points",
            default=str(get_multiplier(pack)),
            check=valid_multiplier
        ))

    if 3 in picked:
        print()
        new_desc = ask("New description", default=pack.get("description", "") or None, required=False)

    if 4 in picked:
        print()
        print("Thumbnail (current: {})".format(pack.get("thumbnail") or "(none)"))
        new_thumb, copy_job = ask_thumbnail(keep_text="keep current thumbnail")
        if new_thumb is None:
            new_thumb = pack.get("thumbnail", "")

    if 5 in picked:
        print()
        print("--- Update Demons in this Pack ---")
        new_levels = pick_levels(order, level_names, already_picked=new_levels)

    print()
    print("-" * 62)
    print("  Proposed changes for '{}':".format(pack.get("name", "")))
    print("-" * 62)
    if 0 in picked:
        print("  Name:         {} -> {}".format(pack.get("name", ""), new_name))
    if 1 in picked:
        print("  Tier:         {} -> {}".format(pack.get("tier", ""), new_tier))
    if 2 in picked:
        print("  Multiplier:   {} -> {}".format(get_multiplier(pack), new_multiplier))
    if 3 in picked:
        print("  Description:  {}".format(new_desc or "(none)"))
    if 4 in picked:
        print("  Thumbnail:    {}".format(new_thumb or "(none)"))
    if 5 in picked:
        print("  Demons ({})".format(len(new_levels)))
        for f in new_levels:
            print("    - " + level_names.get(f, f))
    print()
    if not confirm("Save these changes?"):
        raise Cancelled()

    updated_pack = dict(pack)
    updated_pack.update({
        "id": pack.get("id", make_pack_id(new_name, [])),
        "name": new_name,
        "description": new_desc,
        "thumbnail": new_thumb,
        "tier": new_tier,
        "multiplier": new_multiplier,
        "levels": new_levels,
    })
    updated_pack.pop("multiplier_points", None)

    packs[idx] = updated_pack
    try:
        apply_copy(copy_job)
        save_packs(packs, raw)
    except OSError as error:
        print("\n  ! Could not save file: {}".format(error))
        return

    print()
    print("  Success! Pack '{}' was updated.".format(new_name))


def delete_pack():
    heading("DELETE A PACK")
    packs, raw = load_packs()
    if not packs:
        print("  There are no packs to delete.")
        return

    idx = pick_pack(packs, "1/2  Choose the pack you want to delete")
    if idx is None:
        return
    pack = packs[idx]

    print()
    print("-" * 62)
    print("  WARNING: You are about to delete this pack:")
    print("-" * 62)
    print("  Name:         " + pack.get("name", "(unnamed)"))
    print("  Tier:         " + pack.get("tier", ""))
    print("  Multiplier:   " + str(get_multiplier(pack)))
    print("  Demons:       " + str(len(pack.get("levels", []))))
    print()
    print("2/2  To confirm deletion, type the exact name of the pack.")
    pack_name = pack.get("name", "")
    ask("Type '{}' to confirm".format(pack_name),
        check=lambda s: None if s.strip().lower() == pack_name.lower()
        else "Name does not match '{}'. Try again or type 'cancel'.".format(pack_name))

    packs.pop(idx)
    try:
        save_packs(packs, raw)
    except OSError as error:
        print("\n  ! Could not save file: {}".format(error))
        return

    print()
    print("  Deleted pack '{}'.".format(pack_name))


def list_packs():
    heading("ALL CREATED PACKS")
    packs, _ = load_packs()
    if not packs:
        print("  No packs have been created yet.")
        return
    for i, pack in enumerate(packs):
        print()
        print(pack_label(pack, i))
        desc = pack.get("description", "")
        if desc:
            print("    Description: " + desc)
        levels = pack.get("levels", [])
        if levels:
            order = load_list()
            level_names = load_level_names(order)
            print("    Demons: " + ", ".join(level_names.get(f, f) for f in levels))


# ---------------------------------------------------------------
#  MAIN MENU
# ---------------------------------------------------------------

def run_packs_menu():
    while True:
        try:
            choice = choose("Pack Manager Menu - Choose an option:", [
                "Create a pack",
                "Edit a pack",
                "Delete a pack",
                "List all packs",
                "Exit Manager",
            ])
            if choice == 4:
                break
            if choice == 0:
                create_pack()
            elif choice == 1:
                edit_pack()
            elif choice == 2:
                delete_pack()
            elif choice == 3:
                list_packs()
        except Cancelled:
            print("\n  Action cancelled. No changes were made.")
        except (ValueError, KeyError, TypeError) as error:
            print("\n  ! Data file error detected: {}".format(error))
            print("  No changes were saved.")


def main():
    if not LIST_FILE.exists():
        print("Couldn't find data/_list.json next to this script.")
        print("Make sure manage_packs.py is placed in your website's root folder.")
        return

    heading("BUNKER DEMONS - PACK MANAGER")
    print("  Tip: You can type 'cancel' at any prompt to exit without saving.")
    run_packs_menu()
    print("\nGoodbye!")


if __name__ == "__main__":
    try:
        main()
    finally:
        if sys.stdin and sys.stdin.isatty():
            try:
                input("\nPress Enter to exit...")
            except (EOFError, KeyboardInterrupt):
                pass