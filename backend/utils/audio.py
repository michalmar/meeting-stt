import sys
import os
import wave
from pydub import AudioSegment
# Imports for audio splitting functionality
import numpy as np
from scipy.io import wavfile
from tqdm import tqdm

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
    
def convert_stereo_wav_to_mono(input_path, output_path=None):
    """
    Converts a stereo WAV file to mono by combining channels and saves the result.
    If output_path is not provided, overwrites the original file.
    Returns a dict with success status and message.
    """
    try:
        audio = AudioSegment.from_wav(input_path)
        if audio.channels == 1:
            return {
                "input": input_path,
                "output": output_path or input_path,
                "success": True,
                "message": f"'{input_path}' is already mono. No conversion needed."
            }
        mono_audio = audio.set_channels(1)
        if output_path is None:
            output_path = input_path
        mono_audio.export(output_path, format="wav")
        return {
            "input": input_path,
            "output": output_path,
            "success": True,
            "message": f"Converted stereo WAV '{input_path}' to mono and saved to '{output_path}'."
        }
    except Exception as e:
        return {
            "input": input_path,
            "output": output_path,
            "success": False,
            "message": f"Error converting stereo WAV to mono: {e}"
        }

def extract_audio_channels(input_path, left_output_path=None, right_output_path=None):
    """
    Extracts left and right channels from a stereo WAV file into separate mono files.
    
    Args:
        input_path (str): Path to the input stereo WAV file
        left_output_path (str, optional): Path for the left channel output. 
                                        If not provided, uses input_path with '_left' suffix
        right_output_path (str, optional): Path for the right channel output.
                                         If not provided, uses input_path with '_right' suffix
    
    Returns:
        dict: Contains success status, message, and output paths for both channels
    """
    try:
        # Load the audio file
        audio = AudioSegment.from_wav(input_path)
        
        # Check if the audio is stereo
        if audio.channels == 1:
            return {
                "input": input_path,
                "left_output": None,
                "right_output": None,
                "success": False,
                "message": f"'{input_path}' is mono (1 channel). Cannot extract left/right channels."
            }
        
        if audio.channels > 2:
            return {
                "input": input_path,
                "left_output": None,
                "right_output": None,
                "success": False,
                "message": f"'{input_path}' has {audio.channels} channels. This function only supports stereo (2 channels)."
            }
        
        # Generate output paths if not provided
        if left_output_path is None:
            base_name = os.path.splitext(input_path)[0]
            left_output_path = f"{base_name}_left.wav"
        
        if right_output_path is None:
            base_name = os.path.splitext(input_path)[0]
            right_output_path = f"{base_name}_right.wav"
        
        # Extract left channel (channel 0)
        left_channel = audio.split_to_mono()[0]
        left_channel.export(left_output_path, format="wav")
        
        # Extract right channel (channel 1)
        right_channel = audio.split_to_mono()[1]
        right_channel.export(right_output_path, format="wav")
        
        return {
            "input": input_path,
            "left_output": left_output_path,
            "right_output": right_output_path,
            "success": True,
            "message": f"Successfully extracted channels from '{input_path}'. Left: '{left_output_path}', Right: '{right_output_path}'"
        }
        
    except Exception as e:
        return {
            "input": input_path,
            "left_output": left_output_path,
            "right_output": right_output_path,
            "success": False,
            "message": f"Error extracting audio channels: {e}"
        }
