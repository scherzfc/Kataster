"""
Kataster-Sorter: PDF Processing Logic
Sortiert Liegenschaftskataster-Auszüge nach Fortführungsfallnummer und Grundbuchblatt.
"""

import re
import io
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

import pdfplumber
from pypdf import PdfReader, PdfWriter


@dataclass
class PageInfo:
    """Informationen zu einer einzelnen PDF-Seite."""
    page_number: int  # 0-indexed
    ffn: Optional[int] = None  # Fortführungsfallnummer
    gb_numbers: set = field(default_factory=set)  # Grundbuchblatt-Nummern


@dataclass
class Package:
    """Ein Paket von Seiten mit gleicher Fortführungsfallnummer."""
    ffn: Optional[int]
    pages: list  # List[PageInfo]
    unique_gbs: set = field(default_factory=set)
    is_sonderfall: bool = False
    primary_gb: Optional[int] = None  # Für Sortierung


class KatasterSorter:
    """
    Sortiert PDF-Seiten aus Liegenschaftskataster-Auszügen.
    
    Logik:
    1. Extrahiert FFN und GB von jeder Seite
    2. Gruppiert Seiten nach FFN (untrennbare Pakete)
    3. Analysiert Pakete: Standard (1 GB) vs. Sonderfall (mehrere GBs)
    4. Sortiert Standard-Pakete nach GB-Nummer
    5. Generiert zwei Output-PDFs
    """
    
    # Regex-Patterns für Extraktion
    FFN_PATTERN = re.compile(r"Fortführungsfallnummer[:\s]*(\d+)", re.IGNORECASE)
    GB_PATTERN = re.compile(r"Grundbuchblatt[:\s]*(\d+)", re.IGNORECASE)
    
    def __init__(self):
        self.pages: list[PageInfo] = []
        self.packages: list[Package] = []
        self.standard_packages: list[Package] = []
        self.sonderfall_packages: list[Package] = []
        self.pdf_reader: Optional[PdfReader] = None
    
    def process(self, pdf_file) -> dict:
        """
        Hauptmethode: Verarbeitet eine PDF-Datei.
        
        Args:
            pdf_file: File-like object oder Pfad zur PDF
            
        Returns:
            dict mit Statistiken und generierten PDFs
        """
        # Reset state
        self.pages = []
        self.packages = []
        self.standard_packages = []
        self.sonderfall_packages = []
        
        # Step 1: Extract text and metadata from each page
        self._extract_page_info(pdf_file)
        
        # Step 2: Group pages by FFN
        self._group_by_ffn()
        
        # Step 3: Analyze packages (Standard vs. Sonderfall)
        self._analyze_packages()
        
        # Step 4: Sort standard packages by GB
        self._sort_packages()
        
        # Step 5: Generate output PDFs
        standard_pdf = self._create_output_pdf(self.standard_packages)
        sonderfall_pdf = self._create_output_pdf(self.sonderfall_packages)
        
        return {
            "total_pages": len(self.pages),
            "total_packages": len(self.packages),
            "standard_count": len(self.standard_packages),
            "sonderfall_count": len(self.sonderfall_packages),
            "standard_pdf": standard_pdf,
            "sonderfall_pdf": sonderfall_pdf,
        }
    
    def _extract_page_info(self, pdf_file):
        """Extrahiert FFN und GB von jeder Seite."""
        # Für pypdf brauchen wir das Original-File
        if hasattr(pdf_file, 'read'):
            pdf_bytes = pdf_file.read()
            pdf_file.seek(0)  # Reset für pdfplumber
        else:
            with open(pdf_file, 'rb') as f:
                pdf_bytes = f.read()
        
        self.pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        
        # pdfplumber für Text-Extraktion
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                page_info = PageInfo(page_number=page_num)
                
                # FFN extrahieren (erste Übereinstimmung)
                ffn_match = self.FFN_PATTERN.search(text)
                if ffn_match:
                    page_info.ffn = int(ffn_match.group(1))
                
                # Alle GB-Nummern extrahieren
                gb_matches = self.GB_PATTERN.findall(text)
                page_info.gb_numbers = set(int(gb) for gb in gb_matches)
                
                self.pages.append(page_info)
    
    def _group_by_ffn(self):
        """Gruppiert Seiten nach Fortführungsfallnummer."""
        ffn_groups = defaultdict(list)
        
        current_ffn = None
        for page in self.pages:
            if page.ffn is not None:
                current_ffn = page.ffn
            
            # Seiten ohne FFN gehören zum vorherigen Paket
            ffn_groups[current_ffn].append(page)
        
        # Pakete erstellen
        for ffn, pages in ffn_groups.items():
            package = Package(ffn=ffn, pages=pages)
            self.packages.append(package)
    
    def _analyze_packages(self):
        """Analysiert jedes Paket: Standard oder Sonderfall."""
        for package in self.packages:
            # Alle GB-Nummern im Paket sammeln
            all_gbs = set()
            for page in package.pages:
                all_gbs.update(page.gb_numbers)
            
            package.unique_gbs = all_gbs
            
            # Sonderfall: Mehrere unterschiedliche GBs
            if len(all_gbs) > 1:
                package.is_sonderfall = True
                self.sonderfall_packages.append(package)
            else:
                package.is_sonderfall = False
                # Primary GB für Sortierung
                package.primary_gb = min(all_gbs) if all_gbs else float('inf')
                self.standard_packages.append(package)
    
    def _sort_packages(self):
        """Sortiert Standard-Pakete aufsteigend nach GB-Nummer."""
        self.standard_packages.sort(key=lambda p: p.primary_gb if p.primary_gb else float('inf'))
    
    def _create_output_pdf(self, packages: list[Package]) -> Optional[bytes]:
        """Erstellt eine PDF aus den gegebenen Paketen."""
        if not packages or not self.pdf_reader:
            return None
        
        writer = PdfWriter()
        
        for package in packages:
            for page_info in package.pages:
                writer.add_page(self.pdf_reader.pages[page_info.page_number])
        
        # Als Bytes zurückgeben
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        return output.getvalue()
