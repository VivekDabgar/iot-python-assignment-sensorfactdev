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
