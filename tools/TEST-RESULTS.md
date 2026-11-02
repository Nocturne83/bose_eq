# Hardware test results

Device: Bose QC Ultra Headphones (2nd Gen), colour Driftwood Sand, Windows product ID `PID&4082`
Firmware: 10.12.14+gde0210e (bosectl was tested on 8.2.20)
PC: Windows 11 Enterprise, Intel Core i7-1355U, Windows Python from PowerShell (not WSL)
Connection: Bluetooth RFCOMM, channel 2, Python standard library only

## 2 November 2026 – read test (`connection_test.py`)

Result: 7 of 7 answered.

| Question | Address | Reply | Decoded |
| --- | --- | --- | --- |
| Product name | 1.2 | `00 53 75 69 27 73 20 51 43 20 55 6c 74 72 61 20 49 49` | Sui's QC Ultra II (user-set name) |
| Firmware | 0.5 | ASCII | 10.12.14+gde0210e |
| Battery | 2.2 | `1e ff ff 00` | 30% |
| Current mode | 31.3 | `01` | Aware |
| Noise cancelling | 1.5 | `0b 0a 03` | level 10 of 10, where 0 = most cancelling |
| EQ | 1.7 | `f6 0a 02 00 f6 0a 05 01 f6 0a 02 02` | 3 bands, range −10 to +10: Bass +2, Mid +5, Treble +2 |
| Voice prompts | 1.3 | `41 00 00 81 02 00 00` | off, US English (confirmed by owner) |

## 2 November 2026 – write test (`write_test.py`)

Result: mode change works, EQ change works, settings restored.

| Action | Command | Reply |
| --- | --- | --- |
| Mode Aware → Quiet | START 31.3 `00 00` | RESULT `1f 03 06 01 00` |
| Bass +2 → +3 | SETGET 1.7 `03 00` | STATUS with full EQ, Bass +3 |
| Mode back to Aware | START 31.3 `01 00` | RESULT `1f 03 06 01 01` |
| Bass back to +2 | SETGET 1.7 `02 00` | STATUS with full EQ, Bass +2 |

No Bose cloud login was needed.

## Not tested yet

Noise level 0–10, wind block, spatial audio and custom modes (all via AudioSettings 31.10 or ModeConfig 31.6), voice prompts on/off, shortcut button, auto-pause, multipoint.

## Design notes from the tests

- The device's noise scale is reversed (0 = most cancelling). Hush shows 10 = most cancelling and converts internally.
- The device reports the user's own name, not the model name. Show both (own name large, model name small).
