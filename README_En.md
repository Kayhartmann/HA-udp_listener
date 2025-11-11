# UDP Listener Home Assistant Integration

Receives UDP messages from miners and creates sensors.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg)

## Installation

### Via HACS (recommended)
1. HACS → Integrations → Three dots → Custom repositories
2. Repository URL: `https://github.com/Kayhartmann/HA-udp_listener`
3. Category: Integration
4. Install "UDP Listener"
5. Restart Home Assistant

### Manual Installation
Copy the `udp_listener` folder to your `custom_components` folder.

## Configuration
1. Home Assistant → Settings → Devices & Services
2. "+ Add Integration" → "UDP Listener"
3. Configure port and update interval

## Features
- Receives UDP messages from miners
- Automatic sensor creation
- German and English translations
- Configurable update interval

## Supported Attributes
- Hashrate, temperature, signal strength
- Uptime, shares, difficulty
- Pool information, version, etc.

## License

This integration is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the Home Assistant community for support
- Special thanks to all testers and contributors

## Contributing
Please report bugs and feature requests on [GitHub](https://github.com/Kayhartmann/HA-udp_listener/issues).
