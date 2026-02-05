"""
Kataster-Sorter Desktop Application
Eigenständige Desktop-App für PDF-Sortierung von Liegenschaftskataster-Auszügen.
"""

import os
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from pdf_processor import KatasterSorter


# Design-Einstellungen
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class KatasterSorterApp(ctk.CTk):
    """Hauptfenster der Kataster-Sorter Anwendung."""
    
    def __init__(self):
        super().__init__()
        
        # Fenster-Einstellungen
        self.title("Kataster-Sorter")
        self.geometry("700x500")
        self.minsize(600, 450)
        
        # Icon setzen (falls vorhanden)
        icon_path = self._get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        # Variablen
        self.selected_file = None
        self.result = None
        
        # UI aufbauen
        self._create_ui()
    
    def _get_resource_path(self, filename):
        """Gibt den Pfad zu einer Resource-Datei zurück (PyInstaller-kompatibel)."""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, filename)
    
    def _create_ui(self):
        """Erstellt die Benutzeroberfläche."""
        
        # Hauptcontainer
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # === Header ===
        header_frame = ctk.CTkFrame(self, fg_color="#1a237e", corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📄 Kataster-Sorter",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        title_label.grid(row=0, column=0, pady=(20, 5))
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Automatische Sortierung von Liegenschaftskataster-Auszügen",
            font=ctk.CTkFont(size=14),
            text_color="#b0b0b0"
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 20))
        
        # === Content ===
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=20)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(2, weight=1)
        
        # Upload-Bereich
        upload_frame = ctk.CTkFrame(content_frame, fg_color="#2a2a2a", corner_radius=15)
        upload_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        upload_frame.grid_columnconfigure(0, weight=1)
        
        upload_label = ctk.CTkLabel(
            upload_frame,
            text="📤 PDF-Datei auswählen",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        upload_label.grid(row=0, column=0, pady=(20, 10))
        
        self.file_label = ctk.CTkLabel(
            upload_frame,
            text="Keine Datei ausgewählt",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.file_label.grid(row=1, column=0, pady=(0, 10))
        
        select_btn = ctk.CTkButton(
            upload_frame,
            text="Datei auswählen...",
            command=self._select_file,
            font=ctk.CTkFont(size=14),
            height=40,
            corner_radius=10
        )
        select_btn.grid(row=2, column=0, pady=(0, 20), padx=20)
        
        # Verarbeiten-Button
        self.process_btn = ctk.CTkButton(
            content_frame,
            text="▶️  Verarbeiten",
            command=self._start_processing,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=12,
            state="disabled",
            fg_color="#3949ab",
            hover_color="#5c6bc0"
        )
        self.process_btn.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Progress-Bereich
        self.progress_frame = ctk.CTkFrame(content_frame, fg_color="#2a2a2a", corner_radius=15)
        self.progress_frame.grid(row=2, column=0, sticky="nsew")
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="Bereit",
            font=ctk.CTkFont(size=14),
            text_color="#888888"
        )
        self.status_label.grid(row=0, column=0, pady=(20, 10))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.grid(row=1, column=0, pady=(0, 10), padx=20)
        self.progress_bar.set(0)
        
        # Download-Buttons (initial versteckt)
        self.download_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        self.download_frame.grid(row=2, column=0, pady=(10, 20))
        
        self.btn_standard = ctk.CTkButton(
            self.download_frame,
            text="💾 Sortierte Akten speichern",
            command=lambda: self._save_pdf("standard"),
            font=ctk.CTkFont(size=13),
            height=40,
            corner_radius=10,
            fg_color="#2e7d32",
            hover_color="#388e3c"
        )
        
        self.btn_sonderfall = ctk.CTkButton(
            self.download_frame,
            text="⚠️ Sonderfälle speichern",
            command=lambda: self._save_pdf("sonderfall"),
            font=ctk.CTkFont(size=13),
            height=40,
            corner_radius=10,
            fg_color="#f57c00",
            hover_color="#ff9800"
        )
    
    def _select_file(self):
        """Öffnet den Dateiauswahl-Dialog."""
        file_path = filedialog.askopenfilename(
            title="PDF-Datei auswählen",
            filetypes=[("PDF-Dateien", "*.pdf"), ("Alle Dateien", "*.*")]
        )
        
        if file_path:
            self.selected_file = file_path
            filename = os.path.basename(file_path)
            self.file_label.configure(text=f"✅ {filename}", text_color="#4caf50")
            self.process_btn.configure(state="normal")
            self.status_label.configure(text="Bereit zur Verarbeitung", text_color="#888888")
            self.progress_bar.set(0)
            
            # Download-Buttons verstecken
            self.btn_standard.grid_forget()
            self.btn_sonderfall.grid_forget()
    
    def _start_processing(self):
        """Startet die PDF-Verarbeitung in einem separaten Thread."""
        self.process_btn.configure(state="disabled")
        self.status_label.configure(text="Verarbeite PDF...", text_color="#2196f3")
        self.progress_bar.set(0.1)
        
        # Verarbeitung im Hintergrund
        thread = threading.Thread(target=self._process_pdf, daemon=True)
        thread.start()
    
    def _process_pdf(self):
        """Verarbeitet die PDF-Datei."""
        try:
            sorter = KatasterSorter()
            
            self.after(0, lambda: self._update_progress(0.3, "Extrahiere Seitendaten..."))
            
            with open(self.selected_file, 'rb') as f:
                self.result = sorter.process(f)
            
            self.after(0, lambda: self._update_progress(1.0, "✅ Fertig!"))
            self.after(0, self._show_results)
            
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))
    
    def _update_progress(self, value, text):
        """Aktualisiert die Progress-Anzeige."""
        self.progress_bar.set(value)
        self.status_label.configure(text=text)
    
    def _show_error(self, error_msg):
        """Zeigt eine Fehlermeldung an."""
        self.status_label.configure(text=f"❌ Fehler: {error_msg}", text_color="#f44336")
        self.process_btn.configure(state="normal")
    
    def _show_results(self):
        """Zeigt die Ergebnisse und Download-Buttons an."""
        if not self.result:
            return
        
        stats = f"📊 {self.result['total_pages']} Seiten | {self.result['standard_count']} Standard | {self.result['sonderfall_count']} Sonderfälle"
        self.status_label.configure(text=stats, text_color="#4caf50")
        
        # Download-Buttons anzeigen
        col = 0
        if self.result['standard_pdf']:
            self.btn_standard.grid(row=0, column=col, padx=5)
            col += 1
        
        if self.result['sonderfall_pdf']:
            self.btn_sonderfall.grid(row=0, column=col, padx=5)
        
        self.process_btn.configure(state="normal")
    
    def _save_pdf(self, pdf_type):
        """Speichert eine PDF-Datei."""
        if pdf_type == "standard":
            default_name = "Sortierte_Akten.pdf"
            pdf_data = self.result['standard_pdf']
        else:
            default_name = "Sonderfaelle_Pruefen.pdf"
            pdf_data = self.result['sonderfall_pdf']
        
        if not pdf_data:
            messagebox.showwarning("Keine Daten", "Keine Daten zum Speichern vorhanden.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="PDF speichern",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF-Dateien", "*.pdf")]
        )
        
        if file_path:
            with open(file_path, 'wb') as f:
                f.write(pdf_data)
            messagebox.showinfo("Gespeichert", f"Datei wurde gespeichert:\n{file_path}")


def main():
    """Startet die Anwendung."""
    app = KatasterSorterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
