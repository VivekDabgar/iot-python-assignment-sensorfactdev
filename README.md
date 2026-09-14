# Assignment: Exporter-Ecoadapt

In order to provide more accurate energy measurements for some of our customers, Sensorfact is investigating the addition of new 3rd-party sensors to its portfolio. We have found the [Eco-Adapt Power Elec 3 or 6](https://www.eco-adapt.com/products/) which meets our requirements. There is only one catch: its data can only be read via ModBus (an industrial fieldbus protocol), and we have no solution for that yet. For this assignment, you'll have to make a proof of concept to show that the Sensorfact bridges (Raspberry Pi based) can read data from the EcoAdapt sensor and send it to our backend. The proof of concept will also be used to estimate the complexity of building a production-proof solution.

## Requirements

To get a feel for the usability of the device, we need to read a value from the sensor and transfer it to the cloud. In this assignment you need to make code that:

- Reads the voltage and frequency from the sensor (it should be around 230V / 50Hz)
- Sends these values to a server periodically.

## Resources

In `docs` you will find some resources:

- A user manual for the sensor, for some background information. Unfortunately it is in French only.
- A manual that gives you all the information you need about the ModBus integration.

We have provided some boilerplate code to work with `pymodbus` to read the device in `./src/exporter-ecoadapt/exporter-ecoadapt.py`. You can reuse this code, or start from scratch. To run it, create a virtual environment and install the requirements:

```shell
python3 -m venv ./venv
source ./venv/bin/activate
pip3 install -r ./requirements.txt
```

Since you have no sensor attached to your system, not much will happen. We have provided the output of the script in the comments at the end of the script, this can get you started with some sensor responses. To be compatible with our bridges, the code needs to be deployed and controlled over ssh & scp, and the code will have to be compatible with Pyhon 3.7.3.

If you just need a few more responses from the sensor (for specific registers) we can provide them.

The protocol to send data to a server is left up to you as well. One option could be to send the data over a websocket. A minimal receiving websocket server can be found in `./dev`. It just prints out whatever you send it, but that is enough for this proof of concept (no need for storage, monitoring or analysis). You need to install `requirements-dev` to get the right dependencies, and set a subprotocol (see the `TODO` in the file).

## Process

> TLDR;
> 1. Spend approximately 6 hours on the assignment
> 2. Make a conscious decision on what you want to focus on: it's fine if you
cannot complete all aspects of the assignment
> 3. Send us your solution before the technical interview, as a zip file or by sharing a git repo
> 4. Contact us if you have any questions

Please keep in mind:

- This assignment is a toy example, Sensorfact will not own your code, and does not intend to use it for anything but evaluation of your skills.
- EcoAdapt is a real company and Sensorfact works with their sensors, but they are not aware of this assignment. Please do not contact EcoAdapt for help or support.
- We understand that you may not have experience with all aspects of this assignment. Make sure that you can show something during the technical interview and make an effort to learn something new. It's often really interesting to discuss how you learn and act if you're stuck, as you will also encounter new challenges regularly when working for Sensorfact.
- We intend to be mindful of your time, and expect you to spend only a few hours (<6) on this assignment, which is too little to do everything you might want. We do not need the result to be polished and 'done'. Decide what you want to focus on and reserve some time to wrap it up and communicate how far you got. We are interested in the results as well as the process and the choices that got you there.
- The result of the assignment will be a proof of concept only, but we would like to discuss how you would build it into something we might deploy to hundreds of customers.
- Take this assignment as an opportunity to show us your style: what you like to work on, what you find important. You can neglect or handwave the boring stuff.
- If you have any further questions, do not hesitate to contact us.

# Assignment: Exporter-Ecoadapt

Reads RMS voltage and frequency from an EcoAdapt Power-Elec 6 over Modbus TCP and sends them to a server over a WebSocket, every few seconds.

Proof of concept. Targets a Sensorfact bridge (Raspberry Pi, Python 3.7.3).

Run it:
```shell
python3 -m venv ./venv && source ./venv/bin/activate
pip3 install -r ./requirements.txt -r ./requirements-dev.txt
```

Terminal 1 — a fake PE6 serving the register dump from the boilerplate, so this runs with no hardware:

```shell
python3 dev/fake_pe6.py 5502
```

Terminal 2 — the receiving server provided with the assignment:

```shell
python3 dev/server.py --port 9000
```

Terminal 3 — the exporter:

```shell
python3 src/exporter-ecoadapt/exporter-ecoadapt.py \
    --modbus-host 127.0.0.1 --modbus-port 5502 --ws-url ws://127.0.0.1:9000
```

Against a real meter, skip terminal 1 and use --modbus-host 169.254.20.1 --modbus-port 502.

Terminal 3 logs sent connector 1/1: 238.76 V, 51.46 Hz. Terminal 2 shows it arrive:

```json
{"timestamp":"...","connector":1,"channel":1,"circuit_mode":1,
 "voltage_v":238.76,"frequency_hz":51.46}
 ```

Tests, no hardware needed: python3 -m pytest tests -q → 7 passed.

Attached the screenshot of what server prints:
 ```json
{"timestamp":"...","connector":1,"channel":1,"circuit_mode":1,
 "voltage_v":238.76,"frequency_hz":51.46}
 ```


How it works:
Every 5 seconds the exporter does three small reads from the meter.

Read 1 — "is anything plugged in here?" One register tells you whether this channel has a current sensor attached. If it reads 0x0000, nothing is wired. Stop. Send nothing.
Reads 2 and 3 — the actual numbers. Voltage takes 2 registers, frequency takes 2 registers. Turn each pair into a decimal number, put them in a JSON message, send it over the WebSocket.
Five registers total. That's the whole loop.

Where do the register numbers come from? The manual gives a formula instead of a lookup table, because the meter has 18 channels and listing all of them would be a huge table. The formula converts "connector 2, channel 1" into "register 358":

```python
def get_addr(start, connector, channel, wpc):
    return start + ((connector - 1) * 3 + (channel - 1)) * wpc
	```
wpc means words per channel — how many registers one value takes up. It has to be an argument, not a fixed number, because it changes:

the configuration value is small → 1 register each
voltage and frequency are decimals → 2 registers each

Three things that bite:
1. The two halves arrive backwards.
A decimal number is too big for one register, so the meter splits it in half and sends both. But it sends the small half first. If you join them in the order they arrive, you get −43.32 instead of 238.76.
The dangerous part: −43.32 is still a number. Nothing crashes. It just quietly sends wrong data forever. That's why the tests focus here.

2. There are two ways to ask, and only one is right.
Modbus has different "read" commands. This meter keeps measurements in input registers, so you must use read_input_registers. Use the other one and you get nothing useful back.

3. The meter answers even when nobody's home.
Ask about any of the 18 channels and the meter always replies — even for a socket with no sensor plugged in. Those empty inputs read tiny values like 0.16 V. That's electrical noise, not a measurement. Publish it and your dashboard shows a machine using electricity that doesn't exist.

That's what read 1 prevents.

Not done:
Four honest gaps:

If the server goes down, those readings are gone. The exporter doesn't hold anything in memory to send later.

If either connection drops, the program stops. It doesn't try again.

Three-phase machines aren't handled specially. Doesn't matter here — voltage and frequency are measured once at the meter's power input, so they're the same for every channel. It would matter for power and energy readings.

The Modbus read pauses everything else while it happens. With five registers that's a few milliseconds, so nobody notices. With many meters it would.

START-HERE.md explains the device, the full register map, and which of these I'd fix first.

```Layout
src/exporter-ecoadapt/reader-ecoadapt.py      the exporter
dev/server.py                                 provided server, subprotocol TODO fixed
tests/test_decode.py                          addressing + word order
```