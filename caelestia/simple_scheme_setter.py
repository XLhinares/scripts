import json
import os
import subprocess
import sys

from simple_scheme_generator import Scheme
from simple_scheme_picker import ColorPicker

## PATHS ======================================================================
PATH_SCHEME_PICKER = os.path.expanduser("~/.scripts/caelestia/simple_scheme_picker.py")
PATH_CUSTOM_SCHEME_FOLDER = os.path.expanduser("~/.config/caelestia/schemes")
PATH_CAELESTIA_SCHEME = os.path.expanduser("~/.local/state/caelestia/scheme.json")

# Create custom scheme folder if needed
if not os.path.exists(PATH_CUSTOM_SCHEME_FOLDER):
    os.mkdir(PATH_CUSTOM_SCHEME_FOLDER)
    print(f"Created directory {PATH_CUSTOM_SCHEME_FOLDER}")


def get_custom_scheme_path(filepath: str) -> str:
    """Returns the path of the template matching a file.
    The file path is shortened to its basename to avoid over"""
    filename = os.path.basename(filepath)
    return f"{PATH_CUSTOM_SCHEME_FOLDER}/{filename}.txt"


def load_custom_scheme(name: str) -> Scheme | None:
    """ """
    try:
        scheme_path = get_custom_scheme_path(name)
        return Scheme.from_caelestia_custom_scheme(
            filepath=scheme_path,
        )
    except FileNotFoundError:
        print(f"Error: The file '{get_custom_scheme_path(name)}' was not found.")
        return None
    except Exception:
        print(f"Something went wrong when accessing {get_custom_scheme_path(name)}")
        return None


def save_custom_scheme(name: str, scheme: Scheme) -> None:
    """Replace the Caelestia scheme with the given scheme."""
    scheme_path = get_custom_scheme_path(name)
    if not os.path.exists(scheme_path):
        os.mknod(scheme_path)
    with open(scheme_path, "w") as file_write:
        print(f"Saving custom scheme to {scheme_path}!")
        file_write.writelines(
            [f"{key} {value}\n" for (key, value) in scheme.colours.items()]
        )


def create_scheme_from_image(image_path: str) -> None:
    """Run the color-picker on the image at <path> and generate a scheme from it."""

    # Check for existing values (to allow the color picker to not restart from scratch)
    existing_scheme = load_custom_scheme(image_path)
    base_values = (
        {
            "surface": "#000000",
            "primary": "#000000",
            "secondary": "#000000",
            "tertiary": "#000000",
        }
        if not existing_scheme
        else {
            "surface": f"#{existing_scheme.colours['surface']}",
            "primary": f"#{existing_scheme.colours['primary']}",
            "secondary": f"#{existing_scheme.colours['secondary']}",
            "tertiary": f"#{existing_scheme.colours['tertiary']}",
        }
    )

    color_picker = ColorPicker(image_path, base_values)
    result = color_picker.get_colors()

    try:
        colors_dict = json.loads(result)
        scheme = Scheme.generate_from_base_colors_hex(
            flavor=os.path.basename(image_path),
            surface=colors_dict["surface"],
            primary=colors_dict["primary"],
            secondary=colors_dict["secondary"],
            tertiary=colors_dict["tertiary"],
        )
        save_custom_scheme(image_path, scheme)

    except json.JSONDecodeError:
        print("Error: Failed to parse colors from the color picker.")
        print("Raw output:", result)
        exit(1)


def set_from_name(name: str) -> None:
    """(WIP) Need to wait for caelestia-cli to allow setting custom schemes"""
    custom_scheme_path = get_custom_scheme_path(name)
    if os.path.exists(custom_scheme_path):
        with open(custom_scheme_path, "r") as file_read:
            scheme = json.load(file_read)
            print(f"No caelestia-cli way to apply scheme {scheme}.")
            print("Use `force_set_from_name` for the moment")
    else:
        print(f"No custom template found for {wp_path}")
        subprocess.run(
            ["caelestia", "scheme", "set", "-n", "dynamic"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        exit(1)


def force_set_from_name(name: str) -> None:
    """Replaces the caelestia scheme file with a custom scheme matching the [name].

    This can be used as a posthook but changes will not be applied to apps that only listen to wallpaper changes.
    """
    scheme = load_custom_scheme(name)
    if scheme:
        with open(PATH_CAELESTIA_SCHEME, "w") as file_write:
            json.dump(scheme.to_json(), file_write, indent=2)
    else:
        print(f"Could not load custom scheme `{name}`. Aborting.")
        exit(1)


def remove_custom_scheme(name: str) -> None:
    custom_scheme_path = get_custom_scheme_path(name)
    if os.path.exists(custom_scheme_path):
        os.remove(custom_scheme_path)
    else:
        print(f"No scheme {name} found. Doing nothing.")


def get_current_wallpaper() -> str:
    return subprocess.run(
        ["caelestia", "shell", "wallpaper", "get"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip("\n")


def reload_wallpaper() -> None:
    subprocess.run(
        ["caelestia", "shell", "wallpaper", "set", get_current_wallpaper()],
    )


## MAIN =======================================================================
if __name__ == "__main__":
    ## GENERATE FROM <PATH>
    if len(sys.argv) >= 3 and sys.argv[1] == "create-from-path":
        create_scheme_from_image(sys.argv[2])

    ## GENERATE FROM WALLPAPER
    elif len(sys.argv) >= 2 and sys.argv[1] == "create-from-wp":
        wp_path = get_current_wallpaper()
        create_scheme_from_image(wp_path)
        reload_wallpaper()  # Force Caelestia to reload scheme (only in manual scheme mode)

    elif len(sys.argv) >= 3 and sys.argv[1] == "set-from-name":
        force_set_from_name(sys.argv[2])

    elif len(sys.argv) >= 2 and sys.argv[1] == "set-from-wp":
        wp_path = get_current_wallpaper()
        force_set_from_name(wp_path)

    elif len(sys.argv) >= 3 and sys.argv[1] == "remove-from-name":
        remove_custom_scheme(sys.argv[2])

    elif len(sys.argv) >= 2 and sys.argv[1] == "remove-from-wp":
        wp_path = get_current_wallpaper()
        remove_custom_scheme(wp_path)
        reload_wallpaper()  # Force Caelestia to reload scheme (only in manual scheme mode)

    else:
        CE = "\x1b[33m"  # Color yellow
        CR = "\x1b[0m"  # Color reset
        help_message = f"""Caelestia color scheme generation utility.

Usage: {CE}python simple_scheme_setter.py [arg]{CR}
Arguments:
    {CE}[set-from-name] <n>{CR}     Generates the scheme from its name <n>.
    {CE}[set-from-wp]{CR}           Generates the scheme from the caelestia WP.
    {CE}[create-from-path] <p>{CR}  Let the user create a scheme from the image at <path>.
    {CE}[create-from-wp]{CR}        Let the user create a scheme from the caelestia WP.
    {CE}[remove-from-name] <p>{CR}  Remove the custom scheme matching the <name>.
    {CE}[remove-from-wp]{CR}        Remove the custom scheme matching the caelestia WP.
    {CE}[help]{CR}                  Show this message"
"""
        print(help_message)
