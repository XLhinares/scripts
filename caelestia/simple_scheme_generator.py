import colorsys
import os

from materialyoucolor import scheme as m3


## COLOUR ====================================================================
class Colour(object):
    # CONSTRUCTOR -------------------------------------------------------------
    def __init__(self, value: int):
        self.r = value // 0x10000
        self.g = (value % 0x10000) // 0x100
        self.b = value % 0x100
        self._colour = (self.r, self.g, self.b)

    @classmethod
    def parseHex(cls, string: str) -> "Colour":
        string = string.lstrip("#")
        return Colour(int(string, 16))

    # GETTERS / SETTERS -------------------------------------------------------
    @property
    def tuple(self) -> tuple:
        return self._colour

    @property
    def hex(self) -> int:
        return (self.r << 16) | (self.g << 8) | self.b

    @property
    def argb(self) -> int:
        return (0xFF << 24) | (self.r << 16) | (self.g << 8) | self.b

    @property
    def as_hex_str(self) -> str:
        """Returns the color with as a hex string the format `#123456`"""
        return "#%02X%02X%02X" % self._colour

    @property
    def as_raw_hex_str(self) -> str:
        """Returns the color with as a hex string the format `123456`"""
        return "%02X%02X%02X" % self._colour

    @property
    def luminance(self) -> float:
        return 0.2126 * self.r + 0.7152 * self.g + 0.0722 * self.b

    @property
    def lightness(self) -> float:
        H, L, S = colorsys.rgb_to_hls(self.r / 255.0, self.g / 255.0, self.b / 255.0)
        return L

    @property
    def is_dark(self) -> bool:
        return self.luminance < 128

    def __str__(self) -> str:
        return self.as_raw_hex_str

    # METHODS -----------------------------------------------------------------
    def with_relative_lightness(self, lightness: int = 50) -> "Colour":
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
        return Colour(color_int)

    def with_lightness(self, lightness: int) -> "Colour":
        """Returns this color with the lightness adjusted to the given value.
        This allows use to not generate a tonal palette each time we want a color.
        This method is NOT centered on the base lightness.
        0=white, 100=black
        """
        H, L, S = colorsys.rgb_to_hls(self.r / 255.0, self.g / 255.0, self.b / 255.0)
        r_new, g_new, b_new = colorsys.hls_to_rgb(H, lightness / 100, S)
        color_int = (
            (int(r_new * 255) << 16) | (int(g_new * 255) << 8) | int(b_new * 255)
        )
        return Colour(color_int)

    def get_on_top_color(self) -> "Colour":
        """Return white (for dark colors) or black (for light colors)."""
        return Colour(0xFFFFFF) if self.is_dark else Colour(0x000000)

    def get_container_color(self, is_dark_mode=False, level=0) -> "Colour":
        """Return the color for a container on top of the current color.
        The level allows to stack containers on top of each other.
        """
        lightness = 46 if is_dark_mode else 62
        lightness += level * -3
        return self.with_relative_lightness(lightness)

    def get_on_container_color(self, is_dark_mode=False) -> "Colour":
        """Return the text color for the container (inverse of container)."""
        container = self.get_container_color(is_dark_mode)
        return container.get_on_top_color()


