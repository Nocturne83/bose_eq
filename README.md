# bose_eq

Handoff: Bose QC35 II noise-cancelling control for Windows
Written 1 November 2026. Paste this whole file into a new Claude conversation to pick up where we left off.

Who I am and what I want
I'm not a developer and I'm learning the vocabulary as I go. Please explain terms in plain language.
I own Bose QuietComfort 35 II headphones and want a full Windows companion app for them, so I don't need the Bose phone app.
I found an existing project that handles noise cancelling (High / Low / Off). I want to build on it instead of starting from scratch, but it's only the starting point.
I have GitHub and Python installed on my personal machine.
What I want the finished app to do
Much more than noise cancelling, for example:
EQ (equalizer) settings
Saving and loading presets (named combinations of settings, such as "Office" or "Flight")
Other settings the headphones expose (to be discovered)
A UI that looks and feels like the Bose phone app: a similar layout, flow and ease of use, polished rather than a developer-style debug window.
No copyright or trademark infringement. "Looks and feels like" means inspired by the phone app, not a copy of it.
Open questions and guardrails for these goals
Check what the QC35 II actually supports before designing features. I'm not sure the QC35 II has adjustable EQ in hardware at all. My understanding is that its phone app (Bose Connect) doesn't offer EQ, and adjustable EQ arrived on newer models in the Bose Music app. Verify this, for example against the bosectl project and other public protocol research. Features the headphones don't support could only be faked on the PC side, for example with system-wide audio EQ software such as Equalizer APO, and would only work while listening through the PC.
Other settings the QC35 II is publicly known to expose include battery level, device name, the auto-off timer, voice-prompt language and connected devices. Confirm which ones work.
"Inspired by" vs "copied" (general guidance, not legal advice):
OK: a similar layout, a similar flow (device card → noise-cancelling control → settings), and a clean, modern style.
Not OK: copying Bose's logos, icons, images, illustrations or exact screen designs; taking assets out of the Bose app; or calling the app "Bose" anything. Describing it as "for Bose QC35 II" is normally fine.
Draw our own icons or use openly licensed icon sets, and use our own name and colours.
A rich, phone-app-like UI may be easier to build with a more modern UI toolkit than Tkinter (for example PySide6/Qt, or a web-style UI). We can decide this together.
The project we found
Repo: https://github.com/gustavoperezc/boseqcwindows
Author: Gustavo Perez, a developer from Venezuela, who posted it on Reddit as a free, non-commercial personal project.
It's a small Python desktop app with a simple window (built with Tkinter, which comes with Python). It talks to the headphones over Bluetooth.
What it does (per the README and the code)
Finds paired Bose headphones from Windows' Bluetooth device list. You can also type the headphones' Bluetooth address (MAC) by hand.
Connects over Bluetooth "RFCOMM" (a serial-style connection) on channel 8, the known channel for the QC35.
Sends tiny Bose commands ("BMAP" protocol, worked out by public reverse-engineering):
Startup handshake: 00 01 01 00
ANC High: 01 06 02 01 01
ANC Low: 01 06 02 01 03
ANC Off: 01 06 02 01 00
(Value 02 = "wind" mode also exists but isn't exposed in the buttons.)
A global keyboard shortcut (default Ctrl+Alt+N) cycles High → Low → Off while the app is running.
Writes a debug log to logs/bose_qc35_anc.log and settings to config.json.
Run it with python main.py. No extra packages are needed. pybluez2 is optional as a fallback.
Files in the repo
File	What it is
main.py	Starts the app and sets up logging
app_gui.py	The window, buttons and background work
bluetooth_client.py	Bluetooth connection and device discovery
bose_protocol.py	Builds and reads the Bose commands. This is the hard, valuable part.
hotkey_manager.py	Registers the Ctrl+Alt+N shortcut with Windows
config.json	Saved hotkey setting
tests/test_bose_protocol.py	Small tests that don't need headphones
__pycache__/	Compiled leftovers from the author's PC. Delete these.
BoseQC35AncControl-portable.zip	11.5 MB prebuilt program. Not reviewed. Don't use it.
Safety review findings
All Python source files were read line by line. Nothing was run.

Verdict: the source code looks safe and does what it claims.

No internet access anywhere. It never contacts a server or website, so no data leaves the PC.
The only system command is a fixed, read-only PowerShell query (Get-PnpDevice -Class Bluetooth) that lists paired Bluetooth devices. It uses -ExecutionPolicy Bypass, which is harmless here because the command text is fixed in the code.
The hotkey uses the standard Windows RegisterHotKey function for a single key combination. It is not a keylogger.
It writes files only next to the app: the log and config.json.
Remaining risks and cautions:

The prebuilt .zip can't be verified to match the source code. Run from source instead.
The __pycache__ .pyc files are unreadable compiled files. Delete them before running.
The author's account is new (created Jan 2026; 1 repo, 2 stars, 0 followers). That isn't a red flag in itself, but it has no track record.
If the author pushes new changes later, re-check them before pulling them in. The review above covers the state of the code as of commit 7a00d2a (11 June 2026).
The licensing catch (important before building on it)
The repo has no license. Legally that means "all rights reserved": we may not copy, modify or redistribute it without permission, even though it's public.
That's why we opt for Personal use only while waiting: low risk in practice, but don't publish changes.
Write our own version from scratch. The Bose command format itself isn't owned by anyone. Another public project, bosectl (https://github.com/aaronsb/bosectl), is credited in the README and may have a proper license; check it.
Vocabulary covered so far
Repo (repository): a project folder plus its full change history, stored on a site like GitHub.
Commit: one saved change in that history.
Clone: download a copy of a repo to your computer.
Fork: your own copy of someone's repo on GitHub that you can change freely.
README: the front-page explanation file.
License: the legal terms that say what others may do with the code.
Suggested next steps (in the personal account)
Decide on the license route above, and message the author if you choose to ask.
Fork or clone the repo, delete __pycache__/ and the .zip, and run python main.py with the headphones paired and powered on.
Confirm it works with my QC35 II: connect, then try High / Low / Off.
Research which features the QC35 II really supports over Bluetooth (EQ, battery, auto-off, etc.). See "Open questions" above.
Plan the full app with me: feature list, preset design, and a UI style inspired by (not copied from) the Bose phone app.
Further ideas raised so far:
Start automatically and live in the system tray instead of a window
Auto-connect to the headphones without clicking Connect
Show the current mode, and maybe add "wind" mode
Package it as a simple app I can double-click, built myself from the reviewed source
Note about the earlier session
The safety review was done in a corporate Claude instance that couldn't see my own GitHub or Python setup. 
