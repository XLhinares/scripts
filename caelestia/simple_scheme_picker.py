import json
import sys
import tkinter as tk

from PIL import Image, ImageOps, ImageTk
from simple_scheme_generator import Colour


# COLOR PICKER ================================================================
class ColorPicker:
    # CONSTRUCTOR -------------------------------------------------------------
    def __init__(
        self,
        image_path: str,
        default_colors: dict[str, str] = {
            "surface": "#000000",
            "primary": "#000000",
            "secondary": "#000000",
            "tertiary": "#000000",
        },
    ):
        self.image_path: str = image_path
        self.fallback_color = "#000000"
        self.colors: dict[str, str] = default_colors
        self.current_index: int = 0
        self._hovered_color = self.fallback_color

    # GETTERS / SETTERS -------------------------------------------------------

    @property
    def current_index_is_color(self) -> bool:
        return self.current_index < len(self.colors)

    @property
    def current_name(self) -> str:
        return (
            list(self.colors.keys())[self.current_index]
            if self.current_index_is_color
            else "other"
        )

    @property
    def current_color(self) -> str:
        return (
            self.colors[self.current_name]
            if self.current_index_is_color
            else self.fallback_color
        )

    @current_color.setter
    def current_color(self, value: str) -> None:
        self.colors[self.current_name] = value

    @property
    def hovered_color(self) -> str:
        return (
            self._hovered_color if self.current_index_is_color else self.fallback_color
        )

    @hovered_color.setter
    def hovered_color(self, value: str) -> None:
        self._hovered_color = value
        self.preview_panel.color_boxes[self.current_index].config(bg=value)
        if not hasattr(self.preview_panel, "_slider_dragging"):
            self.preview_panel.lightness = get_lightness_of(value)

    # METHODS -----------------------------------------------------------------

    def get_pixel_color(self, x, y):
        """Get the pixel color at the given coordinates."""
        # x_original = int(x * (self.original_image.width / self.scaled_image.width))
        # y_original = int(y * (self.original_image.height / self.scaled_image.height))
        # pixel = self.original_image.getpixel((x_original, y_original))
        pixel = self.scaled_image.getpixel((x, y))

        if isinstance(pixel, tuple):  # RGB or RGBA
            r, g, b = pixel[:3]
            hex_color = f"#{r:02X}{g:02X}{b:02X}"
        else:  # Grayscale
            hex_color = f"#{pixel:02X}{pixel:02X}{pixel:02X}"

        return hex_color

    def save_current_color(self) -> None:
        """Save the current colors (if needed)"""
        if self.current_index_is_color:
            self.current_color = self.hovered_color
            self.preview_panel.color_boxes[self.current_index].config(
                bg=self.current_color
            )

    def select_index(self, index) -> None:
        """Select an index and propagate the information.
        The index value is clamped between 0 and `len(self.colors) + 2`, to allow selecting the "cancel" and "validate" button.
        """
        # Switch the next index
        self.current_index = index % (
            len(self.colors) + 2
        )  # Add two for the cancel and validate buttons.

        if self.current_index_is_color:
            self.preview_panel.lightness_slider.set(
                get_lightness_of(self.current_color)
            )

        self.preview_panel.select_index(self.current_index, list(self.colors.values()))

    def validate(self) -> None:
        self.root.destroy()

    def cancel(self) -> None:
        self.root.destroy()
        exit(1)

    # INTERACTIONS ------------------------------------------------------------
    def _on_lightness_change(self, value):
        if self.current_index < len(self.colors):
            self.hovered_color = (
                Colour.parseHex(self.current_color)
                .with_lightness(int(value))
                .as_hex_str
            )
            self.current_color = self.hovered_color

    def _on_motion(self, event):
        """Update the live preview when the mouse moves."""
        self.preview_panel.zoom_panel.update(self.scaled_image, event.x, event.y)
        if self.current_index_is_color:
            self.hovered_color = self.get_pixel_color(event.x, event.y)

    def _on_down(self, event) -> None:
        self.select_index(self.current_index + 1)

    def _on_up(self, event) -> None:
        self.select_index(self.current_index - 1)

    def _on_click(self, event) -> None:
        """Update the value of the editing color to match the hovered pixel."""

        self.save_current_color()
        # If the last color is clicked, jump to "validate button",
        # otherwise, just go to next item down.
        if self.current_index == len(self.colors) - 1:
            self._on_down(None)
            self._on_down(None)
        else:
            self._on_down(None)

    def _on_enter(self, event) -> None:
        if self.current_index == len(self.colors):
            self.cancel()
        elif self.current_index == len(self.colors) + 1:
            self.validate()
        else:
            self._on_click(None)

    # TKINTER -----------------------------------------------------------------
    def get_colors(self):
        # WINDOW --------------------------------------------------------------
        self.root = tk.Tk()
        self.root.title("Click 4 colors")
        self.root.wm_attributes("-type", "dialog")  ## Window float

        # Make the window pseudo-fullscreen (cover the entire screen)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")

        # IMAGE ---------------------------------------------------------------
        self.original_image = Image.open(self.image_path)
        self.scaled_image = ImageOps.fit(
            self.original_image,
            (self.screen_width, self.screen_height),
            bleed=0.0,
            centering=(0.5, 0.5),
        )
        self.photo = ImageTk.PhotoImage(self.scaled_image)

        # Setup image canvas (fill the window)
        self.canvas = tk.Canvas(
            self.root,
            width=self.scaled_image.width,
            height=self.scaled_image.height,
            highlightthickness=0,
        )
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.pack()

        # PANEL ---------------------------------------------------------------
        print(f"values: {self.colors}")
        print(f"values: {list(self.colors.values())}")
        self.preview_panel = ColorPreviewPanel(
            self.root,
            color_names=list(self.colors.keys()),
            default_colors=list(self.colors.values()),
            on_lightness_change_callback=self._on_lightness_change,
            select_editing_color_callback=self.select_index,
            validate_callback=self.validate,
            cancel_callback=self.cancel,
        )
        self.preview_panel.frame.place(x=96, y=48, anchor=tk.NW)

        # INTERACTIONS --------------------------------------------------------
        self.canvas.focus_set()
        self.canvas.bind("<Down>", self._on_down)
        self.canvas.bind("<Up>", self._on_up)
        self.canvas.bind("<Return>", self._on_enter)  # "Enter" key
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-3>", self._on_up)
        self.canvas.bind("<Motion>", self._on_motion)

        self.root.mainloop()

        # RESULT --------------------------------------------------------------
        return json.dumps(self.colors)


