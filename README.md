# Technische Dokumentation: FullControl 3D-FrExCo Upgrade

## 1. Einleitung

Diese Erweiterung baut auf der Open-Source-Bibliothek `FullControl GCode Designers` (Original von Andy Gleadall und Dirk Leas, https://fullcontrolgcode.com/; Version 0.1.2) auf und adaptiert diese für den roboterbasierten (nicht-planaren) 3D-Druck. Primäres Zielsystem ist das ABB 3DP-PowerPac für den ABB CRB 150000 FrExCo-Drucker.

Die Standardversion von [FullControl](https://github.com/FullControlXYZ/fullcontrol) ist primär für konventionelle 3-Achs-Drucker konzipiert. Diese Arbeit erweitert das Framework um die Fähigkeit, komplexe Werkzeugorientierungen im Raum (Mehrachsen-Druck) zu berechnen und roboterkompatiblen G-Code unter Berücksichtigung spezifischer Hardware-Bedingungen und Steuerbefehle zu generieren.

### Dateistruktur & Komponenten

Das Repository umfasst folgende Hauptdateien zur Ausführung und Konfiguration des Drucksystems:

* **`FrExCo-PrintProcessor.ipynb`** *Hauptskript zur G-Code-Generierung.* Verarbeitet die Geometriedaten und berechnet den non-planaren G-Code inklusive der erweiterten Werkzeugorientierungen (Vector/Euler-Winkel) für den Roboter.

* **`TCP-Kalibrierung.ipynb`** *Werkzeug-Kalibrierskript.* Dient der präzisen Ermittlung und Berechnung der **TCP-Offsetkoordinaten** (Tool Center Point) des Extruders, um Kinematikfehler beim Schwenken des Roboters zu minimieren.

* **`Frextruder.bat`** *Automatisierungs-Batchskript.* Ein Windows-Shell-Skript zum automatisierten Starten und Öffnen der FrExCo-Weboberfläche für die Steuerung der Extrudereinheit.

> **Hinweis:** Eine detaillierte Schritt-für-Schritt-Anleitung zur Inbetriebnahme und Nutzung der einzelnen Skripte entnehmen Sie bitte dem Begleitdokument **„Anleitung 3D-FREXCO“**.

---

# 2. Konzeptionelle Erweiterung & Architektur

## 2.1 Anpassungen an `fullcontrolgcode`

Die Architektur wurde um spezifische Klassen und Methoden erweitert, die direkt in den Erstellungsprozess des G-Codes eingreifen:

### Mehrachsen-Unterstützung

Die Standard-Koordinaten `(X, Y, Z)` wurden um Normalenvektoren `(nX, nY, nZ)` ergänzt. Diese Einheits-Richtungsvektoren definieren die exakte räumliche Orientierung der Werkzeugachse.

### Erweiterte Zustandsverfolgung

Eine neue Listen-Klasse trackt kontinuierlich die aktuelle absolute Position und räumliche Orientierung des Endeffektors (TCP).

### Benutzerdefinierte Ereignisse (Custom Events)

Integration von hardwarenahen RAPID-Befehlen und G-Code-Routinen für:

- Werkzeugwechsel
- Druckpausen
- Reinigungszyklen

---

## 2.2 Verbesserungen gegenüber dem Standard

Während die Basisbibliothek rein planare G-Code-Befehle generiert, ermöglicht diese Erweiterung:

- Die Erzeugung von G-Code mit integrierten Orientierungsdaten für das euklidische Koordinatensystem des Roboters.
- Transformation und Skalierung der Extrusionswerte (E-Werte), die das ABB PowerPac spezifisch als ganzzahlige Werte zur Prozesssteuerung verarbeitet.
- Automatisiertes „Safe Parking“ und anschließende Rückkehr zum letzten Arbeitspunkt – essenziell für Werkzeugwechsel im laufenden Prozess.
- Eine fortgeschrittene Plotly-Visualisierung, die:
  - den Druckpfad,
  - TCP-Richtungsvektoren,
  - sowie Hardware-Sperrzonen
    darstellt.

---

## 2.3 Hintergrundlogik (G-Code-Transformation)

Damit der G-Code vom ABB 3DP-PowerPac gelesen werden kann, überschreibt die Basisklasse die G-Code-Formatierung.

Mittels regulärer Ausdrücke (Regex) werden die von FullControl standardmäßig generierten G-Code-Strings abgefangen.

Dabei wird:

1. Der E-Wert extrahiert.
2. Auf Basis einer Konstante  skaliert.
3. Gerundet.
4. Als Integer wieder eingefügt.

Zusätzlich wird:

- der G-Code-Zeile die aktuelle Vektorausrichtung `(nX, nY, nZ)` hinzugefügt,
- durch eine Post-Processing-Funktion sichergestellt, dass bei jedem Bewegungsbefehl `(G0/G1)` die Koordinaten `X`, `Y` und `Z` zwingend ausgegeben werden.

Dies verhindert fehlerhafte Interpolationen seitens der Robotersteuerung.

---

# 3. Konfiguration & Systeminitialisierung

Bevor Pfade generiert werden können, muss das System parametriert werden.

Das Setup erfordert die Definition:

- des Referenz-Ursprungs,
- der Prozessparameter,
- sowie des Tool-Mappings.

## Beispielkonfiguration

```python
import fullcontrol as fc

# 1. Festlegung des globalen Referenzpunktes
# (z. B. Mitte der Antennenbasis)
ANT_ORIGIN = fc.Point(x=315, y=315, z=52)

# 2. Initialisierung der Prozessparameter
init_data = {
    'extrusion_width': 0.4,   # Soll-Breite in mm
    'extrusion_height': 0.2,  # Schichthöhe in mm
    'print_speed': 500        # Prozess-Geschwindigkeit in mm/min
}

# 3. Tool-Mapping
# (G-Code ID -> Roboter Tool)
TOOL_MAPPING = {
    'T1': 'T0', # Nozzle
    'T2': 'T1'  # Spritze
}
```

> **Hinweis:**\
> In RobotStudio ist aufgrund der Hardware-Konstruktion häufig ein konstanter Rotations-Basiswinkel (z. B. `[180, 0, 0]`) einzustellen.\
> Ein theoretisch senkrecht nach oben zeigender Normalenvektor entspricht hierbei:
>
> ```text
> nz = 1.0
> ```

---

# 4. API-Referenz & Datenstrukturen

## 4.1 Die `ABBPoint`-Klasse

Die `ABBPoint`-Klasse erbt von `fc.Point` und bildet den elementaren Baustein für Trajektorien.

Sie beinhaltet:

- kartesische Koordinaten
- Orientierungsvektor

## Beispiel

```python
# Instanziierung eines ABBPoints mit Vektorausrichtung
punkt = ABBPoint(
    x=100.0,
    y=100.0,
    z=50.0,
    nx=0.0,
    ny=0.0,
    nz=1.0  # Optional: Standardmäßig vertikale Düse
)
```

---

## 4.2 Die `GCodeList`-Klasse

Die zentrale Steuerungseinheit.

Sie:

- verwaltet die Liste der G-Code-Punkte,
- trackt den TCP,
- stellt spezifische Makros bereit.

## Initialisierung

```python
# Initialisieren einer neuen Liste
# (lädt automatisch ExtrusionGeometry, Extruder, Printer)
gcode_ablauf = GCodeList()
```

---

## Wichtige Kernmethoden der `GCodeList`

### `add_trajectory(points: list)`

Fügt eine zusammenhängende Liste von `ABBPoint`-Objekten ein.

Der erste Punkt wird automatisch im Leerfahrts-Modus `(G0)` angefahren.

---

### `moveToSaveParking(origin=None)`

- Stoppt die Extrusion.
- Sichert die aktuelle Position.
- Fährt das Werkzeug 150 mm in eine sichere Position.

Verhalten:

- Wird `origin(Point)` übergeben, weicht der Roboter radial in der XY-Ebene aus.
- Andernfalls erfolgt die Bewegung entlang des aktuellen Normalenvektors entgegen der Druckrichtung.

---

### `moveToLastPoint()`

Kehrt nach einer Routine (z. B. Parken) mit deaktiviertem Extruder exakt zur gesicherten Arbeitsposition und Orientierung zurück.

---

### `toolChange(tool_id: str)`

- Sichert die Position.
- Fährt in die Parkposition.
- Synchronisiert den TCP-Offset für das neue Tool.
- Kehrt anschließend zum Bauteil zurück.

## Beispiel

```python
gcode_ablauf.toolChange(tool_id='T2')
```

---

## Dosier- und Druckstatus-Kontrollen

### `dosingStart()`

Sendet Event:

```text
UE1
```

### `dosingStop()`

Sendet Event:

```text
UE2
```

### `pausePrint()`

Sendet Event:

```text
UE4
```

### `cleanNozzle()`

Führt eine definierte Wisch- und Reinigungsroutine für die Nozzle durch.

---

# 5. Anwendung

Dieses Beispiel demonstriert die Generierung einer mehrachsigen Test-Trajektorie mit interpolierter Position und Werkzeugorientierung.

Die Orientierung wird dabei über intrinsische ZYX-Euler-Winkel definiert und während der Bewegung kontinuierlich interpoliert. Aus den Euler-Winkeln wird ein orthogonales Vektorsystem berechnet, wobei der Vektor `vz` als Werkzeugnormalenvektor `(nX, nY, nZ)` für das ABB 3DP PowerPac verwendet wird.

---

## Schritt 1: Hilfsfunktion zur Euler-Transformation

Zur Berechnung der Werkzeugorientierung wird zunächst eine Hilfsfunktion definiert, welche intrinsische ZYX-Euler-Winkel in ein orthogonales Vektorsystem transformiert.

```python
# --- HILFSFUNKTION: EULER ZYX ZU VEKTOREN ---
def euler_zyx_to_vectors(yaw: float, pitch: float, roll: float):
    """
    Transformiert ZYX-Euler-Winkel (intrinsisch)
    in ein orthogonales Vektorsystem.
    """

    cz, sz = math.cos(yaw), math.sin(yaw)
    cy, sy = math.cos(pitch), math.sin(pitch)
    cx, sx = math.cos(roll), math.sin(roll)

    # Spalten der Rotationsmatrix
    vx = (cz * cy, sz * cy, -sy)
    vy = (
        cz * sy * sx - sz * cx,
        sz * sy * sx + cz * cx,
        cy * sx
    )
    vz = (
        cz * sy * cx + sz * sx,
        sz * sy * cx - cz * sx,
        cy * cx
    )

    return vx, vy, vz
```

---

## Schritt 2: Initialisierung des Druckablaufs

Es wird eine neue `GCodeList` erzeugt und die Reinigungsroutine der Düse ausgeführt.

```python
# --- INITIALISIERUNG ---
GCODE_linie = GCodeList()

GCODE_linie.cleanNozzle()

GCODE_linie.comment(
    "--- START Test-Linie mit Euler-Interpolation ---"
)
```

---

## Schritt 3: Definition der Trajektorie

Die Trajektorie besteht aus:

- einer Start- und Endposition,
- einer Start- und Endorientierung,
- sowie einer definierten Anzahl interpolierter Segmente.

```python
# --- KONFIGURATION DER TRAJEKTORIE ---

testLinie_1 = []

# Positionen [mm]
start_p = fc.Point(x=50, y=200, z=50)
end_p = fc.Point(x=100, y=210, z=60)

segmente_linie = 20

# Orientierungen [°]
# Start: Werkzeug zeigt senkrecht nach unten
start_angles_deg = (90, 0, 0)

# Ende: Werkzeug leicht geneigt
end_angles_deg = (90, 10, -10)

# Umrechnung in Radiant
start_euler = [math.radians(a) for a in start_angles_deg]
end_euler = [math.radians(a) for a in end_angles_deg]
```

---

## Schritt 4: Interpolation von Position und Orientierung

Für jedes Segment werden:

1. die kartesischen Positionen interpoliert,
2. die Euler-Winkel interpoliert,
3. die Richtungsvektoren berechnet,
4. sowie ein `ABBPoint` erzeugt.

Der Vektor `vz` repräsentiert dabei die Werkzeug-Z-Achse und wird direkt als Normalenvektor `(nX, nY, nZ)` verwendet.

```python
# --- GENERIERUNG (LOOP) ---
for i in range(segmente_linie + 1):

    # Fortschrittsfaktor (0.0 bis 1.0)
    f = i / segmente_linie

    # 1. Lineare Interpolation der Position
    x_pos = start_p.x + f * (end_p.x - start_p.x)
    y_pos = start_p.y + f * (end_p.y - start_p.y)
    z_pos = start_p.z + f * (end_p.z - start_p.z)

    # 2. Lineare Interpolation der Euler-Winkel
    curr_yaw = (
        start_euler[0] +
        f * (end_euler[0] - start_euler[0])
    )

    curr_pitch = (
        start_euler[1] +
        f * (end_euler[1] - start_euler[1])
    )

    curr_roll = (
        start_euler[2] +
        f * (end_euler[2] - start_euler[2])
    )

    # 3. Berechnung der Richtungsvektoren
    # vz entspricht dem Normalenvektor
    # (nX, nY, nZ) für das ABB PowerPac
    vx, vy, vz = euler_zyx_to_vectors(
        curr_yaw,
        curr_pitch,
        curr_roll
    )

    # 4. Hinzufügen des ABBPoints
    testLinie_1.append(
        ABBPoint(
            x=x_pos,
            y=y_pos,
            z=z_pos,
            nx=vz[0],
            ny=vz[1],
            nz=vz[2]
        )
    )
```

---

## Schritt 5: Hinzufügen der Trajektorie und Prozessbefehle

Die generierte Punktliste wird anschließend in die `GCodeList` eingefügt. Zusätzlich können Werkzeugwechsel oder Druckpausen integriert werden.

```python
GCODE_linie.add_trajectory(testLinie_1)

GCODE_linie.comment("--- ENDE Test-Linie ---")

# Werkzeugwechsel
GCODE_linie.toolChange(tool_id='T2')

# Druck pausieren
GCODE_linie.pausePrint()
```

---

## Schritt 6: Visualisierung

Die Plotly-Visualisierung ermöglicht die Überprüfung:

- der Bahnkurve,
- der Werkzeugorientierung,
- sowie der interpolierten TCP-Vektoren.

```python
visualize_gcode(
    gcode_list=GCODE_linie,
    frame_filter_value=1
)
```

---

## Schritt 7: Export des ABB-kompatiblen G-Codes

Im letzten Schritt wird der G-Code inklusive ABB 3DP Header exportiert.

Die Option `forceXYZ=True` erzwingt die vollständige Ausgabe aller kartesischen Koordinaten bei jedem Bewegungsbefehl.

```python
# --- EXPORT ---
export_gcode(
    gcode_list=GCODE_linie,
    file_name="ABB_testLinie1",
    forceXYZ=True
)
```




