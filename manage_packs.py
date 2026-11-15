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

import urllib.request
import urllib.parse
import mimetypes
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


TIER_MULTIPLIERS = {
    "Diamond": 2,
    "Gold": 1,
    "Silver": 0.5,
    "Bronze": 0.25,
}


def calculate_pack_tier(levels, order):
    """Calculate a pack's average rank and automatically assign its tier."""

    if not levels:
        raise ValueError("A pack must contain at least one level.")

    # Map each level filename to its rank.
    ranks = {filename: index + 1 for index, filename in enumerate(order)}

    missing = [level for level in levels if level not in ranks]
    if missing:
        raise ValueError(
            "These pack levels are missing from the demonlist: "
            + ", ".join(missing)
        )

    average_rank = sum(ranks[level] for level in levels) / len(levels)

    total_levels = len(order)

    if total_levels == 0:
        raise ValueError("The demonlist contains no levels.")

    # Divide the entire demonlist into four equal difficulty sections.
    tier_index = min(3, int((average_rank - 1) * 4 / total_levels))

    tier = ["Diamond", "Gold", "Silver", "Bronze"][tier_index]
    multiplier = TIER_MULTIPLIERS[tier]

    return average_rank, tier, multiplier




def update_pack_tier(pack, order):
    """Update tier, preserve custom multiplier, and sort levels."""

    average_rank, tier, default_multiplier = calculate_pack_tier(
        pack.get("levels", []), order
    )

    # Sort levels from hardest to easiest.
    ranks = {filename: index + 1 for index, filename in enumerate(order)}
    pack["levels"] = sorted(
        pack.get("levels", []),
        key=lambda level: ranks[level]
    )

    pack["average_rank"] = round(average_rank, 2)
    pack["tier"] = tier

    # Preserve custom multipliers.
    if not pack.get("custom_multiplier", False):
        pack["multiplier"] = default_multiplier

    pack.pop("multiplier_points", None)

    return pack


def sort_packs(packs):
    """Group packs from easiest tier to hardest, sorting each tier from easiest to hardest."""

    tier_order = {
        "Bronze": 0,
        "Silver": 1,
        "Gold": 2,
        "Diamond": 3,
    }

    return sorted(
        packs,
        key=lambda pack: (
            tier_order.get(pack.get("tier", ""), 4),
            -pack.get("average_rank", 0)
        )
    )



def choose_pack_multiplier(tier, current_custom=False, current_value=None):
    """Let the user choose the default or a custom multiplier."""

    default_multiplier = TIER_MULTIPLIERS[tier]

    print()
    print("  Bonus Multiplier Options:")
    print("  1. Use default tier multiplier ({}x)".format(default_multiplier))
    print("  2. Set a custom multiplier")

    choice = choose("Choose your bonus multiplier:", [
        "Default ({}x)".format(default_multiplier),
        "Custom multiplier",
    ], default=1 if current_custom else 0)

    if choice == 0:
        return default_multiplier, False

    multiplier = parse_multiplier(ask(
        "Enter your custom multiplier",
        default=str(current_value) if current_custom else None,
        check=valid_multiplier
    ))

    return multiplier, True



# ---------------------------------------------------------------
#  FILE LOCATIONS
# ---------------------------------------------------------------

ROOT        = Path(__file__).resolve().parent
DATA_DIR    = ROOT / "data"
LIST_FILE   = DATA_DIR / "_list.json"
PACKS_FILE  = DATA_DIR / "_packs.json"
THUMBS_DIR = ROOT / "assets" / "packs"

IMG_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".webp",
    ".gif", ".bmp", ".tif", ".tiff", ".avif"
)

MAX_IMAGE_SIZE = 15 * 1024 * 1024  # 15 MB
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


def recalculate_all_packs(packs, order):
    """Recalculate and sort every existing pack."""

    for pack in packs:
        update_pack_tier(pack, order)

    packs[:] = sort_packs(packs)

    return packs



def save_packs(packs, raw):
    write_json(PACKS_FILE, packs, like=raw)


