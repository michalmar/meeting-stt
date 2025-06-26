import { HistoryResponse, HistoryDetailResponse, TranscriptionsResponse } from '@/types/history';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class HistoryAPI {
  // Get all history records
  static async getAllHistory(visibleOnly = true, limit = 100): Promise<HistoryResponse> {
    const params = new URLSearchParams({
      visible_only: visibleOnly.toString(),
      limit: limit.toString(),
    });
    
    const response = await fetch(`${API_BASE_URL}/history?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch history: ${response.statusText}`);
    }
    return response.json();
  }

  // Get history for a specific user
  static async getUserHistory(userId: string, visibleOnly = true): Promise<HistoryResponse> {
    const params = new URLSearchParams({
      visible_only: visibleOnly.toString(),
    });
    
    const response = await fetch(`${API_BASE_URL}/history/user/${userId}?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch user history: ${response.statusText}`);
    }
    return response.json();
  }

  // Get history for a specific session
  static async getSessionHistory(sessionId: string, visibleOnly = true): Promise<HistoryResponse> {
    const params = new URLSearchParams({
      visible_only: visibleOnly.toString(),
    });
    
    const response = await fetch(`${API_BASE_URL}/history/session/${sessionId}?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch session history: ${response.statusText}`);
    }
    return response.json();
  }

  // Get specific history record
  static async getHistoryRecord(historyId: string): Promise<HistoryDetailResponse> {
    const response = await fetch(`${API_BASE_URL}/history/${historyId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch history record: ${response.statusText}`);
    }
    return response.json();
  }

  // Get transcriptions from history
  static async getTranscriptionsFromHistory(historyId: string): Promise<TranscriptionsResponse> {
    const response = await fetch(`${API_BASE_URL}/history/${historyId}/transcriptions`);
    if (!response.ok) {
      throw new Error(`Failed to fetch transcriptions: ${response.statusText}`);
    }
    return response.json();
  }

  // Toggle history visibility
  static async toggleHistoryVisibility(historyId: string, visible: boolean): Promise<any> {
    const formData = new FormData();
    formData.append('visible', visible.toString());
    
    const response = await fetch(`${API_BASE_URL}/history/${historyId}/visibility`, {
      method: 'PUT',
      body: formData,
    });
    if (!response.ok) {
      throw new Error(`Failed to toggle visibility: ${response.statusText}`);
    }
    return response.json();
  }

  // Add analysis to transcription
  static async addAnalysisToTranscription(
    historyId: string, 
    transcriptionIndex: number, 
    analysisText: string
  ): Promise<any> {
    const formData = new FormData();
    formData.append('analysis_text', analysisText);
    
    const response = await fetch(
      `${API_BASE_URL}/history/${historyId}/transcription/${transcriptionIndex}/analysis`,
      {
        method: 'POST',
        body: formData,
      }
    );
    if (!response.ok) {
      throw new Error(`Failed to add analysis: ${response.statusText}`);
    }
    return response.json();
  }
}
