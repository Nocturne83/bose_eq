"""Hush connection test for Bose QC Ultra Headphones (2nd Gen) on Windows.

READ-ONLY: this script only asks the headphones questions. It never
changes a setting, never installs anything and never uses the internet.

What it does:
  1. Opens a Bluetooth connection (RFCOMM, channel 2) to the MAC address
     you give it.
  2. Sends seven "GET" (read) requests: product name, firmware, battery,
     current mode, noise-cancelling level, EQ and voice prompts.
  3. Prints what came back, in plain words where possible and as raw
     hex bytes always, so the results can be analysed afterwards.

Usage (in Windows PowerShell or Command Prompt, NOT in WSL):
    py connection_test.py AA:BB:CC:DD:EE:FF
    py connection_test.py AA:BB:CC:DD:EE:FF --channel 8     (try another channel)

Only the Python standard library is used.

Protocol facts (packet layout, channel 2, function addresses) are taken
from bosectl by Aaron Bockelie (https://github.com/aaronsb/bosectl),
MIT License, Copyright (c) Aaron Bockelie. No bosectl code is copied.
"""

import argparse
import platform
import re
import socket
import sys
import time

OP_GET = 1
OP_NAMES = {0: "SET", 1: "GET", 2: "SETGET", 3: "STATUS", 4: "ERROR",
            5: "START", 6: "RESULT", 7: "PROCESSING"}
ERROR_NAMES = {0: "Unknown", 1: "Length", 2: "Checksum", 3: "FblockNotSupported",
               4: "FuncNotSupported", 5: "AuthRequired", 6: "InvalidData",
               7: "DataUnavailable", 8: "Runtime", 9: "Timeout", 10: "InvalidState"}
MODE_NAMES = {0: "Quiet", 1: "Aware", 2: "Immersion", 3: "Cinema"}

# (label, function block, function id) - all read-only GET requests.
QUERIES = [
    ("Product name", 1, 2),
    ("Firmware", 0, 5),
    ("Battery", 2, 2),
    ("Current mode", 31, 3),
    ("Noise cancelling level", 1, 5),
    ("Equalizer", 1, 7),
    ("Voice prompts", 1, 3),
]


def packet(fblock, func, op, payload=b""):
    return bytes([fblock, func, op & 0x0F, len(payload)]) + payload


def split_replies(data):
    out, pos = [], 0
    while pos + 4 <= len(data):
        fb, fn, op, ln = data[pos], data[pos + 1], data[pos + 2] & 0x0F, data[pos + 3]
        if pos + 4 + ln > len(data):
            break
        out.append((fb, fn, op, data[pos + 4:pos + 4 + ln]))
        pos += 4 + ln
    return out


def explain(label, payload):
    try:
        if label == "Product name":
            return payload[1:].decode("utf-8", "replace")
        if label == "Firmware":
            return payload.decode("ascii", "replace")
        if label == "Battery":
            return "%d%%" % payload[0]
        if label == "Current mode":
            return MODE_NAMES.get(payload[0], "custom mode slot %d" % payload[0])
        if label == "Noise cancelling level":
            return "level %d of %d (0 = most cancelling)" % (payload[1], payload[0] - 1)
        if label == "Equalizer":
            names = {0: "Bass", 1: "Mid", 2: "Treble"}
            parts = []
            for i in range(0, len(payload) - 3, 4):
                cur = payload[i + 2]
                cur = cur - 256 if cur > 127 else cur
                parts.append("%s %+d" % (names.get(payload[i + 3], "band%d" % payload[i + 3]), cur))
            return ", ".join(parts)
    except (IndexError, ValueError):
        pass
    return "(not decoded)"


def recv_all(sock, wait=0.6):
    data = b""
    sock.settimeout(3.0)
    try:
        data = sock.recv(4096)
    except socket.timeout:
        return data
    sock.settimeout(wait)
    try:
        while True:
            more = sock.recv(4096)
            if not more:
                break
            data += more
    except (socket.timeout, BlockingIOError):
        pass
    return data


def main():
    ap = argparse.ArgumentParser(description="Read-only connection test for Bose QC Ultra 2.")
    ap.add_argument("mac", help="Bluetooth address, e.g. AA:BB:CC:DD:EE:FF")
    ap.add_argument("--channel", type=int, default=2, help="RFCOMM channel (default 2)")
    args = ap.parse_args()

    mac = args.mac.strip().upper().replace("-", ":")
    if not re.fullmatch(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", mac):
        sys.exit("That doesn't look like a Bluetooth address. Expected AA:BB:CC:DD:EE:FF.")

    print("Hush connection test (read-only)")
    print("Python %s on %s %s" % (platform.python_version(), platform.system(), platform.release()))
    if not hasattr(socket, "AF_BLUETOOTH") or not hasattr(socket, "BTPROTO_RFCOMM"):
        sys.exit("RESULT: This Python has no Bluetooth socket support. "
                 "Run it with Windows Python (py), not inside WSL.")

    print("Connecting to %s on channel %d ..." % (mac, args.channel))
    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    sock.settimeout(8.0)
    try:
        sock.connect((mac, args.channel))
    except OSError as e:
        sock.close()
        sys.exit("RESULT: Could not connect (%s).\n"
                 "Check: headphones on and paired with this PC, Bose app closed on your phone, "
                 "and the address is right." % e)
    print("Connected.\n")

    time.sleep(0.5)
    greeting = recv_all(sock, wait=0.3)
    if greeting:
        print("Device said on connect: %s\n" % greeting.hex(" "))

    ok = 0
    for label, fb, fn in QUERIES:
        try:
            sock.send(packet(fb, fn, OP_GET))
            time.sleep(0.2)
            data = recv_all(sock)
        except OSError as e:
            print("%-24s FAILED: %s" % (label, e))
            continue
        replies = [r for r in split_replies(data) if r[0] == fb and r[1] == fn]
        if not replies:
            print("%-24s no matching reply. Raw: %s" % (label, data.hex(" ") or "(nothing)"))
            continue
        _, _, op, payload = replies[0]
        if op == 4:
            code = payload[0] if payload else -1
            print("%-24s ERROR %s. Raw: %s" % (label, ERROR_NAMES.get(code, code), data.hex(" ")))
            continue
        ok += 1
        print("%-24s %s" % (label, explain(label, payload)))
        print("%-24s raw [%d.%d %s]: %s" % ("", fb, fn, OP_NAMES.get(op, op), payload.hex(" ")))

    sock.close()
    print("\nRESULT: %d of %d questions answered." % (ok, len(QUERIES)))
    print("Copy everything above and send it back. It contains no personal data "
          "except your headphones' name and Bluetooth address (you can blank those out).")


if __name__ == "__main__":
    main()