class ZoomPreviewPanel:
    def __init__(
        self,
        parent,
        item_size: float = 100,
    ):
        self.parent = parent
        self.item_size = item_size
        self.frame = tk.Frame(
            parent,
            bg="black",
            borderwidth=2,
            width=self.item_size,
            height=self.item_size,
        )
        self.canvas = tk.Canvas(
            self.frame,
            name="base",
            width=self.item_size,
            height=self.item_size,
            highlightthickness=0,
            bg="black",
        )
        self._add_crosshair(self.canvas)
        self.canvas.pack()

    def _add_crosshair(self, canvas):
        canvas.create_line(
            self.item_size / 2,
            self.item_size / 2 - 5,
            self.item_size / 2,
            self.item_size / 2 + 5,
            fill="white",
            width=1,
        )
        canvas.create_line(
            self.item_size / 2 - 5,
            self.item_size / 2,
            self.item_size / 2 + 5,
            self.item_size / 2,
            fill="white",
            width=1,
        )

    def update(self, image, x, y):
        self.canvas.delete("base")
        half_size = 10
        x1 = max(0, x - half_size)
        y1 = max(0, y - half_size)
        x2 = min(image.width, x + half_size)
        y2 = min(image.height, y + half_size)

        cropped = image.crop((x1, y1, x2, y2))
        resized = cropped.resize(
            (self.item_size, self.item_size),
            Image.Resampling.NEAREST,
        )
        zoom_photo = ImageTk.PhotoImage(resized)

        self.canvas.create_image(0, 0, anchor=tk.NW, image=zoom_photo)
        self._add_crosshair(self.canvas)
        self.zoom_photo = zoom_photo  # Keep reference


