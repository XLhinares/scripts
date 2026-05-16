import json
import sys
import tkinter as tk

from PIL import Image, ImageOps, ImageTk


class ColorPicker:
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
        self.colors: dict[str, str] = default_colors
        self.current_index: int = 0
        self.hovered_color: str = self.colors[self.get_current_name()]

    def get_current_name(self) -> str:
        return list(self.colors.keys())[self.current_index]

    def get_current_color(self) -> str:
        return self.colors[self.get_current_name()]

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
            select_editing_color_callback=self.select_index,
            validate_callback=self.validate,
            cancel_callback=self.cancel,
        )
        self.preview_panel.frame.place(x=96, y=48, anchor=tk.NW)

        # INTERACTIONS --------------------------------------------------------
        self.canvas.focus_set()
        self.canvas.bind("<Down>", self.on_down)
        self.canvas.bind("<Up>", self.on_up)
        self.canvas.bind("<Return>", self.on_enter)  # "Enter" key
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_up)
        self.canvas.bind("<Motion>", self.on_motion)

        self.root.mainloop()

        # RESULT --------------------------------------------------------------
        return json.dumps(self.colors)

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

    def on_motion(self, event):
        """Update the live preview when the mouse moves."""
        self.preview_panel.zoom_panel.update(self.scaled_image, event.x, event.y)
        if self.current_index < len(self.colors):
            self.hovered_color = self.get_pixel_color(event.x, event.y)
            self.preview_panel.color_boxes[self.current_index].config(
                bg=self.hovered_color
            )

    def on_down(self, event) -> None:
        self.select_index(self.current_index + 1)

    def on_up(self, event) -> None:
        self.select_index(self.current_index - 1)

    def select_index(self, index) -> None:
        """Select an index and propagate the information.
        The index value is clamped between 0 and `len(self.colors) + 2`, to allow selecting the "cancel" and "validate" button.
        """
        if self.current_index < len(self.colors):
            self.preview_panel.color_boxes[self.current_index].config(
                bg=self.get_current_color()
            )
        self.current_index = index % (
            len(self.colors) + 2
        )  # Add two for the cancel and validate buttons.
        self.preview_panel.select_index(self.current_index)

    def on_click(self, event) -> None:
        """Update the value of the editing color to match the hovered pixel."""
        self.colors[self.get_current_name()] = self.hovered_color
        # If the last color is clicked, jump to "validate button",
        # otherwise, just go to next item down.
        if self.current_index == len(self.colors) - 1:
            self.on_down(None)
            self.on_down(None)
        else:
            self.on_down(None)

    def on_enter(self, event) -> None:
        if self.current_index == len(self.colors):
            self.cancel()
        elif self.current_index == len(self.colors) + 1:
            self.validate()
        else:
            self.on_click(None)

    def validate(self) -> None:
        self.root.destroy()

    def cancel(self) -> None:
        self.root.destroy()
        exit(1)


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


class ColorPreviewPanel:
    def __init__(
        self,
        parent,
        color_names: list[str],
        default_colors: list[str],
        select_editing_color_callback,
        validate_callback,
        cancel_callback,
        bg: str = "#1b1b1b",
        text_color: str = "#ffffff",
    ):
        self.parent = parent
        self.color_names = color_names
        self.default_colors = default_colors
        self.select_editing_color_callback = select_editing_color_callback
        self.validate_callback = validate_callback
        self.cancel_callback = cancel_callback
        self.bg = bg
        self.fg = text_color
        self.selectors = []
        self.color_boxes = []
        self.color_editing_index = 0

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
        self._add_separator()
        self._add_buttons()

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

    def select_index(self, index: int) -> None:
        for i in range(len(self.color_names)):
            self.selectors[i].config(text=">" if i == index else "-")
        if index == len(self.color_names):
            self.cancel_button.config(
                bg=self.fg,
                fg=self.bg,
            )
        else:
            self.cancel_button.config(
                bg=self.bg,
                fg=self.fg,
            )
        if index == len(self.color_names) + 1:
            self.validate_button.config(
                bg=self.fg,
                fg=self.bg,
            )
        else:
            self.validate_button.config(
                bg=self.bg,
                fg=self.fg,
            )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python color_picker.py <image_path>")
        sys.exit(1)
    color_picker = ColorPicker(sys.argv[1])
    print(color_picker.get_colors())
