"""
Kataster-Sorter: PDF Processing Logic
Sortiert Liegenschaftskataster-Auszüge nach Fortführungsfallnummer und Grundbuchblatt.
Integriert Deckblätter (Cover Pages) und prüft Antragskennzeichen.
"""

import re
import io
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

import pdfplumber
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PageInfo:
    """Informationen zu einer einzelnen PDF-Seite."""
    page_number: int
    ffn: Optional[int] = None
    gb_numbers: set = field(default_factory=set)
    lfd_nr: Optional[int] = None  # Laufende Nummer
    antragskennzeichen: Optional[str] = None


@dataclass
class CoverPage:
    """Informationen zu einer Deckblatt-Seite."""
    page_number: int
    gb_number: Optional[int] = None
    antragskennzeichen: Optional[str] = None


@dataclass
class Package:
    """Ein Paket von Seiten mit gleicher Fortführungsfallnummer."""
    ffn: Optional[int]
    pages: list
    unique_gbs: set = field(default_factory=set)
    is_sonderfall: bool = False
    primary_gb: Optional[int] = None
    lfd_nr: Optional[int] = None  # Laufende Nummer (für Sortierung innerhalb GB)
    antragskennzeichen: Optional[str] = None


# =============================================================================
# Regex Patterns
# =============================================================================

FFN_PATTERN = re.compile(r"Fortführungsfallnummer[:\s]*(\d+)", re.IGNORECASE)
GB_PATTERN = re.compile(r"Grundbuchblatt[:\s]*(\d+)", re.IGNORECASE)
# Laufende Nummer: "lfd. Nr.: 0002" oder "(0002)" nach GB-Nummer
LFD_NR_PATTERN = re.compile(r"lfd\.?\s*Nr\.?[:\s]*(\d+)", re.IGNORECASE)
GB_LFD_PATTERN = re.compile(r"Grundbuchblatt[:\s]*\d+\s*\((\d+)\)", re.IGNORECASE)
GB_COVER_PATTERN = re.compile(
    r"Grundbuchblatt\s*\(lfd\.\s*Nr\.\)\s*:\s*(\d+)", re.IGNORECASE
)
MEHRERE_GB_PATTERN = re.compile(r"mehrere\s+Grundbuchbl", re.IGNORECASE)
AKZ_PATTERN = re.compile(r"(\d{4}_C?I{1,4}_\d+)")


# =============================================================================
# Auto-Detection
# =============================================================================

def detect_file_type(pdf_bytes: bytes) -> str:
    """
    Erkennt den Typ einer PDF-Datei automatisch.
    
    Returns:
        'kataster' - Auszug aus dem Liegenschaftskataster
        'cover_standard' - Deckblätter mit GB-Nummern
        'cover_sonder' - Deckblätter "mehrere Grundbuchblätter"
    """
    ffn_count = 0
    gb_cover_count = 0
    mehrere_gb_count = 0
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        # Prüfe die ersten 5 Seiten (reicht zur Erkennung)
        for page in pdf.pages[:5]:
            text = page.extract_text() or ""
            
            if FFN_PATTERN.search(text):
                ffn_count += 1
            if GB_COVER_PATTERN.search(text):
                gb_cover_count += 1
            if MEHRERE_GB_PATTERN.search(text):
                mehrere_gb_count += 1
    
    # Kataster-Auszug: enthält Fortführungsfallnummern
    if ffn_count > 0:
        return "kataster"
    
    # Sonderfälle: "mehrere Grundbuchblätter"
    if mehrere_gb_count > 0:
        return "cover_sonder"
    
    # Standard: hat "Grundbuchblatt (lfd. Nr.)"
    if gb_cover_count > 0:
        return "cover_standard"
    
    # Fallback: behandle als Kataster
    return "kataster"


# =============================================================================
# Main Processor
# =============================================================================

