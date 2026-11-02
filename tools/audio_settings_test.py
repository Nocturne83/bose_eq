"""Hush noise / wind / spatial test for Bose QC Ultra Headphones (2nd Gen).

THIS SCRIPT BRIEFLY CHANGES SETTINGS, THEN PUTS THEM BACK.
It asks you to type yes before it changes anything.

It tests the "live audio settings" register [31.10], which holds five
values: noise-cancelling level (0-10, where 0 = MOST cancelling),
auto-CNC, spatial audio (0 off, 1 room/still, 2 head/motion),
wind block (on/off) and ANC (on/off).

Steps, about 3 seconds each so you can hear them (play some music):
  1. Noise level: moves it to a clearly different level.
  2. Wind block: flips it on or off.
  3. Spatial audio: switches it to "room" (or off, if it is already on).
  4. Restores your original five values and checks them.

Even if a step fails, it restores your original settings before exiting.
If anything is left changed, set it back in the Bose app: the script
prints your original values first.

Usage (Windows PowerShell, not WSL):
    python audio_settings_test.py E458BCC12D4A

Protocol facts (channel 2, register [31.10], its 5-byte layout, the
inverted noise scale, auto-CNC must be 0) are from bosectl by Aaron
Bockelie (https://github.com/aaronsb/bosectl), MIT License,
Copyright (c) Aaron Bockelie. No bosectl code is copied.
"""

import argparse
import re
import socket
import sys
import time

OP_GET, OP_SETGET, OP_ERROR = 1, 2, 4
OP_NAMES = {0: "SET", 1: "GET", 2: "SETGET", 3: "STATUS", 4: "ERROR",
            5: "START", 6: "RESULT", 7: "PROCESSING"}
ERROR_NAMES = {0: "Unknown", 1: "Length", 2: "Checksum", 3: "FblockNotSupported",
               4: "FuncNotSupported", 5: "AuthRequired", 6: "InvalidData",
               7: "DataUnavailable", 8: "Runtime", 9: "Timeout", 10: "InvalidState",
               15: "InvalidTransition", 20: "InsecureTransport"}
MODE_NAMES = {0: "Quiet", 1: "Aware", 2: "Immersion", 3: "Cinema"}
SPATIAL = {0: "off", 1: "room (still)", 2: "head (motion)"}
LIVE, MODE = (31, 10), (31, 3)


class Link:
    def __init__(self, mac, channel):
        self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.sock.settimeout(8.0)
        self.sock.connect((mac, channel))
        time.sleep(0.5)
        self._read(0.3)

    def _read(self, wait):
        data = b""
        self.sock.settimeout(wait)
        try:
            while True:
                more = self.sock.recv(4096)
                if not more:
                    break
                data += more
        except (socket.timeout, BlockingIOError):
            pass
        return data

    def ask(self, addr, op, payload=b""):
        self._read(0.05)
        fb, fn = addr
        self.sock.send(bytes([fb, fn, op & 0x0F, len(payload)]) + payload)
        time.sleep(0.25)
        self.sock.settimeout(3.0)
        try:
            data = self.sock.recv(4096)
        except socket.timeout:
            return None
        data += self._read(0.6)
        pos = 0
        while pos + 4 <= len(data):
            rfb, rfn, rop, ln = data[pos], data[pos + 1], data[pos + 2] & 0x0F, data[pos + 3]
            if (rfb, rfn) == addr:
                return rop, data[pos + 4:pos + 4 + ln], data
            pos += 4 + ln
        return None

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def describe(reply):
    if reply is None:
        return "no reply"
    op, body, raw = reply
    if op == OP_ERROR:
        code = body[0] if body else -1
        return "ERROR %s (raw %s)" % (ERROR_NAMES.get(code, code), raw.hex(" "))
    return "%s (raw %s)" % (OP_NAMES.get(op, op), raw.hex(" "))


def read_live(link):
    r = link.ask(LIVE, OP_GET)
    if r and r[0] != OP_ERROR and len(r[1]) >= 5:
        return list(r[1][:5])
    return None


