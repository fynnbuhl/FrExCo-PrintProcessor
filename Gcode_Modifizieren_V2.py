import re
import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

def ersetze_wipe_e_werte(zeilen, faktor):
    # Liste für die neuen Zeilen
    neue_zeilen = []

    # Regulärer Ausdruck, um E-Werte zu finden
    e_wert_muster = re.compile(r"E[-+]?\d*\.?\d*")

    # Flags
    innerhalb_wipe = False
    gerade_wipe_beendet = False
    gerade_layer_gewechselt = False

    for zeile in zeilen:
        if re.match(r';WIPE_START', zeile):
            innerhalb_wipe = True
            neue_zeilen.append(zeile)
        elif re.match(r';WIPE_END', zeile):
            innerhalb_wipe = False
            gerade_wipe_beendet = True
            neue_zeilen.append(zeile)
        elif re.match(r';AFTER_LAYER_CHANGE', zeile):
            gerade_layer_gewechselt = True
            neue_zeilen.append(zeile)
        elif innerhalb_wipe:
            # E-Werte aus der Zeile innerhalb des WIPE-Blocks entfernen
            zeile = e_wert_muster.sub('', zeile)
            neue_zeilen.append(zeile)
        elif gerade_wipe_beendet or gerade_layer_gewechselt:
            # Die erste Extrusionszeile nach dem WIPE-Block oder Layer-Wechsel auskommentieren
            if 'E' in zeile:
                zeile = ';' + zeile
                # Flags zurücksetzen
                gerade_wipe_beendet = False
                gerade_layer_gewechselt = False
            neue_zeilen.append(zeile)
        else:
            neue_zeilen.append(zeile)

    return neue_zeilen

def modifiziere_e_werte(zeilen, faktor):
    # Regulärer Ausdruck, um E-Werte zu finden
    e_wert_muster = re.compile(r"(E[-+]?\d*\.?\d*)")

    modifizierte_zeilen = []

    for zeile in zeilen:
        # Finde alle E-Werte in der Zeile
        treffer = e_wert_muster.findall(zeile)
        if treffer:
            for treffer_wert in treffer:
                original_wert = treffer_wert
                try:
                    zahlen_wert = float(original_wert[1:])
                    neuer_wert = int(zahlen_wert * faktor)
                    # Neuen E-Wert als Zeichenkette erstellen
                    neuer_e_wert = f"E{neuer_wert}"
                    # Ersetze den ursprünglichen E-Wert mit dem neuen in der Zeile
                    zeile = zeile.replace(original_wert, neuer_e_wert)
                except ValueError:
                    # Überspringen, wenn kein gültiger numerischer Wert gefunden wird
                    pass
        modifizierte_zeilen.append(zeile)

    return modifizierte_zeilen

def verarbeite_gcode(eingabe_datei, ausgabe_datei, faktor):
    # Lese die gesamte Datei
    with open(eingabe_datei, 'r') as file:
        zeilen = file.readlines()

    # Ersetze E-Werte in den WIPE-Zeilen und bearbeite besondere Fälle
    zeilen = ersetze_wipe_e_werte(zeilen, faktor)

    # Modifiziere E-Werte
    modifizierte_zeilen = modifiziere_e_werte(zeilen, faktor)

    # Schreibe die modifizierten Zeilen in die Ausgabedatei
    with open(ausgabe_datei, 'w') as file:
        file.writelines(modifizierte_zeilen)

def main():
    # Tkinter initialisieren und Hauptfenster verstecken
    root = tk.Tk()
    root.withdraw()
    # Bringt den Dialog bei manchen Betriebssystemen in den Vordergrund
    root.attributes('-topmost', True) 

    # Dateiauswahldialog öffnen
    dateipfad_str = filedialog.askopenfilename(
        title="Wähle eine G-Code Datei",
        filetypes=[("G-Code Dateien", "*.gcode"), ("Alle Dateien", "*.*")]
    )

    # Beenden, falls der Nutzer auf "Abbrechen" klickt
    if not dateipfad_str:
        print("Vorgang abgebrochen: Keine Datei ausgewählt.")
        return

    original_pfad = Path(dateipfad_str)
    verzeichnis = original_pfad.parent
    dateiname_ohne_ext = original_pfad.stem
    erweiterung = original_pfad.suffix

    # Neue Pfade und Dateinamen definieren
    raw_pfad = verzeichnis / f"{dateiname_ohne_ext}_raw{erweiterung}"
    processed_pfad = verzeichnis / f"{dateiname_ohne_ext}_processed{erweiterung}"

    # 1. Originaldatei umbenennen
    os.rename(original_pfad, raw_pfad)
    print(f"Originaldatei umbenannt in: {raw_pfad.name}")

    # 2. Faktor definieren
    faktor = 10000

    # 3. Hauptlogik ausführen
    verarbeite_gcode(raw_pfad, processed_pfad, faktor)
    print(f"Verarbeitung erfolgreich. Neue Datei erstellt: {processed_pfad.name}")

if __name__ == "__main__":
    main()