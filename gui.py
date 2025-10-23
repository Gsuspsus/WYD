import tkinter as tk
from tkinter import ttk

class ScrollableEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scrollable Editor")

        # --- Toolbar ---
        toolbar = tk.Frame(root, bg="#ddd")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(toolbar, text="Choice", command=lambda: self.add_section("Choice")).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="If", command=lambda: self.add_section("If")).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Text", command=lambda: self.add_section("Text")).pack(side=tk.LEFT, padx=2, pady=2)

        # --- Scrollable Frame Setup ---
        container = ttk.Frame(root)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, borderwidth=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mousewheel scrolling
        self._bind_mousewheel(canvas)

        # --- Start with one section ---
        self.section_count = 0
        self.add_section("Start")

    def add_section(self, title):
        """Add a titled section with a text area."""
        self.section_count += 1
        frame = ttk.Frame(self.scrollable_frame, padding=5)
        frame.pack(fill="x", pady=4, anchor="w")

        # Title label
        label = ttk.Label(frame, text=f"{self.section_count}. {title}", font=("Segoe UI", 10, "bold"))
        label.pack(anchor="w")

        # Editable text area
        text_area = tk.Text(frame, height=3, width=40, wrap="word", relief="solid", borderwidth=1)
        text_area.pack(fill="x", expand=True, pady=(2, 0))

    def _bind_mousewheel(self, widget):
        """Enable mousewheel scrolling on Windows/Mac/Linux."""
        def _on_mousewheel(event):
            widget.yview_scroll(-1 * (event.delta // 120), "units")
        widget.bind_all("<MouseWheel>", _on_mousewheel)  # Windows/macOS
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))  # Linux
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))   # Linux


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x500")
    app = ScrollableEditorApp(root)
    root.mainloop()
