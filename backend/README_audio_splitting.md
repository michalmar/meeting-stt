# Audio Splitting by Silence and Time

This module provides functionality to split WAV audio files using two methods:
1. **Silence-based splitting**: Splits at detected silence periods
2. **Time-based splitting**: Splits into fixed-duration chunks

## Features

- **Automatic silence detection**: Uses energy analysis to identify silence periods
- **Fixed-time splitting**: Split into equal-duration chunks with optional overlap
- **Configurable parameters**: Adjust silence duration, sensitivity, chunk size, and processing steps
- **Output management**: Automatically saves split files to `data/split/` directory
- **Progress tracking**: Shows progress during processing with tqdm progress bars
- **Dry run support**: Test splitting without creating actual files

## Functions

### Silence-Based Splitting

#### `split_wav_by_silence(input_file, ...)`

Main function to split WAV files by silence.

**Parameters:**
- `input_file` (str): Path to the input WAV file
- `output_dir` (str, optional): Output directory for split files. Defaults to `data/split/`
- `min_silence_length` (float): Minimum silence duration for splitting (seconds). Default: 3.0
- `silence_threshold` (float): Energy threshold below which signal is considered silent (0.0-1.0). Default: 1e-6
- `step_duration` (float, optional): Time step for energy calculation. Default: min_silence_length/10
- `dry_run` (bool): If True, don't write files, just return split information. Default: False

#### `quick_split_audio(input_file, silence_duration=3.0, sensitivity=1e-6)`

Convenience function for quick audio splitting with common parameters.

### Time-Based Splitting

#### `split_wav_by_time(input_file, ...)`

Main function to split WAV files into fixed-duration chunks.

**Parameters:**
- `input_file` (str): Path to the input WAV file
- `chunk_duration` (float): Duration of each chunk in seconds. Default: 30.0
- `output_dir` (str, optional): Output directory for split files. Defaults to `data/split/`
- `overlap` (float): Overlap between chunks in seconds. Default: 0.0
- `dry_run` (bool): If True, don't write files, just return split information. Default: False

#### `quick_split_by_time(input_file, chunk_seconds=30.0)`

Convenience function for quick time-based splitting.

**Returns (all functions):**
```python
{
    'success': bool,
    'message': str,
    'output_files': List[str],
    'split_count': int,
    'output_dir': str,
    'total_duration': float,  # time-based only
    'chunk_duration': float,  # time-based only
    'overlap': float         # time-based only
}
```

## Usage Examples

### Python Code

#### Silence-Based Splitting
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

#### Time-Based Splitting
```python
from utils.audio import split_wav_by_time, quick_split_by_time

# Basic time-based splitting (30-second chunks)
result = split_wav_by_time('long_audio.wav')

# Custom chunk duration
result = split_wav_by_time(
    input_file='meeting.wav',
    chunk_duration=10.0,  # 10-second chunks
    overlap=1.0,  # 1-second overlap between chunks
    dry_run=True
)

# Quick time split
result = quick_split_by_time('audio.wav', chunk_seconds=15.0)
```

### Command Line

#### Silence-Based Splitting
```bash
# Basic split
python utils/audio.py split audio_file.wav

# With custom parameters
python utils/audio.py split audio_file.wav \
    --output-dir ./custom_output \
    --min-silence-length 2.0 \
    --silence-threshold 1e-5 \
    --dry-run

# Available options for silence splitting
python utils/audio.py split input_file.wav [OPTIONS]

Options:
  --output-dir DIR              Output directory for split files
  --min-silence-length SECONDS  Minimum silence duration (default: 3.0)
  --silence-threshold THRESHOLD Energy threshold for silence (default: 1e-6)
  --step-duration SECONDS       Processing step duration
  --dry-run                     Test mode - don't create files
```

#### Time-Based Splitting
```bash
# Basic time split (30-second chunks)
python utils/audio.py split_time audio_file.wav

# With custom parameters
python utils/audio.py split_time audio_file.wav \
    --chunk-duration 10.0 \
    --overlap 1.0 \
    --output-dir ./custom_output \
    --dry-run

# Available options for time splitting
python utils/audio.py split_time input_file.wav [OPTIONS]

Options:
  --chunk-duration SECONDS     Duration of each chunk (default: 30.0)
  --overlap SECONDS            Overlap between chunks (default: 0.0)
  --output-dir DIR             Output directory for split files
  --dry-run                    Test mode - don't create files
```

## How It Works

### Silence-Based Splitting
1. **Energy Analysis**: The algorithm calculates the energy of audio windows over time
2. **Silence Detection**: Windows with energy below the threshold are marked as silent
3. **Split Point Identification**: Rising edges (end of silence periods) become split points
4. **File Generation**: Audio segments between split points are saved as separate WAV files

### Time-Based Splitting
1. **Duration Calculation**: Total audio duration is calculated
2. **Chunk Planning**: Audio is divided into fixed-duration chunks with optional overlap
3. **Boundary Handling**: Last chunk includes any remaining audio if it's too short to be a separate chunk
4. **File Generation**: Each time-based chunk is saved as a separate WAV file

## Output Files

Split files are named using different patterns:

- **Silence-based**: `{original_name}_{index:03d}.wav` 
  - Example: `meeting_001.wav`, `meeting_002.wav`
- **Time-based**: `{original_name}_time_{index:03d}.wav`
  - Example: `meeting_time_001.wav`, `meeting_time_002.wav`

## Dependencies

- `scipy`: For audio file I/O and signal processing
- `numpy`: For numerical operations
- `tqdm`: For progress bars
- `os`: For file system operations

## Parameters Tuning

### Silence-Based Splitting
- **Silence Threshold**: Lower values (e.g., 1e-7) detect quieter silences, higher values (e.g., 1e-4) only detect very quiet periods
- **Minimum Silence Length**: Prevents splitting on brief pauses - adjust based on your audio content
- **Step Duration**: Smaller values provide more accurate detection but slower processing

### Time-Based Splitting
- **Chunk Duration**: Choose based on your use case (e.g., 30s for transcription, 10s for detailed analysis)
- **Overlap**: Useful for ensuring continuity in analysis - typically 10-20% of chunk duration
- **Boundary Handling**: Last chunk automatically includes remaining audio if it's too short

## Use Cases

### Silence-Based Splitting
- **Meeting recordings**: Split at natural conversation breaks
- **Lecture recordings**: Split at pauses between topics
- **Interview recordings**: Split at speaker changes
- **Podcast episodes**: Split at segment breaks

### Time-Based Splitting
- **Batch processing**: Process large files in manageable chunks
- **Transcription services**: Send fixed-size chunks to APIs
- **Analysis pipelines**: Consistent chunk sizes for ML models
- **Storage optimization**: Create uniform file sizes for archiving