def live_text(v):
    if not v:
        return "unknown"
    return ("noise level %d (app scale: %d of 10 cancelling), auto-CNC %s, spatial %s, "
            "wind block %s, ANC %s" % (v[0], 10 - v[0], "on" if v[1] else "off",
                                       SPATIAL.get(v[2], v[2]), "on" if v[3] else "off",
                                       "on" if v[4] else "off"))


def write_live(link, v):
    return link.ask(LIVE, OP_SETGET, bytes(v))


def step(link, label, new, check_index):
    print("\n[%s] writing: %s" % (label, live_text(new)))
    r = write_live(link, new)
    print("  reply: %s" % describe(r))
    time.sleep(3.0)
    now = read_live(link)
    print("  now:   %s" % live_text(now))
    return bool(now) and now[check_index] == new[check_index]


def main():
    ap = argparse.ArgumentParser(description="Noise/wind/spatial test (changes and restores).")
    ap.add_argument("mac", help="Bluetooth address, e.g. E458BCC12D4A")
    ap.add_argument("--channel", type=int, default=2)
    args = ap.parse_args()

    mac = args.mac.strip().upper().replace("-", ":")
    if re.fullmatch(r"[0-9A-F]{12}", mac):
        mac = ":".join(mac[i:i + 2] for i in range(0, 12, 2))
    if not re.fullmatch(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", mac):
        sys.exit("That doesn't look like a Bluetooth address.")
    if not hasattr(socket, "AF_BLUETOOTH"):
        sys.exit("This Python has no Bluetooth support. Use Windows Python in PowerShell, not WSL.")

    print("Hush noise / wind / spatial test. Connecting to %s ..." % mac)
    try:
        link = Link(mac, args.channel)
    except OSError as e:
        sys.exit("Could not connect (%s). Headphones on? Bose app on phone closed?" % e)

    mode = link.ask(MODE, OP_GET)
    mode_idx = mode[1][0] if mode and mode[0] != OP_ERROR and mode[1] else None
    orig = read_live(link)
    print("\nYour current settings (write these down if you like):")
    print("  Mode: %s" % (MODE_NAMES.get(mode_idx, "custom slot %s" % mode_idx)))
    print("  Live: %s" % live_text(orig))
    if not orig:
        link.close()
        sys.exit("\nRESULT: Could not read the live audio settings, so nothing was changed.")

    print("\nPut on the headphones and play some music. This test changes the noise level,")
    print("wind block and spatial audio for about 3 seconds each, then restores them.")
    if input("Type yes to continue: ").strip().lower() not in ("yes", "y", "ja", "j"):
        link.close()
        sys.exit("Cancelled. Nothing was changed.")

    base = list(orig)
    base[1] = 0  # auto-CNC must be 0 when writing (firmware rejects 1)
    results = {}
    try:
        v = list(base)
        v[4] = 1                         # ANC on, so the level is audible
        v[3] = 0                         # wind block off, so the level is audible
        v[0] = 0 if orig[0] >= 5 else 10  # jump to the other end of the scale
        results["noise level"] = step(link, "Noise level", v, 0)

        w = list(v)
        w[3] = 0 if v[3] else 1
        results["wind block"] = step(link, "Wind block", w, 3)

        s = list(v)
        s[2] = 1 if orig[2] == 0 else 0
        results["spatial audio"] = step(link, "Spatial audio", s, 2)
    finally:
        print("\n[Restore] Writing your original values back ...")
        r = write_live(link, orig)
        print("  reply: %s" % describe(r))
        time.sleep(1.5)
        end = read_live(link)
        if end != orig and orig[1] != 0:
            print("  first restore didn't match; retrying with auto-CNC off ...")
            write_live(link, base)
            time.sleep(1.5)
            end = read_live(link)
        link.close()
        print("  Now: %s" % live_text(end))
        print("  Was: %s" % live_text(orig))
        print("  Restored: %s" % ("YES" if end == orig else "NO - please check in the Bose app"))

    print("\nRESULT: " + ", ".join("%s %s" % (k, "WORKS" if ok else "FAILED")
                                   for k, ok in results.items()) + ".")
    print("Did you hear the changes? Copy everything above and send it back, with what you heard.")


if __name__ == "__main__":
    main()
