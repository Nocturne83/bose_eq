"""Hush write test for Bose QC Ultra Headphones (2nd Gen) on Windows.

THIS SCRIPT BRIEFLY CHANGES SETTINGS, THEN PUTS THEM BACK.
It asks you to type YES before it changes anything.

What it does:
  1. Reads and remembers your current mode and EQ.
  2. Mode test: switches to Quiet, reads it back, then switches back to
     your original mode.
  3. EQ test: raises Bass by 1 step, reads it back, then restores the
     original Bass value. (A tiny, short change in bass you might hear.)
  4. Reads mode and EQ again to confirm everything is back as it was.

Whatever happens, even if a step fails, the script tries to restore your
original mode and EQ before it exits. If anything is left changed, set it
back in the Bose app: this script prints your original values.

It uses only "SETGET" and "START" commands, which bosectl documents as
working without Bose cloud login on this model. No internet is used.

Usage (Windows PowerShell, not WSL):
    python write_test.py E458BCC12D4A

Protocol facts (channel 2, addresses [31.3] mode and [1.7] EQ, packet
layout) are from bosectl by Aaron Bockelie
(https://github.com/aaronsb/bosectl), MIT License,
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
BAND_NAMES = {0: "Bass", 1: "Mid", 2: "Treble"}
MODE, EQ = (31, 3), (1, 7)


class Link:
    def __init__(self, mac, channel):
        self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.sock.settimeout(8.0)
        self.sock.connect((mac, channel))
        time.sleep(0.5)
        self._read(0.3)  # discard anything sent on connect

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
        """Send one packet; return (op, payload, raw) of the reply from addr, or None."""
        self._read(0.05)  # drop stale notifications
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
            body = data[pos + 4:pos + 4 + ln]
            if (rfb, rfn) == addr:
                return rop, body, data
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
    if r and r[0] != OP_ERROR and r[1]:
        return r[1][0]
    return None


def read_eq(link):
    r = link.ask(EQ, OP_GET)
    if not r or r[0] == OP_ERROR:
        return None
    body, bands = r[1], {}
    for i in range(0, len(body) - 3, 4):
        cur = body[i + 2]
        bands[body[i + 3]] = cur - 256 if cur > 127 else cur
    return bands


def eq_text(bands):
    if not bands:
        return "unknown"
    return ", ".join("%s %+d" % (BAND_NAMES.get(b, b), v) for b, v in sorted(bands.items()))


def mode_text(idx):
    return "unknown" if idx is None else MODE_NAMES.get(idx, "custom slot %d" % idx)


def set_mode(link, idx):
    return link.ask(MODE, OP_START, bytes([idx, 0]))  # 0 = no voice announcement


def set_band(link, band, value):
    return link.ask(EQ, OP_SETGET, bytes([value & 0xFF, band]))


def main():
    ap = argparse.ArgumentParser(description="Write test (changes and restores settings).")
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

    print("Hush write test. Connecting to %s ..." % mac)
    try:
        link = Link(mac, args.channel)
    except OSError as e:
        sys.exit("Could not connect (%s). Headphones on? Bose app on phone closed?" % e)

    orig_mode, orig_eq = read_mode(link), read_eq(link)
    print("\nYour current settings (write these down if you like):")
    print("  Mode: %s" % mode_text(orig_mode))
    print("  EQ:   %s" % eq_text(orig_eq))
    if orig_mode is None or not orig_eq or 0 not in orig_eq:
        link.close()
        sys.exit("\nRESULT: Could not read current settings, so nothing was changed.")

    print("\nThis test will switch to Quiet and back, and nudge Bass by 1 step and back.")
    if input("Type YES to continue: ").strip() != "YES":
        link.close()
        sys.exit("Cancelled. Nothing was changed.")

    results = {}
    try:
        # Mode test
        target = 0 if orig_mode != 0 else 1  # Quiet, or Aware if already Quiet
        print("\n[Mode] Switching to %s ..." % mode_text(target))
        r = set_mode(link, target)
        print("  reply: %s" % describe(r))
        time.sleep(2.0)
        now = read_mode(link)
        print("  mode is now: %s" % mode_text(now))
        results["mode"] = now == target

        # EQ test
        bass = orig_eq[0]
        new_bass = bass + 1 if bass < 10 else bass - 1
        print("\n[EQ] Setting Bass %+d -> %+d ..." % (bass, new_bass))
        r = set_band(link, 0, new_bass)
        print("  reply: %s" % describe(r))
        time.sleep(1.0)
        now_eq = read_eq(link)
        print("  EQ is now: %s" % eq_text(now_eq))
        results["eq"] = bool(now_eq) and now_eq.get(0) == new_bass
    finally:
        print("\n[Restore] Putting everything back ...")
        r1 = set_mode(link, orig_mode)
        time.sleep(1.5)
        r2 = set_band(link, 0, orig_eq[0])
        time.sleep(1.0)
        end_mode, end_eq = read_mode(link), read_eq(link)
        link.close()
        print("  mode restore reply: %s" % describe(r1))
        print("  bass restore reply: %s" % describe(r2))
        print("  Mode now: %s   (was %s)" % (mode_text(end_mode), mode_text(orig_mode)))
        print("  EQ now:   %s   (was %s)" % (eq_text(end_eq), eq_text(orig_eq)))
        restored = end_mode == orig_mode and end_eq == orig_eq
        print("  Restored: %s" % ("YES" if restored else "NO - please check in the Bose app"))

    print("\nRESULT: mode change %s, EQ change %s." % (
        "WORKS" if results.get("mode") else "FAILED",
        "WORKS" if results.get("eq") else "FAILED"))
    print("Copy everything above and send it back.")


if __name__ == "__main__":
    main()
