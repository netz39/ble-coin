# Flashing BLE Coins with a RPi Zero W 1

The coin is connected using a programming jig
that controls power output with a transistor (active-low).

![flashing jig](./IMG_1701.png)

A red LED lights up when the coin is powered.
![flashing jig powered](./IMG_1703.png)

CAD files can be found in the `cad/` folder.
The PCB is not strictly necessary, you can wire it up with just pogo pins and some glue. Having a transistor to control power is recommended though.

The following pins are used:

* 3.3V
* GND
* swclk = GPIO 11
* swdio = GPIO 25
* pwr_en = GPIO 27

The `openocd` package needs to be installed for this to work. A special version configured with `--enable-bcm2835gpio --enable-sysfsgpio` is needed for bitbanging on the RPi GPIO pins.

The `ble_gen_coin.py <name>` script generates a hex file for flashing. A list of coins and names is maintained in `coins.txt` and `names.txt`. The format is compatible with [ble-keykeeper](https://github.com/netz39/ble-keykeeper-role/blob/main/templates/ble_keykeeper.py).

While flashing, the coins are put in a protected mode. You can query that mode with `./check.sh` and factory-reset a coin with `./unlock.sh`.

Flashing is done with `./flash.sh something.hex`.
