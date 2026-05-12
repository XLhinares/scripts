import colorsys
import json
import os
import subprocess
import sys

## PATHS ======================================================================
PATH_SCHEME_DATA = sys.argv[0].replace(".py", "_data.json")
if not os.path.exists(PATH_SCHEME_DATA):
    os.mknod(PATH_SCHEME_DATA)
    print(f"Created file: '{PATH_SCHEME_DATA}'")
PATH_CAELESTIA_SCHEME = os.path.expanduser("~/.local/state/caelestia/scheme.json")
PATH_SCHEME_PICKER = os.path.expanduser("~/.scripts/caelestia/image_scheme_picker.py")


## CLASSES ====================================================================
class Color(object):
    # Color(0x93, 0x03, 0xAA) # set using hex
    # Color(12, 123, 3) # set using int
    def __init__(self, value: int):
        self.r = value // 0x10000
        self.g = (value % 0x10000) // 0x100
        self.b = value % 0x100
        self._color = (self.r, self.g, self.b)

    @classmethod
    def parseHex(cls, string: str):
        string = string.lstrip("#")
        return Color(int(string, 16))

    def get_tuple(self):
        return self._color

    def get_hex_str(self):
        return "#%02X%02X%02X" % self._color

    def hex_as_str(self):
        return "%02X%02X%02X" % self._color

    def __str__(self):
        return self.get_hex_str()

    def get_luminance(self) -> float:
        return 0.2126 * self.r + 0.7152 * self.g + 0.0722 * self.b

    def is_dark(self) -> bool:
        return self.get_luminance() < 128

    def get_tonal_palette(self):
        """Generate a 100-step tonal palette (0=white, 50=base, 100=black)."""
        palette = []
        R, G, B = self.r / 255.0, self.g / 255.0, self.b / 255.0
        H, L, S = colorsys.rgb_to_hls(R, G, B)

        for tone in range(100):
            # Linearly interpolate lightness (0=white, 100=black)
            if tone <= 50:
                new_l = L + (1.0 - L) * (50 - tone) / 50
            else:
                new_l = L - L * (tone - 50) / 50
            new_l = max(0.0, min(1.0, new_l))
            r_new, g_new, b_new = colorsys.hls_to_rgb(H, new_l, S)
            color_int = (
                (int(r_new * 255) << 16) | (int(g_new * 255) << 8) | int(b_new * 255)
            )
            palette.append(Color(color_int))
        return palette

    def with_lightness(self, lightness: int = 50):
        """Returns this color with the lightness adjusted to the given value.
        This allows use to not generate a tonal palette each time we want a color.
        0=white, 50=base, 100=black
        """
        H, L, S = colorsys.rgb_to_hls(self.r / 255.0, self.g / 255.0, self.b / 255.0)
        if lightness <= 50:
            new_l = L + (1.0 - L) * (50 - lightness) / 50
        else:
            new_l = L - L * (lightness - 50) / 50
        new_l = max(0.0, min(1.0, new_l))
        r_new, g_new, b_new = colorsys.hls_to_rgb(H, new_l, S)
        color_int = (
            (int(r_new * 255) << 16) | (int(g_new * 255) << 8) | int(b_new * 255)
        )
        return Color(color_int)

    def get_on_top_color(self):
        """Return white (for dark colors) or black (for light colors)."""
        return Color(0xFFFFFF) if self.is_dark() else Color(0x000000)

    def get_container_color(self, is_dark_mode=False, level=0):
        """Return the color for a container on top of the current color.
        The level allows to stack containers on top of each other.
        """
        lightness = 46 if is_dark_mode else 62
        lightness += level * -3
        return self.with_lightness(lightness)

    def get_on_container_color(self, is_dark_mode=False):
        """Return the text color for the container (inverse of container)."""
        container = self.get_container_color(is_dark_mode)
        return container.get_on_top_color()


