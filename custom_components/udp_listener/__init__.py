"""UDP Listener Integration – empfängt UDP Broadcasts oder Direktnachrichten."""
import asyncio
import json
import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import DOMAIN, VERSION
from .sensor import UDPDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Basis-Setup der Integration (via configuration.yaml nicht benötigt)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entry-Setup bei Aktivierung der Integration."""
    port = entry.data["port"]
    update_interval = entry.data.get("update_interval", 5)  # Default: 5 Sekunden

    # Datencontainer initialisieren
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "port": port,
        "update_interval": update_interval,
        "transport": None,
        "devices": {},  # IP → UDPDevice
        "pending_devices": [],  # Geräte, falls async_add_entities noch nicht bereit
        "async_add_entities": None,
        "update_listener": None
    }

    _LOGGER.info("🚀 UDP Listener Integration Setup für Port %d (Update-Intervall: %ds)", port, update_interval)

    # Sensor-Platform zuerst registrieren (mit await)
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    _LOGGER.info("✅ Sensor Platform erfolgreich eingerichtet")

    # Dann UDP Listener starten
    await _start_udp_listener(hass, entry.entry_id, port)

    # Starte Intervall-Task für ausstehende Updates
    entry_data = hass.data[DOMAIN][entry.entry_id]
    entry_data["update_listener"] = hass.loop.create_task(
        _interval_update_task(hass, entry.entry_id, update_interval)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Beim Entfernen der Integration aufräumen."""
    entry_data = hass.data[DOMAIN].get(entry.entry_id)
    if entry_data:
        # Stoppe Update-Task
        update_listener = entry_data.get("update_listener")
        if update_listener:
            update_listener.cancel()

        # Schließe UDP Transport
        transport = entry_data.get("transport")
        if transport:
            transport.close()

        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return True


async def _start_udp_listener(hass: HomeAssistant, entry_id: str, port: int):
    """Starte den UDP-Server asynchron."""

    class UDPProtocol(asyncio.DatagramProtocol):
        def datagram_received(self, data: bytes, addr):
            ip = addr[0]
            try:
                payload = data.decode("utf-8").strip()
                _LOGGER.debug("📨 UDP von %s: %s", ip, payload)
                asyncio.create_task(_handle_packet(hass, entry_id, ip, payload))
            except UnicodeDecodeError:
                _LOGGER.warning("⚠️ Nicht-UTF8-Daten von %s empfangen", ip)

    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: UDPProtocol(), local_addr=("0.0.0.0", port)
    )

    hass.data[DOMAIN][entry_id]["transport"] = transport
    _LOGGER.info("✅ UDP Listener läuft auf Port %d", port)


async def _handle_packet(hass: HomeAssistant, entry_id: str, ip: str, raw_data: str):
    """UDP-Daten verarbeiten und ggf. Sensoren anlegen oder aktualisieren."""
    entry_data = hass.data[DOMAIN][entry_id]
    devices = entry_data["devices"]
    async_add = entry_data["async_add_entities"]
    update_interval = entry_data["update_interval"]

    # Parse JSON-Daten
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        _LOGGER.warning("⚠️ Ungültiges JSON von %s: %s", ip, raw_data)
        data = {"raw_data": raw_data}

    # Device bereits vorhanden?
    if ip in devices:
        device = devices[ip]
        device.update_data(data, async_add)
    else:
        # Neues Device erzeugen
        device = UDPDevice(hass, ip, entry_id, update_interval)
        devices[ip] = device
        device.update_data(data, async_add)

        if async_add:
            _LOGGER.info("🆕 Neues Device erkannt: %s", ip)
            await device.async_add_to_hass(async_add)
        else:
            # Nur wenn nicht bereits vorhanden, zur pending list hinzufügen
            if device not in entry_data["pending_devices"]:
                _LOGGER.info("⏳ Device %s wird vorgemerkt", ip)
                entry_data["pending_devices"].append(device)


async def _interval_update_task(hass: HomeAssistant, entry_id: str, update_interval: int):
    """Task für regelmäßige Verarbeitung ausstehender Updates."""
    try:
        while True:
            await asyncio.sleep(update_interval)
            
            entry_data = hass.data[DOMAIN].get(entry_id)
            if not entry_data:
                break
                
            devices = entry_data["devices"]
            _LOGGER.debug("🔄 Verarbeite ausstehende Updates für %d Geräte", len(devices))
            
            for device in devices.values():
                device.process_pending_updates()
                
    except asyncio.CancelledError:
        _LOGGER.info("⏹️ Update-Task wurde beendet")
    except Exception as e:
        _LOGGER.error("❌ Fehler in Update-Task: %s", e)
