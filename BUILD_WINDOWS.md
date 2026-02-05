# Kataster-Sorter - Windows Installer erstellen

## Voraussetzungen auf Windows-PC

1. **Python installieren**: https://www.python.org/downloads/
   - Bei Installation: "Add Python to PATH" aktivieren!

2. **Inno Setup installieren**: https://jrsoftware.org/isdl.php
   - Für den Installer-Wizard

---

## Build-Anleitung

### Schritt 1: Repository klonen
```cmd
git clone https://github.com/scherzfc/Kataster.git
cd Kataster
```

### Schritt 2: Executable erstellen
Doppelklick auf `build_windows.bat` oder im Terminal:
```cmd
build_windows.bat
```

Ergebnis: `dist\Kataster-Sorter.exe`

### Schritt 3: Installer erstellen (optional)
1. Inno Setup Compiler öffnen
2. Datei `installer.iss` laden
3. "Compile" klicken

Ergebnis: `installer\Kataster-Sorter-Setup.exe`

---

## Fertige Dateien

| Datei | Beschreibung |
|-------|--------------|
| `dist\Kataster-Sorter.exe` | Portable Version (direkt ausführbar) |
| `installer\Kataster-Sorter-Setup.exe` | Installer mit Wizard |

Die Setup-Datei kann per USB-Stick zur Arbeit gebracht werden!
