#!/usr/bin/env python3
"""
Test script for the audio splitting functionality.
This script demonstrates how to use the split_wav_by_silence function.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.audio import split_wav_by_silence, quick_split_audio, split_wav_by_time, quick_split_by_time, join_wav_by_time, quick_join_by_time, quick_join_filenames

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
    # test_file ="./data/upload_upload_upload_KREDO - Sample conversation - Ukrainian.wav"
    print(f"Testing with file: {test_file}")
    
    # Test with dry run first
    print("\n--- Dry Run Test ---")
    result = split_wav_by_silence(
        input_file=test_file,
        min_silence_length=1.0,  # 2 seconds of silence
        silence_threshold=1e-5,  # Slightly less sensitive
        dry_run=True
    )
    
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Would create {result['split_count']} files")
    
    # Test quick split function
    print("\n--- Quick Split Test (dry run) ---")
    result2 = quick_split_audio(test_file, silence_duration=1.0, sensitivity=1e-5)
    print(f"Quick split success: {result2}")
    print(f"Quick split result: {result2['message']}")
    test_files = result2.get('output_files', [])
    if test_files:
        print(f"{len(test_files)} have been created:")
    else:
        print("No files created in quick split test")

    # # Test time-based splitting
    # print("\n--- Time-based Split Test (dry run) ---")
    # result3 = split_wav_by_time(
    #     input_file=test_file,
    #     chunk_duration=10.0,  # 10-second chunks
    #     overlap=1.0,  # 1-second overlap
    #     dry_run=True
    # )
    
    # print(f"Time split success: {result3['success']}")
    # print(f"Time split message: {result3['message']}")
    # print(f"Would create {result3['split_count']} time-based chunks")
    
    # # Test quick time split
    # print("\n--- Quick Time Split Test (dry run) ---")
    # result4 = quick_split_by_time(test_file, chunk_seconds=15.0)
    # print(f"Quick time split result: {result4['message']}")
    
    # # Test joining functionality
    # print("\n--- Join Files Test (dry run) ---")
    # result5 = join_wav_by_time(
    #     max_duration=30.0,  # 30 seconds max per joined file
    #     output_prefix="test_joined",
    #     dry_run=True
    # )
    
    # print(f"Join success: {result5['success']}")
    # print(f"Join message: {result5['message']}")
    # if result5['success']:
    #     print(f"Would join {result5.get('input_files_processed', 0)} files into {result5['join_count']} larger files")
    
    # # Test quick join
    # print("\n--- Quick Join Test (dry run) ---")
    # result6 = quick_join_by_time(max_minutes=0.5)  # 30 seconds
    # print(f"Quick join result: {result6['message']}")
    
    # Test joining specific files by filename
    print("\n--- Join Specific Files Test (dry run) ---")
    # Get a few split files to test with
    # data_dir = os.path.join(os.path.dirname(__file__), 'data', 'split')
    # test_files = []
    # for f in os.listdir(data_dir):
    #     if f.endswith('.wav') and '_time_' not in f and not f.startswith('joined_'):
    #         test_files.append(os.path.join(data_dir, f))
    #         if len(test_files) >= 3:  # Take first 3 files
    #             break
    
    if test_files:
        result7 = join_wav_by_time(
            filenames=test_files,
            max_duration=20.0,
            output_prefix="test_specific",
            dry_run=True
        )
        print(f"Specific files join success: {result7['success']}")
        print(f"Specific files join message: {result7['message']}")
        
        # Test quick join filenames
        print("\n--- Quick Join Filenames Test (dry run) ---")
        result8 = quick_join_filenames(test_files, max_minutes=0.3, output_prefix="quick_specific")
        print(f"Quick join filenames result: {result8['message']}")
    else:
        print("No suitable files found for specific filename testing")

if __name__ == "__main__":
    test_audio_splitting()
