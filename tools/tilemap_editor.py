#!/usr/bin/env python3
"""Simple 20x15 tilemap editor using a 16-color palette (.mem).

Standard library only (tkinter).

Controls
  Left click / drag   paint with the primary color
  Right click / drag  paint with the secondary color (Ctrl+click also works)
  Shift + click       flood fill with primary (left) / secondary (right)
  Alt/Option + click  eyedropper into primary (left) / secondary (right)
  Palette L/R click   choose primary / secondary color
  0-9, A-F keys       select primary color
  X                   swap primary and secondary
  Ctrl/Cmd+N/O/S      new / open / save
"""

import os
import re
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox

COLS, ROWS = 20, 15
TILE = 32
NUM_COLORS = 16

DEFAULT_PALETTE = [
    "000", "70C", "0F0", "F00", "00F", "FF0", "0FF", "F0F",
    "FFF", "888", "444", "F80", "08F", "060", "840", "222",
]


# ---------------------------------------------------------------- file I/O

def strip_comment(line):
    return line.split("//", 1)[0].strip()


DEFAULT_NAMES = [
    "black", "purple", "green", "red", "blue", "yellow", "cyan", "magenta",
    "white", "gray", "dark gray", "orange", "sky blue", "dark green", "brown",
    "near black",
]


def load_palette_full(path):
    """Parse a .mem palette: 16 lines of 3-hex-digit RGB, // comments allowed.

    Returns (colors, names). A color's name is the trailing comment on its
    line, minus a leading index digit if present ("F80  // B orange" -> "orange").
    """
    colors, names = [], []
    with open(path, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = strip_comment(raw)
            if not line:
                continue
            toks = line.split()
            for tok in toks:
                if not re.fullmatch(r"[0-9A-Fa-f]{3}", tok):
                    raise ValueError(f"Line {lineno}: invalid color '{tok}' "
                                     "(expected 3 hex digits, e.g. F80)")
                colors.append(tok.upper())
            comment = raw.split("//", 1)[1].strip() if "//" in raw else ""
            parts = comment.split(None, 1)
            if parts and parts[0].upper() == f"{len(colors) - 1:X}":
                comment = parts[1] if len(parts) > 1 else ""
            names.extend([comment] + [""] * (len(toks) - 1))
    if len(colors) != NUM_COLORS:
        raise ValueError(f"Palette must have exactly {NUM_COLORS} colors, "
                         f"found {len(colors)}")
    return colors, names


def load_palette(path):
    return load_palette_full(path)[0]


def save_palette(path, colors, names):
    with open(path, "w", encoding="utf-8") as f:
        f.write("// 16-color palette, 12-bit RGB (one hex digit per channel)\n")
        for i, (col, name) in enumerate(zip(colors, names)):
            f.write(f"{col}  // {i:X} {name}".rstrip() + "\n")


def quantize(r8, g8, b8):
    """8-bit-per-channel RGB -> 12-bit 'RGB' string."""
    return "".join(f"{min(15, round(v / 17)):X}" for v in (r8, g8, b8))


def rgb12_to_tk(c):
    """'F80' -> '#ff8800'."""
    return "#" + "".join(ch * 2 for ch in c.lower())


def parse_grid(lines):
    """Parse 15 rows of 20 hex indices (comments/blank lines ignored)."""
    grid = []
    for raw in lines:
        line = strip_comment(raw)
        if not line:
            continue
        toks = line.split()
        if len(toks) != COLS:
            raise ValueError(f"Row {len(grid) + 1}: expected {COLS} tiles, "
                             f"found {len(toks)}")
        row = []
        for tok in toks:
            if not re.fullmatch(r"[0-9A-Fa-f]", tok):
                raise ValueError(f"Row {len(grid) + 1}: invalid tile '{tok}'")
            row.append(int(tok, 16))
        grid.append(row)
    if len(grid) != ROWS:
        raise ValueError(f"Expected {ROWS} rows, found {len(grid)}")
    return grid


def grid_lines(grid):
    return [" ".join(f"{v:X}" for v in row) for row in grid]


def save_tmp(path, grid, palette_path):
    """.tmp format: header, optional palette reference, then the grid."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"// tilemap {COLS}x{ROWS}\n")
        if palette_path:
            f.write(f"// palette: {palette_path}\n")
        f.write("\n".join(grid_lines(grid)) + "\n")


def load_tmp(path):
    """Returns (grid, palette_path_or_None)."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    palette_path = None
    for raw in lines:
        m = re.match(r"\s*//\s*palette:\s*(.+?)\s*$", raw)
        if m:
            palette_path = m.group(1)
            break
    return parse_grid(lines), palette_path


def export_mem(path, grid):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"// {COLS} x {ROWS} tilemap, one palette index (hex) per tile\n")
        f.write("\n".join(grid_lines(grid)) + "\n")