def split_wav_by_silence(input_file, 
                        output_dir=None, 
                        min_silence_length=3.0, 
                        silence_threshold=1e-6, 
                        step_duration=None, 
                        dry_run=False):
    """
    Split a WAV file at silence points.
    
    Args:
        input_file (str): Path to the input WAV file
        output_dir (str): Output directory for split files. Defaults to data/split folder
        min_silence_length (float): Minimum length of silence at which split may occur (seconds). Default: 3.0
        silence_threshold (float): Energy level below which signal is regarded as silent (0.0-1.0). Default: 1e-6
        step_duration (float): Time step for energy calculation. Smaller = more accurate but slower. Default: min_silence_length/10
        dry_run (bool): If True, don't write files, just return split information. Default: False
    
    Returns:
        dict: Contains success status, message, and list of output files
    """
    
    # Utility functions for audio processing
    def windows(signal, window_size, step_size):
        """Generate sliding windows over the signal"""
        if type(window_size) is not int:
            raise AttributeError("Window size must be an integer.")
        if type(step_size) is not int:
            raise AttributeError("Step size must be an integer.")
        for i_start in range(0, len(signal), step_size):
            i_end = i_start + window_size
            if i_end >= len(signal):
                break
            yield signal[i_start:i_end]

    def energy(samples):
        """Calculate energy of audio samples"""
        return np.sum(np.power(samples, 2.)) / float(len(samples))

    def rising_edges(binary_signal):
        """Find rising edges in binary signal"""
        previous_value = 0
        index = 0
        for x in binary_signal:
            if x and not previous_value:
                yield index
            previous_value = x
            index += 1
    
    try:
        # Set default output directory to data/split
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'split')
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Set default step duration
        if step_duration is None:
            step_duration = min_silence_length / 10.0
        
        # Get output filename prefix
        output_filename_prefix = os.path.splitext(os.path.basename(input_file))[0]
        
        print(f"Splitting {input_file} where energy is below {silence_threshold * 100:.4f}% for longer than {min_silence_length}s.")
        
        # Read the WAV file
        sample_rate, samples = wavfile.read(filename=input_file, mmap=True)
        
        # Calculate energy parameters
        max_amplitude = np.iinfo(samples.dtype).max
        max_energy = energy([max_amplitude])
        
        window_size = int(min_silence_length * sample_rate)
        step_size = int(step_duration * sample_rate)
        
        # Generate windows and calculate energy
        signal_windows = windows(
            signal=samples,
            window_size=window_size,
            step_size=step_size
        )
        
        window_energy = (energy(w) / max_energy for w in tqdm(
            signal_windows,
            total=int(len(samples) / float(step_size)),
            desc="Calculating energy"
        ))
        
        # Determine silence windows (inverted logic: energy below threshold = silence)
        window_silence = (e < silence_threshold for e in window_energy)
        
        # Find cut points at rising edges (end of silence periods)
        cut_times = (r * step_duration for r in rising_edges(window_silence))
        
        # Convert to sample indices
        print("Finding silence points...")
        cut_samples = [int(t * sample_rate) for t in cut_times]
        cut_samples.append(len(samples))  # Add end of file
        
        # Create ranges for splitting
        if len(cut_samples) <= 1:
            # No silence found, return original file info
            return {
                'success': True,
                'message': f'No silence periods found in {input_file}. File not split.',
                'output_files': [],
                'split_count': 0
            }
        
        # Add start of file if not already there
        if cut_samples[0] != 0:
            cut_samples.insert(0, 0)
        
        cut_ranges = [(i, cut_samples[i], cut_samples[i+1]) for i in range(len(cut_samples) - 1)]
        
        output_files = []
        
        # Write split files
        for i, start, stop in tqdm(cut_ranges, desc="Writing split files"):
            output_file_path = os.path.join(output_dir, f"{output_filename_prefix}_{i:03d}.wav")
            
            if not dry_run:
                print(f"Writing file {output_file_path}")
                wavfile.write(
                    filename=output_file_path,
                    rate=sample_rate,
                    data=samples[start:stop]
                )
                output_files.append(output_file_path)
            else:
                print(f"Would write file {output_file_path}")
                output_files.append(output_file_path)
        
        return {
            'success': True,
            'message': f'Successfully split {input_file} into {len(cut_ranges)} files.',
            'output_files': output_files,
            'split_count': len(cut_ranges),
            'output_dir': output_dir,
            'input_file': input_file,
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error splitting audio file: {str(e)}',
            'output_files': [],
            'split_count': 0
        }

