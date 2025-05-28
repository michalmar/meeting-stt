import sys
import wave

def inspect_wav(filepath):
    with wave.open(filepath, 'rb') as wav_file:
        channels = wav_file.getnchannels()
        samples_per_second = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()
        bit_per_sample = sample_width * 8

        print(f"channels: {channels}")
        print(f"bits_per_sample: {bit_per_sample}")
        print(f"samples_per_second: {samples_per_second}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_wav.py <wav_file_path>")
        sys.exit(1)
    inspect_wav(sys.argv[1])