class KatasterSorter:
    """Sortiert PDF-Seiten aus Liegenschaftskataster-Auszügen."""
    
    def __init__(self):
        self.pages: list[PageInfo] = []
        self.packages: list[Package] = []
        self.standard_packages: list[Package] = []
        self.sonderfall_packages: list[Package] = []
        self.pdf_reader: Optional[PdfReader] = None
        
        self.cover_standard_reader: Optional[PdfReader] = None
        self.cover_standard_pages: list[CoverPage] = []
        self.cover_sonder_reader: Optional[PdfReader] = None
        self.cover_sonder_pages: list[CoverPage] = []
        
        self.kataster_akz: Optional[str] = None
        self.akz_mismatches: list[str] = []
        self.debug_log: list[str] = []
    
    def process_files(self, file_bytes_list: list[tuple[str, bytes]]) -> dict:
        """
        Hauptmethode: Nimmt eine Liste von (filename, bytes) Tupeln entgegen,
        klassifiziert die Dateien automatisch und verarbeitet sie.
        """
        # Reset
        self.pages = []
        self.packages = []
        self.standard_packages = []
        self.sonderfall_packages = []
        self.cover_standard_pages = []
        self.cover_sonder_pages = []
        self.kataster_akz = None
        self.akz_mismatches = []
        self.debug_log = []
        
        # === Auto-Klassifikation ===
        kataster_bytes = None
        cover_std_bytes = None
        cover_snd_bytes = None
        
        for filename, data in file_bytes_list:
            file_type = detect_file_type(data)
            self.debug_log.append(f"'{filename}' → {file_type}")
            
            if file_type == "kataster":
                kataster_bytes = data
            elif file_type == "cover_standard":
                cover_std_bytes = data
            elif file_type == "cover_sonder":
                cover_snd_bytes = data
        
        if not kataster_bytes:
            raise ValueError("Kein Kataster-Auszug erkannt! "
                           "(Datei muss 'Fortführungsfallnummer' enthalten)")
        
        # === Verarbeitung ===
        self._extract_page_info(kataster_bytes)
        self.debug_log.append(f"Kataster: {len(self.pages)} Seiten")
        
        self._extract_kataster_akz()
        if self.kataster_akz:
            self.debug_log.append(f"AKZ: {self.kataster_akz}")
        
        self._group_by_ffn()
        self._analyze_packages()
        self._sort_packages()
        
        self.debug_log.append(
            f"Pakete: {len(self.standard_packages)} Standard, "
            f"{len(self.sonderfall_packages)} Sonderfälle"
        )
        # Debug: Paket-Details (erste 10)
        for pkg in self.standard_packages[:10]:
            self.debug_log.append(
                f"  FFN={pkg.ffn} GB={pkg.primary_gb} lfd={pkg.lfd_nr}"
            )
        
        if cover_std_bytes:
            self._parse_standard_covers(cover_std_bytes)
            gbs = [c.gb_number for c in self.cover_standard_pages]
            self.debug_log.append(f"Standard-Deckbl.: {len(gbs)} (GBs: {gbs})")
        
        if cover_snd_bytes:
            self._parse_sonder_covers(cover_snd_bytes)
            self.debug_log.append(
                f"Sonderf.-Deckbl.: {len(self.cover_sonder_pages)}"
            )
        
        combined_pdf = self._create_combined_pdf()
        
        return {
            "total_pages": len(self.pages),
            "total_packages": len(self.packages),
            "standard_count": len(self.standard_packages),
            "sonderfall_count": len(self.sonderfall_packages),
            "cover_standard_count": len(self.cover_standard_pages),
            "cover_sonder_count": len(self.cover_sonder_pages),
            "kataster_akz": self.kataster_akz,
            "akz_mismatches": self.akz_mismatches,
            "combined_pdf": combined_pdf,
            "debug_log": self.debug_log,
        }
    
    # =========================================================================
    # Kataster-Auszug
    # =========================================================================
    
    def _extract_page_info(self, pdf_bytes):
        self.pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                info = PageInfo(page_number=page_num)
                
                ffn_match = FFN_PATTERN.search(text)
                if ffn_match:
                    info.ffn = int(ffn_match.group(1))
                
                gb_matches = GB_PATTERN.findall(text)
                info.gb_numbers = set(int(gb) for gb in gb_matches)
                
                # Laufende Nummer extrahieren
                lfd_match = GB_LFD_PATTERN.search(text)
                if lfd_match:
                    info.lfd_nr = int(lfd_match.group(1))
                else:
                    lfd_match2 = LFD_NR_PATTERN.search(text)
                    if lfd_match2:
                        info.lfd_nr = int(lfd_match2.group(1))
                
                akz_match = AKZ_PATTERN.search(text)
                if akz_match:
                    info.antragskennzeichen = akz_match.group(1)
                
                self.pages.append(info)
    
    def _extract_kataster_akz(self):
        for page in self.pages:
            if page.antragskennzeichen:
                self.kataster_akz = page.antragskennzeichen
                break
    
    def _group_by_ffn(self):
        ffn_groups = defaultdict(list)
        current_ffn = None
        for page in self.pages:
            if page.ffn is not None:
                current_ffn = page.ffn
            ffn_groups[current_ffn].append(page)
        
        for ffn, pages in ffn_groups.items():
            pkg = Package(ffn=ffn, pages=pages)
            # Lfd. Nr. und AKZ aus den Seiten übernehmen
            for p in pages:
                if p.lfd_nr is not None and pkg.lfd_nr is None:
                    pkg.lfd_nr = p.lfd_nr
                if p.antragskennzeichen and not pkg.antragskennzeichen:
                    pkg.antragskennzeichen = p.antragskennzeichen
            self.packages.append(pkg)
    
    def _analyze_packages(self):
        for pkg in self.packages:
            all_gbs = set()
            for page in pkg.pages:
                all_gbs.update(page.gb_numbers)
            pkg.unique_gbs = all_gbs
            
            if len(all_gbs) > 1:
                pkg.is_sonderfall = True
                self.sonderfall_packages.append(pkg)
            else:
                pkg.is_sonderfall = False
                pkg.primary_gb = min(all_gbs) if all_gbs else None
                self.standard_packages.append(pkg)
    
    def _sort_packages(self):
        self.standard_packages.sort(
            key=lambda p: p.primary_gb if p.primary_gb is not None else float('inf')
        )
    
    # =========================================================================
    # Deckblätter
    # =========================================================================
    
    def _parse_standard_covers(self, pdf_bytes):
        self.cover_standard_reader = PdfReader(io.BytesIO(pdf_bytes))
        
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                cover = CoverPage(page_number=page_num)
                
                gb_match = GB_COVER_PATTERN.search(text)
                if gb_match:
                    cover.gb_number = int(gb_match.group(1))
                else:
                    gb_match2 = GB_PATTERN.search(text)
                    if gb_match2:
                        cover.gb_number = int(gb_match2.group(1))
                
                akz_match = AKZ_PATTERN.search(text)
                if akz_match:
                    cover.antragskennzeichen = akz_match.group(1)
                
                self.cover_standard_pages.append(cover)
    
    def _parse_sonder_covers(self, pdf_bytes):
        self.cover_sonder_reader = PdfReader(io.BytesIO(pdf_bytes))
        
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                cover = CoverPage(page_number=page_num)
                
                akz_match = AKZ_PATTERN.search(text)
                if akz_match:
                    cover.antragskennzeichen = akz_match.group(1)
                
                self.cover_sonder_pages.append(cover)
    
    # =========================================================================
    # AKZ-Korrektur
    # =========================================================================
    
    def _create_akz_overlay(self, old_akz, new_akz, page_width, page_height):
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(float(page_width), float(page_height)))
        y_pos = float(page_height) - 230
        x_pos = 170
        c.setFillColorRGB(1, 1, 1)
        c.rect(x_pos - 5, y_pos - 5, 200, 18, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 10)
        c.drawString(x_pos, y_pos, new_akz)
        c.save()
        buf.seek(0)
        return buf.getvalue()
    
    def _apply_akz_correction(self, page, cover):
        if (self.kataster_akz and cover.antragskennzeichen
                and cover.antragskennzeichen != self.kataster_akz):
            self.akz_mismatches.append(
                f"Deckblatt S.{cover.page_number+1}: "
                f"'{cover.antragskennzeichen}' → '{self.kataster_akz}'"
            )
            mediabox = page.mediabox
            overlay_bytes = self._create_akz_overlay(
                cover.antragskennzeichen, self.kataster_akz,
                mediabox.width, mediabox.height
            )
            overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
            page.merge_page(overlay_reader.pages[0])
        return page
    
    # =========================================================================
    # Combined PDF
    # =========================================================================
    
    def _create_combined_pdf(self) -> Optional[bytes]:
        """
        Erstellt EINE kombinierte PDF.
        
        Standard-Pakete mit gleicher GB werden gebündelt:
        EIN Deckblatt → alle FFN-Pakete dieser GB (sortiert nach FFN).
        """
        if not self.pdf_reader:
            return None
        
        writer = PdfWriter()
        
        # Index: Standard-Deckblätter nach GB
        cover_by_gb = {}
        if self.cover_standard_reader:
            for cover in self.cover_standard_pages:
                if cover.gb_number is not None:
                    cover_by_gb[cover.gb_number] = cover
        
        pages_added = 0
        
        # --- Standard-Pakete: Gruppiert nach GB-Nummer ---
        # Mehrere FFN-Pakete können die gleiche GB haben (verschiedene lfd. Nr.)
        gb_groups = defaultdict(list)
        no_gb_packages = []
        
        for pkg in self.standard_packages:
            if pkg.primary_gb is not None:
                gb_groups[pkg.primary_gb].append(pkg)
            else:
                no_gb_packages.append(pkg)
        
        # Sortiert nach GB-Nummer
        for gb_number in sorted(gb_groups.keys()):
            packages = gb_groups[gb_number]
            # Innerhalb der GB-Gruppe nach lfd. Nr. sortieren (Fallback: FFN)
            packages.sort(key=lambda p: (
                p.lfd_nr if p.lfd_nr is not None else float('inf'),
                p.ffn if p.ffn is not None else 0
            ))
            
            # EIN Deckblatt pro GB-Gruppe
            if gb_number in cover_by_gb:
                cover = cover_by_gb[gb_number]
                page = self.cover_standard_reader.pages[cover.page_number]
                page = self._apply_akz_correction(page, cover)
                writer.add_page(page)
                pages_added += 1
            
            # Alle FFN-Pakete dieser GB
            for pkg in packages:
                for page_info in pkg.pages:
                    writer.add_page(self.pdf_reader.pages[page_info.page_number])
                    pages_added += 1
        
        # Pakete ohne GB-Nummer (am Ende)
        for pkg in no_gb_packages:
            for page_info in pkg.pages:
                writer.add_page(self.pdf_reader.pages[page_info.page_number])
                pages_added += 1
        
        # --- Sonderfall-Pakete ---
        sonder_idx = 0
        for pkg in self.sonderfall_packages:
            if self.cover_sonder_reader and self.cover_sonder_pages:
                cover = self.cover_sonder_pages[sonder_idx % len(self.cover_sonder_pages)]
                page = self.cover_sonder_reader.pages[cover.page_number]
                page = self._apply_akz_correction(page, cover)
                writer.add_page(page)
                pages_added += 1
                sonder_idx += 1
            
            for page_info in pkg.pages:
                writer.add_page(self.pdf_reader.pages[page_info.page_number])
                pages_added += 1
        
        self.debug_log.append(f"Output: {pages_added} Seiten")
        
        if pages_added == 0:
            return None
        
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        return output.getvalue()