def quick_split_audio(input_file, silence_duration=3.0, sensitivity=1e-6):
    """
    Convenience function to quickly split audio with common parameters.
    
    Args:
        input_file (str): Path to the input WAV file
        silence_duration (float): Minimum silence duration for splitting (seconds)
        sensitivity (float): Sensitivity for silence detection (lower = more sensitive)
    
    Returns:
        dict: Contains success status and list of output files
    """
    return split_wav_by_silence(
        input_file=input_file,
        min_silence_length=silence_duration,
        silence_threshold=sensitivity
    )


def split_wav_by_time(input_file, 
                     chunk_duration=30.0, 
                     output_dir=None, 
                     overlap=0.0,
                     dry_run=False):
    """
    Split a WAV file into fixed-duration chunks.
    
    Args:
        input_file (str): Path to the input WAV file
        chunk_duration (float): Duration of each chunk in seconds. Default: 30.0
        output_dir (str): Output directory for split files. Defaults to data/split folder
        overlap (float): Overlap between chunks in seconds. Default: 0.0
        dry_run (bool): If True, don't write files, just return split information. Default: False
    
    Returns:
        dict: Contains success status, message, and list of output files
    """
    
    try:
        # Set default output directory to data/split
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'split')
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Get output filename prefix
        output_filename_prefix = os.path.splitext(os.path.basename(input_file))[0]
        
        print(f"Splitting {input_file} into {chunk_duration}s chunks with {overlap}s overlap.")
        
        # Read the WAV file
        sample_rate, samples = wavfile.read(filename=input_file)
        
        # Calculate total duration
        total_duration = len(samples) / sample_rate
        print(f"Total audio duration: {total_duration:.2f} seconds")
        
        # Calculate chunk parameters
        chunk_samples = int(chunk_duration * sample_rate)
        overlap_samples = int(overlap * sample_rate)
        step_samples = chunk_samples - overlap_samples
        
        if step_samples <= 0:
            return {
                'success': False,
                'message': f'Overlap ({overlap}s) must be less than chunk duration ({chunk_duration}s)',
                'output_files': [],
                'split_count': 0
            }
        
        # Calculate number of chunks
        if len(samples) <= chunk_samples:
            # File is shorter than chunk duration
            chunk_count = 1
            chunks = [(0, len(samples))]
        else:
            chunks = []
            start = 0
            chunk_index = 0
            
            while start < len(samples):
                end = min(start + chunk_samples, len(samples))
                chunks.append((start, end))
                start += step_samples
                chunk_index += 1
                
                # Break if the remaining audio is too short to be meaningful
                if len(samples) - start < chunk_samples * 0.1:  # Less than 10% of chunk duration
                    if end < len(samples):
                        # Extend the last chunk to include remaining audio
                        chunks[-1] = (chunks[-1][0], len(samples))
                    break
        
        chunk_count = len(chunks)
        output_files = []
        
        # Write split files
        for i, (start, end) in enumerate(tqdm(chunks, desc="Writing time-based chunks")):
            chunk_duration_actual = (end - start) / sample_rate
            output_file_path = os.path.join(output_dir, f"{output_filename_prefix}_time_{i:03d}.wav")
            
            if not dry_run:
                print(f"Writing chunk {i+1}/{chunk_count}: {output_file_path} ({chunk_duration_actual:.2f}s)")
                wavfile.write(
                    filename=output_file_path,
                    rate=sample_rate,
                    data=samples[start:end]
                )
                output_files.append(output_file_path)
            else:
                print(f"Would write chunk {i+1}/{chunk_count}: {output_file_path} ({chunk_duration_actual:.2f}s)")
                output_files.append(output_file_path)
        
        return {
            'success': True,
            'message': f'Successfully split {input_file} into {chunk_count} time-based chunks of {chunk_duration}s each.',
            'output_files': output_files,
            'split_count': chunk_count,
            'output_dir': output_dir,
            'total_duration': total_duration,
            'chunk_duration': chunk_duration,
            'overlap': overlap,
            'input_file': input_file,
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error splitting audio file by time: {str(e)}',
            'output_files': [],
            'split_count': 0
        }