# SCHEME ======================================================================
class Scheme(object):
    # Color(0x93, 0x03, 0xAA) # set using hex
    # Color(12, 123, 3) # set using int
    def __init__(
        self,
        flavor: str,
        colors: dict[str, str],
        mode: str | None = None,
        name: str = "manual",
        variant: str = "default",
    ):
        self.name = name
        self.flavor = flavor
        self.mode = mode or (
            "dark" if Colour.parseHex(colors["surface"]).is_dark else "light"
        )
        self.variant = variant
        self.colours = colors

    @classmethod
    def from_caelestia_custom_scheme(
        cls,
        filepath: str,
    ) -> "Scheme":
        """Returns a scheme from a caelestia custom scheme file.

        The file should follows the format:
        ```
        background 16172C
        onBackground FFFFFF
        surface 16172C
        surfaceDim 16172C
        ```
        """
        with open(filepath, "r") as file_read:
            colors = {
                k.strip(): v.strip()
                for line in file_read.readlines()
                for (k, v) in [line.split(None, 1)]  # Split on first whitespace
            }
            return Scheme(
                flavor=f"{os.path.basename(filepath)}",
                colors=colors,
            )

    @classmethod
    def generate_from_base_colors(
        cls,
        flavor: str,
        surface: Colour,
        primary: Colour,
        secondary: Colour,
        tertiary: Colour,
        error: Colour = Colour(0xFFB4AB),
        success: Colour = Colour(0xB5CCBA),
    ) -> "Scheme":
        """Returns a dictionary matching m3 color scheme format,
        with colors changed to fit the provided colors.
        """

        dark_mode: bool = surface.is_dark
        # surface_scheme = (
        #     m3.Scheme.dark(surface.get_argb())
        #     if surface.is_dark()
        #     else m3.Scheme.light(surface.get_argb())
        # )
        colors = {
            # PALETTE
            "primary_paletteKeyColor": primary.as_raw_hex_str,
            "secondary_paletteKeyColor": secondary.as_raw_hex_str,
            "tertiary_paletteKeyColor": tertiary.as_raw_hex_str,
            "neutral_paletteKeyColor": surface.as_raw_hex_str,
            "neutral_variant_paletteKeyColor": surface.get_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            # SURFACE
            "background": surface.as_raw_hex_str,
            "onBackground": surface.get_on_top_color().as_raw_hex_str,
            "surface": surface.as_raw_hex_str,
            "surfaceDim": surface.as_raw_hex_str,  # unused?
            "surfaceBright": surface.as_raw_hex_str,  # unused?
            "surfaceContainerLowest": surface.get_container_color(
                is_dark_mode=dark_mode,
                level=-2,
            ).as_raw_hex_str,
            "surfaceContainerLow": surface.get_container_color(
                is_dark_mode=dark_mode,
                level=-1,
            ).as_raw_hex_str,
            "surfaceContainer": surface.get_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            "surfaceContainerHigh": surface.get_container_color(
                is_dark_mode=dark_mode,
                level=1,
            ).as_raw_hex_str,
            "surfaceContainerHighest": surface.get_container_color(
                is_dark_mode=dark_mode,
                level=2,
            ).as_raw_hex_str,
            "onSurface": surface.get_on_top_color().as_raw_hex_str,
            "surfaceVariant": surface.as_raw_hex_str,  # unused?
            "onSurfaceVariant": surface.get_on_top_color()
            .get_container_color(is_dark_mode=dark_mode, level=-8)
            .as_raw_hex_str,
            "inverseSurface": surface.get_on_top_color().as_raw_hex_str,  # unused?
            "inverseOnSurface": surface.as_raw_hex_str,  # unused?
            # PRIMARY
            "primary": primary.as_raw_hex_str,
            "onPrimary": primary.get_on_top_color().as_raw_hex_str,
            "primaryContainer": primary.get_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            "onPrimaryContainer": primary.get_on_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            "inversePrimary": primary.as_raw_hex_str,
            "primaryFixed": primary.as_raw_hex_str,
            "primaryFixedDim": primary.as_raw_hex_str,
            "onPrimaryFixed": primary.get_on_top_color().as_raw_hex_str,
            "onPrimaryFixedVariant": primary.as_raw_hex_str,
            # SECONDARY
            "secondary": secondary.as_raw_hex_str,
            "onSecondary": secondary.get_on_top_color().as_raw_hex_str,
            "secondaryContainer": secondary.get_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            "onSecondaryContainer": secondary.get_on_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            "secondaryFixed": secondary.as_raw_hex_str,
            "secondaryFixedDim": secondary.as_raw_hex_str,
            "onSecondaryFixed": secondary.get_on_top_color().as_raw_hex_str,
            "onSecondaryFixedVariant": secondary.as_raw_hex_str,
            # TERTIARY
            "tertiary": tertiary.as_raw_hex_str,
            "onTertiary": tertiary.get_on_top_color().as_raw_hex_str,
            "tertiaryContainer": tertiary.get_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            "onTertiaryContainer": tertiary.get_on_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            "tertiaryFixed": tertiary.as_raw_hex_str,
            "tertiaryFixedDim": tertiary.as_raw_hex_str,
            "onTertiaryFixed": tertiary.get_on_top_color().as_raw_hex_str,
            "onTertiaryFixedVariant": tertiary.as_raw_hex_str,
            # EXTRA
            "outline": surface.get_on_top_color()
            .get_container_color(is_dark_mode=dark_mode, level=-8)
            .as_raw_hex_str,
            "outlineVariant": surface.with_relative_lightness(
                47 if dark_mode else 55
            ).as_raw_hex_str,
            "shadow": surface.with_relative_lightness(95).as_raw_hex_str,
            "scrim": "000000",
            "surfaceTint": primary.as_raw_hex_str,
            # ERROR
            "error": error.as_raw_hex_str,
            "onError": error.get_on_top_color().as_raw_hex_str,
            "errorContainer": error.get_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            "onErrorContainer": error.get_on_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            # SUCCESS
            "success": success.as_raw_hex_str,
            "onSuccess": success.get_on_top_color().as_raw_hex_str,
            "successContainer": success.get_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            "onSuccessContainer": success.get_on_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
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
            "text": surface.get_on_top_color().as_raw_hex_str,
            "subtext1": surface.get_on_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            "subtext0": surface.get_on_container_color(
                is_dark_mode=dark_mode
            ).as_raw_hex_str,
            "overlay2": surface.get_container_color(
                is_dark_mode=dark_mode, level=2
            ).as_raw_hex_str,  # unused?
            "overlay1": surface.get_container_color(
                is_dark_mode=dark_mode, level=1
            ).as_raw_hex_str,  # unused?
            "overlay0": surface.get_container_color(
                is_dark_mode=dark_mode, level=0
            ).as_raw_hex_str,  # unused?
            "surface2": surface.as_raw_hex_str,  # unused?
            "surface1": surface.as_raw_hex_str,  # unused?
            "surface0": surface.as_raw_hex_str,  # unused?
            "base": surface.as_raw_hex_str,  # unused?
            "mantle": surface.as_raw_hex_str,  # unused?
            "crust": surface.as_raw_hex_str,  # unused?
        }

        return Scheme(
            flavor=flavor,
            mode="dark" if dark_mode else "light",
            colors=colors,
        )

    @classmethod
    def generate_from_base_colors_hex(
        cls,
        flavor: str,
        surface: str,
        primary: str,
        secondary: str,
        tertiary: str,
        error: str = "FFB4AB",
        success: str = "B5CCBA",
    ) -> "Scheme":
        """Returns a dictionary matching m3 color scheme format,
        with colors changed to fit the provided colors.
        """

        return Scheme.generate_from_base_colors(
            flavor=flavor,
            surface=Colour.parseHex(surface),
            primary=Colour.parseHex(primary),
            secondary=Colour.parseHex(secondary),
            tertiary=Colour.parseHex(tertiary),
        )

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "flavour": self.flavor,
            "mode": self.mode,
            "variant": self.variant,
            "colours": self.colours,
        }