# COLOR PREVIEW PANEL =========================================================
class ColorPreviewPanel:
    # CONSTRUCTOR -------------------------------------------------------------
    def __init__(
        self,
        parent,
        color_names: list[str],
        default_colors: list[str],
        select_editing_color_callback,
        on_lightness_change_callback,
        validate_callback,
        cancel_callback,
        bg: str = "#1b1b1b",
        text_color: str = "#ffffff",
    ):
        self.parent = parent
        self.color_names = color_names
        self.default_colors = default_colors
        self.select_editing_color_callback = select_editing_color_callback
        self._lightness: int = int(
            Colour.parseHex(self.default_colors[0]).lightness * 100
        )
        self.on_adjust_lightness_callback = on_lightness_change_callback
        self.validate_callback = validate_callback
        self.cancel_callback = cancel_callback
        self.bg: str = bg
        self.fg: str = text_color
        self.selectors: list[tk.Button] = []
        self.color_boxes: list[tk.Frame] = []
        self.color_editing_index: int = 0

        self.frame = tk.Frame(
            parent,
            bd=1,
            relief=tk.FLAT,
            borderwidth=2,
            border=0xFFFFFF,
            bg=self.bg,
            padx=8,
            pady=8,
        )

        self._add_title()
        self._add_zoom_panel()
        self._add_separator()
        self._add_color_rows()
        self._add_lightness_slider()
        self._add_separator()
        self._add_buttons()

    # GETTERS / SETTERS

    @property
    def lightness(self) -> int:
        return self._lightness

    @lightness.setter
    def lightness(self, value: int) -> None:
        self._lightness = value
        self.lightness_slider.set(value)
        self.lightness_var.set(str(value))
        if hasattr(self, "_slider_dragging"):
            self.on_adjust_lightness_callback(self._lightness)

    # TKINTER -----------------------------------------------------------------
    def _add_separator(self):
        separator = tk.Frame(self.frame, height=1, bg="#444444")
        separator.pack(fill=tk.X, padx=16, pady=8)

    def _add_title(self):
        row_frame = tk.Frame(self.frame, background=self.bg)
        row_frame.pack(fill=tk.BOTH, padx=16, pady=8)
        label = tk.Label(
            row_frame,
            text="COLOR PICKER",
            anchor=tk.CENTER,
            foreground=self.fg,
            background=self.bg,
        )
        label.pack(side=tk.TOP)

    def _add_zoom_panel(self):
        self.zoom_panel = ZoomPreviewPanel(self.frame)
        self.zoom_panel.frame.pack(fill=tk.X, padx=16, pady=8)

    def _add_color_rows(self):

        for index in range(len(self.color_names)):
            row_frame = tk.Frame(self.frame, background=self.bg)
            row_frame.pack(fill=tk.X, padx=16, pady=4)
            selector = tk.Button(
                row_frame,
                text=">" if index == self.color_editing_index else "-",
                command=lambda i=index: self.select_editing_color_callback(i),
                anchor=tk.CENTER,
                borderwidth=0,
                width=2,
                padx=4,
                pady=4,
                bg=self.bg,
                fg=self.fg,
            )
            selector.pack(side=tk.LEFT)

            label = tk.Label(
                row_frame,
                text=f"{self.color_names[index]}:",
                padx=5,
                width=10,
                anchor=tk.W,
                foreground=self.fg,
                background=self.bg,
            )
            label.pack(side=tk.LEFT)

            color_box = tk.Frame(
                row_frame,
                width=30,
                height=20,
                bg=self.default_colors[index],
                bd=1,
                relief=tk.SOLID,
            )
            color_box.pack(side=tk.LEFT, padx=8)

            self.selectors.append(selector)
            self.color_boxes.append(color_box)

    def _add_lightness_slider(self):
        self.lightness_var = tk.StringVar()
        self.lightness_var.set(str(self._lightness))
        slider_frame = tk.Frame(self.frame, background=self.bg)
        slider_frame.pack(fill=tk.X, padx=16, pady=4)

        label = tk.Label(
            slider_frame,
            text="🔆",
            padx=0,
            width=3,
            anchor=tk.W,
            foreground=self.fg,
            background=self.bg,
        )
        label.pack(side=tk.LEFT)
        label = tk.Label(
            slider_frame,
            textvariable=self.lightness_var,
            padx=0,
            width=4,
            anchor=tk.W,
            foreground=self.fg,
            background=self.bg,
        )
        label.pack(side=tk.LEFT)
        self.lightness_slider = tk.Scale(
            slider_frame,
            showvalue=False,
            from_=1,
            to=99,
            orient=tk.HORIZONTAL,
            bg=self.bg,
            fg=self.fg,
            troughcolor="#333333",
            command=lambda value: setattr(self, "lightness", int(value)),
        )
        self.lightness_slider.set(self._lightness)
        self.lightness_slider.pack(fill=tk.X)
        # Track slider dragging
        self.lightness_slider.bind(
            "<ButtonPress-1>", lambda e: setattr(self, "_slider_dragging", True)
        )
        self.lightness_slider.bind(
            "<B1-Motion>", lambda e: setattr(self, "_slider_dragging", True)
        )
        self.lightness_slider.bind(
            "<ButtonRelease-1>", lambda e: setattr(self, "_slider_dragging", False)
        )

    def _add_buttons(self):
        button_frame = tk.Frame(self.frame, background=self.bg)
        button_frame.pack(fill=tk.X, padx=16, pady=8)

        self.validate_button = tk.Button(
            button_frame,
            text="Validate",
            command=self.validate_callback,
            bg=self.bg,
            fg=self.fg,
        )
        self.validate_button.pack(side=tk.RIGHT, padx=4)

        self.cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_callback,
            bg=self.bg,
            fg=self.fg,
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=4)

    # METHODS -----------------------------------------------------------------
    def select_index(self, index: int, current_colors: list[str]) -> None:
        for i in range(len(self.color_names)):
            self.selectors[i].config(text=">" if i == index else "-")
            self.color_boxes[i].config(bg=current_colors[i])

        if index == len(self.color_names):
            self.cancel_button.config(
                bg=self.fg,
                fg=self.bg,
            )
            self.validate_button.config(
                bg=self.bg,
                fg=self.fg,
            )
        elif index == len(self.color_names) + 1:
            self.validate_button.config(
                bg=self.fg,
                fg=self.bg,
            )
            self.cancel_button.config(
                bg=self.bg,
                fg=self.fg,
            )
        else:  ## A color is currently selected for edition
            self.validate_button.config(
                bg=self.bg,
                fg=self.fg,
            )
            self.cancel_button.config(
                bg=self.bg,
                fg=self.fg,
            )


# FUNCTIONS ===================================================================


def get_lightness_of(colour: str) -> int:
    return int(Colour.parseHex(colour).lightness * 100)


# MAIN ========================================================================

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python color_picker.py <image_path>")
        sys.exit(1)
    color_picker = ColorPicker(sys.argv[1])
    print(color_picker.get_colors())
