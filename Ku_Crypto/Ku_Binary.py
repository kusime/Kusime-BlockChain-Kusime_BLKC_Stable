import binascii


def string2_utf8_bin(string: str):
    return string.encode("utf-8")


def bin2hex(binary):
    return binascii.hexlify(binary).decode('ascii')


def hex2bin(hex_string: str):
    # wrap with str
    return binascii.unhexlify(str(hex_string))
