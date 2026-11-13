#!/usr/bin/env python3
"""Visual editor for 8x8 monochrome glyph fonts stored in .mem files.

Standard library only (tkinter).

File format: one 64-bit hex value per line (one glyph per line); the first
byte is the top row and the MSB of each byte is the leftmost pixel.
0 = black, 1 = white. // comments, blank lines and @address lines are kept.

Order is preserved by design:
  * glyphs live in fixed slots - there is no insert/delete/reorder;
  * saving rewrites only the hex token on lines whose glyph changed, every
    other byte of the file is kept as-is;
  * the new text is re-parsed and checked against the editor before it is
    written, and the write is atomic (temp file + rename).

Usage: python3 glyph_editor.py [font.mem]

Controls
  Left click / drag     toggle pixel (drag paints the same value)
  Right click / drag    paint black (Ctrl+click also works)
  Left / Right          previous / next glyph   (Up / Down: +-16)
  Shift + arrows        shift the glyph's pixels
  Cmd/Ctrl+Z            undo         Cmd/Ctrl+C / V   copy / paste glyph
  Cmd/Ctrl+S / O        save / open
"""

import os
import re
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox

SIZE = 8
CELL = 40          # editor cell size in px
THUMB = 3          # browser thumbnail scale
BROWSER_COLS = 16
HEX_DIGITS = 16
MASK = (1 << 64) - 1

BLACK, WHITE = "#000000", "#ffffff"
GRID_LINE = "#3a3a3a"
SELECT = "#ff3b30"
MODIFIED = "#ff9500"


# ---------------------------------------------------------------- file model

class FontFile:
    """A .mem file's lines plus the location of every glyph value in them."""

    def __init__(self, text):
        self.lines = text.splitlines(keepends=True)
        # one entry per glyph: [line_index, token_start, token_end, address]
        self.slots = []
        self.values = []
        self._parse()
        self.saved = list(self.values)

    def _parse(self):
        addr = 0
        for li, line in enumerate(self.lines):
            code = line.split("//", 1)[0]
            toks = code.split()
            if not toks:
                continue
            if len(toks) != 1:
                raise ValueError(f"Line {li + 1}: expected one value per line, "
                                 f"found {len(toks)}")
            tok = toks[0]
            if tok.startswith("@"):
                if not re.fullmatch(r"@[0-9A-Fa-f]+", tok):
                    raise ValueError(f"Line {li + 1}: bad address '{tok}'")
                addr = int(tok[1:], 16)
                continue
            digits = tok.replace("_", "")
            if not re.fullmatch(r"[0-9A-Fa-f]{1,%d}" % HEX_DIGITS, digits):
                raise ValueError(f"Line {li + 1}: '{tok}' is not a 64-bit hex value")
            start = code.index(tok)
            self.slots.append([li, start, start + len(tok), addr])
            self.values.append(int(digits, 16))
            addr += 1
        if not self.slots:
            raise ValueError("No glyph values found")

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8", newline="") as f:
            return cls(f.read())

    def render(self):
        """File text with only the changed glyph tokens replaced."""
        lines = list(self.lines)
        for (li, s, e, _), new, old in zip(self.slots, self.values, self.saved):
            if new != old:
                lines[li] = lines[li][:s] + f"{new:0{HEX_DIGITS}X}" + lines[li][e:]
        return "".join(lines)

    def save(self, path):
        text = self.render()
        # Safety check: re-parse what we are about to write.
        check = FontFile(text)
        if ([s[3] for s in check.slots] != [s[3] for s in self.slots]
                or check.values != self.values):
            raise RuntimeError("Verification failed: glyph order/values would change. "
                               "File not written.")
        d = os.path.dirname(os.path.abspath(path))
        fd, tmp = tempfile.mkstemp(prefix=".glyph-", suffix=".mem", dir=d)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            if os.path.exists(path):
                os.chmod(tmp, os.stat(path).st_mode & 0o777)
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        # Adopt the new layout (token widths may have changed).
        self.lines, self.slots = check.lines, check.slots
        self.saved = list(self.values)

    def modified(self, i):
        return self.values[i] != self.saved[i]


# ---------------------------------------------------------------- bit helpers

def to_rows(v):
    return [(v >> (56 - 8 * r)) & 0xFF for r in range(SIZE)]


def from_rows(rows):
    v = 0
    for r in rows:
        v = (v << 8) | (r & 0xFF)
    return v


def get_pixel(v, r, c):
    return (v >> (63 - (8 * r + c))) & 1