def load_list():
    """Load only officially ranked levels. Legacy levels are excluded."""
    if LIST_FILE.exists():
        data, _ = read_json(LIST_FILE)
        if isinstance(data, list):
            return data
    return []


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
    avg = pack.get("average_rank", "N/A")

    return "{}. {}  [{}]  (Average: #{} | {} levels, {}x multiplier)".format(
        index + 1, pack.get("name", "(unnamed)"),
        tier, avg, lvls, pts)


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

def detect_image_extension(data):
    """Identify an image using its actual file signature."""

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"

    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"

    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"

    if data.startswith(b"BM"):
        return ".bmp"

    if data.startswith((b"II*\x00", b"MM\x00*")):
        return ".tiff"

    if (
        len(data) >= 12
        and data[:4] == b"RIFF"
        and data[8:12] == b"WEBP"
    ):
        return ".webp"

    if (
        len(data) >= 12
        and data[4:8] == b"ftyp"
        and data[8:12] in (b"avif", b"avis")
    ):
        return ".avif"

    return None


def unique_image_path(filename, extension):
    """Generate a filename that won't overwrite an existing image."""

    stem = Path(filename).stem
    stem = re.sub(r"[^\w-]", "_", stem.lower()).strip("_")

    if not stem:
        stem = "thumbnail"

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)

    candidate = THUMBS_DIR / (stem + extension)
    number = 2

    while candidate.exists():
        candidate = THUMBS_DIR / "{}_{}{}".format(
            stem, number, extension
        )
        number += 1

    return candidate


