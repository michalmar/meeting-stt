
import sys
import os
import wave
from pydub import AudioSegment

def inspect_audio(filepath):
    """
    Inspects the audio file and returns its type (wav, mp3, mp4/m4a, or unknown).
    Returns a dict with keys: 'filetype', 'success', and 'message'.
    """
    import mimetypes
    ext = os.path.splitext(filepath)[1].lower()
    # Check by extension first
    if ext == '.wav':
        return {'filetype': 'wav', 'success': True, 'message': f"File '{filepath}' is a WAV file."}
    elif ext == '.mp3':
        return {'filetype': 'mp3', 'success': True, 'message': f"File '{filepath}' is an MP3 file."}
    elif ext in ['.mp4', '.m4a']:
        return {'filetype': 'mp4', 'success': True, 'message': f"File '{filepath}' is an MP4/M4A file."}
    # Fallback: try mimetypes
    mime, _ = mimetypes.guess_type(filepath)
    if mime:
        if mime == 'audio/wav' or mime == 'audio/x-wav':
            return {'filetype': 'wav', 'success': True, 'message': f"File '{filepath}' is a WAV file (mimetype)."}
        elif mime == 'audio/mpeg':
            return {'filetype': 'mp3', 'success': True, 'message': f"File '{filepath}' is an MP3 file (mimetype)."}
        elif mime in ['audio/mp4', 'audio/x-m4a', 'video/mp4']:
            return {'filetype': 'mp4', 'success': True, 'message': f"File '{filepath}' is an MP4/M4A file (mimetype)."}
    # Fallback: try reading file header (magic bytes)
    try:
        with open(filepath, 'rb') as f:
            header = f.read(12)
            if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                return {'filetype': 'wav', 'success': True, 'message': f"File '{filepath}' is a WAV file (header)."}
            elif header[:3] == b'ID3' or header[:2] == b'\xff\xfb':
                return {'filetype': 'mp3', 'success': True, 'message': f"File '{filepath}' is an MP3 file (header)."}
            elif header[4:8] == b'ftyp':
                return {'filetype': 'mp4', 'success': True, 'message': f"File '{filepath}' is an MP4/M4A file (header)."}
    except Exception as e:
        return {'filetype': 'unknown', 'success': False, 'message': f"Error reading file: {e}"}
    return {'filetype': 'unknown', 'success': False, 'message': f"File type of '{filepath}' could not be determined."}

def convert_m4a_to_wav(input_path, output_path=None):
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".wav"
    audio = AudioSegment.from_file(input_path, format="m4a")
    audio.export(output_path, format="wav")
    result = {
        "input": input_path,
        "output": output_path,
        "success": True,
        "message": f"Converted '{input_path}' to '{output_path}'."
    }
    return result

def convert_mp3_to_wav(input_path, output_path=None):
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".wav"
    audio = AudioSegment.from_file(input_path, format="mp3")
    audio.export(output_path, format="wav")
    result = {
        "input": input_path,
        "output": output_path,
        "success": True,
        "message": f"Converted '{input_path}' to '{output_path}'."
    }
    return result

def inspect_wav(filepath):
    with wave.open(filepath, 'rb') as wav_file:
        channels = wav_file.getnchannels()
        samples_per_second = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()
        bit_per_sample = sample_width * 8
        audio_length = wav_file.getnframes() / samples_per_second
        result = {
            "channels": channels,
            "bits_per_sample": bit_per_sample,
            "samples_per_second": samples_per_second,
            "audio_length": audio_length,
            "success": True,
        }
        return result
def inspect_mp3(filepath):
    """
    Inspects an MP3 file and returns basic info: duration (seconds), channels, frame_rate, sample_width (bytes).
    Returns a dict with keys: 'duration', 'channels', 'frame_rate', 'sample_width', 'success', and 'message'.
    """
    try:
        audio = AudioSegment.from_mp3(filepath)
        info = {
            'duration': len(audio) / 1000.0,  # duration in seconds
            'channels': audio.channels,
            'frame_rate': audio.frame_rate,
            'sample_width': audio.sample_width,
            'success': True,
            'message': f"Inspected MP3 file '{filepath}'."
        }
        return info
    except Exception as e:
        return {
            'success': False,
            'message': f"Error inspecting MP3 file: {e}"
        }