def import_mem(path):
    with open(path, "r", encoding="utf-8") as f:
        return parse_grid(f.readlines())


# ---------------------------------------------------------------- editor

class TilemapEditor:
    def __init__(self, root):
        self.root = root
        self.palette = list(DEFAULT_PALETTE)
        self.palette_names = list(DEFAULT_NAMES)
        self.palette_path = None
        self.palette_dirty = False   # palette edited but not saved to its file
        self.palette_editor = None
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.selected = 0      # primary (left button)
        self.secondary = 8     # secondary (right button)
        self.file_path = None
        self.dirty = False
        self.show_grid = tk.BooleanVar(value=True)

        self._build_menu()
        self._build_ui()
        self._bind_keys()
        self.redraw_all()
        self.update_title()
        root.protocol("WM_DELETE_WINDOW", self.on_quit)

    # ---- UI construction
    def _build_menu(self):
        mod = "Command" if self.root.tk.call("tk", "windowingsystem") == "aqua" else "Control"
        acc = "Cmd" if mod == "Command" else "Ctrl"
        self.mod = mod

        menubar = tk.Menu(self.root)
        fm = tk.Menu(menubar, tearoff=0)
        fm.add_command(label="New", accelerator=f"{acc}+N", command=self.new_map)
        fm.add_command(label="Open .tmp...", accelerator=f"{acc}+O", command=self.open_map)
        fm.add_command(label="Save", accelerator=f"{acc}+S", command=self.save_map)
        fm.add_command(label="Save As...", command=self.save_map_as)
        fm.add_separator()
        fm.add_command(label="Import .mem tilemap...", command=self.import_mem)
        fm.add_command(label="Export to .mem...", accelerator=f"{acc}+E", command=self.export_mem)
        fm.add_separator()
        fm.add_command(label="Quit", command=self.on_quit)
        menubar.add_cascade(label="File", menu=fm)

        pm = tk.Menu(menubar, tearoff=0)
        pm.add_command(label="Load Palette (.mem)...", accelerator=f"{acc}+P",
                       command=self.choose_palette)
        pm.add_command(label="Edit Palette...", accelerator=f"{acc}+K",
                       command=self.open_palette_editor)
        pm.add_separator()
        pm.add_command(label="Save Palette", command=self.save_palette)
        pm.add_command(label="Save Palette As...", command=self.save_palette_as)
        pm.add_separator()
        pm.add_command(label="Reset to Default Palette", command=self.reset_palette)
        menubar.add_cascade(label="Palette", menu=pm)

        vm = tk.Menu(menubar, tearoff=0)
        vm.add_checkbutton(label="Show Grid Lines", variable=self.show_grid,
                           command=self.redraw_all)
        menubar.add_cascade(label="View", menu=vm)

        em = tk.Menu(menubar, tearoff=0)
        em.add_command(label="Fill All with Selected Color", command=self.fill_all)
        menubar.add_cascade(label="Edit", menu=em)

        self.root.config(menu=menubar)

    def _build_ui(self):
        main = tk.Frame(self.root, padx=8, pady=8)
        main.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(main, width=COLS * TILE, height=ROWS * TILE,
                                highlightthickness=1, highlightbackground="#555",
                                bg="#000")
        self.canvas.grid(row=0, column=0, sticky="n")
        self.rects = [[self.canvas.create_rectangle(
            c * TILE, r * TILE, (c + 1) * TILE, (r + 1) * TILE, width=1)
            for c in range(COLS)] for r in range(ROWS)]

        prim = lambda: self.selected
        sec = lambda: self.secondary
        self.canvas.bind("<Button-1>", lambda e: self.on_paint(e, prim()))
        self.canvas.bind("<B1-Motion>", lambda e: self.on_paint(e, prim()))
        self.canvas.bind("<Shift-Button-1>", lambda e: self.on_fill(e, prim()))
        # Right button: Button-3 on X11/Windows; on macOS it is Button-2 in
        # Tk 8.6 and Button-3 in Tk 8.7+. Ctrl+click also acts as right click.
        right = ["3"]
        if self.root.tk.call("tk", "windowingsystem") == "aqua":
            right.append("2")
        for b in right:
            self.canvas.bind(f"<Button-{b}>", lambda e: self.on_paint(e, sec()))
            self.canvas.bind(f"<B{b}-Motion>", lambda e: self.on_paint(e, sec()))
            self.canvas.bind(f"<Shift-Button-{b}>", lambda e: self.on_fill(e, sec()))
        self.canvas.bind("<Control-Button-1>", lambda e: self.on_paint(e, sec()))
        self.canvas.bind("<Control-B1-Motion>", lambda e: self.on_paint(e, sec()))
        # Eyedropper: Alt/Option + left picks primary, + right picks secondary
        for mod in ("Alt", "Option"):
            try:
                self.canvas.bind(f"<{mod}-Button-1>", lambda e: self.on_pick(e, False))
                for b in right:
                    self.canvas.bind(f"<{mod}-Button-{b}>", lambda e: self.on_pick(e, True))
            except tk.TclError:
                pass  # "Option" only exists on macOS
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Leave>", lambda e: self.coord_var.set(""))

        side = tk.Frame(main, padx=10)
        side.grid(row=0, column=1, sticky="n")
        tk.Label(side, text="Palette", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        self.pal_canvas = tk.Canvas(side, width=2 * 56 + 4, height=8 * 36 + 4,
                                    highlightthickness=0)
        self.pal_canvas.pack(pady=(4, 8))
        self.pal_canvas.bind("<Button-1>", lambda e: self.on_palette_click(e, False))
        for b in right:
            self.pal_canvas.bind(f"<Button-{b}>", lambda e: self.on_palette_click(e, True))
        self.pal_canvas.bind("<Control-Button-1>", lambda e: self.on_palette_click(e, True))
        self.pal_canvas.bind("<Double-Button-1>", self.on_palette_double)

        tk.Label(side, text="Primary (L) / Secondary (R):").pack(anchor="w")
        self.sel_swatch = tk.Canvas(side, width=116, height=40, highlightthickness=0)
        self.sel_swatch.pack(anchor="w", pady=(2, 2))
        self.sel_swatch.bind("<Button-1>", lambda e: self.swap_colors())
        self.sel_label = tk.Label(side, text="", font=("Courier", 11), justify="left")
        self.sel_label.pack(anchor="w")
        tk.Label(side, text="X or click swatches to swap", fg="#666").pack(anchor="w")

        self.palname_var = tk.StringVar()
        tk.Label(side, textvariable=self.palname_var, wraplength=120, justify="left",
                 fg="#666").pack(anchor="w", pady=(10, 0))

        status = tk.Frame(self.root, padx=8, pady=4)
        status.pack(fill="x")
        self.coord_var = tk.StringVar()
        tk.Label(status, textvariable=self.coord_var, font=("Courier", 11)).pack(side="left")
        tk.Label(status, text="L/R: paint   Shift: fill   Alt: pick   0-F: color   X: swap",
                 fg="#666").pack(side="right")

    def _bind_keys(self):
        m = self.mod
        self.root.bind(f"<{m}-n>", lambda e: self.new_map())
        self.root.bind(f"<{m}-o>", lambda e: self.open_map())
        self.root.bind(f"<{m}-s>", lambda e: self.save_map())
        self.root.bind(f"<{m}-e>", lambda e: self.export_mem())
        self.root.bind(f"<{m}-p>", lambda e: self.choose_palette())
        self.root.bind(f"<{m}-k>", lambda e: self.open_palette_editor())
        self.root.bind("<Key>", self.on_key)

    # ---- drawing
    def redraw_all(self):
        for r in range(ROWS):
            for c in range(COLS):
                self.draw_tile(r, c)
        self.draw_palette()

    def draw_tile(self, r, c):
        color = rgb12_to_tk(self.palette[self.grid[r][c]])
        self.canvas.itemconfig(self.rects[r][c], fill=color,
                               outline="#333333" if self.show_grid.get() else color)

    def draw_palette(self):
        pc = self.pal_canvas
        pc.delete("all")
        for i, col in enumerate(self.palette):
            x = (i // 8) * 56 + 2
            y = (i % 8) * 36 + 2
            pc.create_rectangle(x, y, x + 52, y + 32, fill=rgb12_to_tk(col),
                                outline="#555", width=1)
            txt = self.text_color(col)
            pc.create_text(x + 26, y + 16, text=f"{i:X}:{col}", fill=txt,
                           font=("Courier", 10, "bold"))
            if i == self.secondary:
                pc.create_rectangle(x + 3, y + 3, x + 49, y + 29,
                                    outline="#2299ff", width=3)
                pc.create_text(x + 46, y + 9, text="R", fill="#2299ff",
                               font=("TkDefaultFont", 8, "bold"))
            if i == self.selected:
                pc.create_rectangle(x, y, x + 52, y + 32, outline="#ff2222", width=3)
                pc.create_text(x + 7, y + 9, text="L", fill="#ff2222",
                               font=("TkDefaultFont", 8, "bold"))

        sw = self.sel_swatch
        sw.delete("all")
        for idx, x0, tag in ((self.selected, 0, "L"), (self.secondary, 60, "R")):
            col = self.palette[idx]
            sw.create_rectangle(x0 + 1, 1, x0 + 55, 39, fill=rgb12_to_tk(col), outline="#555")
            sw.create_text(x0 + 28, 20, text=f"{tag}:{idx:X}", fill=self.text_color(col),
                           font=("Courier", 11, "bold"))
        self.sel_label.config(text=f"L {self.selected:X}  #{self.palette[self.selected]}\n"
                                   f"R {self.secondary:X}  #{self.palette[self.secondary]}")
        name = os.path.basename(self.palette_path) if self.palette_path else "(default)"
        self.palname_var.set(f"Palette file:\n{'*' if self.palette_dirty else ''}{name}\n"
                             "(double-click a color to edit)")

    # ---- event helpers
    def cell_at(self, event):
        c, r = event.x // TILE, event.y // TILE
        if 0 <= c < COLS and 0 <= r < ROWS:
            return r, c
        return None

    def set_tile(self, r, c, v):
        if self.grid[r][c] != v:
            self.grid[r][c] = v
            self.draw_tile(r, c)
            self.mark_dirty()

    @staticmethod
    def text_color(col):
        r, g, b = (int(ch, 16) for ch in col)
        return "#000" if (r * 299 + g * 587 + b * 114) / 1000 > 7 else "#fff"

    def on_paint(self, event, value):
        cell = self.cell_at(event)
        if cell:
            self.set_tile(*cell, value)
        self.on_hover(event)
        return "break"

    def on_fill(self, event, new):
        cell = self.cell_at(event)
        if not cell:
            return "break"
        r0, c0 = cell
        target = self.grid[r0][c0]
        if target == new:
            return "break"
        stack = [(r0, c0)]
        while stack:
            r, c = stack.pop()
            if 0 <= r < ROWS and 0 <= c < COLS and self.grid[r][c] == target:
                self.grid[r][c] = new
                self.draw_tile(r, c)
                stack.extend([(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)])
        self.mark_dirty()
        return "break"

    def on_pick(self, event, secondary):
        cell = self.cell_at(event)
        if cell:
            self.select_color(self.grid[cell[0]][cell[1]], secondary)
        return "break"

    def on_hover(self, event):
        cell = self.cell_at(event)
        if cell:
            r, c = cell
            v = self.grid[r][c]
            self.coord_var.set(f"x={c:2d} y={r:2d}  tile={v:X} (#{self.palette[v]})")

    def on_palette_click(self, event, secondary):
        col, row = (event.x - 2) // 56, (event.y - 2) // 36
        if 0 <= col < 2 and 0 <= row < 8:
            self.select_color(col * 8 + row, secondary)
        return "break"

    def on_key(self, event):
        if event.state & 0x4 or event.state & 0x8:  # Ctrl / Cmd / Alt held
            return
        ch = event.char.upper() if event.char else ""
        if len(ch) != 1:
            return
        if ch in "0123456789ABCDEF":
            self.select_color(int(ch, 16))
        elif ch == "X":
            self.swap_colors()

    def select_color(self, i, secondary=False):
        if secondary:
            self.secondary = i
        else:
            self.selected = i
        self.draw_palette()

    def swap_colors(self):
        self.selected, self.secondary = self.secondary, self.selected
        self.draw_palette()

    # ---- state / title
    def mark_dirty(self):
        if not self.dirty:
            self.dirty = True
            self.update_title()

    def update_title(self):
        name = os.path.basename(self.file_path) if self.file_path else "Untitled"
        self.root.title(f"{'*' if self.dirty else ''}{name} - Tilemap Editor ({COLS}x{ROWS})")

    def confirm_discard(self):
        if not self.dirty:
            return True
        ans = messagebox.askyesnocancel("Unsaved changes", "Save changes before continuing?")
        if ans is None:
            return False
        if ans:
            return self.save_map()
        return True

    # ---- file actions
    def new_map(self):
        if not self.confirm_discard():
            return
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.file_path = None
        self.dirty = False
        self.redraw_all()
        self.update_title()

    def open_map(self):
        if not self.confirm_discard() or not self.maybe_save_palette():
            return
        path = filedialog.askopenfilename(
            title="Open tilemap", filetypes=[("Tilemap", "*.tmp"), ("All files", "*")])
        if not path:
            return
        try:
            grid, pal = load_tmp(path)
        except (OSError, ValueError) as e:
            messagebox.showerror("Open failed", str(e))
            return
        self.grid = grid
        self.file_path = path
        self.dirty = False
        if pal:
            pal_full = pal if os.path.isabs(pal) else os.path.join(os.path.dirname(path), pal)
            try:
                self.load_palette_file(pal_full)
            except (OSError, ValueError) as e:
                messagebox.showwarning("Palette not loaded",
                                       f"Could not load palette '{pal}':\n{e}\n\n"
                                       "Keeping the current palette.")
        self.redraw_all()
        self.update_title()

    def save_map(self):
        if not self.file_path:
            return self.save_map_as()
        return self._write_tmp(self.file_path)

    def save_map_as(self):
        path = filedialog.asksaveasfilename(
            title="Save tilemap", defaultextension=".tmp",
            filetypes=[("Tilemap", "*.tmp")])
        if not path:
            return False
        return self._write_tmp(path)

    def _write_tmp(self, path):
        pal_ref = None
        if self.palette_path:
            try:
                pal_ref = os.path.relpath(self.palette_path, os.path.dirname(path))
            except ValueError:  # different drives on Windows
                pal_ref = self.palette_path
        try:
            save_tmp(path, self.grid, pal_ref)
        except OSError as e:
            messagebox.showerror("Save failed", str(e))
            return False
        self.file_path = path
        self.dirty = False
        self.update_title()
        return True

    def export_mem(self):
        initial = (os.path.splitext(os.path.basename(self.file_path))[0] + ".mem"
                   if self.file_path else "tilemap.mem")
        path = filedialog.asksaveasfilename(
            title="Export tilemap to .mem", defaultextension=".mem",
            initialfile=initial, filetypes=[("Memory file", "*.mem")])
        if not path:
            return
        try:
            export_mem(path, self.grid)
        except OSError as e:
            messagebox.showerror("Export failed", str(e))

    def import_mem(self):
        if not self.confirm_discard():
            return
        path = filedialog.askopenfilename(
            title="Import .mem tilemap", filetypes=[("Memory file", "*.mem"), ("All files", "*")])
        if not path:
            return
        try:
            self.grid = import_mem(path)
        except (OSError, ValueError) as e:
            messagebox.showerror("Import failed", str(e))
            return
        self.file_path = None
        self.dirty = True
        self.redraw_all()
        self.update_title()

    # ---- palette files
    def load_palette_file(self, path):
        colors, names = load_palette_full(path)
        self.palette, self.palette_names = colors, names
        self.palette_path = path
        self.palette_dirty = False
        self.palette_replaced()

    def palette_replaced(self):
        self.redraw_all()
        if self.palette_editor:
            self.palette_editor.reload()

    def choose_palette(self):
        if not self.maybe_save_palette():
            return
        path = filedialog.askopenfilename(
            title="Load palette", filetypes=[("Palette", "*.mem"), ("All files", "*")])
        if not path:
            return
        try:
            self.load_palette_file(path)
        except (OSError, ValueError) as e:
            messagebox.showerror("Palette load failed", str(e))
            return
        self.mark_dirty()

    def reset_palette(self):
        if not self.maybe_save_palette():
            return
        self.palette = list(DEFAULT_PALETTE)
        self.palette_names = list(DEFAULT_NAMES)
        self.palette_path = None
        self.palette_dirty = False
        self.mark_dirty()
        self.palette_replaced()

    def palette_edited(self):
        """Called by the palette editor after any change."""
        self.palette_dirty = True
        self.redraw_all()

    def save_palette(self, parent=None):
        if not self.palette_path:
            return self.save_palette_as(parent)
        return self._write_palette(self.palette_path)

    def save_palette_as(self, parent=None):
        initial = os.path.basename(self.palette_path) if self.palette_path else "palette.mem"
        path = filedialog.asksaveasfilename(
            parent=parent or self.root, title="Save palette", defaultextension=".mem",
            initialfile=initial, filetypes=[("Palette", "*.mem")])
        if not path:
            return False
        if not self._write_palette(path, parent):
            return False
        if path != self.palette_path:
            self.palette_path = path
            self.mark_dirty()  # the map now references a different palette file
        self.draw_palette()
        return True

    def _write_palette(self, path, parent=None):
        try:
            save_palette(path, self.palette, self.palette_names)
        except OSError as e:
            messagebox.showerror("Palette save failed", str(e), parent=parent or self.root)
            return False
        self.palette_dirty = False
        self.draw_palette()
        if self.palette_editor:
            self.palette_editor.mark_saved()
        return True

    def maybe_save_palette(self, parent=None):
        """Offer to save unsaved palette edits. False means the user cancelled."""
        if not self.palette_dirty:
            return True
        ans = messagebox.askyesnocancel(
            "Unsaved palette", "The palette has unsaved changes. Save them to a .mem file?",
            parent=parent or self.root)
        if ans is None:
            return False
        return self.save_palette(parent) if ans else True

    def open_palette_editor(self, index=None):
        if index is None:
            index = self.selected
        if self.palette_editor:
            self.palette_editor.select(index)
            self.palette_editor.win.lift()
            self.palette_editor.win.focus_force()
        else:
            self.palette_editor = PaletteEditor(self, index)

    def on_palette_double(self, event):
        col, row = (event.x - 2) // 56, (event.y - 2) // 36
        if 0 <= col < 2 and 0 <= row < 8:
            self.open_palette_editor(col * 8 + row)
        return "break"

    def fill_all(self):
        self.grid = [[self.selected] * COLS for _ in range(ROWS)]
        self.mark_dirty()
        self.redraw_all()

    def on_quit(self):
        if self.maybe_save_palette() and self.confirm_discard():
            self.root.destroy()


# ---------------------------------------------------------------- palette editor

class PaletteEditor:
    """Toplevel window for editing the 16 palette colors. Edits apply live."""

    SW = 52  # swatch size

    def __init__(self, app, index=0):
        self.app = app
        self.index = index
        self.win = tk.Toplevel(app.root)
        self.win.title("Palette Editor")
        self.win.resizable(False, False)
        self.win.transient(app.root)
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.mark_saved()
        self._build()
        m = app.mod
        self.win.bind(f"<{m}-s>", lambda e: self.app.save_palette(self.win))
        self.win.bind(f"<{m}-z>", lambda e: self.revert())
        self.win.bind("<Escape>", lambda e: self.close())
        self.refresh()

    def _build(self):
        frm = tk.Frame(self.win, padx=10, pady=10)
        frm.pack()
        n = self.SW
        self.sw = tk.Canvas(frm, width=4 * n + 4, height=4 * n + 4, highlightthickness=0)
        self.sw.grid(row=0, column=0, sticky="n")
        self.sw.bind("<Button-1>", self.on_swatch_click)

        right = tk.Frame(frm, padx=12)
        right.grid(row=0, column=1, sticky="n")
        self.idx_label = tk.Label(right, font=("TkDefaultFont", 12, "bold"))
        self.idx_label.grid(row=0, column=0, columnspan=3, sticky="w")
        self.preview = tk.Canvas(right, width=240, height=44, highlightthickness=1,
                                 highlightbackground="#555")
        self.preview.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 8))

        self.scales = []
        for row, (label, fg) in enumerate((("R", "#c22"), ("G", "#1a1"), ("B", "#22c")), 2):
            tk.Label(right, text=label, fg=fg, font=("TkDefaultFont", 11, "bold"),
                     width=2).grid(row=row, column=0, sticky="w")
            s = tk.Scale(right, from_=0, to=15, orient="horizontal", length=210,
                         showvalue=True, command=lambda v: self.on_scale())
            s.grid(row=row, column=1, columnspan=2, sticky="w")
            self.scales.append(s)

        tk.Label(right, text="Hex").grid(row=5, column=0, sticky="w", pady=(6, 0))
        self.hex_var = tk.StringVar()
        hex_entry = tk.Entry(right, textvariable=self.hex_var, width=6, font=("Courier", 12))
        hex_entry.grid(row=5, column=1, sticky="w", pady=(6, 0))
        hex_entry.bind("<Return>", self.on_hex)
        hex_entry.bind("<FocusOut>", self.on_hex)
        tk.Button(right, text="Pick...", command=self.on_pick).grid(
            row=5, column=2, sticky="e", pady=(6, 0))

        tk.Label(right, text="Name").grid(row=6, column=0, sticky="w", pady=(6, 0))
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(right, textvariable=self.name_var, width=22)
        name_entry.grid(row=6, column=1, columnspan=2, sticky="w", pady=(6, 0))
        name_entry.bind("<KeyRelease>", self.on_name)

        self.file_var = tk.StringVar()
        tk.Label(right, textvariable=self.file_var, fg="#666", wraplength=250,
                 justify="left").grid(row=7, column=0, columnspan=3, sticky="w", pady=(10, 0))

        btns = tk.Frame(frm, pady=(10))
        btns.grid(row=1, column=0, columnspan=2, sticky="ew")
        tk.Button(btns, text="Revert", command=self.revert).pack(side="left")
        tk.Button(btns, text="Done", width=8, command=self.close).pack(side="right")
        tk.Button(btns, text="Save As...",
                  command=lambda: self.app.save_palette_as(self.win)).pack(side="right", padx=4)
        tk.Button(btns, text="Save",
                  command=lambda: self.app.save_palette(self.win)).pack(side="right")

    # ---- state
    def mark_saved(self):
        """Remember the current palette as the point Revert returns to."""
        self.snapshot = (list(self.app.palette), list(self.app.palette_names),
                         self.app.palette_dirty)
        if hasattr(self, "file_var"):
            self.refresh()

    def reload(self):
        """The app loaded or reset its palette underneath us."""
        self.mark_saved()

    def revert(self):
        colors, names, dirty = self.snapshot
        self.app.palette[:] = colors
        self.app.palette_names[:] = names
        self.app.palette_dirty = dirty
        self.app.redraw_all()
        self.refresh()

    def close(self):
        if not self.app.maybe_save_palette(self.win):
            return
        self.app.palette_editor = None
        self.win.destroy()

    # ---- display
    def refresh(self):
        n = self.SW
        self.sw.delete("all")
        for i, col in enumerate(self.app.palette):
            r, c = divmod(i, 4)
            x, y = c * n + 2, r * n + 2
            self.sw.create_rectangle(x, y, x + n - 4, y + n - 4, fill=rgb12_to_tk(col),
                                     outline="#555")
            self.sw.create_text(x + (n - 4) / 2, y + (n - 4) / 2, text=f"{i:X}",
                                fill=TilemapEditor.text_color(col),
                                font=("Courier", 12, "bold"))
        r, c = divmod(self.index, 4)
        self.sw.create_rectangle(c * n + 1, r * n + 1, c * n + n - 1, r * n + n - 1,
                                 outline="#ff2222", width=3)

        col = self.app.palette[self.index]
        for s, ch in zip(self.scales, col):
            s.set(int(ch, 16))
        self.hex_var.set(col)
        self.name_var.set(self.app.palette_names[self.index])
        self.idx_label.config(text=f"Color {self.index:X}")
        self.preview.config(bg=rgb12_to_tk(col))
        self.update_file_label()

    def update_file_label(self):
        path = self.app.palette_path
        name = os.path.basename(path) if path else "(default, not saved to a file)"
        self.file_var.set(f"File: {name}" + ("  — unsaved changes" if self.app.palette_dirty else ""))

    # ---- editing
    def set_color(self, col):
        if col == self.app.palette[self.index]:
            return
        self.app.palette[self.index] = col
        self.app.palette_edited()
        self.refresh()

    def select(self, i):
        self.index = i
        self.refresh()

    def on_swatch_click(self, event):
        c, r = (event.x - 2) // self.SW, (event.y - 2) // self.SW
        if 0 <= c < 4 and 0 <= r < 4:
            self.select(r * 4 + c)

    def on_scale(self):
        # Also fires when refresh() sets the sliders; set_color ignores no-op changes.
        self.set_color("".join(f"{s.get():X}" for s in self.scales))

    def on_hex(self, event=None):
        v = self.hex_var.get().strip().lstrip("#").upper()
        if re.fullmatch(r"[0-9A-F]{3}", v):
            self.set_color(v)
        elif re.fullmatch(r"[0-9A-F]{6}", v):
            self.set_color(quantize(*(int(v[i:i + 2], 16) for i in (0, 2, 4))))
        else:
            if v != self.app.palette[self.index]:
                self.win.bell()
        self.hex_var.set(self.app.palette[self.index])

    def on_pick(self):
        rgb, _ = colorchooser.askcolor(color=rgb12_to_tk(self.app.palette[self.index]),
                                       parent=self.win, title=f"Color {self.index:X}")
        if rgb:
            self.set_color(quantize(*(int(v) for v in rgb)))

    def on_name(self, event=None):
        name = self.name_var.get()
        if name != self.app.palette_names[self.index]:
            self.app.palette_names[self.index] = name
            self.app.palette_dirty = True
            self.app.draw_palette()
            self.update_file_label()


def main():
    root = tk.Tk()
    root.resizable(False, False)
    app = TilemapEditor(root)
    here = os.path.dirname(os.path.abspath(__file__))
    default_pal = os.path.join(here, "palette.mem")
    if os.path.exists(default_pal):
        try:
            app.load_palette_file(default_pal)
        except (OSError, ValueError):
            pass
    root.mainloop()


if __name__ == "__main__":
    main()