def quick_split_by_time(input_file, chunk_seconds=30.0):
    """
    Convenience function to quickly split audio into time-based chunks.
    
    Args:
        input_file (str): Path to the input WAV file
        chunk_seconds (float): Duration of each chunk in seconds
    
    Returns:
        dict: Contains success status and list of output files
    """
    return split_wav_by_time(
        input_file=input_file,
        chunk_duration=chunk_seconds
    )


def join_wav_by_time(filenames=None,
                    input_dir=None,
                    max_duration=600.0, 
                    output_dir=None, 
                    output_prefix="joined",
                    dry_run=False):
    """
    Join WAV files from split_wav_by_silence into larger chunks with maximum duration.
    
    This function takes individual chunks created by split_wav_by_silence and combines them
    into larger files that don't exceed the specified maximum duration.
    
    Args:
        filenames (list): List of WAV filenames to join. Takes precedence over input_dir scanning.
        input_dir (str): Directory containing split WAV files. Used only if filenames is None.
        max_duration (float): Maximum duration for joined files in seconds. Default: 600.0 (10 minutes)
        output_dir (str): Output directory for joined files. Defaults to data/split/joined folder
        output_prefix (str): Prefix for output filenames. Default: "joined"
        dry_run (bool): If True, don't write files, just return join information. Default: False
    
    Returns:
        dict: Contains success status, message, and list of output files
    """
    
    try:
        # Handle filenames parameter
        if filenames is not None:
            if not isinstance(filenames, list):
                return {
                    'success': False,
                    'message': 'filenames parameter must be a list of file paths',
                    'output_files': [],
                    'join_count': 0
                }
            
            if not filenames:
                return {
                    'success': False,
                    'message': 'filenames list is empty',
                    'output_files': [],
                    'join_count': 0
                }
            
            # Convert to full paths and validate files exist
            wav_file_paths = []
            for filename in filenames:
                if os.path.isfile(filename):
                    wav_file_paths.append(filename)
                else:
                    print(f"Warning: File not found: {filename}")
            
            if not wav_file_paths:
                return {
                    'success': False,
                    'message': 'No valid files found in the provided filenames list',
                    'output_files': [],
                    'join_count': 0
                }
            
            # Set default output directory based on first file's directory if not specified
            if output_dir is None:
                first_file_dir = os.path.dirname(wav_file_paths[0])
                if first_file_dir:
                    output_dir = os.path.join(first_file_dir, 'joined')
                else:
                    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'split', 'joined')
        else:
            # Original directory scanning logic
            # Set default input directory to data/split
            if input_dir is None:
                input_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'split')
            
            # Set default output directory to data/split/joined
            if output_dir is None:
                output_dir = os.path.join(input_dir, 'joined')
            
            # Find all WAV files in input directory (exclude time-based splits and joined files)
            wav_files = []
            for filename in os.listdir(input_dir):
                if (filename.lower().endswith('.wav') and 
                    not filename.startswith('joined_') and 
                    '_time_' not in filename and
                    os.path.isfile(os.path.join(input_dir, filename))):
                    wav_files.append(filename)
            
            if not wav_files:
                return {
                    'success': False,
                    'message': f'No suitable WAV files found in {input_dir}',
                    'output_files': [],
                    'join_count': 0
                }
            
            # Convert to full paths
            wav_file_paths = [os.path.join(input_dir, filename) for filename in wav_files]
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Sort files by name to maintain order (assuming split files are numbered)
        wav_file_paths.sort()
        
        print(f"Found {len(wav_file_paths)} WAV files to join")
        print(f"Maximum duration per joined file: {max_duration} seconds")
        
        # Group files by their base name (before the _xxx.wav part)
        file_groups = {}
        for filepath in wav_file_paths:
            filename = os.path.basename(filepath)
            # Extract base name (everything before the last _xxx.wav pattern)
            base_match = filename.rsplit('_', 1)[0] if '_' in filename else filename.rsplit('.', 1)[0]
            if base_match not in file_groups:
                file_groups[base_match] = []
            file_groups[base_name].append(filepath)
        
        # Sort files within each group
        for base_name in file_groups:
            file_groups[base_name].sort()
        
        output_files = []
        total_joined_files = 0
        
        # Process each group separately
        for base_name, file_paths in file_groups.items():
            print(f"\nProcessing group: {base_name} ({len(file_paths)} files)")
            
            current_group = []
            current_duration = 0.0
            group_index = 0
            
            for filepath in tqdm(file_paths, desc=f"Processing {base_name}"):
                
                # Get duration of current file
                try:
                    sample_rate, samples = wavfile.read(filepath)
                    file_duration = len(samples) / sample_rate
                except Exception as e:
                    print(f"Warning: Could not read {os.path.basename(filepath)}: {e}")
                    continue
                
                # Check if adding this file would exceed max duration
                if current_group and (current_duration + file_duration) > max_duration:
                    # Save current group and start a new one
                    if current_group:
                        output_filename = f"{output_prefix}_{base_name}_{group_index:03d}.wav"
                        output_path = os.path.join(output_dir, output_filename)
                        
                        if not dry_run:
                            join_result = _join_wav_files(current_group, output_path)
                            if join_result['success']:
                                output_files.append(output_path)
                                total_joined_files += 1
                                print(f"Created: {output_filename} ({current_duration:.2f}s from {len(current_group)} files)")
                            else:
                                print(f"Error creating {output_filename}: {join_result['message']}")
                        else:
                            output_files.append(output_path)
                            total_joined_files += 1
                            print(f"Would create: {output_filename} ({current_duration:.2f}s from {len(current_group)} files)")
                        
                        group_index += 1
                    
                    # Start new group with current file
                    current_group = [filepath]
                    current_duration = file_duration
                else:
                    # Add file to current group
                    current_group.append(filepath)
                    current_duration += file_duration
            
            # Handle the last group if it has files
            if current_group:
                output_filename = f"{output_prefix}_{base_name}_{group_index:03d}.wav"
                output_path = os.path.join(output_dir, output_filename)
                
                if not dry_run:
                    join_result = _join_wav_files(current_group, output_path)
                    if join_result['success']:
                        output_files.append(output_path)
                        total_joined_files += 1
                        print(f"Created: {output_filename} ({current_duration:.2f}s from {len(current_group)} files)")
                    else:
                        print(f"Error creating {output_filename}: {join_result['message']}")
                else:
                    output_files.append(output_path)
                    total_joined_files += 1
                    print(f"Would create: {output_filename} ({current_duration:.2f}s from {len(current_group)} files)")
        
        return {
            'success': True,
            'message': f'Successfully joined {len(wav_file_paths)} files into {total_joined_files} larger files.',
            'output_files': output_files,
            'join_count': total_joined_files,
            'output_dir': output_dir,
            'max_duration': max_duration,
            'input_files_processed': len(wav_file_paths)
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error joining audio files: {str(e)}',
            'output_files': [],
            'join_count': 0
        }