def set_pixel(v, r, c, bit):
    m = 1 << (63 - (8 * r + c))
    return (v | m) if bit else (v & ~m & MASK)


def reverse_byte(b):
    return int(f"{b:08b}"[::-1], 2)


TRANSFORMS = {
    "up":     lambda v: from_rows(to_rows(v)[1:] + [0]),
    "down":   lambda v: from_rows([0] + to_rows(v)[:-1]),
    "left":   lambda v: from_rows([(r << 1) & 0xFF for r in to_rows(v)]),
    "right":  lambda v: from_rows([r >> 1 for r in to_rows(v)]),
    "flip_h": lambda v: from_rows([reverse_byte(r) for r in to_rows(v)]),
    "flip_v": lambda v: from_rows(to_rows(v)[::-1]),
    "invert": lambda v: ~v & MASK,
    "clear":  lambda v: 0,
}


def glyph_label(addr):
    if 0x20 < addr < 0x7F:
        return chr(addr)
    if addr == 0x20:
        return "SP"
    return f"{addr:02X}"


def glyph_image(v, scale):
    img = tk.PhotoImage(width=SIZE, height=SIZE)
    data = " ".join("{" + " ".join(WHITE if get_pixel(v, r, c) else BLACK
                                   for c in range(SIZE)) + "}" for r in range(SIZE))
    img.put(data)
    return img.zoom(scale) if scale > 1 else img


# ---------------------------------------------------------------- editor