## FUNCTIONS ==================================================================
def generate_scheme(
    surface: Color,
    primary: Color,
    secondary: Color,
    tertiary: Color,
    error: Color = Color(0xFFB4AB),
    success: Color = Color(0xB5CCBA),
):
    test = Color(0xFF0000)
    dark_mode: bool = surface.is_dark()
    new_scheme = {
        "name": "dynamic",
        "flavour": "default",
        "mode": "dark" if dark_mode else "light",
        "variant": "tonalspot",
        "colours": {
            # PALETTE
            "primary_paletteKeyColor": primary.hex_as_str(),
            "secondary_paletteKeyColor": secondary.hex_as_str(),
            "tertiary_paletteKeyColor": tertiary.hex_as_str(),
            "neutral_paletteKeyColor": surface.hex_as_str(),
            "neutral_variant_paletteKeyColor": surface.get_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            # SURFACE
            "background": surface.hex_as_str(),
            "onBackground": surface.get_on_top_color().hex_as_str(),
            "surface": surface.hex_as_str(),
            "surfaceDim": surface.hex_as_str(),  # unused?
            "surfaceBright": surface.hex_as_str(),  # unused?
            "surfaceContainerLowest": surface.get_container_color(
                is_dark_mode=dark_mode,
                level=-2,
            ).hex_as_str(),
            "surfaceContainerLow": surface.get_container_color(
                is_dark_mode=dark_mode,
                level=-1,
            ).hex_as_str(),
            "surfaceContainer": surface.get_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            "surfaceContainerHigh": surface.get_container_color(
                is_dark_mode=dark_mode,
                level=1,
            ).hex_as_str(),
            "surfaceContainerHighest": surface.get_container_color(
                is_dark_mode=dark_mode,
                level=2,
            ).hex_as_str(),
            "onSurface": surface.get_on_top_color().hex_as_str(),
            "surfaceVariant": surface.hex_as_str(),  # unused?
            "onSurfaceVariant": surface.get_on_top_color()
            .get_container_color(is_dark_mode=dark_mode, level=-8)
            .hex_as_str(),
            "inverseSurface": surface.get_on_top_color().hex_as_str(),  # unused?
            "inverseOnSurface": surface.hex_as_str(),  # unused?
            # PRIMARY
            "primary": primary.hex_as_str(),
            "onPrimary": primary.get_on_top_color().hex_as_str(),
            "primaryContainer": primary.get_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            "onPrimaryContainer": primary.get_on_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            "inversePrimary": primary.hex_as_str(),
            "primaryFixed": primary.hex_as_str(),
            "primaryFixedDim": primary.hex_as_str(),
            "onPrimaryFixed": primary.get_on_top_color().hex_as_str(),
            "onPrimaryFixedVariant": primary.hex_as_str(),
            # SECONDARY
            "secondary": secondary.hex_as_str(),
            "onSecondary": secondary.get_on_top_color().hex_as_str(),
            "secondaryContainer": secondary.get_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            "onSecondaryContainer": secondary.get_on_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            "secondaryFixed": secondary.hex_as_str(),
            "secondaryFixedDim": secondary.hex_as_str(),
            "onSecondaryFixed": secondary.get_on_top_color().hex_as_str(),
            "onSecondaryFixedVariant": secondary.hex_as_str(),
            # TERTIARY
            "tertiary": tertiary.hex_as_str(),
            "onTertiary": tertiary.get_on_top_color().hex_as_str(),
            "tertiaryContainer": tertiary.get_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            "onTertiaryContainer": tertiary.get_on_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            "tertiaryFixed": tertiary.hex_as_str(),
            "tertiaryFixedDim": tertiary.hex_as_str(),
            "onTertiaryFixed": tertiary.get_on_top_color().hex_as_str(),
            "onTertiaryFixedVariant": tertiary.hex_as_str(),
            # EXTRA
            "outline": surface.get_on_top_color()
            .get_container_color(is_dark_mode=dark_mode, level=-8)
            .hex_as_str(),
            "outlineVariant": surface.with_lightness(
                47 if dark_mode else 55
            ).hex_as_str(),
            "shadow": surface.with_lightness(95).hex_as_str(),
            "scrim": "000000",
            "surfaceTint": primary.hex_as_str(),
            # ERROR
            "error": error.hex_as_str(),
            "onError": error.get_on_top_color().hex_as_str(),
            "errorContainer": error.get_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            "onErrorContainer": error.get_on_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            # SUCCESS
            "success": success.hex_as_str(),
            "onSuccess": success.get_on_top_color().hex_as_str(),
            "successContainer": success.get_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            "onSuccessContainer": success.get_on_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            # TERMINAL COLORS (hardcoded, as they're typically fixed)
            "term0": "080808",
            "term1": "cd7f00",
            "term2": "fbc342",
            "term3": "ffe2b8",
            "term4": "b7ac67",
            "term5": "e59a51",
            "term6": "e5c76d",
            "term7": "e7d6bf",
            "term8": "afa18f",
            "term9": "ee9400",
            "term10": "ffd88b",
            "term11": "fff2e3",
            "term12": "cec193",
            "term13": "f4b170",
            "term14": "fcd773",
            "term15": "ffffff",
            # CATPPUCCIN COLORS (hardcoded)
            "rosewater": "ffefe1",
            "flamingo": "faddc2",
            "pink": "ffd5b6",
            "mauve": "ffad7f",
            "red": "f4a24b",
            "maroon": "eeb378",
            "peach": "f9c581",
            "yellow": "ffefda",
            "green": "ffdd7b",
            "teal": "f3e08a",
            "sky": "e1df87",
            "sapphire": "b3d27e",
            "blue": "ffa2bd",
            "lavender": "ffbcbb",
            # KLINK COLORS (hardcoded)
            "klink": "559652",
            "klinkSelection": "559652",
            "kvisited": "c56810",
            "kvisitedSelection": "c4680d",
            "knegative": "c37600",
            "knegativeSelection": "c37600",
            "kneutral": "eb9900",
            "kneutralSelection": "ea9a00",
            "kpositive": "cca500",
            "kpositiveSelection": "cba500",
            # TEXT COLORS (derived from onSurface)
            "text": surface.get_on_top_color().hex_as_str(),
            "subtext1": surface.get_on_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            "subtext0": surface.get_on_container_color(
                is_dark_mode=dark_mode
            ).hex_as_str(),
            "overlay2": surface.get_container_color(
                is_dark_mode=dark_mode, level=2
            ).hex_as_str(),  # unused?
            "overlay1": surface.get_container_color(
                is_dark_mode=dark_mode, level=1
            ).hex_as_str(),  # unused?
            "overlay0": surface.get_container_color(
                is_dark_mode=dark_mode, level=0
            ).hex_as_str(),  # unused?
            "surface2": surface.hex_as_str(),  # unused?
            "surface1": surface.hex_as_str(),  # unused?
            "surface0": surface.hex_as_str(),  # unused?
            "base": surface.hex_as_str(),  # unused?
            "mantle": surface.hex_as_str(),  # unused?
            "crust": surface.hex_as_str(),  # unused?
        },
    }

    # Write as proper JSON (not Python dict string)
    with open(PATH_CAELESTIA_SCHEME, "w") as f:
        json.dump(new_scheme, f, indent=2)


