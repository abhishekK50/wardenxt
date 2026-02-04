'use client';

import { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Loader2, HelpCircle } from 'lucide-react';
import VoiceResponsePopup from './VoiceResponsePopup';
import VoiceCommandsHelp from './VoiceCommandsHelp';

type RecordingState = 'idle' | 'recording' | 'processing' | 'playing';

interface VoiceResponse {
  transcript: string;
  response_text: string;
  audio_base64?: string;
  action_taken?: string;
  incident_ids?: string[];
  confidence: number;
}

export default function VoiceCommander() {
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [response, setResponse] = useState<VoiceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const [permissionGranted, setPermissionGranted] = useState<boolean | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      if (audioElementRef.current) {
        audioElementRef.current.pause();
      }
    };
  }, []);

  const requestMicrophonePermission = async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop()); // Stop immediately, just testing permission
      setPermissionGranted(true);
      return true;
    } catch (err) {
      console.error('Microphone permission denied:', err);
      setPermissionGranted(false);
      setError('Microphone access is required for voice commands. Please grant permission in your browser settings.');
      return false;
    }
  };

  const startRecording = async () => {
    try {
      setError(null);
      setResponse(null);

      // Request permission if not already granted
      if (permissionGranted === null || permissionGranted === false) {
        const granted = await requestMicrophonePermission();
        if (!granted) return;
      }

      // Get media stream
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());

        // Process recorded audio
        await processRecording();
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;

      setRecordingState('recording');
      setRecordingTime(0);

      // Start timer
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      // Auto-stop after 5 seconds
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          stopRecording();
        }
      }, 5000);

    } catch (err) {
      console.error('Failed to start recording:', err);
      setError('Failed to access microphone. Please check your browser permissions.');
      setRecordingState('idle');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();

      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    }
  };

  const processRecording = async () => {
    try {
      setRecordingState('processing');

      // Create blob from recorded chunks
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

      // Send to backend
      const formData = new FormData();
      formData.append('audio', audioBlob, 'voice_query.webm');

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const response = await fetch(`${apiUrl}/api/voice/query`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data: VoiceResponse = await response.json();
      setResponse(data);

      // Auto-play audio response if available
      if (data.audio_base64) {
        playAudioResponse(data.audio_base64);
      } else {
        setRecordingState('idle');
      }

    } catch (err) {
      console.error('Failed to process recording:', err);
      setError(err instanceof Error ? err.message : 'Failed to process voice query');
      setRecordingState('idle');
    }
  };

  const playAudioResponse = (audioBase64: string) => {
    try {
      setRecordingState('playing');

      // Convert base64 to blob
      const audioData = atob(audioBase64);
      const arrayBuffer = new ArrayBuffer(audioData.length);
      const uint8Array = new Uint8Array(arrayBuffer);

      for (let i = 0; i < audioData.length; i++) {
        uint8Array[i] = audioData.charCodeAt(i);
      }

      const audioBlob = new Blob([uint8Array], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);

      // Play audio
      const audio = new Audio(audioUrl);
      audioElementRef.current = audio;

      audio.onended = () => {
        setRecordingState('idle');
        URL.revokeObjectURL(audioUrl);
      };

      audio.onerror = (err) => {
        console.error('Audio playback error:', err);
        setRecordingState('idle');
        URL.revokeObjectURL(audioUrl);
      };

      audio.play().catch(err => {
        console.error('Failed to play audio:', err);
        setRecordingState('idle');
      });

    } catch (err) {
      console.error('Failed to play audio response:', err);
      setRecordingState('idle');
    }
  };

  const handleButtonClick = () => {
    if (recordingState === 'idle') {
      startRecording();
    } else if (recordingState === 'recording') {
      stopRecording();
    }
  };

  const closeResponse = () => {
    setResponse(null);
    setError(null);
  };

  // Button styles based on state
  const getButtonStyles = () => {
    switch (recordingState) {
      case 'recording':
        return 'bg-red-600 hover:bg-red-700 animate-pulse';
      case 'processing':
        return 'bg-blue-600 cursor-wait';
      case 'playing':
        return 'bg-green-600';
      default:
        return 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 hover:scale-110';
    }
  };

  return (
    <>
      {/* Voice Response Popup */}
      {response && (
        <VoiceResponsePopup
          response={response}
          onClose={closeResponse}
          isPlaying={recordingState === 'playing'}
        />
      )}

      {/* Help Modal */}
      {showHelp && <VoiceCommandsHelp onClose={() => setShowHelp(false)} />}

      {/* Voice Commander Button */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
        {/* Error Message */}
        {error && !response && (
          <div className="bg-red-900/90 border border-red-500 text-red-200 px-4 py-3 rounded-lg shadow-2xl max-w-sm backdrop-blur-sm">
            <p className="text-sm">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-xs text-red-400 hover:text-red-300 mt-1"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Recording Timer */}
        {recordingState === 'recording' && (
          <div className="bg-red-900/90 border border-red-500 text-red-200 px-4 py-2 rounded-lg shadow-2xl backdrop-blur-sm">
            <p className="text-sm font-mono">Recording... {recordingTime}s / 5s</p>
          </div>
        )}

        {/* Processing Indicator */}
        {recordingState === 'processing' && (
          <div className="bg-blue-900/90 border border-blue-500 text-blue-200 px-4 py-2 rounded-lg shadow-2xl backdrop-blur-sm">
            <p className="text-sm">Processing your request...</p>
          </div>
        )}

        {/* Button Group */}
        <div className="flex items-center gap-2">
          {/* Help Button */}
          <button
            onClick={() => setShowHelp(true)}
            className="w-10 h-10 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white shadow-lg transition-all duration-200 flex items-center justify-center"
            title="Voice Commands Help"
          >
            <HelpCircle className="h-5 w-5" />
          </button>

          {/* Main Voice Button */}
          <button
            onClick={handleButtonClick}
            disabled={recordingState === 'processing' || recordingState === 'playing'}
            className={`w-16 h-16 rounded-full shadow-2xl transition-all duration-200 flex items-center justify-center ${getButtonStyles()}`}
            title={recordingState === 'recording' ? 'Stop Recording' : 'Start Voice Command'}
          >
            {recordingState === 'processing' ? (
              <Loader2 className="h-8 w-8 text-white animate-spin" />
            ) : recordingState === 'recording' ? (
              <MicOff className="h-8 w-8 text-white" />
            ) : (
              <Mic className="h-8 w-8 text-white" />
            )}
          </button>
        </div>
      </div>
    </>
  );
}
