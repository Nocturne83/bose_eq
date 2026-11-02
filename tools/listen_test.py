"""Hush listening test for Bose QC Ultra Headphones (2nd Gen).

THIS SCRIPT CHANGES SETTINGS, ONE STEP AT A TIME, THEN PUTS THEM BACK.
Each change stays on until you press Enter, so you can listen properly.
After each step it asks what you heard and prints a summary at the end.

Before you start: put the headphones on, play music, and if you can,
sit near some background noise (a fan, a running tap, a noisy video on
speakers). Noise cancelling is hard to hear in a quiet room.

Steps:
  1. Switch to Quiet mode, WITH Bose's voice announcement.
  2. Switch to Aware mode, WITH the voice announcement.
  3. Still in Aware: set the live noise level to maximum cancelling.
  4. Spatial audio on, head tracking (turn your head while listening).
  5. Extreme EQ: Bass +10, Treble -10 (very obvious; turn the volume down a bit).
  Then: restore your original mode, live settings and EQ, and check them.

Even if a step fails or you press Ctrl+C, it restores your original
settings before exiting. The script prints your originals first, so you
can also set them back in the Bose app if needed.

Usage (Windows PowerShell, not WSL):
    python listen_test.py E458BCC12D4A

Protocol facts (channel 2, [31.3] mode switch with announce flag,
[31.10] live audio settings, [1.7] EQ) are from bosectl by Aaron
Bockelie (https://github.com/aaronsb/bosectl), MIT License,
Copyright (c) Aaron Bockelie. No bosectl code is copied.
"""

import argparse
import re
import socket
import sys
import time

OP_GET, OP_SETGET, OP_ERROR, OP_START = 1, 2, 4, 5
OP_NAMES = {0: "SET", 1: "GET", 2: "SETGET", 3: "STATUS", 4: "ERROR",
            5: "START", 6: "RESULT", 7: "PROCESSING"}
ERROR_NAMES = {0: "Unknown", 1: "Length", 2: "Checksum", 3: "FblockNotSupported",
               4: "FuncNotSupported", 5: "AuthRequired", 6: "InvalidData",
               7: "DataUnavailable", 8: "Runtime", 9: "Timeout", 10: "InvalidState",
               15: "InvalidTransition", 20: "InsecureTransport"}
MODE_NAMES = {0: "Quiet", 1: "Aware", 2: "Immersion", 3: "Cinema"}
SPATIAL = {0: "off", 1: "room (still)", 2: "head (motion)"}
MODE, LIVE, EQ = (31, 3), (31, 10), (1, 7)


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


def read_mode(link):
    r = link.ask(MODE, OP_GET)
    return r[1][0] if r and r[0] != OP_ERROR and r[1] else None


def read_live(link):
    r = link.ask(LIVE, OP_GET)
    return list(r[1][:5]) if r and r[0] != OP_ERROR and len(r[1]) >= 5 else None


def read_eq(link):
    r = link.ask(EQ, OP_GET)
    if not r or r[0] == OP_ERROR:
        return None
    body, bands = r[1], {}
    for i in range(0, len(body) - 3, 4):
        cur = body[i + 2]
        bands[body[i + 3]] = cur - 256 if cur > 127 else cur
    return bands


def mode_text(i):
    return "unknown" if i is None else MODE_NAMES.get(i, "custom slot %d" % i)


def live_text(v):
    if not v:
        return "unknown"
    return ("noise level %d (app scale %d of 10), spatial %s, wind block %s, ANC %s"
            % (v[0], 10 - v[0], SPATIAL.get(v[2], v[2]), "on" if v[3] else "off",
               "on" if v[4] else "off"))


def eq_text(b):
    if not b:
        return "unknown"
    names = {0: "Bass", 1: "Mid", 2: "Treble"}
    return ", ".join("%s %+d" % (names.get(k, k), v) for k, v in sorted(b.items()))


def set_band(link, band, value):
    return link.ask(EQ, OP_SETGET, bytes([value & 0xFF, band]))


def listen(step_name, notes):
    heard = input("  Listen now. What did you hear? (type a few words, then Enter): ").strip()
    notes.append((step_name, heard or "(nothing typed)"))