def download_image(url):
    """Download and validate an image from a URL."""

    parsed = urllib.parse.urlsplit(url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Please provide a valid HTTP or HTTPS URL.")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "BunkerDemons-PackManager/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        content_type = response.headers.get("Content-Type", "")
        data = response.read(MAX_IMAGE_SIZE + 1)

    if len(data) > MAX_IMAGE_SIZE:
        raise ValueError("Image exceeds the 15 MB download limit.")

    extension = detect_image_extension(data)

    if extension is None:
        raise ValueError(
            "The URL did not return a supported image. "
            "Make sure it links directly to an image."
        )

    original_name = Path(
        urllib.parse.unquote(parsed.path)
    ).name

    if original_name:
        filename = Path(original_name).stem
    else:
        filename = "downloaded_thumbnail"

    destination = unique_image_path(filename, extension)

    return data, destination


def ask_thumbnail(keep_text=None):
    print()
    print("  Thumbnail options:")
    print("   - Drag an image file directly into the terminal")
    print("   - Paste a direct image URL (Discord attachments supported)")
    print("   - Enter an image file name inside assets/packs/")
    print("   - Enter a path to an image on your computer")
    print("   - CSS gradient string (e.g. linear-gradient(...))")
    print("   - Solid color (e.g. #ff4500, blue)")

    if THUMBS_DIR.exists():
        images = sorted(
            p.name for p in THUMBS_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in IMG_EXTENSIONS
        )

        if images:
            print("  Available in assets/packs/: " + ", ".join(images[:10])
                  + (", ..." if len(images) > 10 else ""))

    if keep_text:
        print("  Press Enter to {}, or type 'none' to remove it.".format(
            keep_text
        ))
    else:
        print("  Press Enter to skip (you can add one later).")

    while True:
        text = ask("Thumbnail", required=False).strip().strip("\"'")

        if not text:
            return (None, None) if keep_text else ("", None)

        if text.lower() == "none" and keep_text:
            return "", None

        # -------------------------------------------------------
        # URL IMPORT
        # -------------------------------------------------------

        if re.match(r"^https?://\S+$", text, re.IGNORECASE):
            print("  Downloading image...")

            try:
                data, destination = download_image(text)

                relative_path = destination.relative_to(ROOT).as_posix()

                print("  Successfully downloaded image!")
                print("  Saved as: " + relative_path)

                job = {
                    "data": data,
                    "destination": destination
                }

                return relative_path, job

            except Exception as error:
                print("  ! Image download failed: {}".format(error))
                continue

        # -------------------------------------------------------
        # GRADIENT / COLOR
        # -------------------------------------------------------

        if "-gradient(" in text.lower():
            return text, None

        if (
            text.startswith("#")
            or text.lower().startswith("rgb")
            or text.lower().startswith("hsl")
        ):
            return text, None

        # -------------------------------------------------------
        # LOCAL IMAGE IMPORT
        # -------------------------------------------------------

        path = Path(text).expanduser()

        if path.is_file():
            if path.suffix.lower() not in IMG_EXTENSIONS:
                print("  ! Unsupported image format.")
                print("  Supported: " + ", ".join(IMG_EXTENSIONS))
                continue

            try:
                with path.open("rb") as file:
                    data = file.read(MAX_IMAGE_SIZE + 1)

                if len(data) > MAX_IMAGE_SIZE:
                    print("  ! Image exceeds the 15 MB size limit.")
                    continue

                extension = detect_image_extension(data)

                if extension is None:
                    print("  ! The selected file is not a supported image.")
                    continue

                # If the image is already inside assets/packs,
                # simply reference it instead of copying it again.

                try:
                    relative = path.resolve().relative_to(
                        THUMBS_DIR.resolve()
                    )

                    return (
                        "assets/packs/" + relative.as_posix(),
                        None
                    )

                except ValueError:
                    pass

                destination = unique_image_path(
                    path.stem,
                    extension
                )

                relative_path = destination.relative_to(ROOT).as_posix()

                print("  Image ready to import: " + relative_path)

                job = {
                    "source": path,
                    "destination": destination
                }

                return relative_path, job

            except OSError as error:
                print("  ! Could not read image: {}".format(error))
                continue

        # -------------------------------------------------------
        # EXISTING IMAGE IN ASSETS/PACKS
        # -------------------------------------------------------

        existing = THUMBS_DIR / text

        if existing.is_file():
            if existing.suffix.lower() in IMG_EXTENSIONS:
                return "assets/packs/" + existing.name, None

        # -------------------------------------------------------
        # UNKNOWN INPUT
        # -------------------------------------------------------

        if not any(c in text for c in ("/", "\\")):
            if confirm(
                "'{}' is not a file or URL. "
                "Treat it as a solid color?".format(text),
                default=True
            ):
                return text, None

        print(
            "  ! Could not find that file. Enter a valid image URL, "
            "file path, gradient, or color."
        )


def apply_copy(job):
    """Save an imported image after the user confirms the pack."""

    if not job:
        return

    destination = job["destination"]

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)

    if "data" in job:
        # Downloaded image
        destination.write_bytes(job["data"])

    elif "source" in job:
        # Locally selected image
        shutil.copy2(
            str(job["source"]),
            str(destination)
        )



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

        
        # Select multiple demons at once
        if answer.lower() == "all":
            selected_indices = list(range(len(shown)))
        else:
            parts = answer.replace(" ", "").split(",")
            selected_indices = []

            for part in parts:
                if part.isdigit() and 1 <= int(part) <= len(shown):
                    index = int(part) - 1
                    if index not in selected_indices:
                        selected_indices.append(index)
                else:
                    print("  ! '{}' is not a valid number.".format(part))

        for index in selected_indices:
            file_name = shown[index]

            if file_name not in picked:
                picked.append(file_name)
                print("  Added: " + level_names.get(file_name, file_name))

        if picked:
            print("  Selection updated ({} demons): {}".format(
                len(picked),
                ", ".join(level_names.get(f, f) for f in picked)
            ))



# ---------------------------------------------------------------
#  PACK ACTIONS
# ---------------------------------------------------------------


