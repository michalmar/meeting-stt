from pydub import AudioSegment
import sys
import os

def convert_m4a_to_wav(input_path, output_path=None):
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".wav"
    audio = AudioSegment.from_file(input_path, format="m4a")
    audio.export(output_path, format="wav")
    print(f"Converted '{input_path}' to '{output_path}'.")

def convert_mp3_to_wav(input_path, output_path=None):
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".wav"
    audio = AudioSegment.from_file(input_path, format="mp3")
    audio.export(output_path, format="wav")
    print(f"Converted '{input_path}' to '{output_path}'.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_to_wav.py input_file.m4a [output_file.wav]")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    convert_m4a_to_wav(input_file, output_file)
