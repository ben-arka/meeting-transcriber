#!/usr/bin/env python3
"""
Meeting Transcription Tool
--------------------------
Drop in an audio or video file, get back a clean meeting transcript.
Powered entirely by Groq — fast transcription + smart cleanup, all in one.

You'll need:
    pip install groq
    brew install ffmpeg   <-- only needed for .m4v and other non-standard formats

How to run:
    python transcribe_meeting.py my_meeting.m4v
    python transcribe_meeting.py my_meeting.mp3 notes.txt   <-- custom output name

Don't forget to set your Groq key first:
    export GROQ_API_KEY=your_key_here

Get a free API key at: console.groq.com
"""

import sys
import os
import argparse
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # picks up your GROQ_API_KEY from the .env file

# Formats Groq accepts natively — anything else gets converted to mp3 first
GROQ_SUPPORTED = {".flac", ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".ogg", ".opus", ".wav", ".webm"}



# --- Add your custom word corrections here ---
# Whisper often mishears names, acronyms, and company-specific terms.
# Just add "wrong version": "correct version" and the script handles the rest.
WORD_CORRECTIONS = {
    "Arca": "Arka",
    "arca": "Arka",
    "indopaycom": "Indopacom",
    "Indopaycom": "Indopacom",
    "indo pay com": "Indopacom",
    # add more as you discover them:
    # "mis-heard word": "correct word",
}


def apply_corrections(text):
    # Swap out any known mistranscriptions before sending to the LLM
    for wrong, right in WORD_CORRECTIONS.items():
        text = text.replace(wrong, right)
    corrected_count = sum(text.count(right) for right in WORD_CORRECTIONS.values())
    print(f"Applied word corrections ({len(WORD_CORRECTIONS)} rules in dictionary)")
    return text

def convert_to_supported(input_path):
    ext = os.path.splitext(input_path)[1].lower()

    # Already good to go — no conversion needed
    if ext in GROQ_SUPPORTED:
        return input_path, False

    # Not supported natively, so we'll convert it to mp3 via ffmpeg
    converted_path = os.path.splitext(input_path)[0] + "_converted.mp3"
    print(f"'{ext}' isn't directly supported by Groq — converting to mp3 first...")

    exit_code = os.system(f'ffmpeg -y -i "{input_path}" "{converted_path}" -loglevel error')
    if exit_code != 0 or not os.path.isfile(converted_path):
        print("\nConversion failed. Make sure ffmpeg is installed:")
        print("  brew install ffmpeg\n")
        sys.exit(1)

    print("Conversion done!\n")
    return converted_path, True  # True = we made a temp file, clean it up after


def transcribe_audio(input_path, client):
    file_to_send, was_converted = convert_to_supported(input_path)

    print(f"Sending audio to Groq for transcription: {input_path}")

    with open(file_to_send, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            file=(os.path.basename(file_to_send), audio_file.read()),
            model="whisper-large-v3",  # Groq's fastest + most accurate Whisper model
            response_format="text",
        )

    # Tidy up the temp file if we created one
    if was_converted:
        os.remove(file_to_send)

    raw_text = result.strip()
    print(f"Got it! Pulled out {len(raw_text)} characters of speech.\n")
    return raw_text


def clean_up_with_groq(raw_text, client):
    print("Sending to Groq to clean things up...")

    prompt = f"""Hey! I've got a raw audio transcription from a work meeting and I need your help 
turning it into something readable. It's a bit rough since it came straight from speech-to-text.

Here's the raw transcription:
\"\"\"
{raw_text}
\"\"\"

Can you please:
- Fix up the grammar and punctuation (speech-to-text gets messy)
- Try to spot different speakers and label them (Speaker 1, Speaker 2, etc. — or use their names if they're mentioned)
- Break it into paragraphs when the topic shifts
- Add a short Meeting Summary at the top so someone can skim it
- Add a Key Action Items section at the bottom if there were any to-dos mentioned
- Keep everything that was said — don't cut anything important
- Keep it as plain text (no markdown symbols or bullet dots — just plain dashes for lists)

Just give me the finished transcript, no need for any intro or explanation from you."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Great balance of speed and quality on Groq
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(
        description="Turn an audio or video recording into a clean, readable transcript."
    )
    parser.add_argument("input_file", help="The audio/video file you want to transcribe")
    parser.add_argument(
        "output_txt",
        nargs="?",
        help="Where to save the transcript (optional — we'll name it for you if you skip this)",
    )
    args = parser.parse_args()

    # Make sure the file actually exists
    if not os.path.isfile(args.input_file):
        print(f"\nCouldn't find that file: {args.input_file}")
        print("Double-check the path and try again.\n")
        sys.exit(1)

    # Figure out where to save the output
    if args.output_txt:
        output_path = args.output_txt
    else:
        base = os.path.splitext(args.input_file)[0]
        output_path = f"{base}_transcript.txt"

    # Make sure the API key is ready to go
    if not os.environ.get("GROQ_API_KEY"):
        print("\nOne thing — your GROQ_API_KEY isn't set.")
        print("Add it like this:  export GROQ_API_KEY=your_key_here")
        print("You can grab a free key at: console.groq.com\n")
        sys.exit(1)

    # One client for everything — transcription and cleanup
    client = Groq()

    # Step 1: Speech to text via Groq Whisper (converts format first if needed)
    raw_transcript = transcribe_audio(args.input_file, client)

    if not raw_transcript:
        print("\nHmm, the transcription came back empty. The audio might be too quiet or unclear.")
        print("Try a different file and see if that helps.\n")
        sys.exit(1)

    # Step 1.5: Fix any known mistranscriptions before sending to the LLM
    raw_transcript = apply_corrections(raw_transcript)

    # Step 2: Polish it up with Groq LLM
    final_transcript = clean_up_with_groq(raw_transcript, client)

    # Step 3: Save it
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_transcript)

    print(f"\nAll done! Your transcript is ready at: {output_path}\n")


if __name__ == "__main__":
    main()