def main():
    ap = argparse.ArgumentParser(description="Listening test (changes and restores settings).")
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

    print("Hush listening test. Connecting to %s ..." % mac)
    try:
        link = Link(mac, args.channel)
    except OSError as e:
        sys.exit("Could not connect (%s). Headphones on? Bose app on phone closed?" % e)

    o_mode, o_live, o_eq = read_mode(link), read_live(link), read_eq(link)
    print("\nYour current settings (write these down if you like):")
    print("  Mode: %s" % mode_text(o_mode))
    print("  Live: %s" % live_text(o_live))
    print("  EQ:   %s" % eq_text(o_eq))
    if o_mode is None or not o_live or not o_eq or len(o_eq) < 3:
        link.close()
        sys.exit("\nRESULT: Could not read all current settings, so nothing was changed.")

    print("\nPut the headphones on, play music, ideally with some background noise nearby.")
    if input("Type yes to start: ").strip().lower() not in ("yes", "y", "ja", "j"):
        link.close()
        sys.exit("Cancelled. Nothing was changed.")

    notes = []
    try:
        print("\n[1] Switching to Quiet, with voice announcement ...")
        print("  reply: %s" % describe(link.ask(MODE, OP_START, bytes([0, 1]))))
        time.sleep(1.5)
        print("  mode is now: %s" % mode_text(read_mode(link)))
        listen("1 Quiet + announcement", notes)

        print("\n[2] Switching to Aware, with voice announcement ...")
        print("  reply: %s" % describe(link.ask(MODE, OP_START, bytes([1, 1]))))
        time.sleep(1.5)
        print("  mode is now: %s" % mode_text(read_mode(link)))
        listen("2 Aware + announcement", notes)

        print("\n[3] Still in Aware: live noise level to MAXIMUM cancelling ...")
        cur = read_live(link) or list(o_live)
        v = [0, 0, cur[2], 0, 1]  # level 0 = max cancelling, wind off, ANC on
        print("  reply: %s" % describe(link.ask(LIVE, OP_SETGET, bytes(v))))
        time.sleep(1.0)
        print("  live is now: %s" % live_text(read_live(link)))
        listen("3 Aware + live max cancelling", notes)

        print("\n[4] Spatial audio ON, head tracking. Turn your head slowly ...")
        v[2] = 2
        print("  reply: %s" % describe(link.ask(LIVE, OP_SETGET, bytes(v))))
        time.sleep(1.0)
        print("  live is now: %s" % live_text(read_live(link)))
        listen("4 Spatial head tracking", notes)

        print("\n[5] Extreme EQ: Bass +10, Treble -10 (very obvious) ...")
        print("  bass reply:   %s" % describe(set_band(link, 0, 10)))
        print("  treble reply: %s" % describe(set_band(link, 2, -10)))
        time.sleep(1.0)
        print("  EQ is now: %s" % eq_text(read_eq(link)))
        listen("5 Extreme EQ", notes)
    except KeyboardInterrupt:
        print("\nStopped early.")
    finally:
        print("\n[Restore] Putting everything back ...")
        link.ask(MODE, OP_START, bytes([o_mode, 0]))
        time.sleep(1.5)
        link.ask(LIVE, OP_SETGET, bytes([o_live[0], 0, o_live[2], o_live[3], o_live[4]]))
        time.sleep(0.5)
        for band in (0, 1, 2):
            set_band(link, band, o_eq[band])
        time.sleep(1.0)
        e_mode, e_live, e_eq = read_mode(link), read_live(link), read_eq(link)
        link.close()
        print("  Mode: %s   (was %s)" % (mode_text(e_mode), mode_text(o_mode)))
        print("  Live: %s" % live_text(e_live))
        print("  was:  %s" % live_text(o_live))
        print("  EQ:   %s   (was %s)" % (eq_text(e_eq), eq_text(o_eq)))
        ok = e_mode == o_mode and e_eq == o_eq and e_live and e_live[0] == o_live[0] \
            and e_live[2:] == o_live[2:]
        print("  Restored: %s" % ("YES" if ok else "NO - please check in the Bose app"))

    print("\nWHAT YOU HEARD")
    for step, heard in notes:
        print("  %-30s %s" % (step, heard))
    print("\nCopy everything above and send it back.")


if __name__ == "__main__":
    main()