class GlyphEditor:
    def __init__(self, root):
        self.root = root
        self.font = None
        self.path = None
        self.index = 0
        self.undo = []         # (glyph_index, previous_value)
        self.clip = None
        self.paint_val = None
        self.thumbs = []
        self.mod = "Command" if root.tk.call("tk", "windowingsystem") == "aqua" else "Control"
        self._build()
        self.update_title()
        root.protocol("WM_DELETE_WINDOW", self.on_quit)

    # ---- UI
    def _build(self):
        acc = "Cmd" if self.mod == "Command" else "Ctrl"
        menubar = tk.Menu(self.root)
        fm = tk.Menu(menubar, tearoff=0)
        fm.add_command(label="Open...", accelerator=f"{acc}+O", command=self.open_file)
        fm.add_command(label="Save", accelerator=f"{acc}+S", command=self.save)
        fm.add_command(label="Save As...", command=self.save_as)
        fm.add_separator()
        fm.add_command(label="Quit", command=self.on_quit)
        menubar.add_cascade(label="File", menu=fm)
        em = tk.Menu(menubar, tearoff=0)
        em.add_command(label="Undo", accelerator=f"{acc}+Z", command=self.do_undo)
        em.add_command(label="Copy Glyph", accelerator=f"{acc}+C", command=self.copy)
        em.add_command(label="Paste Glyph", accelerator=f"{acc}+V", command=self.paste)
        em.add_separator()
        em.add_command(label="Revert Glyph to Saved", command=self.revert_glyph)
        menubar.add_cascade(label="Edit", menu=em)
        self.root.config(menu=menubar)

        main = tk.Frame(self.root, padx=8, pady=8)
        main.pack(fill="both", expand=True)

        # Glyph browser
        left = tk.Frame(main)
        left.grid(row=0, column=0, sticky="ns")
        tk.Label(left, text="Glyphs (fixed order)", font=("TkDefaultFont", 11, "bold")
                 ).pack(anchor="w")
        self.tw = SIZE * THUMB + 8
        self.th = SIZE * THUMB + 20
        bw = BROWSER_COLS * self.tw + 4
        box = tk.Frame(left)
        box.pack(fill="y", expand=True)
        self.browser = tk.Canvas(box, width=bw, height=8 * self.th + 4, bg="#202020",
                                 highlightthickness=0)
        sb = tk.Scrollbar(box, orient="vertical", command=self.browser.yview)
        self.browser.configure(yscrollcommand=sb.set)
        self.browser.pack(side="left", fill="y")
        sb.pack(side="left", fill="y")
        self.browser.bind("<Button-1>", self.on_browser_click)
        self.browser.bind("<MouseWheel>",
                          lambda e: self.browser.yview_scroll(-1 if e.delta > 0 else 1, "units"))

        # Pixel editor
        right = tk.Frame(main, padx=12)
        right.grid(row=0, column=1, sticky="n")
        self.info = tk.Label(right, text="", font=("Courier", 13, "bold"))
        self.info.pack(anchor="w")
        self.grid_cv = tk.Canvas(right, width=SIZE * CELL + 1, height=SIZE * CELL + 1,
                                 highlightthickness=1, highlightbackground="#555", bg=BLACK)
        self.grid_cv.pack(pady=(4, 6))
        self.cells = [[self.grid_cv.create_rectangle(
            c * CELL + 1, r * CELL + 1, (c + 1) * CELL + 1, (r + 1) * CELL + 1,
            outline=GRID_LINE, fill=BLACK) for c in range(SIZE)] for r in range(SIZE)]
        g = self.grid_cv
        g.bind("<Button-1>", lambda e: self.on_press(e, toggle=True))
        g.bind("<B1-Motion>", self.on_drag)
        g.bind("<ButtonRelease-1>", self.on_release)
        right_btns = ["3"] + (["2"] if self.mod == "Command" else [])
        for b in right_btns:
            g.bind(f"<Button-{b}>", lambda e: self.on_press(e, toggle=False))
            g.bind(f"<B{b}-Motion>", self.on_drag)
            g.bind(f"<ButtonRelease-{b}>", self.on_release)
        g.bind("<Control-Button-1>", lambda e: self.on_press(e, toggle=False))
        g.bind("<Control-B1-Motion>", self.on_drag)
        g.bind("<Control-ButtonRelease-1>", self.on_release)

        hexrow = tk.Frame(right)
        hexrow.pack(anchor="w", pady=(0, 6))
        tk.Label(hexrow, text="Hex").pack(side="left")
        self.hex_var = tk.StringVar()
        self.hex_entry = tk.Entry(hexrow, textvariable=self.hex_var, width=18,
                                  font=("Courier", 12))
        self.hex_entry.pack(side="left", padx=4)
        self.hex_entry.bind("<Return>", self.on_hex)
        self.hex_entry.bind("<FocusOut>", self.on_hex)
        self.preview_cv = tk.Label(hexrow, bg=BLACK)
        self.preview_cv.pack(side="left", padx=6)

        tools = tk.Frame(right)
        tools.pack(anchor="w")
        for i, (label, key) in enumerate((("↑", "up"), ("↓", "down"), ("←", "left"),
                                          ("→", "right"), ("Flip H", "flip_h"),
                                          ("Flip V", "flip_v"), ("Invert", "invert"),
                                          ("Clear", "clear"))):
            tk.Button(tools, text=label, width=5,
                      command=lambda k=key: self.transform(k)).grid(row=i // 4, column=i % 4)

        nav = tk.Frame(right)
        nav.pack(anchor="w", pady=(6, 0))
        tk.Button(nav, text="◀ Prev", command=lambda: self.select(self.index - 1)).pack(side="left")
        tk.Button(nav, text="Next ▶", command=lambda: self.select(self.index + 1)).pack(side="left")
        tk.Button(nav, text="Revert glyph", command=self.revert_glyph).pack(side="left", padx=6)

        # Text preview
        bottom = tk.Frame(main, pady=8)
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew")
        tk.Label(bottom, text="Preview text:").pack(side="left")
        self.text_var = tk.StringVar(value="The quick brown fox 0123!?")
        te = tk.Entry(bottom, textvariable=self.text_var, width=40)
        te.pack(side="left", padx=4)
        self.text_var.trace_add("write", lambda *a: self.draw_text_preview())
        self.text_preview = tk.Label(main, bg=BLACK, anchor="w")
        self.text_preview.grid(row=2, column=0, columnspan=2, sticky="w")

        self.status = tk.StringVar()
        tk.Label(self.root, textvariable=self.status, fg="#666", anchor="w",
                 padx=8).pack(fill="x", pady=(0, 4))

        m = self.mod
        r = self.root
        r.bind(f"<{m}-o>", lambda e: self.open_file())
        r.bind(f"<{m}-s>", lambda e: self.save())
        r.bind(f"<{m}-z>", lambda e: self.key_cmd(self.do_undo))
        r.bind(f"<{m}-c>", lambda e: self.key_cmd(self.copy))
        r.bind(f"<{m}-v>", lambda e: self.key_cmd(self.paste))
        for key, step in (("Left", -1), ("Right", 1), ("Up", -BROWSER_COLS),
                          ("Down", BROWSER_COLS)):
            r.bind(f"<{key}>", lambda e, s=step: self.key_cmd(
                lambda: self.select(self.index + s)))
            r.bind(f"<Shift-{key}>", lambda e, k=key.lower(): self.key_cmd(
                lambda: self.transform(k)))

    def key_cmd(self, fn):
        """Run a shortcut unless a text entry has focus (so it keeps native keys)."""
        if isinstance(self.root.focus_get(), tk.Entry):
            return
        if self.font:
            fn()
        return "break"

    # ---- drawing
    def redraw_browser(self):
        b = self.browser
        b.delete("all")
        self.thumbs = []
        for i, v in enumerate(self.font.values):
            r, c = divmod(i, BROWSER_COLS)
            x, y = c * self.tw + 2, r * self.th + 2
            img = glyph_image(v, THUMB)
            self.thumbs.append(img)
            b.create_rectangle(x, y, x + self.tw - 2, y + self.th - 2,
                               outline="#444", tags=f"box{i}")
            b.create_image(x + 3, y + 3, image=img, anchor="nw", tags=f"img{i}")
            b.create_text(x + self.tw / 2 - 1, y + self.th - 9,
                          text=glyph_label(self.font.slots[i][3]),
                          fill="#ccc", font=("Courier", 9))
        rows = (len(self.font.values) + BROWSER_COLS - 1) // BROWSER_COLS
        b.configure(scrollregion=(0, 0, BROWSER_COLS * self.tw + 4, rows * self.th + 4))
        self.update_box_styles()

    def update_box_styles(self):
        for i in range(len(self.font.values)):
            if i == self.index:
                color, w = SELECT, 2
            elif self.font.modified(i):
                color, w = MODIFIED, 2
            else:
                color, w = "#444", 1
            self.browser.itemconfig(f"box{i}", outline=color, width=w)

    def update_thumb(self, i):
        img = glyph_image(self.font.values[i], THUMB)
        self.thumbs[i] = img
        self.browser.itemconfig(f"img{i}", image=img)

    def redraw_editor(self):
        v = self.font.values[self.index]
        for r in range(SIZE):
            for c in range(SIZE):
                self.grid_cv.itemconfig(self.cells[r][c],
                                        fill=WHITE if get_pixel(v, r, c) else BLACK)
        addr = self.font.slots[self.index][3]
        line = self.font.slots[self.index][0] + 1
        ch = f"'{chr(addr)}'" if 0x20 <= addr < 0x7F else ""
        self.info.config(text=f"Glyph 0x{addr:02X} {ch}  (line {line})")
        self.hex_var.set(f"{v:0{HEX_DIGITS}X}")
        self._preview_img = glyph_image(v, 2)
        self.preview_cv.config(image=self._preview_img)

    def draw_text_preview(self):
        if not self.font:
            return
        text = self.text_var.get()[:80] or " "
        by_addr = {s[3]: v for s, v in zip(self.font.slots, self.font.values)}
        w = SIZE * len(text)
        img = tk.PhotoImage(width=w, height=SIZE)
        rows = []
        for r in range(SIZE):
            px = []
            for ch in text:
                v = by_addr.get(ord(ch), 0)
                px.extend(WHITE if get_pixel(v, r, c) else BLACK for c in range(SIZE))
            rows.append("{" + " ".join(px) + "}")
        img.put(" ".join(rows))
        self._text_img = img.zoom(2)
        self.text_preview.config(image=self._text_img)

    def refresh_glyph(self, i):
        self.update_thumb(i)
        if i == self.index:
            self.redraw_editor()
        self.update_box_styles()
        self.draw_text_preview()
        self.update_title()

    # ---- editing
    def set_value(self, i, v, record=True):
        old = self.font.values[i]
        if v == old:
            return
        if record:
            self.undo.append((i, old))
        self.font.values[i] = v
        self.refresh_glyph(i)

    def cell_at(self, e):
        c, r = (e.x - 1) // CELL, (e.y - 1) // CELL
        return (r, c) if 0 <= r < SIZE and 0 <= c < SIZE else None

    def on_press(self, e, toggle):
        if not self.font:
            return "break"
        cell = self.cell_at(e)
        if not cell:
            return "break"
        v = self.font.values[self.index]
        self.stroke_start = v
        self.paint_val = (1 - get_pixel(v, *cell)) if toggle else 0
        self.font.values[self.index] = set_pixel(v, *cell, self.paint_val)
        self.refresh_glyph(self.index)
        return "break"

    def on_drag(self, e):
        if self.paint_val is None:
            return
        cell = self.cell_at(e)
        if cell:
            v = self.font.values[self.index]
            nv = set_pixel(v, *cell, self.paint_val)
            if nv != v:
                self.font.values[self.index] = nv
                self.refresh_glyph(self.index)

    def on_release(self, e):
        if self.paint_val is not None and self.font.values[self.index] != self.stroke_start:
            self.undo.append((self.index, self.stroke_start))
        self.paint_val = None

    def transform(self, key):
        self.set_value(self.index, TRANSFORMS[key](self.font.values[self.index]))

    def on_hex(self, e=None):
        if not self.font:
            return
        t = self.hex_var.get().strip().replace("_", "")
        if t.lower().startswith("0x"):
            t = t[2:]
        if re.fullmatch(r"[0-9A-Fa-f]{1,%d}" % HEX_DIGITS, t):
            self.set_value(self.index, int(t, 16))
        elif e is not None and e.type == tk.EventType.KeyPress:
            self.root.bell()
        self.hex_var.set(f"{self.font.values[self.index]:0{HEX_DIGITS}X}")

    def do_undo(self):
        if not self.undo:
            self.root.bell()
            return
        i, v = self.undo.pop()
        self.select(i)
        self.set_value(i, v, record=False)

    def copy(self):
        v = self.font.values[self.index]
        self.clip = v
        self.root.clipboard_clear()
        self.root.clipboard_append(f"{v:0{HEX_DIGITS}X}")
        self.status.set(f"Copied glyph {self.index:02X}")

    def paste(self):
        if self.clip is None:
            self.root.bell()
            return
        self.set_value(self.index, self.clip)

    def revert_glyph(self):
        if self.font:
            self.set_value(self.index, self.font.saved[self.index])

    def select(self, i):
        if not self.font:
            return
        i = max(0, min(len(self.font.values) - 1, i))
        self.index = i
        self.redraw_editor()
        self.update_box_styles()
        r = i // BROWSER_COLS
        rows = (len(self.font.values) + BROWSER_COLS - 1) // BROWSER_COLS
        top, bot = self.browser.yview()
        if not (top * rows <= r < bot * rows - 0.5):
            self.browser.yview_moveto(max(0, r - 2) / rows)

    def on_browser_click(self, e):
        if not self.font:
            return
        x, y = self.browser.canvasx(e.x), self.browser.canvasy(e.y)
        c, r = int(x - 2) // self.tw, int(y - 2) // self.th
        i = r * BROWSER_COLS + c
        if 0 <= c < BROWSER_COLS and 0 <= i < len(self.font.values):
            self.select(i)

    # ---- files
    def dirty(self):
        return bool(self.font) and self.font.values != self.font.saved

    def update_title(self):
        name = os.path.basename(self.path) if self.path else "No file"
        self.root.title(f"{'*' if self.dirty() else ''}{name} - Glyph Editor")
        if self.font:
            n = sum(self.font.modified(i) for i in range(len(self.font.values)))
            self.status.set(f"{len(self.font.values)} glyphs   {n} modified (orange)   "
                            "L: toggle  R: black  Shift+arrows: shift")

    def confirm_discard(self):
        if not self.dirty():
            return True
        ans = messagebox.askyesnocancel("Unsaved changes", "Save changes first?")
        if ans is None:
            return False
        return self.save() if ans else True

    def open_file(self, path=None):
        if not self.confirm_discard():
            return
        if not path:
            path = filedialog.askopenfilename(
                title="Open glyph font", filetypes=[("Memory file", "*.mem"), ("All files", "*")])
            if not path:
                return
        try:
            font = FontFile.load(path)
        except (OSError, ValueError, UnicodeDecodeError) as e:
            messagebox.showerror("Open failed", str(e))
            return
        self.font, self.path, self.undo = font, path, []
        self.redraw_browser()
        self.select(0x41 if len(font.values) > 0x41 else 0)
        self.draw_text_preview()
        self.update_title()

    def save(self):
        if not self.font:
            return False
        if not self.path:
            return self.save_as()
        return self._save_to(self.path)

    def save_as(self):
        if not self.font:
            return False
        path = filedialog.asksaveasfilename(
            title="Save glyph font", defaultextension=".mem",
            initialfile=os.path.basename(self.path or "font.mem"),
            filetypes=[("Memory file", "*.mem")])
        return self._save_to(path) if path else False

    def _save_to(self, path):
        try:
            self.font.save(path)
        except (OSError, RuntimeError, ValueError) as e:
            messagebox.showerror("Save failed", str(e))
            return False
        self.path = path
        self.update_box_styles()
        self.update_title()
        return True

    def on_quit(self):
        if self.confirm_discard():
            self.root.destroy()


def main():
    root = tk.Tk()
    root.resizable(False, False)
    app = GlyphEditor(root)
    if len(sys.argv) > 1:
        app.open_file(sys.argv[1])
    else:
        root.after(100, app.open_file)
    root.mainloop()


if __name__ == "__main__":
    main()
