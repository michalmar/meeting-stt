#!/usr/bin/env python3
"""
Test script for the audio splitting functionality.
This script demonstrates how to use the split_wav_by_silence function.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.audio import split_wav_by_silence, quick_split_audio, split_wav_by_time, quick_split_by_time

def test_audio_splitting():
    """Test the audio splitting functionality"""
    
    # Example usage with default parameters
    print("=== Audio Splitting Test ===")
    
    # Check if there are any WAV files in the data directory to test with
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    wav_files = [f for f in os.listdir(data_dir) if f.lower().endswith('.wav')]
    
    if not wav_files:
        print("No WAV files found in data directory for testing.")
        print("Available files:")
        for f in os.listdir(data_dir):
            print(f"  - {f}")
        return
    
    # Use the first WAV file found
    test_file = os.path.join(data_dir, wav_files[0])
    print(f"Testing with file: {test_file}")
    
    # Test with dry run first
    print("\n--- Dry Run Test ---")
    result = split_wav_by_silence(
        input_file=test_file,
        min_silence_length=2.0,  # 2 seconds of silence
        silence_threshold=1e-5,  # Slightly less sensitive
        dry_run=True
    )
    
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Would create {result['split_count']} files")
    
    # Test quick split function
    print("\n--- Quick Split Test (dry run) ---")
    result2 = quick_split_audio(test_file, silence_duration=1.5, sensitivity=1e-5)
    print(f"Quick split result: {result2['message']}")
    
    # Test time-based splitting
    print("\n--- Time-based Split Test (dry run) ---")
    result3 = split_wav_by_time(
        input_file=test_file,
        chunk_duration=10.0,  # 10-second chunks
        overlap=1.0,  # 1-second overlap
        dry_run=True
    )
    
    print(f"Time split success: {result3['success']}")
    print(f"Time split message: {result3['message']}")
    print(f"Would create {result3['split_count']} time-based chunks")
    
    # Test quick time split
    print("\n--- Quick Time Split Test (dry run) ---")
    result4 = quick_split_by_time(test_file, chunk_seconds=15.0)
    print(f"Quick time split result: {result4['message']}")

if __name__ == "__main__":
    test_audio_splitting()
