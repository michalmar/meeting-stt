// Types for history management
export interface TranscriptChunk {
  event_type: string;
  session?: string | null;
  offset: number;
  duration?: number | null;
  text: string;
  speaker_id?: string | null;
  result_id?: string | null;
  filename: string;
  language: string;
}

export interface Transcription {
  file_name: string;
  file_name_original: string;
  transcript_chunks: TranscriptChunk[];
  language?: string;
  model?: string;
  temperature?: number;
  diarization?: string;
  combine?: string;
  analysis?: string;
  timestamp: string;
  status: 'pending' | 'completed' | 'failed';
}

export interface History {
  id: string;
  user_id: string;
  session_id: string;
  transcriptions: Transcription[];
  timestamp: string;
  visible: boolean;
  type: string;
}

export interface HistoryResponse {
  status: string;
  count: number;
  histories: History[];
}

export interface HistoryDetailResponse {
  status: string;
  history: History;
}

export interface TranscriptionsResponse {
  status: string;
  history_id: string;
  count: number;
  transcriptions: Transcription[];
}
