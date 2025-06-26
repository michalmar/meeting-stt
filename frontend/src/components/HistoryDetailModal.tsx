import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { 
  FileAudio, 
  Clock, 
  User, 
  Monitor, 
  Globe, 
  Thermometer,
  Users,
  Combine,
  FileText,
  Eye,
  EyeOff,
  Save,
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { History } from '@/types/history';
import { HistoryAPI } from '@/api/history';

// Simple Badge component
interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'secondary' | 'outline';
  className?: string;
}

const Badge = ({ children, variant = 'default', className = '' }: BadgeProps) => {
  const baseClasses = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold';
  const variantClasses = {
    default: 'bg-primary text-primary-foreground',
    secondary: 'bg-secondary text-secondary-foreground',
    outline: 'border border-input bg-background text-foreground'
  };
  
  return (
    <span className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
};

interface HistoryDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  historyId: string | null;
}

export function HistoryDetailModal({ isOpen, onClose, historyId }: HistoryDetailModalProps) {
  const [history, setHistory] = useState<History | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTranscription, setSelectedTranscription] = useState<number>(0);
  const [analysisText, setAnalysisText] = useState('');
  const [savingAnalysis, setSavingAnalysis] = useState(false);

  useEffect(() => {
    if (isOpen && historyId) {
      fetchHistoryDetails();
    }
  }, [isOpen, historyId]);

  const fetchHistoryDetails = async () => {
    if (!historyId) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await HistoryAPI.getHistoryRecord(historyId);
      setHistory(response.history);
      if (response.history.transcriptions.length > 0) {
        setAnalysisText(response.history.transcriptions[0].analysis || '');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch history details');
    } finally {
      setLoading(false);
    }
  };

  const handleTranscriptionSelect = (index: number) => {
    setSelectedTranscription(index);
    if (history?.transcriptions[index]) {
      setAnalysisText(history.transcriptions[index].analysis || '');
    }
  };

  const handleSaveAnalysis = async () => {
    if (!history || !analysisText.trim()) return;
    
    setSavingAnalysis(true);
    try {
      await HistoryAPI.addAnalysisToTranscription(
        history.id,
        selectedTranscription,
        analysisText
      );
      
      // Update local state
      const updatedHistory = { ...history };
      updatedHistory.transcriptions[selectedTranscription].analysis = analysisText;
      setHistory(updatedHistory);
      
      // Show success message (you might want to add a toast here)
      console.log('Analysis saved successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save analysis');
    } finally {
      setSavingAnalysis(false);
    }
  };

  const toggleVisibility = async () => {
    if (!history) return;
    
    try {
      await HistoryAPI.toggleHistoryVisibility(history.id, !history.visible);
      setHistory({ ...history, visible: !history.visible });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle visibility');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatTime = (milliseconds: number) => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getFullTranscriptText = (chunks: any[]) => {
    if (!chunks || chunks.length === 0) return '';
    return chunks.map(chunk => chunk.text || '').join(' ');
  };

  const getSpeakerColor = (speakerId: string | null) => {
    if (!speakerId) return 'text-gray-600';
    const colors = [
      'text-blue-600',
      'text-green-600', 
      'text-purple-600',
      'text-orange-600',
      'text-red-600',
      'text-indigo-600'
    ];
    const hash = speakerId.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    return colors[Math.abs(hash) % colors.length];
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileAudio className="h-5 w-5" />
            History Details
          </DialogTitle>
          <DialogDescription>
            View and manage transcription history record
          </DialogDescription>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700">
            {error}
          </div>
        )}

        {history && (
          <div className="space-y-4">
            {/* Header Information */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Session Information</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant={history.visible ? "default" : "secondary"}>
                      {history.visible ? (
                        <>
                          <Eye className="h-3 w-3 mr-1" />
                          Visible
                        </>
                      ) : (
                        <>
                          <EyeOff className="h-3 w-3 mr-1" />
                          Hidden
                        </>
                      )}
                    </Badge>
                    <Button variant="outline" size="sm" onClick={toggleVisibility}>
                      {history.visible ? 'Hide' : 'Show'}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="font-medium">User ID</p>
                      <p className="text-muted-foreground">{history.user_id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Monitor className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="font-medium">Session ID</p>
                      <p className="text-muted-foreground">{history.session_id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="font-medium">Created</p>
                      <p className="text-muted-foreground">{formatDateTime(history.timestamp)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="font-medium">Type</p>
                      <p className="text-muted-foreground">{history.type}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Transcriptions */}
            <Card className="flex-1">
              <CardHeader>
                <CardTitle>Transcriptions ({history.transcriptions.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {history.transcriptions.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No transcriptions found</p>
                ) : (
                  <Tabs value={selectedTranscription.toString()} onValueChange={(value) => handleTranscriptionSelect(parseInt(value))}>
                    <TabsList className="grid w-full grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-1 h-auto">
                      {history.transcriptions.map((transcription, index) => (
                        <TabsTrigger 
                          key={index} 
                          value={index.toString()}
                          className="flex items-center gap-2 p-2 text-left justify-start"
                        >
                          {getStatusIcon(transcription.status)}
                          <div className="truncate">
                            <p className="font-medium text-xs truncate">{transcription.file_name_original}</p>
                            <p className="text-xs text-muted-foreground">{transcription.model}</p>
                          </div>
                        </TabsTrigger>
                      ))}
                    </TabsList>

                    {history.transcriptions.map((transcription, index) => (
                      <TabsContent key={index} value={index.toString()} className="mt-4">
                        <ScrollArea className="h-96">
                          <div className="space-y-4">
                            {/* Transcription Details */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <Card>
                                <CardHeader className="pb-2">
                                  <CardTitle className="text-sm">File Information</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-2 text-sm">
                                  <div className="flex items-center gap-2">
                                    <FileAudio className="h-4 w-4" />
                                    <span className="font-medium">Original:</span>
                                    <span className="truncate">{transcription.file_name_original}</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <FileAudio className="h-4 w-4" />
                                    <span className="font-medium">Processed:</span>
                                    <span className="truncate">{transcription.file_name}</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Clock className="h-4 w-4" />
                                    <span className="font-medium">Created:</span>
                                    <span>{formatDateTime(transcription.timestamp)}</span>
                                  </div>
                                </CardContent>
                              </Card>

                              <Card>
                                <CardHeader className="pb-2">
                                  <CardTitle className="text-sm">Settings</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-2 text-sm">
                                  <div className="flex items-center gap-2">
                                    <Monitor className="h-4 w-4" />
                                    <span className="font-medium">Model:</span>
                                    <Badge variant="outline">{transcription.model}</Badge>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Globe className="h-4 w-4" />
                                    <span className="font-medium">Language:</span>
                                    <span>{transcription.language}</span>
                                  </div>
                                  {transcription.temperature !== undefined && (
                                    <div className="flex items-center gap-2">
                                      <Thermometer className="h-4 w-4" />
                                      <span className="font-medium">Temperature:</span>
                                      <span>{transcription.temperature}</span>
                                    </div>
                                  )}
                                  <div className="flex items-center gap-2">
                                    <Users className="h-4 w-4" />
                                    <span className="font-medium">Diarization:</span>
                                    <span>{transcription.diarization}</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Combine className="h-4 w-4" />
                                    <span className="font-medium">Combine:</span>
                                    <span>{transcription.combine}</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    {getStatusIcon(transcription.status)}
                                    <span className="font-medium">Status:</span>
                                    <Badge className={getStatusColor(transcription.status)}>
                                      {transcription.status}
                                    </Badge>
                                  </div>
                                </CardContent>
                              </Card>
                            </div>

                            {/* Transcript Chunks */}
                            {transcription.transcript_chunks && transcription.transcript_chunks.length > 0 && (
                              <Card>
                                <CardHeader>
                                  <div className="flex items-center justify-between">
                                    <CardTitle className="text-sm">Transcript ({transcription.transcript_chunks.length} chunks)</CardTitle>
                                    <div className="text-xs text-muted-foreground">
                                      Total: {getFullTranscriptText(transcription.transcript_chunks).length} characters
                                    </div>
                                  </div>
                                </CardHeader>
                                <CardContent>
                                  <Tabs defaultValue="chunks">
                                    <TabsList className="grid w-full grid-cols-2">
                                      <TabsTrigger value="chunks">Detailed Chunks</TabsTrigger>
                                      <TabsTrigger value="full">Full Text</TabsTrigger>
                                    </TabsList>
                                    
                                    <TabsContent value="chunks" className="mt-4">
                                      <ScrollArea className="h-64 w-full border rounded-md p-3">
                                        <div className="space-y-3">
                                          {transcription.transcript_chunks.map((chunk, chunkIndex) => (
                                            <div key={chunkIndex} className="border-l-2 border-blue-200 pl-3 py-2">
                                              <div className="flex items-center gap-2 mb-1">
                                                <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                                                  {formatTime(chunk.offset)}
                                                </span>
                                                {chunk.speaker_id && (
                                                  <Badge variant="outline" className={`text-xs ${getSpeakerColor(chunk.speaker_id)}`}>
                                                    <Users className="h-3 w-3 mr-1" />
                                                    {chunk.speaker_id}
                                                  </Badge>
                                                )}
                                                {chunk.duration && (
                                                  <span className="text-xs text-muted-foreground">
                                                    Duration: {formatTime(chunk.duration)}
                                                  </span>
                                                )}
                                              </div>
                                              <p className="text-sm leading-relaxed">{chunk.text}</p>
                                              {chunk.language && chunk.language !== transcription.language && (
                                                <div className="mt-1">
                                                  <Badge variant="outline" className="text-xs">
                                                    <Globe className="h-3 w-3 mr-1" />
                                                    {chunk.language}
                                                  </Badge>
                                                </div>
                                              )}
                                            </div>
                                          ))}
                                        </div>
                                      </ScrollArea>
                                    </TabsContent>
                                    
                                    <TabsContent value="full" className="mt-4">
                                      <ScrollArea className="h-64 w-full border rounded-md p-3">
                                        <p className="text-sm whitespace-pre-wrap leading-relaxed">
                                          {getFullTranscriptText(transcription.transcript_chunks)}
                                        </p>
                                      </ScrollArea>
                                    </TabsContent>
                                  </Tabs>
                                </CardContent>
                              </Card>
                            )}

                            {/* Analysis Section */}
                            <Card>
                              <CardHeader>
                                <div className="flex items-center justify-between">
                                  <CardTitle className="text-sm">Analysis</CardTitle>
                                  <Button 
                                    size="sm" 
                                    onClick={handleSaveAnalysis}
                                    disabled={savingAnalysis || !analysisText.trim()}
                                  >
                                    <Save className="h-4 w-4 mr-1" />
                                    {savingAnalysis ? 'Saving...' : 'Save Analysis'}
                                  </Button>
                                </div>
                              </CardHeader>
                              <CardContent>
                                <Textarea
                                  placeholder="Add analysis for this transcription..."
                                  value={analysisText}
                                  onChange={(e) => setAnalysisText(e.target.value)}
                                  className="min-h-24"
                                />
                              </CardContent>
                            </Card>
                          </div>
                        </ScrollArea>
                      </TabsContent>
                    ))}
                  </Tabs>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
