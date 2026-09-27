"""
MP3 Tag Editor
A simple GUI app for viewing and editing MP3 metadata (ID3 tags).

Requirements:
    pip install mutagen

Run:
    python MP3edit.py
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, TRCK, APIC


class MP3TagEditor(tk.Tk):
    FIELDS = [
        ("Title", "title"),
        ("Artist", "artist"),
        ("Album", "album"),
        ("Year", "year"),
        ("Genre", "genre"),
        ("Track #", "track"),
    ]

    def __init__(self):
        super().__init__()
        self.title("MP3 Tag Editor")
        self.geometry("480x420")
        self.resizable(False, False)

        self.filepath = None
        self.entries = {}
        self.cover_data = None  # holds new cover art bytes if changed

        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # File chooser row
        top = ttk.Frame(self)
        top.pack(fill="x", **pad)

        self.file_label = ttk.Label(top, text="No file selected", anchor="w")
        self.file_label.pack(side="left", fill="x", expand=True)

        ttk.Button(top, text="Open MP3...", command=self.open_file).pack(side="right")

        # Metadata fields
        form = ttk.Frame(self)
        form.pack(fill="x", **pad)

        for label_text, key in self.FIELDS:
            row = ttk.Frame(form)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label_text, width=10).pack(side="left")
            entry = ttk.Entry(row)
            entry.pack(side="left", fill="x", expand=True)
            self.entries[key] = entry

        # Cover art
        cover_row = ttk.Frame(self)
        cover_row.pack(fill="x", **pad)
        ttk.Button(cover_row, text="Set Cover Image...", command=self.choose_cover).pack(side="left")
        self.cover_label = ttk.Label(cover_row, text="No new cover selected")
        self.cover_label.pack(side="left", padx=10)

        # Status / actions
        ttk.Separator(self).pack(fill="x", pady=10)

        actions = ttk.Frame(self)
        actions.pack(fill="x", **pad)
        ttk.Button(actions, text="Save Changes", command=self.save_file).pack(side="right")

        self.status = ttk.Label(self, text="", foreground="green")
        self.status.pack(fill="x", padx=10)

    # ---------- Actions ----------
    def open_file(self):
        path = filedialog.askopenfilename(
            title="Select an MP3 file",
            filetypes=[("MP3 files", "*.mp3")]
        )
        if not path:
            return

        self.filepath = path
        self.cover_data = None
        self.cover_label.config(text="No new cover selected")
        self.file_label.config(text=os.path.basename(path))
        self.status.config(text="")

        try:
            audio = MP3(path, ID3=ID3)
            tags = audio.tags
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")
            return

        values = {
            "title": self._get_text(tags, "TIT2"),
            "artist": self._get_text(tags, "TPE1"),
            "album": self._get_text(tags, "TALB"),
            "year": self._get_text(tags, "TDRC"),
            "genre": self._get_text(tags, "TCON"),
            "track": self._get_text(tags, "TRCK"),
        }

        for key, entry in self.entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, values.get(key, ""))

    @staticmethod
    def _get_text(tags, frame_id):
        if tags is None or frame_id not in tags:
            return ""
        return str(tags[frame_id].text[0])

    def choose_cover(self):
        path = filedialog.askopenfilename(
            title="Select cover image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if not path:
            return
        with open(path, "rb") as f:
            self.cover_data = f.read()
        mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
        self.cover_mime = mime
        self.cover_label.config(text=os.path.basename(path))

    def save_file(self):
        if not self.filepath:
            messagebox.showwarning("No file", "Open an MP3 file first.")
            return

        try:
            audio = MP3(self.filepath, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            tags = audio.tags

            values = {k: e.get().strip() for k, e in self.entries.items()}

            self._set_or_remove(tags, "TIT2", TIT2, values["title"])
            self._set_or_remove(tags, "TPE1", TPE1, values["artist"])
            self._set_or_remove(tags, "TALB", TALB, values["album"])
            self._set_or_remove(tags, "TDRC", TDRC, values["year"])
            self._set_or_remove(tags, "TCON", TCON, values["genre"])
            self._set_or_remove(tags, "TRCK", TRCK, values["track"])

            if self.cover_data:
                # Remove existing cover art frames, then add the new one
                tags.delall("APIC")
                tags.add(APIC(
                    encoding=3,
                    mime=self.cover_mime,
                    type=3,  # front cover
                    desc="Cover",
                    data=self.cover_data,
                ))

            audio.save()
            self.status.config(text="Saved successfully.", foreground="green")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")
            self.status.config(text="Save failed.", foreground="red")

    @staticmethod
    def _set_or_remove(tags, frame_id, frame_cls, value):
        if value:
            tags.setall(frame_id, [frame_cls(encoding=3, text=value)])
        else:
            tags.delall(frame_id)


if __name__ == "__main__":
    app = MP3TagEditor()
    app.mainloop()