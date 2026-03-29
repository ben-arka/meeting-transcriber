# Meeting Transcription Tool

Drop in an audio or video file, get back a clean formatted meeting transcript. Powered entirely by Groq — fast transcription via Whisper and smart cleanup via LLaMA, all in one script.

---

## What it does

- Transcribes your recording using Groq's Whisper API
- Automatically converts unsupported formats (like `.m4v`) to mp3 before sending
- Fixes known mistranscriptions using a customizable word correction dictionary
- Cleans up the raw transcript with an LLM — fixes grammar, labels speakers, adds a Meeting Summary and Key Action Items

---

## Requirements

- Python 3.12+
- A free Groq API key → [console.groq.com](https://console.groq.com)
- ffmpeg (only needed for `.m4v` and other non-standard formats)

Install ffmpeg on Mac:
```bash
brew install ffmpeg
```

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

**2. Install dependencies**
```bash
python3.12 -m pip install groq python-dotenv
```

**3. Add your API key**

Create a `.env` file in the project folder:
```
GROQ_API_KEY=your_key_here
```

> Your `.env` file is in `.gitignore` and will never be uploaded to GitHub.

---

## Usage

```bash
# Output file is named automatically (my_meeting_transcript.txt)
python3.12 transcribe_meeting.py my_meeting.mp3

# Or specify a custom output name
python3.12 transcribe_meeting.py my_meeting.m4v notes.txt
```

---

## Supported formats

`.mp3` `.m4a` `.mp4` `.m4v` `.wav` `.ogg` `.flac` `.webm` `.mpeg` `.opus`

Anything not natively supported by Groq gets auto-converted to mp3 via ffmpeg first.

---

## Custom word corrections

Whisper sometimes mishears names, acronyms, or company-specific terms. You can add your own fixes at the top of `transcribe_meeting.py`:

```python
WORD_CORRECTIONS = {
    "Arca": "Arka",
    "indopaycom": "Indopacom",
    # add more as you find them:
    # "wrong word": "Correct Word",
}
```

Corrections are applied after transcription and before the LLM cleanup step.

---

## Project structure

```
transcribe_meeting/
├── transcribe_meeting.py   # main script
├── .env                    # your API key (never committed)
├── .env.example            # template for others
├── .gitignore
└── README.md
```

---

## .env.example

```
GROQ_API_KEY=your_key_here
```