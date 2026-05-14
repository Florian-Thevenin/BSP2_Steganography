import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
import os
import numpy as np

from Steg.Image_Process import load_image, save_image, save_gif
from Steg.LSB_Embed import embed_lsb
from Steg.LSB_Extract import extract_lsb
from Misc.Utils import (
    text_to_bytes, bytes_to_text,
    compress_data, decompress_data
)
from Misc.Render import render_text_on_image, MAX_SINGLE_RENDER_CHARS
from Crypto.Key_Generation import derive_key
from Crypto.Encrypt import encrypt_data
from Crypto.Decrypt import decrypt_data


# ─── Palette — moody pastel blue sky ────────────────────────────────────────
BG        = "#d6e8f5"   # pale morning sky
SURFACE   = "#b8d4ea"   # soft cloud blue
SURFACE2  = "#cfe0ef"   # lighter cloud surface
BORDER    = "#8ab4d4"   # horizon line blue
ACCENT    = "#3a7fc1"   # deep sky blue
ACCENT2   = "#2563a8"   # darker accent / hover
TEXT      = "#1a2e42"   # dark ink
MUTED     = "#5a7a96"   # faded cloud text
SUCCESS   = "#2d7a4f"   # muted green
ERROR     = "#b03030"   # muted red
NAV_BG    = "#a8c8e0"   # slightly deeper for nav
NAV_SEL   = "#cfe0ef"   # selected nav item
NAV_W     = 180

# ─── Fonts ───────────────────────────────────────────────────────────────────
FONT_UI   = ("Segoe UI", 12)
FONT_SM   = ("Segoe UI", 10)
FONT_XS   = ("Segoe UI", 9)
FONT_H    = ("Segoe UI", 14, "bold")
FONT_MONO = ("Consolas", 10)


# ─── Widget helpers ───────────────────────────────────────────────────────────

def make_scrollbar(parent, command):
    """Thin styled scrollbar (8 px wide)."""
    return tk.Scrollbar(
        parent, command=command,
        bg=SURFACE, troughcolor=BG,
        activebackground=ACCENT,
        relief="flat", width=8, bd=0, highlightthickness=0
    )


def make_textbox(parent, height=7):
    """Bordered frame containing a Text widget + thin scrollbar.
    Returns (outer_frame, text_widget)."""
    outer = tk.Frame(parent, bg=BORDER, bd=1, relief="flat", highlightthickness=0)
    inner = tk.Frame(outer, bg=SURFACE2)
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    txt = tk.Text(
        inner, bg=SURFACE2, fg=TEXT,
        insertbackground=ACCENT,
        relief="flat", font=FONT_MONO,
        height=height, wrap="word",
        padx=8, pady=8,
        bd=0, highlightthickness=0
    )
    sb = make_scrollbar(inner, txt.yview)
    sb.pack(side="right", fill="y")
    txt.pack(side="left", fill="both", expand=True)
    txt.config(yscrollcommand=sb.set)
    return outer, txt


def styled_button(parent, text, command, accent=False, small=False, **kwargs):
    bg = ACCENT if accent else SURFACE
    fg = "#ffffff" if accent else TEXT
    af = ACCENT2 if accent else BORDER
    f  = FONT_SM  if small  else FONT_UI
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg,
        activebackground=af,
        activeforeground="#ffffff" if accent else TEXT,
        relief="flat", cursor="hand2", font=f,
        padx=12, pady=6 if not small else 4,
        bd=0, highlightthickness=0,
        **kwargs
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=af))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def styled_entry(parent, width=30):
    """Plain visible-text entry (no masking)."""
    return tk.Entry(
        parent, bg=SURFACE2, fg=TEXT,
        insertbackground=ACCENT,
        relief="flat", font=FONT_UI,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT,
        width=width
    )


def label(parent, text, muted=False, heading=False, bg=None, **kwargs):
    f  = FONT_H if heading else (FONT_XS if muted else FONT_UI)
    fg = MUTED  if muted   else TEXT
    bg = bg or BG
    return tk.Label(parent, text=text, bg=bg, fg=fg, font=f, **kwargs)


def divider(parent):
    return tk.Frame(parent, bg=BORDER, height=1)