def _join_wav_files(file_paths, output_path):
    """
    Helper function to join multiple WAV files into a single file.
    
    Args:
        file_paths (list): List of WAV file paths to join
        output_path (str): Path for the output joined file
    
    Returns:
        dict: Success status and message
    """
    try:
        if not file_paths:
            return {'success': False, 'message': 'No files to join'}
        
        # Read the first file to get audio properties
        sample_rate, first_samples = wavfile.read(file_paths[0])
        
        # Start with the first file's samples
        joined_samples = first_samples.copy()
        
        # Append subsequent files
        for file_path in file_paths[1:]:
            try:
                rate, samples = wavfile.read(file_path)
                if rate != sample_rate:
                    return {
                        'success': False, 
                        'message': f'Sample rate mismatch: {rate} vs {sample_rate} in {file_path}'
                    }
                joined_samples = np.concatenate([joined_samples, samples])
            except Exception as e:
                return {
                    'success': False,
                    'message': f'Error reading {file_path}: {str(e)}'
                }
        
        # Write the joined audio
        wavfile.write(output_path, sample_rate, joined_samples)
        
        return {
            'success': True,
            'message': f'Successfully joined {len(file_paths)} files into {output_path}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error joining files: {str(e)}'
        }


def quick_join_by_time(input_dir=None, max_minutes=10.0):
    """
    Convenience function to quickly join split audio files from a directory.
    
    Args:
        input_dir (str): Directory containing split WAV files
        max_minutes (float): Maximum duration for joined files in minutes
    
    Returns:
        dict: Contains success status and list of output files
    """
    return join_wav_by_time(
        input_dir=input_dir,
        max_duration=max_minutes * 60.0
    )


