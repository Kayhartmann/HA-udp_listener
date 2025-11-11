
# UDP Listener Home Assistant Integration
> 🌐 Choose your language / Sprache wählen
> - [English](README_En.md)
> - [Deutsch](README.de.md)

Empfängt UDP-Nachrichten von Minern und erstellt Sensoren.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg)

## Installation

### Über HACS (empfohlen)
1. HACS → Integrationen → Drei Punkte → Custom repositories
2. Repository URL: `https://github.com/Kayhartmann/HA-udp_listener`
3. Kategorie: Integration
4. "UDP Listener" installieren
5. Home Assistant neustarten

### Manuelle Installation
Kopieren Sie den `udp_listener` Ordner in Ihren `custom_components` Ordner.

## Konfiguration
1. Home Assistant → Einstellungen → Geräte & Dienste
2. "+ Integration hinzufügen" → "UDP Listener"
3. Port und Update-Intervall konfigurieren

## Features
- Empfängt UDP-Nachrichten von Minern
- Automatische Sensor-Erstellung
- Deutsche und englische Übersetzungen
- Konfigurierbares Update-Intervall

## Unterstützte Attribute
- Hashrate, Temperatur, Signalstärke
- Betriebszeit, Shares, Schwierigkeit
- Pool-Informationen, Version, etc.
## Lizenz

Diese Integration ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) Datei für Details.

## Danksagungen

- Dank an die Home Assistant Community für die Unterstützung
- Besonderer Dank an alle Tester und Beitragenden
  
## Beitragen
Fehler und Feature-Requests bitte auf [GitHub](https://github.com/Kayhartmann/HA-udp_listener/issues) melden.
