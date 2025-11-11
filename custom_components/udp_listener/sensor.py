"""Sensor entity for UDP Listener."""
from __future__ import annotations
from typing import Any
import logging
import re
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Statische Übersetzungen als Fallback
ATTRIBUTE_TRANSLATIONS = {
    "bestdiff": "Beste Schwierigkeit",
    "boardtype": "Board-Typ", 
    "freeheap": "Freier Heap-Speicher",
    "hashrate": "Hashrate",
    "ip": "IP-Adresse",
    "lastdiff": "Letzte Schwierigkeit", 
    "netdiff": "Netzwerk-Schwierigkeit",
    "pooldiff": "Pool-Schwierigkeit",
    "poolinuse": "Aktiver Pool",
    "progress": "Fortschritt",
    "rssi": "Signalstärke (RSSI)",
    "share": "Shares",
    "temp": "Temperatur",
    "uptime": "Betriebszeit",
    "valid": "Gültige Shares",
    "version": "Version"
}

class UDPAttributeSensor(SensorEntity):
    """Represents a single attribute from UDP data as a sensor."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        ip: str,
        entry_id: str,
        attribute_name: str,
        initial_value: Any,
        update_interval: int
    ) -> None:
        self.hass = hass
        self._ip = ip
        self._entry_id = entry_id
        self._attribute_name = attribute_name
        self._update_interval = update_interval
        self._last_update = None
        self._pending_value = None
        self._attr_native_value = self._format_value(initial_value)

        self._attr_unique_id = f"udp_miner_{ip.replace('.', '_')}_{attribute_name}"
        
        # Verwende statische Übersetzung als Fallback
        attr_lower = attribute_name.lower()
        self._attr_name = ATTRIBUTE_TRANSLATIONS.get(attr_lower, attribute_name)
        
        # Setze translation_key für dynamische Übersetzungen
        self._attr_translation_key = attr_lower

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ip)},
            name=f"Miner {ip}",
            manufacturer="Benutzerdefinierte UDP-Geräte"
        )

        # Setze passende Einheiten und Device Classes für bestimmte Sensoren
        self._set_unit_and_icon(attribute_name)

    def _set_unit_and_icon(self, attribute_name):
        """Setzt Einheiten und Icons basierend auf dem Attributnamen."""
        attr_lower = attribute_name.lower()
        
        # Einheiten-Mapping
        unit_mapping = {
            "temp": "°C",
            "freeheap": "KB",
            "rssi": "dBm",
        }
        
        # Icon-Mapping
        icon_mapping = {
            "hashrate": "mdi:chip",
            "temp": "mdi:thermometer",
            "freeheap": "mdi:memory",
            "rssi": "mdi:wifi",
            "uptime": "mdi:timer",
            "version": "mdi:information",
            "boardtype": "mdi:chip",
            "ip": "mdi:ip-network",
            "poolinuse": "mdi:server-network",
            "share": "mdi:chart-pie",
            "valid": "mdi:check-circle",
            "bestdiff": "mdi:chart-line",
            "lastdiff": "mdi:chart-line",
            "netdiff": "mdi:chart-line",
            "pooldiff": "mdi:chart-line",
            "progress": "mdi:progress-check",
        }
        
        # Device Classes für bessere Integration
        device_class_mapping = {
            "temp": "temperature",
            "rssi": "signal_strength",
        }
        
        self._attr_native_unit_of_measurement = unit_mapping.get(attr_lower)
        self._attr_icon = icon_mapping.get(attr_lower)
        self._attr_device_class = device_class_mapping.get(attr_lower)

    def _convert_hashrate_to_number(self, hashrate_str):
        """Konvertiert Hashrate-String in eine Zahl."""
        try:
            # Entferne Leerzeichen und konvertiere zu lowercase
            hashrate_str = hashrate_str.strip().lower()
            
            # Ersetze Komma durch Punkt für deutsche Zahlen
            hashrate_str = hashrate_str.replace(',', '.')
            
            # Entferne "h/s" und konvertiere Präfixe
            if "kh/s" in hashrate_str:
                number_str = hashrate_str.replace("kh/s", "").strip()
                return float(number_str) * 1000
            elif "mh/s" in hashrate_str:
                number_str = hashrate_str.replace("mh/s", "").strip()
                return float(number_str) * 1000000
            elif "gh/s" in hashrate_str:
                number_str = hashrate_str.replace("gh/s", "").strip()
                return float(number_str) * 1000000000
            elif "th/s" in hashrate_str:
                number_str = hashrate_str.replace("th/s", "").strip()
                return float(number_str) * 1000000000000
            elif "h/s" in hashrate_str:
                number_str = hashrate_str.replace("h/s", "").strip()
                return float(number_str)
            else:
                # Fallback: versuche direkt zu konvertieren
                return float(hashrate_str)
        except (ValueError, TypeError):
            _LOGGER.warning("Could not convert hashrate value: %s", hashrate_str)
            return 0

    def _format_value(self, value):
        """Format value for display."""
        if isinstance(value, str):
            # Entferne Steuerzeichen und trimme
            cleaned = value.split('\r')[0].strip()
            
            attr_lower = self._attribute_name.lower()
            
            # Spezielle Behandlung für Hashrate - konvertiere zu Zahl
            if attr_lower == "hashrate":
                numeric_value = self._convert_hashrate_to_number(cleaned)
                # Setze Einheit für Hashrate
                self._attr_native_unit_of_measurement = "H/s"
                return numeric_value
            
            # Spezielle Behandlung für andere numerische Werte
            if attr_lower in ["temp", "rssi", "bestdiff", "lastdiff", "netdiff", "pooldiff", "progress"]:
                try:
                    # Ersetze Komma durch Punkt für float-Konvertierung
                    cleaned = cleaned.replace(',', '.')
                    return float(cleaned)
                except (ValueError, TypeError):
                    # Falls Konvertierung fehlschlägt, behalte Originalwert
                    return cleaned
            
            # Für FreeHeap - behalte den originalen String, da er Einheit enthält
            if attr_lower == "freeheap":
                return cleaned
                
            return cleaned
        return value

    @callback
    def update_value(self, value: Any) -> None:
        """Update sensor value only if changed and interval passed."""
        new_value = self._format_value(value)
        current_time = datetime.now()
        
        # Prüfe ob Intervall abgelaufen ist oder erstes Update
        if (self._last_update is None or 
            (current_time - self._last_update).total_seconds() >= self._update_interval):
            
            if self._attr_native_value != new_value:
                self._attr_native_value = new_value
                self._last_update = current_time
                self.async_write_ha_state()
                _LOGGER.debug("🔄 Sensor %s aktualisiert (Intervall: %ds)", self._attr_name, self._update_interval)
        else:
            # Wert hat sich geändert, aber Intervall nicht abgelaufen
            if self._attr_native_value != new_value:
                self._pending_value = new_value
                _LOGGER.debug("⏳ Sensor %s: Wert geändert, warte auf Intervall", self._attr_name)

    @callback
    def process_pending_update(self) -> None:
        """Verarbeite ausstehende Updates wenn Intervall abgelaufen ist."""
        if self._pending_value is not None:
            current_time = datetime.now()
            if (self._last_update is None or 
                (current_time - self._last_update).total_seconds() >= self._update_interval):
                
                self._attr_native_value = self._pending_value
                self._last_update = current_time
                self._pending_value = None
                self.async_write_ha_state()
                _LOGGER.debug("🔄 Sensor %s mit ausstehendem Wert aktualisiert", self._attr_name)

class UDPDevice:
    """Represents a UDP device with multiple attribute sensors."""

    def __init__(self, hass: HomeAssistant, ip: str, entry_id: str, update_interval: int):
        self.hass = hass
        self.ip = ip
        self.entry_id = entry_id
        self.update_interval = update_interval
        self.sensors = {}
        self._added = False

    async def async_add_to_hass(self, async_add_entities):
        """Add all sensors to Home Assistant."""
        self._added = True
        if self.sensors:
            async_add_entities(self.sensors.values())
            _LOGGER.debug("✅ %d Sensoren für %s hinzugefügt", len(self.sensors), self.ip)

    def update_data(self, data: dict[str, Any], async_add_entities):
        """Update or create sensors for all attributes in data."""
        new_sensors = []
        
        for attr_name, value in data.items():
            if attr_name not in self.sensors:
                # Create new sensor
                sensor = UDPAttributeSensor(
                    self.hass,
                    self.ip,
                    self.entry_id,
                    attr_name,
                    value,
                    self.update_interval
                )
                self.sensors[attr_name] = sensor
                if self._added:
                    new_sensors.append(sensor)
            else:
                # Update existing sensor
                self.sensors[attr_name].update_value(value)

        # Add new sensors in batch
        if new_sensors and async_add_entities:
            _LOGGER.info("➕ %d neue Sensoren für %s", len(new_sensors), self.ip)
            async_add_entities(new_sensors)

    def process_pending_updates(self):
        """Process pending updates for all sensors."""
        for sensor in self.sensors.values():
            sensor.process_pending_update()

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Register sensor entities when the integration is set up."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    entry_data["async_add_entities"] = async_add_entities
    
    # Füge alle ausstehenden Geräte hinzu
    if entry_data["pending_devices"]:
        pending_devices = entry_data["pending_devices"].copy()
        entry_data["pending_devices"].clear()
        
        for device in pending_devices:
            await device.async_add_to_hass(async_add_entities)