def generate_scheme_from_name(scheme: str):
    try:
        with open(PATH_SCHEME_DATA, mode="r", encoding="utf-8") as read_file:
            data = json.load(read_file)

            if scheme in data:
                scheme_data = data[scheme]
                generate_scheme(
                    surface=Color.parseHex(scheme_data["surface"]),
                    primary=Color.parseHex(scheme_data["primary"]),
                    secondary=Color.parseHex(scheme_data["secondary"]),
                    tertiary=Color.parseHex(scheme_data["tertiary"]),
                )
            else:
                print(f"Error: Scheme '{scheme}' not found in the JSON file.")

    except FileNotFoundError:
        print(f"Error: The file '{PATH_SCHEME_DATA}' was not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the file.")


def set_from(path: str):
    # Run the color picker and capture its output
    result = subprocess.run(
        ["python", PATH_SCHEME_PICKER, path],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Parse the JSON output
    try:
        colors = json.loads(result.stdout.strip())
        print("Selected colors:", colors)
        # Load existing data
        with open(PATH_SCHEME_DATA, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Add the new scheme
        data[path] = {
            "surface": colors[0].lstrip("#"),
            "primary": colors[1].lstrip("#"),
            "secondary": colors[2].lstrip("#"),
            "tertiary": colors[3].lstrip("#"),
        }

        # Save the updated data
        with open(PATH_SCHEME_DATA, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        generate_scheme_from_name(path)

    except json.JSONDecodeError:
        print("Error: Failed to parse colors from the color picker.")
        print("Raw output:", result.stdout)


def get_current_wallpaper():
    return subprocess.run(
        ["caelestia", "shell", "wallpaper", "get"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip("\n")


## MAIN =======================================================================
if __name__ == "__main__":
    ## GENERATE FROM <PATH>
    if len(sys.argv) >= 3 and sys.argv[1] == "generate-from":
        generate_scheme_from_name(sys.argv[2])

    ## SET FROM <PATH>
    elif len(sys.argv) >= 3 and sys.argv[1] == "set-from":
        wp_path = sys.argv[2]
        set_from(wp_path)

    ## GENERATE FROM WALLPAPER
    elif len(sys.argv) >= 2 and sys.argv[1] == "generate-from-wp":
        wp_path = get_current_wallpaper()
        generate_scheme_from_name(wp_path)

    ## SET FROM WALLPAPER
    elif len(sys.argv) >= 2 and sys.argv[1] == "set-from-wp":
        wp_path = get_current_wallpaper()
        set_from(wp_path)

    else:
        print("Caelestia color scheme generation utility.")
        print(
            "Basically, it pulls the base colors of a scheme from the [theme-generator-base.json] file. It can be used to define a custom scheme for a wallpaper and hooked to caelestia's client."
        )
        print("")
        print("Usage: python theme-generator.py [arg]")
        print("Arguments:")
        print("  [generate-from] <name>     Generates the scheme from its name.")
        print(
            "  [generate-from-wp]         Generates the scheme from the caelestia WP."
        )
        print(
            "  [set-from] <path>          Let the user create a scheme from the image at <path>."
        )
        print(
            "  [set-from-wp]              Let the user create a scheme from the caelestia WP."
        )
        print("  [help]                     Show this message")