def pick_pack(packs, title="Select a pack"):
    if not packs:
        print("  There are no packs available.")
        return None

    print()
    print(title)
    print("  Type part of a pack's name to search.")
    print("  Type 'all' to display every pack.")
    print("  Type 'cancel' to go back.")

    while True:
        query = ask("Search pack")

        if query.lower() == "all":
            matches = list(range(len(packs)))
        else:
            query_lower = query.lower()

            matches = [
                i for i, pack in enumerate(packs)
                if query_lower in pack.get("name", "").lower()
            ]

        if not matches:
            print("  ! No packs found matching '{}'. Try another search.".format(query))
            continue

        print()
        print("  Matching packs:")

        for display_index, pack_index in enumerate(matches, 1):
            print("  {}) {}".format(
                display_index,
                pack_label(packs[pack_index], pack_index)
            ))

        print()
        print("  Type the number of the pack you want to select.")
        print("  Or type 'search' to search again.")

        def check(text):
            if text.lower() == "search":
                return None
            if text.isdigit() and 1 <= int(text) <= len(matches):
                return None
            return "Please enter a number from 1 to {}, or 'search'.".format(
                len(matches)
            )

        answer = ask("Your choice", check=check)

        if answer.lower() == "search":
            continue

        return matches[int(answer) - 1]


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

    # 2. Description
    print()
    description = ask(
        "2/4 Description",
        hint="A brief sentence describing the pack (optional).",
        required=False
    )

    # 3. Thumbnail
    print()
    print("5/5 Pack Thumbnail")
    thumbnail, copy_job = ask_thumbnail()

    # 4. Demons
    print()
    print("--- Select Demons for this Pack ---")
    levels = pick_levels(order, level_names)
    average_rank, tier, multiplier = calculate_pack_tier(levels, order)
    multiplier, custom_multiplier = choose_pack_multiplier(tier)

    pack_id = make_pack_id(name, [p.get("id", "") for p in packs])

    print()
    print("-" * 62)
    print("  Summary of the new pack:")
    print("-" * 62)
    print("  Name:         " + name)
    print("  ID:           " + pack_id)
    print("  Average Rank: {:.2f}".format(average_rank))
    print("  Tier:         " + tier)
    print("  Multiplier:   " + str(multiplier) + "x")
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
        "average_rank": round(average_rank, 2),
        "tier": tier,
        "multiplier": multiplier,
        "custom_multiplier": custom_multiplier,
        "levels": levels,
    }

    update_pack_tier(new_pack, order)
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
    "Description",
    "Thumbnail",
    "Demons (levels in the pack)",
    "Bonus Multiplier",
])

    new_name       = pack.get("name", "")
    new_tier       = pack.get("tier", "")
    new_multiplier = get_multiplier(pack)
    new_custom_multiplier = pack.get("custom_multiplier", False)
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
        new_desc = ask("New description", default=pack.get("description", "") or None, required=False)

    if 2 in picked:
        print()
        print("Thumbnail (current: {})".format(pack.get("thumbnail") or "(none)"))
        new_thumb, copy_job = ask_thumbnail(keep_text="keep current thumbnail")
        if new_thumb is None:
            new_thumb = pack.get("thumbnail", "")

    if 3 in picked:
        print()
        print("--- Update Demons in this Pack ---")
        new_levels = pick_levels(order, level_names, already_picked=new_levels)

    if 4 in picked:
        print("  Multiplier:   {}x -> {}x".format(
        get_multiplier(pack), new_multiplier
    ))

    # Calculate the current tier after any proposed level changes.
    _, calculated_tier, _ = calculate_pack_tier(new_levels, order)

    new_multiplier, new_custom_multiplier = choose_pack_multiplier(
        calculated_tier,
        current_custom=pack.get("custom_multiplier", False),
        current_value=get_multiplier(pack)
    )

    print()
    print("-" * 62)
    print("  Proposed changes for '{}':".format(pack.get("name", "")))
    print("-" * 62)
    if 0 in picked:
        print("  Name:         {} -> {}".format(pack.get("name", ""), new_name))
    if 1 in picked:
        print("  Description:  {}".format(new_desc or "(none)"))
    if 2 in picked:
        print("  Thumbnail:    {}".format(new_thumb or "(none)"))
    if 3 in picked:
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
        "multiplier": new_multiplier, 
        "custom_multiplier": new_custom_multiplier,
        "levels": new_levels,
    })

    update_pack_tier(updated_pack, order)

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

    # Automatically synchronize all existing pack tiers.
    try:
        packs, raw = load_packs()
        order = load_list()

        if packs:
            original = json.dumps(packs, sort_keys=True)

            recalculate_all_packs(packs, order)

            updated = json.dumps(packs, sort_keys=True)

            if original != updated:
                save_packs(packs, raw)
                print("  Automatically updated pack tiers and multipliers!")

    except (ValueError, KeyError, TypeError) as error:
        print("  ! Could not automatically update pack tiers: {}".format(error))

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