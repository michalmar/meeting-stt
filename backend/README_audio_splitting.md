# Audio Splitting by Silence

This module provides functionality to split WAV audio files at silence points using energy-based detection.

## Features

- **Automatic silence detection**: Uses energy analysis to identify silence periods
- **Configurable parameters**: Adjust silence duration, sensitivity, and processing steps
- **Output management**: Automatically saves split files to `data/split/` directory
- **Progress tracking**: Shows progress during processing with tqdm progress bars
- **Dry run support**: Test splitting without creating actual files

## Functions

### `split_wav_by_silence(input_file, ...)`

Main function to split WAV files by silence.

**Parameters:**
- `input_file` (str): Path to the input WAV file
- `output_dir` (str, optional): Output directory for split files. Defaults to `data/split/`
- `min_silence_length` (float): Minimum silence duration for splitting (seconds). Default: 3.0
- `silence_threshold` (float): Energy threshold below which signal is considered silent (0.0-1.0). Default: 1e-6
- `step_duration` (float, optional): Time step for energy calculation. Default: min_silence_length/10
- `dry_run` (bool): If True, don't write files, just return split information. Default: False

**Returns:**
```python
{
    'success': bool,
    'message': str,
    'output_files': List[str],
    'split_count': int,
    'output_dir': str
}
```

### `quick_split_audio(input_file, silence_duration=3.0, sensitivity=1e-6)`

Convenience function for quick audio splitting with common parameters.

## Usage Examples

### Python Code
```python
from utils.audio import split_wav_by_silence, quick_split_audio

# Basic usage
result = split_wav_by_silence('audio_file.wav')

# Custom parameters
result = split_wav_by_silence(
    input_file='long_meeting.wav',
    min_silence_length=2.0,  # Split at 2+ seconds of silence
    silence_threshold=1e-5,  # More sensitive detection
    dry_run=True  # Test without creating files
)

# Quick split with convenience function
result = quick_split_audio('audio_file.wav', silence_duration=1.5)
```

### Command Line
```bash
# Basic split
python utils/audio.py split audio_file.wav

# With custom parameters
python utils/audio.py split audio_file.wav \
    --output-dir ./custom_output \
    --min-silence-length 2.0 \
    --silence-threshold 1e-5 \
    --dry-run

# Available commands
python utils/audio.py split input_file.wav [OPTIONS]

Options:
  --output-dir DIR              Output directory for split files
  --min-silence-length SECONDS  Minimum silence duration (default: 3.0)
  --silence-threshold THRESHOLD Energy threshold for silence (default: 1e-6)
  --step-duration SECONDS       Processing step duration
  --dry-run                     Test mode - don't create files
```

## How It Works

1. **Energy Analysis**: The algorithm calculates the energy of audio windows over time
2. **Silence Detection**: Windows with energy below the threshold are marked as silent
3. **Split Point Identification**: Rising edges (end of silence periods) become split points
4. **File Generation**: Audio segments between split points are saved as separate WAV files

## Parameters Tuning

- **Silence Threshold**: Lower values (e.g., 1e-7) detect quieter silences, higher values (e.g., 1e-4) only detect very quiet periods
- **Minimum Silence Length**: Prevents splitting on brief pauses - adjust based on your audio content
- **Step Duration**: Smaller values provide more accurate detection but slower processing

## Output Files

Split files are named using the pattern: `{original_name}_{index:03d}.wav`

Example: `meeting_001.wav`, `meeting_002.wav`, etc.

## Dependencies

- `scipy`: For audio file I/O and signal processing
- `numpy`: For numerical operations
- `tqdm`: For progress bars
- `os`: For file system operations
