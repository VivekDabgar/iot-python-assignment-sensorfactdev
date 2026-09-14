#!/usr/bin/env python3
"""
Reads RMS voltage and frequency from one channel of an EcoAdapt Power-Elec 6
over Modbus TCP and sends them to a server over a WebSocket, periodically.
 
Python 3.7.3 compatible.
"""

import argparse
import asyncio
import logging
import struct
import json
from datetime import datetime
from urllib.parse import urlparse

from autobahn.asyncio.websocket import WebSocketClientFactory, WebSocketClientProtocol
from pymodbus.client.sync import ModbusTcpClient

# Both ends of the WebSocket must agree on this (see dev/server.py)
SUBPROTOCOL = "sensorfact.v1"

FORMAT = "%(asctime)-15s %(levelname)-8s %(message)s"
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.INFO)

START_CONFIG = 8
START_VOLTAGE = 352
START_FREQUENCY = 424

WPC_CONFIG = 1       # configuration is one uint16 per channel
WPC_FLOAT = 2        # every electrical value is a float32 -> two registers

CIRCUIT_DISABLED = 0x0000    # no current sensor wired to this channel

def get_addr(start, connector, channel, wpc):
    """Register address calculation for EcoAdapt Power-Elec 6."""

    return start + ((connector - 1) * 3 + (channel - 1)) * wpc


def decode_float32(low_word, high_word):
    """Decode a 32-bit float from two 16-bit registers."""

    return struct.unpack(">f", struct.pack(">HH", high_word, low_word))[0]


def read_registers(client, address, count, unit):
    """Read registers from the EcoAdapt device."""

    response = client.read_input_registers(address, count, unit=unit)
    if response is None or response.isError():
        raise IOError("Modbus read of %d register(s) at %d failed: %r"
                      % (count, address, response))
    return response.registers


def read_channel(client, connector, channel, unit):
    """ Read voltage and frequency from a channel of the EcoAdapt device.

    The meter answers for all 18 channels whether or not a current sensor is
    attached. An unwired channel returns floating-input noise (0.16 V in the
    captured dump), which must not be published as a measurement. Registers
    8..25 hold one configuration enum per channel; 0x0000 means disabled.
    """
    config_addr = get_addr(START_CONFIG, connector, channel, WPC_CONFIG)
    config = read_registers(client, config_addr, WPC_CONFIG, unit)[0]
    if config == CIRCUIT_DISABLED:
        return None
 
    v_addr = get_addr(START_VOLTAGE, connector, channel, WPC_FLOAT)
    f_addr = get_addr(START_FREQUENCY, connector, channel, WPC_FLOAT)
 
    v_regs = read_registers(client, v_addr, WPC_FLOAT, unit)
    f_regs = read_registers(client, f_addr, WPC_FLOAT, unit)

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "connector": connector,
        "channel": channel,
        "circuit_mode": config,
        "voltage_v": round(decode_float32(v_regs[0], v_regs[1]), 2),
        "frequency_hz": round(decode_float32(f_regs[0], f_regs[1]), 2),
    }


# ---------------------------------------------------------------------------
# WebSocket client
# ---------------------------------------------------------------------------

class ExporterProtocol(WebSocketClientProtocol):

  def onConnect(self, res):
    log.info("Connected: %r", res.protocol)

  def onOpen(self):
    asyncio.create_task(self.publish_loop())

  async def publish_loop(self):
    cfg = self.factory
    while self.is_open:
      try:
        sample = read_channel(cfg.modbus, cfg.connector, cfg.channel, cfg.unit)
      except IOError as e:
        log.warning("%s", e)
      else:
        if sample is None:
          log.warning("Connector %d channel %d is disabled", cfg.connector, cfg.channel)
        else:
          self.sendMessage(json.dumps(sample).encode("utf8"))
          log.info(
              "Sent %d/%d: %.2fV, %.2fHz",
              sample["connector"],
              sample["channel"],
              sample["voltage_v"],
              sample["frequency_hz"],
          )
      await asyncio.sleep(cfg.interval)

  def onClose(self, clean, code, reason):
    log.info("Closed: %s", reason)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modbus-host", default="169.254.20.1", help="PE6 IP address")
    parser.add_argument("--modbus-port", default=502, type=int, help="PE6 Modbus port")
    parser.add_argument("--ws-url", default="ws://127.0.0.1:9000", help="WebSocket URL to send data to")
    return parser.parse_args()



def main():
    args = parse_args()

    log.info("Connecting to PE6 at %s:%d", args.modbus_host, args.modbus_port)
    modbus = ModbusTcpClient(args.modbus_host, port=args.modbus_port, timeout=3)
    if not modbus.connect():
        raise SystemExit("cannot reach the meter at %s:%d" % (args.modbus_host, args.modbus_port))

    factory = WebSocketClientFactory(args.ws_url, protocols=[SUBPROTOCOL])
    factory.protocol = ExporterProtocol
    factory.modbus = modbus
    factory.unit = 1
    factory.connector = 1
    factory.channel = 1
    factory.interval = 5.0

    parsed = urlparse(args.ws_url)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_connection(factory, parsed.hostname, parsed.port or 80))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        log.info("Interrupted, closing connections")
    finally:
        modbus.close()
        loop.close()

if __name__ == "__main__":
    main()