def quick_join_filenames(filenames, max_minutes=10.0, output_prefix="joined"):
    """
    Convenience function to quickly join specific audio files by their filenames.
    
    Args:
        filenames (list): List of WAV file paths to join
        max_minutes (float): Maximum duration for joined files in minutes
        output_prefix (str): Prefix for output filenames
    
    Returns:
        dict: Contains success status and list of output files
    """
    return join_wav_by_time(
        filenames=filenames,
        max_duration=max_minutes * 60.0,
        output_prefix=output_prefix
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python utils_audio.py <command> <args>")
        print("Commands:")
        print("  convert_m4a input_file.m4a [output_file.wav]")
        print("  convert_mp3 input_file.mp3 [output_file.wav]")
        print("  inspect input_file.wav")
        print("  trim input_file.wav number_of_seconds [output_file.wav]")
        print("  split input_file.wav [--output-dir DIR] [--min-silence-length SECONDS] [--silence-threshold THRESHOLD] [--step-duration SECONDS] [--dry-run]")
        print("  split_time input_file.wav [--chunk-duration SECONDS] [--overlap SECONDS] [--output-dir DIR] [--dry-run]")
        print("  join_time [--input-dir DIR] [--files FILE1,FILE2,...] [--max-duration SECONDS] [--output-dir DIR] [--output-prefix PREFIX] [--dry-run]")
        print("  join_wav_by_time [input_dir] [max_duration] [output_dir] [output_prefix] [dry_run]")
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
    elif command == "split":
        if len(sys.argv) < 3:
            print("Usage: python utils_audio.py split input_file.wav [--output-dir DIR] [--min-silence-length SECONDS] [--silence-threshold THRESHOLD] [--step-duration SECONDS] [--dry-run]")
            sys.exit(1)
        
        input_file = sys.argv[2]
        
        # Parse optional arguments
        output_dir = None
        min_silence_length = 3.0
        silence_threshold = 1e-6
        step_duration = None
        dry_run = False
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--output-dir" and i + 1 < len(sys.argv):
                output_dir = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--min-silence-length" and i + 1 < len(sys.argv):
                try:
                    min_silence_length = float(sys.argv[i + 1])
                except ValueError:
                    print("--min-silence-length must be a number")
                    sys.exit(1)
                i += 2
            elif sys.argv[i] == "--silence-threshold" and i + 1 < len(sys.argv):
                try:
                    silence_threshold = float(sys.argv[i + 1])
                except ValueError:
                    print("--silence-threshold must be a number")
                    sys.exit(1)
                i += 2
            elif sys.argv[i] == "--step-duration" and i + 1 < len(sys.argv):
                try:
                    step_duration = float(sys.argv[i + 1])
                except ValueError:
                    print("--step-duration must be a number")
                    sys.exit(1)
                i += 2
            elif sys.argv[i] == "--dry-run":
                dry_run = True
                i += 1
            else:
                print(f"Unknown argument: {sys.argv[i]}")
                sys.exit(1)
        
        result = split_wav_by_silence(
            input_file=input_file,
            output_dir=output_dir,
            min_silence_length=min_silence_length,
            silence_threshold=silence_threshold,
            step_duration=step_duration,
            dry_run=dry_run
        )
        
        print(result["message"])
        if result["success"]:
            print(f"Split into {result['split_count']} files")
            if result['output_files']:
                print("Output files:")
                for file in result['output_files']:
                    print(f"  - {file}")
    elif command == "split_time":
        if len(sys.argv) < 3:
            print("Usage: python utils_audio.py split_time input_file.wav [--output-dir DIR] [--chunk-duration SECONDS] [--overlap SECONDS] [--dry-run]")
            sys.exit(1)
        
        input_file = sys.argv[2]
        
        # Parse optional arguments
        output_dir = None
        chunk_duration = 30.0
        overlap = 0.0
        dry_run = False
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--output-dir" and i + 1 < len(sys.argv):
                output_dir = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--chunk-duration" and i + 1 < len(sys.argv):
                try:
                    chunk_duration = float(sys.argv[i + 1])
                except ValueError:
                    print("--chunk-duration must be a number")
                    sys.exit(1)
                i += 2
            elif sys.argv[i] == "--overlap" and i + 1 < len(sys.argv):
                try:
                    overlap = float(sys.argv[i + 1])
                except ValueError:
                    print("--overlap must be a number")
                    sys.exit(1)
                i += 2
            elif sys.argv[i] == "--dry-run":
                dry_run = True
                i += 1
            else:
                print(f"Unknown argument: {sys.argv[i]}")
                sys.exit(1)
        
        result = split_wav_by_time(
            input_file=input_file,
            chunk_duration=chunk_duration,
            output_dir=output_dir,
            overlap=overlap,
            dry_run=dry_run
        )
        
        print(result["message"])
        if result["success"]:
            print(f"Split into {result['split_count']} chunks")
            if result['output_files']:
                print("Output files:")
                for file in result['output_files']:
                    print(f"  - {file}")
    elif command == "join_wav_by_time":
        input_dir = sys.argv[2] if len(sys.argv) > 2 else None
        max_duration = float(sys.argv[3]) if len(sys.argv) > 3 else 600.0
        output_dir = sys.argv[4] if len(sys.argv) > 4 else None
        output_prefix = sys.argv[5] if len(sys.argv) > 5 else "joined"
        dry_run = "--dry-run" in sys.argv
        
        result = join_wav_by_time(
            input_dir=input_dir,
            max_duration=max_duration,
            output_dir=output_dir,
            output_prefix=output_prefix,
            dry_run=dry_run
        )
        
        print(result["message"])
        if result["success"]:
            print(f"Joined into {result['join_count']} files")
            if result['output_files']:
                print("Output files:")
                for file in result['output_files']:
                    print(f"  - {file}")
    elif command == "join_time":
        # Parse optional arguments
        input_dir = None
        filenames = None
        max_duration = 600.0
        output_dir = None
        output_prefix = "joined"
        dry_run = False
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--input-dir" and i + 1 < len(sys.argv):
                input_dir = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--files" and i + 1 < len(sys.argv):
                # Parse comma-separated file list
                filenames = [f.strip() for f in sys.argv[i + 1].split(',') if f.strip()]
                i += 2
            elif sys.argv[i] == "--max-duration" and i + 1 < len(sys.argv):
                try:
                    max_duration = float(sys.argv[i + 1])
                except ValueError:
                    print("--max-duration must be a number")
                    sys.exit(1)
                i += 2
            elif sys.argv[i] == "--output-dir" and i + 1 < len(sys.argv):
                output_dir = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--output-prefix" and i + 1 < len(sys.argv):
                output_prefix = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--dry-run":
                dry_run = True
                i += 1
            else:
                print(f"Unknown argument: {sys.argv[i]}")
                sys.exit(1)
        
        result = join_wav_by_time(
            filenames=filenames,
            input_dir=input_dir,
            max_duration=max_duration,
            output_dir=output_dir,
            output_prefix=output_prefix,
            dry_run=dry_run
        )
        
        print(result["message"])
        if result["success"]:
            print(f"Joined {result['input_files_processed']} files into {result['join_count']} larger files")
            print(f"Max duration per file: {result['max_duration']}s")
            if result['output_files']:
                print("Output files:")
                for file in result['output_files']:
                    print(f"  - {file}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
