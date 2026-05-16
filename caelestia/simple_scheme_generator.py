import colorsys

from materialyoucolor import scheme as m3


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
    def parseHex(cls, string: str) -> "Color":
        string = string.lstrip("#")
        return Color(int(string, 16))

    def get_tuple(self) -> tuple:
        return self._color

    def get_hex(self) -> int:
        return (self.r << 16) | (self.g << 8) | self.b

    def get_argb(self) -> int:
        return (0xFF << 24) | (self.r << 16) | (self.g << 8) | self.b

    def get_hex_str(self) -> str:
        return "#%02X%02X%02X" % self._color

    def hex_as_str(self) -> str:
        return "%02X%02X%02X" % self._color

    def __str__(self) -> str:
        return self.get_hex_str()

    def get_luminance(self) -> float:
        return 0.2126 * self.r + 0.7152 * self.g + 0.0722 * self.b

    def is_dark(self) -> bool:
        return self.get_luminance() < 128

    def with_lightness(self, lightness: int = 50) -> "Color":
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

    def get_on_top_color(self) -> "Color":
        """Return white (for dark colors) or black (for light colors)."""
        return Color(0xFFFFFF) if self.is_dark() else Color(0x000000)

    def get_container_color(self, is_dark_mode=False, level=0) -> "Color":
        """Return the color for a container on top of the current color.
        The level allows to stack containers on top of each other.
        """
        lightness = 46 if is_dark_mode else 62
        lightness += level * -3
        return self.with_lightness(lightness)

    def get_on_container_color(self, is_dark_mode=False) -> "Color":
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
) -> dict:
    """Returns a dictionary matching m3 color scheme format,
    with colors changed to fit the provided colors.
    """

    dark_mode: bool = surface.is_dark()
    # surface_scheme = (
    #     m3.Scheme.dark(surface.get_argb())
    #     if surface.is_dark()
    #     else m3.Scheme.light(surface.get_argb())
    # )
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

    return new_scheme


def generate_scheme_from_hex(
    surface: str,
    primary: str,
    secondary: str,
    tertiary: str,
    error: str = "FFB4AB",
    success: str = "B5CCBA",
) -> dict:
    """Returns a dictionary matching m3 color scheme format,
    with colors changed to fit the provided colors.
    """

    return generate_scheme(
        surface=Color.parseHex(surface),
        primary=Color.parseHex(primary),
        secondary=Color.parseHex(secondary),
        tertiary=Color.parseHex(tertiary),
    )
