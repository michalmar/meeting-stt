# History Management Documentation

## Overview

The application now includes comprehensive history management functionality that tracks transcription sessions and their associated data. This feature allows you to maintain a complete audit trail of all transcription activities.

## Core Components

### 1. Data Classes

#### `Transcription` Class
Represents an individual transcription for each file:
- `file_name`: Name of the transcribed file
- `file_name_original`: Original filename before processing
- `transcript_text`: The transcription text result
- `language`: Language used for transcription
- `model`: Model used (msft, llm, whisper)
- `temperature`: Temperature setting used
- `diarization`: Diarization setting
- `combine`: Combine setting
- `analysis`: Analysis results if performed
- `timestamp`: When transcription was created (ISO format)
- `status`: Current status (pending, completed, failed)

#### `History` Class
Contains the history of transcriptions:
- `id`: Unique ID of history record
- `user_id`: ID of user making transcription
- `session_id`: ID of session of user
- `transcriptions`: List of Transcription objects
- `timestamp`: ANSI date string (ISO format)
- `visible`: Boolean visibility flag (default: true)
- `type`: Type of history record (default: "transcription")

### 2. Application State

The history is stored in the application lifespan state:
```python
app.state.history = []  # List to store History objects
```

This state is:
- Initialized during app startup
- Cleared during app shutdown
- Accessible throughout the application lifecycle

## API Endpoints

### History Management

#### Create History Record
```
POST /history/create
```
**Parameters:**
- `user_id` (required): User identifier
- `session_id` (required): Session identifier
- `history_type` (optional): Type of history record (default: "transcription")

#### Get User History
```
GET /history/user/{user_id}
```
**Query Parameters:**
- `visible_only` (optional): Show only visible records (default: true)

#### Get Session History
```
GET /history/session/{session_id}
```
**Query Parameters:**
- `visible_only` (optional): Show only visible records (default: true)

#### Get Specific History Record
```
GET /history/{history_id}
```

#### Toggle History Visibility
```
PUT /history/{history_id}/visibility
```
**Parameters:**
- `visible` (required): Boolean visibility flag

#### Get All History
```
GET /history
```
**Query Parameters:**
- `visible_only` (optional): Show only visible records (default: true)
- `limit` (optional): Maximum number of records (default: 100)

### Transcription Management

#### Get Transcriptions from History
```
GET /history/{history_id}/transcriptions
```

#### Add Analysis to Transcription
```
POST /history/{history_id}/transcription/{transcription_index}/analysis
```
**Parameters:**
- `analysis_text` (required): Analysis results text

## Automatic Integration

### Transcription Tracking

When a transcription is submitted via `/submit`, the system automatically:

1. **Creates or Reuses History Record**: 
   - If `user_id` and `session_id` are provided
   - Reuses existing session history or creates new one

2. **Creates Transcription Record**:
   - Captures all transcription parameters
   - Sets initial status to "pending"

3. **Updates During Processing**:
   - Updates status to "completed" when transcript is ready
   - Sets status to "failed" if errors occur
   - Captures transcript text when available

4. **Maintains Audit Trail**:
   - All activities are timestamped
   - Complete parameter history is preserved

## Usage Examples

### Basic History Creation
```python
# Create a new history record
history_record = add_history_record("user123", "session456")

# Create a transcription
transcription = Transcription(
    file_name="audio.wav",
    file_name_original="audio.wav",
    language="en",
    model="whisper"
)

# Add transcription to history
add_transcription_to_history(history_record.id, transcription)
```

### Querying History
```python
# Get all history for a user
user_histories = get_user_history("user123")

# Get history for a specific session
session_histories = get_session_history("session456")

# Get specific history record
history = get_history_by_id("history-uuid")
```

### Testing

Run the test script to verify functionality:
```bash
cd backend
python test_history.py
```

The test script will:
- Create a test history record
- Retrieve history by user and session
- Toggle visibility
- Verify all endpoints work correctly

## Notes

- History is stored in memory and will be lost when the application restarts
- For production use, consider implementing persistent storage (database)
- All timestamps use ISO format for consistency
- The system is designed to be thread-safe for concurrent operations
- History records can be filtered by visibility for soft deletion functionality
