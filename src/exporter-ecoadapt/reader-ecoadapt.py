#!/usr/bin/env python3
"""
Reads RMS voltage and frequency from one channel of an EcoAdapt Power-Elec 6
over Modbus TCP and sends them to a server over a WebSocket, periodically.
 
Python 3.7.3 compatible.
"""

import logging
import struct
from pymodbus.client.sync import ModbusTcpClient

START_VOLTAGE = 352
START_FREQUENCY = 424

FORMAT = "%(asctime)-15s %(levelname)-8s %(message)s"
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.INFO)

def get_addr(start, connector, channel, wpc):
    """Register address calculation for EcoAdapt Power-Elec 6."""

    return start + ((connector - 1) * 3 + (channel - 1)) * wpc

def decode_float32(low_word, high_word):
    """Decode a 32-bit float from two 16-bit registers."""

    return struct.unpack(">f", struct.pack(">HH", high_word, low_word))[0]

def read_registers(client, address, count, unit):
    """Read registers from the EcoAdapt device."""

    response = client.read_input_registers(address, count, unit=unit)
    if response.isError():
        raise IOError("Modbus read of %d register(s) at %d failed: %r"
                      % (count, address, response))
    return response.registers


def main():
    modbus = ModbusTcpClient("169.254.20.1", port=502, timeout=3)
    if not modbus.connect():
        raise SystemExit("cannot reach the meter at 169.254.20.1:502")


if __name__ == "__main__":
    main()