# Meeting Copilot — AI Meeting Assistant

[Português](README.md) | [English](README.en.md)

A Python (PySide6) desktop application that follows meetings in real time:
it transcribes audio locally (faster-whisper) and suggests talking points
using a language model — cloud-based (OpenAI) or fully local (Ollama) —
with transparent disclosure to meeting participants.

## How it works

- **Audio capture**: two independent streams — your microphone ("You") and
  system/loopback audio ("Others", e.g. the other participants in a
  Zoom/Meet/Teams call).
- **Transcription**: 100% local via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
  — audio is never sent to any server for transcription.
- **Suggestions**: the recent transcript is sent to a language model to
  generate short, actionable talking points (clarifying questions, risks,
  next steps). Two options, chosen in Settings:
  - **OpenAI (cloud)** — requires an API key and credits on the account.
  - **Ollama (local, no API)** — runs an open-source LLM on your own
    machine, sending no text to third parties and at no per-use cost.
- **Transparency**: while a meeting is active, an always-visible banner is
  shown on screen (useful if you're screen-sharing) informing participants
  that an AI is assisting the meeting, with a button to copy a ready-made
  disclosure notice to paste into the chat.
- **No suggestions is also an option**: if you configure neither OpenAI nor
  Ollama, the app still works normally with local transcription only — the
  suggestions panel simply stays empty.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Interface: performance mode and language

The toolbar has two switches:

- **Light / Performance** — instantly toggles between a light transcription
  profile (`tiny` model, larger chunks, fewer CPU threads) and a
  performance profile (`small` model, smaller chunks, lower latency). If a
  meeting is running, capture and the model are automatically restarted
  with the new profile. A third "Balanced" profile is available in
  Settings.
- **PT / EN** — switches the entire interface language (titles, buttons,
  status messages, transparency banner) instantly, with no app restart.
  The preference is saved and restored the next time the app is launched.

> Note: this interface language is independent of the **transcription
> language** (Settings → "Transcription language"), which controls which
> language Whisper should recognize speech in.

## Using Ollama (fully local suggestions)

1. Install Ollama: <https://ollama.com>
2. Pull a model, for example:
   ```bash
   ollama pull llama3.1        # good quality/size balance
   ollama pull qwen2.5:3b      # lighter, for weak hardware
   ```
3. In **Settings**, switch "Suggestion engine (AI)" to
   **Ollama (local, no API)** and confirm the server URL (default
   `http://localhost:11434/v1`) and the pulled model's name.
4. No API key is required in this mode.

## Optimizing for weak hardware

The app's biggest CPU cost is local transcription (Whisper). Adjustments,
from most to least impactful:

1. **Capture only the microphone.** Without system audio, the model runs
   once per chunk instead of twice — cutting transcription CPU usage in
   half. Leave "System audio" as "None" in Settings.
2. **Use the Light switch in the toolbar** (or the "Light" profile in
   Settings) — `tiny` model, 10s chunks, 2 CPU threads. Recommended for
   weak laptops, mini PCs, or when the app runs alongside the video call
   itself.
3. **Increase the audio chunk duration.** Larger chunks mean fewer Whisper
   calls per minute (less fixed overhead per call), at the cost of the
   transcript taking longer to appear on screen.
4. **Limit CPU threads.** By default (`0`) transcription uses all
   available cores, which can make the interface and the rest of the
   system stutter during transcription on machines with few cores.
   Lowering it to 1–2 threads leaves cores free for the rest of the
   system, at the cost of slower transcription.
5. **`whisper_compute_type: int8`** (default) is already the lowest
   memory/CPU setting for running on CPU — no need to change it unless you
   have an NVIDIA GPU (in that case, see `whisper_device` in the config
   file).
6. **If using Ollama, prefer a small model** (e.g. `qwen2.5:3b` or
   `llama3.2:3b`) — it runs at the same time as Whisper and competes with
   it for CPU/RAM.

Transcription uses VAD (voice activity detection) to automatically skip
silent stretches — most of the real CPU cost only happens while someone is
actually speaking.

## Audio setup on Linux (PipeWire/PulseAudio)

To capture other participants' audio (loopback), the app lists available
input devices and tries to auto-detect a "monitor" device (e.g. `Monitor
of Built-in Audio`). If none shows up:

```bash
pactl list sources short   # look for a source ending in ".monitor"
```

If none exists, you can enable one in PipeWire/PulseAudio (e.g. via
`pavucontrol`, "Recording" tab, or by creating a monitor sink). Select the
microphone and system devices in the app's **Settings**.

## Usage

```bash
python -m meeting_copilot
```

1. Open **Settings**, choose the suggestion engine (OpenAI or Ollama) and
   provide what it needs (API key, or Ollama URL/model), the Whisper model
   size (start with `small` for a good speed/quality balance on CPU), and
   your audio devices.
2. Click **Start meeting**. The Whisper model loads (can take a few
   seconds), then audio capture and transcription begin.
3. The transparency banner appears automatically — use "Copy notice" to
   let participants know an AI is in use.
4. Talking points appear periodically in the right panel; use **Generate
   suggestions now** to force a refresh.
5. Use the **Light/Performance** and **PT/EN** switches in the toolbar at
   any time.
6. Click **End meeting** to stop everything.

## Privacy and ethics

- Transcription runs locally; audio is never sent to third parties.
- If you use the OpenAI engine, only transcript text snippets (not audio)
  are sent to generate suggestions. With the Ollama engine, not even that
  leaves your machine.
- The transparency banner is shown whenever capture is active — **use this
  tool ethically**: tell participants verbally or via chat that an AI is
  assisting the meeting before using it, especially on calls with third
  parties.
- The API key (when used) is stored in plain text in the local config file
  (`~/.config/MeetingCopilot/config.json`).

## Project structure

```
meeting_copilot/
  audio/       microphone and system audio capture (sounddevice)
  stt/         local transcription with faster-whisper
  llm/         suggestion generation via OpenAI or Ollama
  core/        config and transcript storage
  ui/          main window, transparency banner, settings, i18n
```