# ═══════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stag Hide")
        self.configure(bg=BG)
        self.minsize(900, 600)
        self.geometry("1200x750")

        # App icon (.docs/Stag.ico)
        icon_path = os.path.join(".docs", "Stag.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Shared state
        self.current_image_path = None   # path of the image currently loaded
        self.current_np_image   = None   # numpy array of that image
        self.extracted_message  = None   # last successfully decoded message
        self.rendered_result    = None   # numpy array OR list[PIL.Image] from render
        self.active_nav         = None

        self._build_layout()
        self._show_section("embed")

    # ── Layout ───────────────────────────────────────────────────────────────
    def _build_layout(self):
        # Left navigation strip
        self.nav = tk.Frame(self, bg=NAV_BG, width=NAV_W)
        self.nav.pack(side="left", fill="y")
        self.nav.pack_propagate(False)

        tk.Label(
            self.nav, text="Stag Hide", bg=NAV_BG, fg=ACCENT2,
            font=("Segoe UI", 13, "bold"), pady=26
        ).pack(fill="x")
        divider(self.nav).pack(fill="x", padx=12)

        tk.Label(self.nav, text="TOOLS", bg=NAV_BG, fg=MUTED,
                 font=FONT_XS, pady=12).pack(fill="x", padx=18, anchor="w")

        self.nav_buttons = {}
        for key, label_text in [("embed", "Embed"),
                                 ("extract", "Extract"),
                                 ("render", "Render")]:
            btn = tk.Button(
                self.nav, text=label_text,
                bg=NAV_BG, fg=TEXT,
                activebackground=NAV_SEL, activeforeground=ACCENT2,
                relief="flat", anchor="w", font=FONT_UI,
                padx=20, pady=11, bd=0, highlightthickness=0,
                cursor="hand2",
                command=lambda k=key: self._show_section(k)
            )
            btn.pack(fill="x")
            self.nav_buttons[key] = btn

        tk.Label(self.nav, text="v1.0", bg=NAV_BG, fg=MUTED,
                 font=FONT_XS).pack(side="bottom", pady=12)

        # Main area
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)

        # Right side — image preview
        self.right = tk.Frame(self.main, bg=BG)
        self.right.pack(side="right", fill="both", expand=True)

        self.preview_frame = tk.Frame(
            self.right, bg=SURFACE,
            highlightthickness=1, highlightbackground=BORDER
        )
        self.preview_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        self.preview_label = tk.Label(
            self.preview_frame, bg=SURFACE,
            text="No image loaded", fg=MUTED, font=FONT_UI
        )
        self.preview_label.pack(fill="both", expand=True)

        # Left side — form content panel
        self.content = tk.Frame(self.main, bg=BG, width=380)
        self.content.pack(side="left", fill="both", padx=(20, 0), pady=20)
        self.content.pack_propagate(False)

    # ── Nav highlight ─────────────────────────────────────────────────────────
    def _highlight_nav(self, key):
        for k, btn in self.nav_buttons.items():
            btn.config(bg=NAV_SEL if k == key else NAV_BG,
                       fg=ACCENT2  if k == key else TEXT)
        self.active_nav = key

    # ── State management ──────────────────────────────────────────────────────
    def _reset_state(self):
        self.current_image_path = None
        self.current_np_image   = None
        self.extracted_message  = None
        self.rendered_result    = None
        self._clear_preview()

    def _clear_preview(self):
        self.preview_label.config(image="", text="No image loaded",
                                  fg=MUTED, compound="none")
        self.preview_label.image = None

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ── Preview display ───────────────────────────────────────────────────────
    def _show_np_in_preview(self, np_img):
        self._show_pil_in_preview(Image.fromarray(np_img.astype("uint8")))

    def _show_pil_in_preview(self, pil_img):
        """Fit-display a PIL image. Always copies first so the source is never mutated."""
        self.preview_frame.update_idletasks()
        fw = self.preview_frame.winfo_width()  or 620
        fh = self.preview_frame.winfo_height() or 460
        display = pil_img.copy()                          # ← protects GIF frames from being resized
        display.thumbnail((fw - 8, fh - 8), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(display)
        self.preview_label.config(image=tk_img, text="", compound="none")
        self.preview_label.image = tk_img

    def _show_path_in_preview(self, path):
        try:
            self._show_pil_in_preview(Image.open(path).convert("RGB"))
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image:\n{e}")

    # ── Section router ────────────────────────────────────────────────────────
    def _show_section(self, key):
        if key != self.active_nav:
            self._reset_state()
        self._highlight_nav(key)
        self._clear_content()
        {"embed": self._build_embed,
         "extract": self._build_extract,
         "render": self._build_render}[key]()

    # ══════════════════════════════════════════════════════════════════════════
    # EMBED
    # ══════════════════════════════════════════════════════════════════════════
    def _build_embed(self):
        c = self.content

        label(c, "Embed", heading=True).pack(anchor="w", pady=(0, 4))
        label(c, "Hide a message inside an image.", muted=True).pack(anchor="w")
        divider(c).pack(fill="x", pady=14)

        # Image picker
        label(c, "Cover Image").pack(anchor="w")
        row = tk.Frame(c, bg=BG)
        row.pack(fill="x", pady=(4, 12))
        self._embed_img_lbl = tk.Label(
            row, text="No file chosen",
            bg=SURFACE2, fg=MUTED, font=FONT_XS, anchor="w", padx=8, pady=6
        )
        self._embed_img_lbl.pack(side="left", fill="x", expand=True)
        styled_button(row, "Browse…", self._embed_pick_image, small=True).pack(side="right", padx=(6, 0))

        # Message box with thin scrollbar
        label(c, "Message").pack(anchor="w")
        txt_frame, self._embed_msg = make_textbox(c, height=7)
        txt_frame.pack(fill="both", pady=(4, 4))
        styled_button(c, "Load .txt file", self._embed_load_txt, small=True).pack(anchor="w", pady=(2, 12))

        divider(c).pack(fill="x", pady=10)

        # Password — visible text
        label(c, "Encryption (Fernet)").pack(anchor="w")
        self._embed_use_pw = tk.BooleanVar(value=False)
        tk.Checkbutton(
            c, text="Use password", variable=self._embed_use_pw,
            bg=BG, fg=TEXT, selectcolor=SURFACE2,
            activebackground=BG, activeforeground=ACCENT2,
            font=FONT_UI, command=self._embed_toggle_pw
        ).pack(anchor="w", pady=(4, 0))

        self._embed_pw_frame = tk.Frame(c, bg=BG)
        self._embed_pw_frame.pack(fill="x", pady=(4, 0))
        # entry prepared but not placed until checkbox ticked
        self._embed_pw_entry = styled_entry(self._embed_pw_frame)

        divider(c).pack(fill="x", pady=14)
        styled_button(c, "Encode & Save Image", self._embed_run, accent=True).pack(fill="x")

        self._embed_status = tk.Label(
            c, text="", bg=BG, fg=SUCCESS, font=FONT_XS, wraplength=340, justify="left"
        )
        self._embed_status.pack(anchor="w", pady=(8, 0))

    def _embed_toggle_pw(self):
        for w in self._embed_pw_frame.winfo_children():
            w.destroy()
        self._embed_pw_entry = styled_entry(self._embed_pw_frame)
        if self._embed_use_pw.get():
            label(self._embed_pw_frame, "Password").pack(anchor="w")
            self._embed_pw_entry.pack(fill="x", pady=(4, 0))

    def _embed_pick_image(self):
        path = filedialog.askopenfilename(
            title="Choose cover image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All files", "*.*")]
        )
        if not path:
            return
        self.current_image_path = path
        self._embed_img_lbl.config(text=os.path.basename(path), fg=TEXT)
        try:
            self.current_np_image = load_image(path)
            self._show_path_in_preview(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _embed_load_txt(self):
        path = filedialog.askopenfilename(
            title="Load text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self._embed_msg.delete("1.0", "end")
            self._embed_msg.insert("1.0", content)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _embed_run(self):
        if self.current_np_image is None:
            messagebox.showwarning("Missing", "Please choose a cover image first.")
            return
        message = self._embed_msg.get("1.0", "end").strip()
        if not message:
            messagebox.showwarning("Missing", "Please enter a message.")
            return
        password = None
        if self._embed_use_pw.get():
            password = self._embed_pw_entry.get()
            if not password:
                messagebox.showwarning("Missing", "Please enter a password.")
                return

        out_path = filedialog.asksaveasfilename(
            title="Save encoded image",
            defaultextension=".png",
            initialfile="output.png",
            filetypes=[("PNG Image", "*.png")]
        )
        if not out_path:
            return

        self._embed_status.config(text="Encoding…", fg=MUTED)
        self.update_idletasks()

        def _run():
            try:
                data = compress_data(text_to_bytes(message))
                if password:
                    data = encrypt_data(data, derive_key(password))
                encoded = embed_lsb(self.current_np_image, data)
                save_image(encoded, out_path)
                self.after(0, lambda: self._embed_status.config(
                    text=f"✓ Saved to {os.path.basename(out_path)}", fg=SUCCESS))
            except Exception as e:
                self.after(0, lambda: self._embed_status.config(text=f"✗ {e}", fg=ERROR))

        threading.Thread(target=_run, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # EXTRACT
    # ══════════════════════════════════════════════════════════════════════════
    def _build_extract(self):
        c = self.content

        label(c, "Extract", heading=True).pack(anchor="w", pady=(0, 4))
        label(c, "Recover a hidden message from an image.", muted=True).pack(anchor="w")
        divider(c).pack(fill="x", pady=14)

        # Image picker
        label(c, "Encoded Image").pack(anchor="w")
        row = tk.Frame(c, bg=BG)
        row.pack(fill="x", pady=(4, 12))
        self._ext_img_lbl = tk.Label(
            row, text="No file chosen",
            bg=SURFACE2, fg=MUTED, font=FONT_XS, anchor="w", padx=8, pady=6
        )
        self._ext_img_lbl.pack(side="left", fill="x", expand=True)
        styled_button(row, "Browse…", self._ext_pick_image, small=True).pack(side="right", padx=(6, 0))

        # Password — visible text
        label(c, "Decryption (Fernet)").pack(anchor="w")
        self._ext_use_pw = tk.BooleanVar(value=False)
        tk.Checkbutton(
            c, text="Use password", variable=self._ext_use_pw,
            bg=BG, fg=TEXT, selectcolor=SURFACE2,
            activebackground=BG, activeforeground=ACCENT2,
            font=FONT_UI, command=self._ext_toggle_pw
        ).pack(anchor="w", pady=(4, 0))

        self._ext_pw_frame = tk.Frame(c, bg=BG)
        self._ext_pw_frame.pack(fill="x", pady=(4, 0))
        self._ext_pw_entry = styled_entry(self._ext_pw_frame)

        divider(c).pack(fill="x", pady=14)
        styled_button(c, "Extract Message", self._ext_run, accent=True).pack(fill="x")

        self._ext_status = tk.Label(
            c, text="", bg=BG, fg=SUCCESS, font=FONT_XS, wraplength=340, justify="left"
        )
        self._ext_status.pack(anchor="w", pady=(8, 0))

        self._ext_result_frame = tk.Frame(c, bg=BG)
        self._ext_result_frame.pack(fill="both", expand=True)

    def _ext_toggle_pw(self):
        for w in self._ext_pw_frame.winfo_children():
            w.destroy()
        self._ext_pw_entry = styled_entry(self._ext_pw_frame)
        if self._ext_use_pw.get():
            label(self._ext_pw_frame, "Password").pack(anchor="w")
            self._ext_pw_entry.pack(fill="x", pady=(4, 0))

    def _ext_pick_image(self):
        path = filedialog.askopenfilename(
            title="Choose encoded image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All files", "*.*")]
        )
        if not path:
            return
        self.current_image_path = path
        self._ext_img_lbl.config(text=os.path.basename(path), fg=TEXT)
        try:
            self.current_np_image = load_image(path)
            self._show_path_in_preview(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _ext_run(self):
        if self.current_np_image is None:
            messagebox.showwarning("Missing", "Please choose an encoded image first.")
            return
        password = None
        if self._ext_use_pw.get():
            password = self._ext_pw_entry.get()
            if not password:
                messagebox.showwarning("Missing", "Please enter the password.")
                return

        self._ext_status.config(text="Extracting…", fg=MUTED)
        self.update_idletasks()

        def _run():
            try:
                raw = extract_lsb(self.current_np_image)
                data = raw

                if password:
                    try:
                        data = decrypt_data(raw, derive_key(password))
                    except Exception:
                        self.after(0, lambda: self._ext_status.config(
                            text="✗ Decryption failed — wrong password or corrupted data.", fg=ERROR))
                        return

                try:
                    decompressed = decompress_data(data)
                except Exception:
                    self.after(0, lambda: self._ext_status.config(
                        text="✗ Decompression failed — incorrect password or no hidden message.", fg=ERROR))
                    return

                try:
                    message = bytes_to_text(decompressed)
                except Exception:
                    self.after(0, lambda: self._ext_status.config(
                        text="✗ Could not decode message — data may be corrupted.", fg=ERROR))
                    return

                self.extracted_message = message
                self.after(0, lambda: self._ext_show_result(message))

            except Exception as e:
                self.after(0, lambda: self._ext_status.config(text=f"✗ {e}", fg=ERROR))

        threading.Thread(target=_run, daemon=True).start()

    def _ext_show_result(self, message):
        self._ext_status.config(text="✓ Message extracted successfully.", fg=SUCCESS)

        for w in self._ext_result_frame.winfo_children():
            w.destroy()

        divider(self._ext_result_frame).pack(fill="x", pady=10)
        label(self._ext_result_frame, "Extracted Message").pack(anchor="w")

        txt_frame, txt = make_textbox(self._ext_result_frame, height=6)
        txt_frame.pack(fill="both", pady=(4, 8))
        txt.insert("1.0", message)
        txt.config(state="disabled")

        styled_button(self._ext_result_frame, "⬇  Save as .txt",
                      self._ext_save_txt, small=True).pack(anchor="w", pady=(0, 10))

        divider(self._ext_result_frame).pack(fill="x", pady=6)
        label(self._ext_result_frame, "Render message onto image?").pack(anchor="w")
        row = tk.Frame(self._ext_result_frame, bg=BG)
        row.pack(fill="x", pady=(6, 0))
        styled_button(row, "Render", self._ext_go_render, accent=True, small=True).pack(side="left")
        styled_button(row, "Skip",   self._ext_skip_render, small=True).pack(side="left", padx=(8, 0))

    def _ext_save_txt(self):
        if not self.extracted_message:
            return
        path = filedialog.asksaveasfilename(
            title="Save message",
            defaultextension=".txt",
            initialfile="message.txt",
            filetypes=[("Text files", "*.txt")]
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.extracted_message)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _ext_go_render(self):
        self._highlight_nav("render")
        self._clear_content()
        self._build_render(prefill_message=self.extracted_message)

    def _ext_skip_render(self):
        self._clear_preview()
        self.current_image_path = None
        self.current_np_image   = None

    # ══════════════════════════════════════════════════════════════════════════
    # RENDER
    # ══════════════════════════════════════════════════════════════════════════
    def _build_render(self, prefill_message=None):
        c = self.content

        label(c, "Render", heading=True).pack(anchor="w", pady=(0, 4))
        label(c, "Overlay text on an image or GIF.", muted=True).pack(anchor="w")
        divider(c).pack(fill="x", pady=14)

        # Image picker
        label(c, "Base Image").pack(anchor="w")
        row = tk.Frame(c, bg=BG)
        row.pack(fill="x", pady=(4, 12))
        self._rnd_img_lbl = tk.Label(
            row, text="No file chosen",
            bg=SURFACE2, fg=MUTED, font=FONT_XS, anchor="w", padx=8, pady=6
        )
        self._rnd_img_lbl.pack(side="left", fill="x", expand=True)
        styled_button(row, "Browse…", self._rnd_pick_image, small=True).pack(side="right", padx=(6, 0))

        # Message box with thin scrollbar
        label(c, "Message").pack(anchor="w")
        txt_frame, self._rnd_msg = make_textbox(c, height=6)
        txt_frame.pack(fill="both", pady=(4, 4))

        if prefill_message:
            self._rnd_msg.insert("1.0", prefill_message)

        divider(c).pack(fill="x", pady=10)

        # Font size — checkbox shows/hides spinbox
        self._rnd_custom_fs = tk.BooleanVar(value=False)
        tk.Checkbutton(
            c, text="Override font size", variable=self._rnd_custom_fs,
            bg=BG, fg=TEXT, selectcolor=SURFACE2,
            activebackground=BG, activeforeground=ACCENT2,
            font=FONT_UI, command=self._rnd_toggle_fs
        ).pack(anchor="w", pady=(0, 4))

        # Container for the spinbox row — empty until checkbox ticked
        self._rnd_fs_frame = tk.Frame(c, bg=BG)
        self._rnd_fs_frame.pack(fill="x", pady=(0, 10))
        self._rnd_font_size = tk.IntVar(value=80)

        styled_button(c, "Render Preview", self._rnd_run, accent=True).pack(fill="x")

        self._rnd_status = tk.Label(
            c, text="", bg=BG, fg=SUCCESS, font=FONT_XS, wraplength=340, justify="left"
        )
        self._rnd_status.pack(anchor="w", pady=(8, 0))

        self._rnd_save_frame = tk.Frame(c, bg=BG)
        self._rnd_save_frame.pack(fill="x", pady=(8, 0))

    def _rnd_toggle_fs(self):
        """Show or hide the font-size spinbox based on checkbox state."""
        for w in self._rnd_fs_frame.winfo_children():
            w.destroy()
        if self._rnd_custom_fs.get():
            row = tk.Frame(self._rnd_fs_frame, bg=BG)
            row.pack(fill="x")
            label(row, "Font size:", bg=BG).pack(side="left")
            tk.Spinbox(
                row, from_=8, to=300,
                textvariable=self._rnd_font_size,
                width=6, bg=SURFACE2, fg=TEXT,
                relief="flat", font=FONT_UI,
                buttonbackground=SURFACE,
                insertbackground=ACCENT,
                highlightthickness=1, highlightbackground=BORDER
            ).pack(side="left", padx=(8, 0))
            label(row, "px", muted=True, bg=BG).pack(side="left", padx=(4, 0))

    def _rnd_pick_image(self):
        path = filedialog.askopenfilename(
            title="Choose base image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All files", "*.*")]
        )
        if not path:
            return
        self.current_image_path = path
        self._rnd_img_lbl.config(text=os.path.basename(path), fg=TEXT)
        try:
            self.current_np_image = load_image(path)
            self._show_path_in_preview(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _rnd_run(self):
        if self.current_np_image is None:
            messagebox.showwarning("Missing", "Please choose a base image first.")
            return
        message = self._rnd_msg.get("1.0", "end").strip()
        if not message:
            messagebox.showwarning("Missing", "Please enter a message to render.")
            return

        font_size_override = None
        if self._rnd_custom_fs.get():
            v = self._rnd_font_size.get()
            if v > 0:
                font_size_override = v

        self._rnd_status.config(text="Rendering…", fg=MUTED)
        for w in self._rnd_save_frame.winfo_children():
            w.destroy()
        self.update_idletasks()

        def _run():
            try:
                result = render_text_on_image(
                    self.current_np_image, message,
                    font_size_override=font_size_override
                )
                self.rendered_result = result
                self.after(0, lambda: self._rnd_show_preview(result))
            except Exception as e:
                self.after(0, lambda: self._rnd_status.config(text=f"✗ {e}", fg=ERROR))

        threading.Thread(target=_run, daemon=True).start()

    def _rnd_show_preview(self, result):
        self._rnd_status.config(text="✓ Rendered. Adjust and re-render if needed.", fg=SUCCESS)

        if isinstance(result, list):
            # GIF: show first frame. _show_pil_in_preview copies before thumbnailing,
            # so result[0] is never mutated and the saved GIF has full-size frames.
            self._show_pil_in_preview(result[0])
        else:
            self._show_np_in_preview(result)

        for w in self._rnd_save_frame.winfo_children():
            w.destroy()
        styled_button(self._rnd_save_frame, "⬇  Save Render",
                      self._rnd_save, accent=True).pack(fill="x")

    def _rnd_save(self):
        if self.rendered_result is None:
            return

        is_gif    = isinstance(self.rendered_result, list)
        base_name = "RENDER"
        if self.current_image_path:
            stem      = os.path.splitext(os.path.basename(self.current_image_path))[0]
            base_name = stem + "_RENDER"

        if is_gif:
            path = filedialog.asksaveasfilename(
                title="Save rendered GIF",
                defaultextension=".gif",
                initialfile=base_name + ".gif",
                filetypes=[("GIF", "*.gif")]
            )
            if path:
                try:
                    save_gif(self.rendered_result, path)
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        else:
            path = filedialog.asksaveasfilename(
                title="Save rendered image",
                defaultextension=".png",
                initialfile=base_name + ".png",
                filetypes=[("PNG Image", "*.png")]
            )
            if path:
                try:
                    save_image(self.rendered_result, path)
                except Exception as e:
                    messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = App()
    app.mainloop()