def trim_wav(filepath, number_of_seconds, output_path=None):
    """
    Trims the first `number_of_seconds` seconds from a WAV file at `filepath` and saves the result.
    If output_path is not provided, overwrites the original file.
    Returns a dict with success status and message.
    """
    try:
        audio = AudioSegment.from_wav(filepath)
        end_ms = int(number_of_seconds * 1000)
        trimmed_audio = audio[:end_ms]
        if output_path is None:
            output_path = filepath
        trimmed_audio.export(output_path, format="wav")
        return {
            "input": filepath,
            "output": output_path,
            "success": True,
            "message": f"Trimmed to first {number_of_seconds} seconds from '{filepath}' and saved to '{output_path}'."
        }
    except Exception as e:
        return {
            "input": filepath,
            "output": output_path,
            "success": False,
            "message": f"Error trimming WAV file: {e}"
        }
    
def trim_mp3(filepath, number_of_seconds, output_path=None):
    """
    Trims the first `number_of_seconds` seconds from an MP3 file at `filepath` and saves the result.
    If output_path is not provided, overwrites the original file.
    Returns a dict with success status and message.
    """
    try:
        audio = AudioSegment.from_mp3(filepath)
        end_ms = int(number_of_seconds * 1000)
        trimmed_audio = audio[:end_ms]
        if output_path is None:
            output_path = filepath
        trimmed_audio.export(output_path, format="mp3")
        return {
            "input": filepath,
            "output": output_path,
            "success": True,
            "message": f"Trimmed to first {number_of_seconds} seconds from '{filepath}' and saved to '{output_path}'."
        }
    except Exception as e:
        return {
            "input": filepath,
            "output": output_path,
            "success": False,
            "message": f"Error trimming MP3 file: {e}"
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python utils_audio.py <command> <args>")
        print("Commands:")
        print("  convert_m4a input_file.m4a [output_file.wav]")
        print("  convert_mp3 input_file.mp3 [output_file.wav]")
        print("  inspect input_file.wav")
        print("  trim input_file.wav number_of_seconds [output_file.wav]")
        sys.exit(1)
    command = sys.argv[1]
    if command == "convert_m4a":
        if len(sys.argv) < 3:
            print("Usage: python utils_audio.py convert_m4a input_file.m4a [output_file.wav]")
            sys.exit(1)
        input_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        result = convert_m4a_to_wav(input_file, output_file)
        print(result["message"])
    elif command == "convert_mp3":
        if len(sys.argv) < 3:
            print("Usage: python utils_audio.py convert_mp3 input_file.mp3 [output_file.wav]")
            sys.exit(1)
        input_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        result = convert_mp3_to_wav(input_file, output_file)
        print(result["message"])
    elif command == "inspect":
        if len(sys.argv) != 3:
            print("Usage: python utils_audio.py inspect input_file.wav")
            sys.exit(1)
        result = inspect_wav(sys.argv[2])
        print(f"channels: {result['channels']}")
        print(f"bits_per_sample: {result['bits_per_sample']}")
        print(f"samples_per_second: {result['samples_per_second']}")
    elif command == "trim":
        if len(sys.argv) < 4:
            print("Usage: python utils_audio.py trim input_file.wav number_of_seconds [output_file.wav]")
            sys.exit(1)
        input_file = sys.argv[2]
        try:
            number_of_seconds = float(sys.argv[3])
        except ValueError:
            print("number_of_seconds must be a number.")
            sys.exit(1)
        output_file = sys.argv[4] if len(sys.argv) > 4 else None
        result = trim_wav(input_file, number_of_seconds, output_file)
        print(result["message"])
    elif command == "trim_mp3":
        if len(sys.argv) < 4:
            print("Usage: python utils_audio.py trim_mp3 input_file.mp3 number_of_seconds [output_file.wav]")
            sys.exit(1)
        input_file = sys.argv[2]
        try:
            number_of_seconds = float(sys.argv[3])
        except ValueError:
            print("number_of_seconds must be a number.")
            sys.exit(1)
        output_file = sys.argv[4] if len(sys.argv) > 4 else None
        result = trim_mp3(input_file, number_of_seconds, output_file)
        print(result["message"])
    elif command == "inspect_audio":
        if len(sys.argv) != 3:
            print("Usage: python utils_audio.py inspect_audio input_file")
            sys.exit(1)
        result = inspect_audio(sys.argv[2])
        print(result["message"])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
