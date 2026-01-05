#!/usr/bin/python3
import binascii
from intelhex import IntelHex
from ble_helpers import KeykeeperDB, str_to_addr, str_to_key, addr_to_str
import sys
import time

# CRC-8-CCITT with initial value 0xFF: checksum used in FCB
def fcb_crc8(data):
    crc8_ccitt_small_table = bytes([0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15,
                                    0x38, 0x3f, 0x36, 0x31, 0x24, 0x23, 0x2a, 0x2d])
    val = 0xFF
    for b in data:
        val ^= b
        val = ((val << 4) & 0xFF) ^ crc8_ccitt_small_table[val >> 4]
        val = ((val << 4) & 0xFF) ^ crc8_ccitt_small_table[val >> 4]
    return val


# generate FCB storage item from data
def gen_storage_item(data):
    assert len(data) < 0x4000
    if len(data) < 0x80:
        data_w_len = bytes([len(data)]) + data
    else:
        data_w_len = bytes([(len(data) & 0x7f) | 0x80, len(data) >> 7]) + data
    return data_w_len + bytes([fcb_crc8(data_w_len)])


# generate storage partition
def periph_storage_partition(periph_addr, periph_irk, central_addr, central_irk, ltk,
                             spacekey):
    magic_header = b'\xee\xee\xff\xc0\x01\xff\x00\x00'
    bt_id = b'bt/id=\x01' + bytes(periph_addr)
    bt_irk = b'bt/irk=' + bytes(periph_irk)
    bt_keys = b'bt/keys/' + binascii.hexlify(central_addr[::-1]) + b'1=\x10\x11"\x00' + b'\x00' * 10 + \
              bytes(ltk) + bytes(central_irk) + b'\x00' * 6
    space_key = b'space/key=' + bytes(spacekey)
    data = magic_header + \
        gen_storage_item(bt_id) + \
        gen_storage_item(bt_irk) + \
        gen_storage_item(bt_keys) + \
        gen_storage_item(space_key)
    return data + b'\xff' * (0x6000 - len(data))  # partition length from DTS


if __name__ == '__main__':
    db = KeykeeperDB()

    if len(sys.argv) == 2:
        name = sys.argv[1]
    else:
        name = f"namehere_{int(time.time())}"

    p_addr, p_irk, ltk, spacekey = db.new_coin(name)

    # prepare IDs
    c_addr_str, c_irk_str = db.identity
    c_addr = str_to_addr(c_addr_str)
    c_irk = str_to_key(c_irk_str)

    print("Central: " + c_addr_str)
    print("Peripheral: " + addr_to_str(p_addr))

    # create storage partition
    storage_bytes = periph_storage_partition(
        p_addr, p_irk, c_addr, c_irk, ltk, spacekey)

    addr_hex = binascii.hexlify(p_addr[::-1]).decode()

    # create merged hex file for easy programming
    storage = IntelHex()
    # partition address from DTS
    storage[0x32000:0x38000] = list(storage_bytes)
    # storage.tofile("storage_%s.hex" % addr_hex, format="hex")
    coin = IntelHex("coin.hex")
    coin.merge(storage, overlap="replace")
    coin[0x10001208:0x10001208 + 4] = [0x00] * \
        4  # enable Access Port Protection
    coin.tofile("coin_%s.hex" % addr_hex, format="hex")
