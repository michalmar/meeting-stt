import { History } from '@/types/history';

// Demo data for testing the History interface
export const demoHistoryData: History[] = [
  {
    id: "hist-001",
    user_id: "user_12345",
    session_id: "session_20250626_001",
    type: "transcription",
    visible: true,
    timestamp: "2025-06-26T10:30:00.000Z",
    transcriptions: [
      {
        file_name: "upload_meeting_audio.wav",
        file_name_original: "meeting_audio.wav",
        transcript_chunks: [
          {
            event_type: "transcribed",
            session: "session_20250626_001",
            offset: 0,
            duration: 5000,
            text: "Welcome to today's meeting.",
            speaker_id: "Speaker_1",
            result_id: "result_001",
            filename: "meeting_audio.wav",
            language: "en"
          },
          {
            event_type: "transcribed",
            session: "session_20250626_001",
            offset: 5000,
            duration: 8000,
            text: "We will be discussing the quarterly results and our plans for the next quarter.",
            speaker_id: "Speaker_1",
            result_id: "result_002",
            filename: "meeting_audio.wav",
            language: "en"
          },
          {
            event_type: "transcribed",
            session: "session_20250626_001",
            offset: 13000,
            duration: 4000,
            text: "Let's start with the sales figures from John.",
            speaker_id: "Speaker_1",
            result_id: "result_003",
            filename: "meeting_audio.wav",
            language: "en"
          },
          {
            event_type: "transcribed",
            session: "session_20250626_001",
            offset: 17000,
            duration: 6000,
            text: "Thank you. Our Q1 sales exceeded expectations by 15%.",
            speaker_id: "Speaker_2",
            result_id: "result_004",
            filename: "meeting_audio.wav",
            language: "en"
          }
        ],
        language: "en",
        model: "whisper",
        temperature: 0.0,
        diarization: "enabled",
        combine: "true",
        analysis: "This meeting transcript shows a professional business discussion focused on quarterly performance review. Key topics include sales results and future planning.",
        timestamp: "2025-06-26T10:30:15.000Z",
        status: "completed"
      },
      {
        file_name: "upload_interview_recording.wav",
        file_name_original: "interview_recording.wav",
        transcript_chunks: [
          {
            event_type: "transcribed",
            session: "session_20250626_001",
            offset: 0,
            duration: 3000,
            text: "Thank you for joining us today.",
            speaker_id: "Interviewer",
            result_id: "result_005",
            filename: "interview_recording.wav",
            language: "en"
          },
          {
            event_type: "transcribed",
            session: "session_20250626_001",
            offset: 3000,
            duration: 7000,
            text: "Can you tell us about your experience with customer service?",
            speaker_id: "Interviewer",
            result_id: "result_006",
            filename: "interview_recording.wav",
            language: "en"
          }
        ],
        language: "en",
        model: "llm",
        temperature: 0.2,
        diarization: "disabled",
        combine: "false",
        analysis: "",
        timestamp: "2025-06-26T10:45:30.000Z",
        status: "completed"
      }
    ]
  },
  {
    id: "hist-002",
    user_id: "user_67890",
    session_id: "session_20250626_002",
    type: "transcription",
    visible: true,
    timestamp: "2025-06-26T11:15:00.000Z",
    transcriptions: [
      {
        file_name: "upload_conference_call.wav",
        file_name_original: "conference_call.wav",
        transcript_chunks: [],
        language: "en",
        model: "msft",
        temperature: 0.1,
        diarization: "enabled",
        combine: "true",
        analysis: "",
        timestamp: "2025-06-26T11:15:20.000Z",
        status: "pending"
      }
    ]
  },
  {
    id: "hist-003",
    user_id: "user_54321",
    session_id: "session_20250625_001",
    type: "transcription",
    visible: false,
    timestamp: "2025-06-25T14:20:00.000Z",
    transcriptions: [
      {
        file_name: "upload_webinar_audio.wav",
        file_name_original: "webinar_audio.wav",
        transcript_chunks: [
          {
            event_type: "transcribed",
            session: "session_20250625_001",
            offset: 0,
            duration: 12000,
            text: "In today's webinar, we'll explore the latest trends in artificial intelligence and machine learning.",
            speaker_id: "Presenter",
            result_id: "result_007",
            filename: "webinar_audio.wav",
            language: "en"
          }
        ],
        language: "en",
        model: "whisper",
        temperature: 0.0,
        diarization: "disabled",
        combine: "false",
        analysis: "Educational content focusing on AI/ML trends. Suitable for technical audience.",
        timestamp: "2025-06-25T14:25:10.000Z",
        status: "completed"
      }
    ]
  },
  {
    id: "hist-004",
    user_id: "user_11111",
    session_id: "session_20250626_003",
    type: "transcription",
    visible: true,
    timestamp: "2025-06-26T09:00:00.000Z",
    transcriptions: [
      {
        file_name: "upload_presentation.wav",
        file_name_original: "presentation.wav",
        transcript_chunks: [],
        language: "en",
        model: "llm",
        temperature: 0.3,
        diarization: "enabled",
        combine: "true",
        analysis: "",
        timestamp: "2025-06-26T09:05:00.000Z",
        status: "failed"
      },
      {
        file_name: "upload_backup_audio.wav",
        file_name_original: "backup_audio.wav",
        transcript_chunks: [
          {
            event_type: "transcribed",
            session: "session_20250626_003",
            offset: 0,
            duration: 8000,
            text: "This is a backup recording of the presentation for quality assurance purposes.",
            speaker_id: null,
            result_id: "result_008",
            filename: "backup_audio.wav",
            language: "en"
          }
        ],
        language: "en",
        model: "whisper",
        temperature: 0.0,
        diarization: "disabled",
        combine: "false",
        analysis: "",
        timestamp: "2025-06-26T09:10:00.000Z",
        status: "completed"
      }
    ]
  }
];
