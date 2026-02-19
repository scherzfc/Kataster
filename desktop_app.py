"""
Kataster-Sorter Desktop Application
Eigenständige Desktop-App mit automatischer Dateierkennung.
"""

import os
import sys
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk
from pdf_processor import KatasterSorter


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class KatasterSorterApp(ctk.CTk):
    
    def __init__(self):
        super().__init__()
        
        self.title("Kataster-Sorter")
        self.geometry("720x700")
        self.minsize(500, 400)
        
        icon_path = self._get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        self.selected_files: list[str] = []
        self.result = None
        
        self._create_ui()
    
    def _get_resource_path(self, filename):
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, filename)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    
    def _create_ui(self):
        # Hauptlayout: Alles in einer vertikalen Spalte
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)   # Header
        self.grid_rowconfigure(1, weight=1)   # Scrollbarer Inhalt
        self.grid_rowconfigure(2, weight=0)   # Aktions-Leiste (immer sichtbar)
        
        # === Header (kompakt) ===
        header = ctk.CTkFrame(self, fg_color="#1a237e", corner_radius=0, height=70)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)
        
        ctk.CTkLabel(
            header, text="📄 Kataster-Sorter",
            font=ctk.CTkFont(size=22, weight="bold"), text_color="white"
        ).grid(row=0, column=0, pady=(12, 2))
        
        ctk.CTkLabel(
            header,
            text="PDFs auswählen – automatische Erkennung & Sortierung",
            font=ctk.CTkFont(size=11), text_color="#b0b0b0"
        ).grid(row=1, column=0, pady=(0, 10))
        
        # === Scrollbarer Inhalt ===
        scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color="#444444",
            scrollbar_button_hover_color="#555555"
        )
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(10, 5))
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        # --- Upload-Bereich ---
        upload_frame = ctk.CTkFrame(scroll_frame, fg_color="#2a2a2a", corner_radius=10)
        upload_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        upload_frame.grid_columnconfigure(0, weight=1)
        upload_frame.grid_columnconfigure(1, weight=0)
        
        upload_left = ctk.CTkFrame(upload_frame, fg_color="transparent")
        upload_left.grid(row=0, column=0, sticky="ew", padx=15, pady=12)
        upload_left.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            upload_left, text="📤 PDF-Dateien",
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).grid(row=0, column=0, sticky="w")
        
        self.file_label = ctk.CTkLabel(
            upload_left, text="Keine Dateien ausgewählt",
            font=ctk.CTkFont(size=11), text_color="#888888", anchor="w",
            wraplength=400
        )
        self.file_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        
        ctk.CTkButton(
            upload_frame, text="Auswählen...",
            command=self._select_files, height=32, width=120,
            corner_radius=8, font=ctk.CTkFont(size=12)
        ).grid(row=0, column=1, padx=15, pady=12)
        
        # --- Status-Bereich ---
        self.status_frame = ctk.CTkFrame(scroll_frame, fg_color="#2a2a2a", corner_radius=10)
        self.status_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame, text="Bereit",
            font=ctk.CTkFont(size=13), text_color="#888888"
        )
        self.status_label.grid(row=0, column=0, pady=(12, 4), padx=15)
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        self.progress_bar.grid(row=1, column=0, pady=(0, 4), padx=15, sticky="ew")
        self.progress_bar.set(0)
        
        self.stats_label = ctk.CTkLabel(
            self.status_frame, text="",
            font=ctk.CTkFont(size=12), text_color="#4caf50"
        )
        self.stats_label.grid(row=2, column=0, pady=(0, 2), padx=15)
        
        self.akz_label = ctk.CTkLabel(
            self.status_frame, text="",
            font=ctk.CTkFont(size=11), text_color="#ff9800"
        )
        self.akz_label.grid(row=3, column=0, pady=(0, 12), padx=15)
        
        # --- Debug-Bereich (ausklappbar) ---
        self.debug_frame = ctk.CTkFrame(scroll_frame, fg_color="#222222", corner_radius=10)
        self.debug_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.debug_frame.grid_columnconfigure(0, weight=1)
        
        self.debug_toggle_btn = ctk.CTkButton(
            self.debug_frame, text="▶ Debug-Info",
            command=self._toggle_debug,
            font=ctk.CTkFont(size=11), height=28,
            fg_color="transparent", hover_color="#333333",
            text_color="#666666", anchor="w"
        )
        self.debug_toggle_btn.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        self.debug_textbox = ctk.CTkTextbox(
            self.debug_frame, height=120,
            font=ctk.CTkFont(family="Courier", size=10),
            fg_color="#1a1a1a", text_color="#888888",
            wrap="word"
        )
        self.debug_visible = False
        # Textbox ist initial versteckt
        
        # === Aktions-Leiste (immer sichtbar, unten fixiert) ===
        action_bar = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=0)
        action_bar.grid(row=2, column=0, sticky="ew")
        action_bar.grid_columnconfigure(0, weight=1)
        action_bar.grid_columnconfigure(1, weight=1)
        
        self.process_btn = ctk.CTkButton(
            action_bar, text="▶️  Verarbeiten",
            command=self._start_processing,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42, corner_radius=10, state="disabled",
            fg_color="#3949ab", hover_color="#5c6bc0"
        )
        self.process_btn.grid(row=0, column=0, padx=(15, 5), pady=12, sticky="ew")
        
        self.download_btn = ctk.CTkButton(
            action_bar, text="💾 PDF Speichern",
            command=self._save_combined,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42, corner_radius=10, state="disabled",
            fg_color="#2e7d32", hover_color="#388e3c"
        )
        self.download_btn.grid(row=0, column=1, padx=(5, 15), pady=12, sticky="ew")
    
    # =========================================================================
    # Debug Toggle
    # =========================================================================
    
    def _toggle_debug(self):
        if self.debug_visible:
            self.debug_textbox.grid_forget()
            self.debug_toggle_btn.configure(text="▶ Debug-Info")
            self.debug_visible = False
        else:
            self.debug_textbox.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
            self.debug_toggle_btn.configure(text="▼ Debug-Info")
            self.debug_visible = True
    
    # =========================================================================
    # File Selection
    # =========================================================================
    
    def _select_files(self):
        paths = filedialog.askopenfilenames(
            title="Alle PDF-Dateien auswählen",
            filetypes=[("PDF-Dateien", "*.pdf")]
        )
        if paths:
            self.selected_files = list(paths)
            names = [os.path.basename(p) for p in paths]
            self.file_label.configure(
                text=f"✅ {len(paths)} Datei(en): {', '.join(names)}",
                text_color="#4caf50"
            )
            self.process_btn.configure(state="normal")
            self._reset_results()
    
    def _reset_results(self):
        self.status_label.configure(text="Bereit", text_color="#888888")
        self.progress_bar.set(0)
        self.stats_label.configure(text="")
        self.akz_label.configure(text="")
        self.debug_textbox.delete("1.0", "end")
        self.download_btn.configure(state="disabled")
        self.result = None
    
    # =========================================================================
    # Processing
    # =========================================================================
    
    def _start_processing(self):
        self.process_btn.configure(state="disabled")
        self._reset_results()
        self.status_label.configure(text="Erkenne Dateitypen...", text_color="#2196f3")
        self.progress_bar.set(0.1)
        
        thread = threading.Thread(target=self._process, daemon=True)
        thread.start()
    
    def _process(self):
        try:
            sorter = KatasterSorter()
            
            file_data = []
            for path in self.selected_files:
                with open(path, 'rb') as f:
                    file_data.append((os.path.basename(path), f.read()))
            
            self.after(0, lambda: self._update_progress(
                0.3, "Analysiere und sortiere..."
            ))
            
            self.result = sorter.process_files(file_data)
            
            self.after(0, lambda: self._update_progress(1.0, "✅ Fertig!"))
            self.after(0, self._show_results)
            
        except Exception as e:
            import traceback
            err = f"{e}\n{traceback.format_exc()}"
            self.after(0, lambda: self._show_error(err))
    
    def _update_progress(self, value, text):
        self.progress_bar.set(value)
        self.status_label.configure(text=text)
    
    def _show_error(self, error_msg):
        self.status_label.configure(text="❌ Fehler", text_color="#f44336")
        self.debug_textbox.delete("1.0", "end")
        self.debug_textbox.insert("1.0", error_msg)
        if not self.debug_visible:
            self._toggle_debug()
        self.process_btn.configure(state="normal")
    
    def _show_results(self):
        if not self.result:
            return
        
        r = self.result
        
        stats = (
            f"📊 {r['total_pages']} Seiten  │  "
            f"{r['standard_count']} Standard  │  "
            f"{r['sonderfall_count']} Sonderfälle  │  "
            f"Deckbl.: {r['cover_standard_count']}+{r['cover_sonder_count']}"
        )
        self.stats_label.configure(text=stats)
        
        if r['kataster_akz']:
            akz_text = f"AKZ: {r['kataster_akz']}"
            if r['akz_mismatches']:
                akz_text += f"  │  {len(r['akz_mismatches'])} Korrektur(en)"
            self.akz_label.configure(text=akz_text)
        
        # Debug
        debug_text = "\n".join(r.get('debug_log', []))
        self.debug_textbox.delete("1.0", "end")
        self.debug_textbox.insert("1.0", debug_text)
        
        if r['combined_pdf']:
            self.status_label.configure(text="✅ Fertig!", text_color="#4caf50")
            self.download_btn.configure(state="normal")
        else:
            self.status_label.configure(
                text="⚠️ Keine Output-Daten. Prüfe Debug-Info.",
                text_color="#ff9800"
            )
            if not self.debug_visible:
                self._toggle_debug()
        
        self.process_btn.configure(state="normal")
    
    # =========================================================================
    # Save
    # =========================================================================
    
    def _save_combined(self):
        if not self.result or not self.result['combined_pdf']:
            messagebox.showwarning("Fehler", "Keine Daten zum Speichern.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Kombinierte PDF speichern",
            defaultextension=".pdf",
            initialfile="Kataster_Komplett.pdf",
            filetypes=[("PDF-Dateien", "*.pdf")]
        )
        
        if file_path:
            with open(file_path, 'wb') as f:
                f.write(self.result['combined_pdf'])
            
            r = self.result
            messagebox.showinfo("Gespeichert",
                f"Datei gespeichert:\n{file_path}\n\n"
                f"Standard: {r['standard_count']} Pakete\n"
                f"Sonderfälle: {r['sonderfall_count']} Pakete\n"
                f"AKZ-Korrekturen: {len(r['akz_mismatches'])}"
            )


def main():
    app = KatasterSorterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
