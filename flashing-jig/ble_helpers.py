import secrets
import re
import logging
import time
import os
import binascii
from typing import Tuple


def addr_to_str(addr: bytes) -> str:
    hex_arr = ["%02X" % b for b in addr[::-1]]
    return ":".join(hex_arr)


def str_to_addr(addr: str) -> bytes:
    hex_arr = addr.split(":")
    return bytes([int(b, 16) for b in hex_arr[::-1]])

def key_to_str(key: bytes) -> str:
    return key.hex().upper()

def str_to_key(key: str) -> bytes:
    return binascii.unhexlify(key)


def new_addr() -> bytes:
    addr = bytearray(secrets.token_bytes(6))
    addr[5] |= 0xc0
    return bytes(addr)


def new_keys() -> Tuple[bytes, bytes, bytes]:
    irk = secrets.token_bytes(16)
    ltk = secrets.token_bytes(16)
    spacekey = secrets.token_bytes(32)
    return irk, ltk, spacekey


class KeykeeperDB:
    '''
    This data structure is a helper struct that manages addresses, keys and names.
    It is meant to be replaceable in case someone wants to keep their data in a different manner.
    '''

    def __init__(self, coins_file="coins.txt",
                 central_file="central.txt",
                 names_file="names.txt"):
        '''
        self.coins is: {"<addr>":("<irk>", "<ltk>", "<spacekey>"),...}
        self.identity is: ["<addr>", "<irk>"]
        self.names is: {"<addr>":"<name>",...}
        '''
        self.coins = {}
        self.identity = []
        self.names = {}
        self.coins_file = coins_file
        self.central_file = central_file
        self.names_file = names_file
        self.load()

    def new_coin(self, name : str=None):
        # new addr has to be unique
        while True:
            addr = new_addr()
            addr_str = addr_to_str(addr)
            if addr_str != self.identity[0] and addr_str not in self.coins:
                break

        irk, ltk, spacekey = new_keys()

        self.coins[addr_str] = (
            irk.hex().upper(),
            ltk.hex().upper(),
            spacekey.hex().upper(),
        )

        self.append_coin(addr_str)

        self.names[addr_str] = name
        self.append_name(addr_str)

        return addr, irk, ltk, spacekey

    def append_coin(self, address: str):
        '''
        This appends a new coin to the database.
        '''
        irk, ltk, spacekey = self.coins[address]
        with open(self.coins_file, "a") as f:
            f.write(f"{address} {irk} {ltk} {spacekey}\n")

    def append_name(self, address: str):
        '''
        This appends a name to the database.
        '''
        name = self.names[address]
        with open(self.names_file, "a") as f:
            f.write(f"{address} {name}\n")

    def _init_central(self):
        logging.warning("init database")
        suffix = str(int(time.time()))

        for f in [self.coins_file, self.central_file, self.names_file]:
            # back up old files
            if os.path.exists(f):
                dest = f"{f}.bak-{suffix}"
                os.rename(f, dest)
                logging.warning("move {f} -> {dest}")
            # create new file
            open(f, 'a').close()

        # generate central keys
        addr = new_addr()
        irk, _, _ = new_keys()
        self.identity = (addr_to_str(addr), irk.hex().upper())

        # create central file
        with open(self.central_file, "w") as f:
            f.write(f"{self.identity[0]} {self.identity[1]}")

    def load(self):
        '''
        This loads the database from three text files:

        [central.txt] contains one line: "<central_addr> <central_irk>"
        [coins.txt] has a line for every coin: "<addr> <irk> <ltk> <spacekey>"
        [names.txt] has a line for every coin: "<addr> <name>"

        It is optional but helpful to specify a name for every coin.
        '''

        if not os.path.exists(self.coins_file):
            self._init_central()
            return

        # load central info
        with open(self.central_file, "r") as f:
            line = f.readline()
            m = re.match(r"(.{17})\s+(.{32})", line)
            if m:
                self.identity = m.groups()
            else:
                self._init_central()
                return
        logging.info(f"loaded [central] info")

        # load coins file
        with open(self.coins_file, "r") as f:
            for line in f:
                m = re.match(r"(.{17})\s+(.{32})\s+(.{32})\s+(.{64})", line)
                if m:
                    self.coins[m.group(1)] = m.groups()[1:]
        logging.info(f"loaded {len(self.coins)} coins")

        # load names file (optional)
        try:
            with open(self.names_file, "r") as f:
                for line in f:
                    m = re.match(r"(.{17})\s+(.+)", line)
                    if m:
                        self.names[m.group(1)] = m.group(2)
        except:
            logging.warning("could not load [names] file")
