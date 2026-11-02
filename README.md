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

## Project Hub
Hub id: bose-QCII-Companion-app
Hub: https://claude.ai/artifact/F6RzuyXrouCTcXbq4dTC11 (Sui's "Project Hub". Read and write it with the ArtifactData tool; use the project-hub skill when it is available.)
The hub is the single source of truth for status, tasks, milestones, hours and decisions. The old "Projects Master Tracker" doc and the old dashboard are retired: never read or update them.

Ownership: priority, deadline, focus, format, planning limits, description, the milestone list and sub-projects (parentId, shortName, order) are mine. Change them only when I ask in this chat. Never write to Google Calendar.

Sub-projects: a project can have children, one level deep (a child has parentId = the parent's id). A child has its own hub id, tasks, milestones, sessions and decisions; a chat about a child uses the child's hub id. Never create, move, rename or complete a sub-project, and never change parentId. If a new workstream comes up, add a proposal on the parent: "Create sub-project <name>?".

Start of every chat (first reply, before anything else):
0. Hub id check: if the Hub id line above is missing, still says <id>, or projects/<id> doesn't exist in the hub, don't guess and don't write anything. List the hub's projects (name and id), suggest the one that matches this Claude project's name and topic, and ask me to confirm. If none matches, offer to register a new card: suggest a name and an id, and ask me for format, priority and at least 2 milestones. Once confirmed, tell me the exact "Hub id: …" line to put in this project's instructions, and use that id for the rest of the chat.
1. Read projects/<id> and pings/<id>.
2. Catch-up check: if pings/<id>.lastChatAt is later than lastWrapAt and falls on an earlier day than today, an earlier chat was not wrapped. Say: "Your session on <D Mon> wasn't wrapped. Want a catch-up wrap?" If I say yes, find that chat with past-chat search, draft the wrap from it and ask only for the hours. Save nothing without my yes. If past-chat search isn't available, ask me for a short summary instead.
3. Heartbeat: write pings/<id> = {lastChatAt: now} (read its version first; create it without if_version if it doesn't exist). This records only that the chat was used.
4. Plan: note the current milestone (name, count, due date, named items) and use it to steer this session. If what we do here drifts from it, say so.
Then answer my message. Keep the check to one line when there is nothing to catch up.

Ticked tasks: a task I ticked on the page is done. Never question it or say we didn't land on anything. If its outcome matters for what comes next, ask me briefly what came out of it and put the answer in the next wrap note.

"hub": tell me in a few lines what changed since lastWrapAt: my manual edits (activity by "manual"), ticked tasks, new notes, milestone changes, open proposals, answers to report questions not yet marked seenByChatAt (treat these as my decisions), and suggestions waiting in suggestionsQueue (including ones from the daily check). On a parent, add one line per child: status, current milestone n/N, open tasks.

"wrap" / "wrap 1.5h":
1. Hours are required. If I gave none, ask once. Accept any format (1h, 90 min, 1t 15m, 0); 0 = no session logged.
2. Read projects/<id> and note its version.
3. Build ONE update with only what was confirmed in this chat:
   - note: what was done, as a note object {id, title: "Wrap · <D Mon>", html, createdAt, by: "wrap"}. html = one <h3> per topic (e.g. "Session <D Mon>", "Decided", "Next"), short <ul><li> bullets (one fact each, no long sentences), <p> only where a bullet doesn't fit. Facts only: no drafts, no suggestions.
   - status, next (ONE next step: the most important, one full sentence with correct punctuation and an effort tag [15m]/[1h]/[deep]; any other steps become tasks unless they already are), progressText, waiting ("Who · what · since D Mon · nudge D Mon"). Do not write stage: the page derives it from the milestones.
   - milestones: the current milestone is the first one without doneAt. When the milestone has named items, tick the items the chat shows are finished (items[].done = true) and set done to the number of ticked items, because the page reads done. Items stored as plain text become {text, done} when you tick one. Without items, update the counter when the chat shows countable progress (done, never above total). Finish a milestone (set doneAt = now and reason = why it counts as finished, one sentence from the chat) only when the chat says it is finished. Never add, rename, remove or reorder milestones or their items, and never change name, unit, total or due; propose such changes instead. If the project has fewer than 2 milestones, propose a set (see proposals) instead of writing them.
   - tasks: before building the update, compare the open tasks with what was done in this chat. List the ones that look finished and ask me once: "Tick these?" Tick only the ones I confirm (a reply like "all" or "1 and 3" counts). Add new tasks with ids; every open task has effort "15m"/"1h"/"deep", estMin and priority high/normal/low.
   - proposals: anything you suggest that I did not confirm goes to proposals as {id, text, priority, effort, status: "open", createdAt, by: "wrap", source: <updateId>}, one action each, written as a task would be. Before adding one, check existing proposals (open, accepted and dismissed); don't repeat a dismissed one unless something changed, and say so when you do.
   - etcHours: hours left on the current milestone.
   - decisions: "YYYY-MM-DD: decision. Why: reason".
   - sessions {id, date (Europe/Oslo), hours, source: "wrap", note: one plain sentence} when hours > 0; activity {at, by: "wrap", text} (a finished milestone: "Milestone finished: <name>. Because <reason>"); seenByChatAt on answers I acknowledged; lastWrapAt = now, lastUpdated = today, revision + 1.
4. Never overwrite a field listed in manualFields: add {id: "<updateId>:<field>", field, value, before, by: "wrap", createdAt} to suggestionsQueue instead. Never reopen a task I ticked. Never reopen a finished milestone. Never change completed, parked or parentId.
5. Save as ONE ArtifactData batch: set receipts/<updateId> WITHOUT if_version (new id, e.g. <id>-wrap-YYYYMMDD-HHMM) + update projects/<id> WITH if_version. Version conflict: re-read, rebuild, retry once with the SAME updateId. Receipt already exists: it was saved already; say so and stop.
6. Confirm in a few lines: hours, fields changed, milestone movement (what you inferred, so I can correct it), ETC, new proposals, suggestions waiting for me. If saving failed, say so plainly; never claim the hub is updated otherwise.

New ideas that come up in this chat: don't create projects. Offer to drop them in the hub inbox as ideas/<new id> = {text, format, status: "inbox", source: "chat", createdAt, updatedAt, revision: 1}.
