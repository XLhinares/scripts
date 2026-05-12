import json
import sys
import tkinter as tk

from PIL import Image, ImageOps, ImageTk


class ColorPicker:
    def __init__(self, image_path):
        self.image_path = image_path
        self.selected_colors = []
        self.color_boxes = []  # Store references to color boxes

        # Initialize Tkinter root
        self.root = tk.Tk()
        self.root.title("Click 4 colors")

        # Make the window float on Hyprland
        self.root.wm_attributes("-type", "dialog")

        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Make the window fullscreen (cover the entire screen)
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        # self.root.attributes("-fullscreen", True)  # Optional: true fullscreen

        # Load image
        self.original_image = Image.open(image_path)
        # Load and scale image to cover the screen
        self.original_image = Image.open(image_path)
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

        # Bind mouse events to the canvas
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_motion)

        # Color preview panel (overlaid on the canvas)
        self.preview_frame_bg = "#1b1b1b"
        self.preview_text_color = "#ffffff"
        self.preview_frame = tk.Frame(
            self.root,
            bd=1,
            relief=tk.FLAT,
            borderwidth=2,
            bg=self.preview_frame_bg,
            padx=8,
            pady=8,
        )
        self.preview_frame.place(
            x=96,  # 16px from left
            y=32,  # 16px from top
            anchor=tk.NW,
        )

        row_frame = tk.Frame(
            self.preview_frame,
            background=self.preview_frame_bg,
        )
        row_frame.pack(fill=tk.X, padx=16, pady=8)
        label = tk.Label(
            row_frame,
            text="Click to pick colors",
            anchor=tk.W,
            foreground=self.preview_text_color,
            background=self.preview_frame_bg,
        )
        label.pack(side=tk.LEFT)

        # Add 4 rows for Background, Primary, Secondary, Tertiary
        color_names = ["Background", "Primary", "Secondary", "Tertiary"]
        for name in color_names:
            row_frame = tk.Frame(
                self.preview_frame,
                background=self.preview_frame_bg,
            )
            row_frame.pack(fill=tk.X, padx=16, pady=4)  # Padding inside the panel

            label = tk.Label(
                row_frame,
                text=f"{name}:",
                width=10,
                anchor=tk.W,
                foreground=self.preview_text_color,
                background=self.preview_frame_bg,
            )
            label.pack(side=tk.LEFT)

            color_box = tk.Frame(
                row_frame,
                width=30,
                height=20,
                bg=self.preview_text_color,
                bd=1,
                relief=tk.SOLID,
            )
            color_box.pack(side=tk.LEFT, padx=8)
            self.color_boxes.append(color_box)

        self.root.mainloop()

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
        hex_color = self.get_pixel_color(event.x, event.y)
        # Update the live preview (next empty color box)
        if len(self.selected_colors) < 4:
            self.color_boxes[len(self.selected_colors)].config(bg=hex_color)

    def on_click(self, event):
        if len(self.selected_colors) >= 4:
            self.root.destroy()
            return

        hex_color = self.get_pixel_color(event.x, event.y)
        self.selected_colors.append(hex_color)
        # print(f"Selected color {len(self.selected_colors)}: {hex_color}")

        # Lock the color in the box
        if len(self.selected_colors) <= 4:
            self.color_boxes[len(self.selected_colors) - 1].config(bg=hex_color)

        if len(self.selected_colors) == 4:
            self.root.destroy()
            print(json.dumps(self.selected_colors))
            # print("\nFinal colors:", self.selected_colors)
            sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python color_picker.py <image_path>")
        sys.exit(1)
    ColorPicker(sys.argv[1])
