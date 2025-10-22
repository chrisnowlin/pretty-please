import React, { useEffect, useState } from 'react';
import { WebSocketClient } from '../../services/websocket';
import type { ProgressMessage } from '../../services/websocket';
import { apiClient } from '../../services/api';

interface ProgressTrackerProps {
  taskId: string;
  onComplete: () => void;
}

export default function ProgressTracker({ taskId, onComplete }: ProgressTrackerProps) {
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState<string | null>(null);
  const [processedFiles, setProcessedFiles] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);
  const [status, setStatus] = useState('loading');
  const [errors, setErrors] = useState<Array<{ file: string; error: string }>>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const wsClient = new WebSocketClient();

    const handleMessage = (message: ProgressMessage) => {
      if (message.type === 'progress') {
        setProgress(message.progress || 0);
        setCurrentFile(message.current_file || null);
        setProcessedFiles(message.processed_files || 0);
        setIsLoading(false);
      } else if (message.type === 'complete') {
        setProgress(100);
        setStatus('completed');
        if (message.errors) {
          setErrors(message.errors);
        }
        setIsLoading(false);
        // Auto-return only if no errors
        if (!message.errors || message.errors.length === 0) {
          setTimeout(() => { onComplete(); }, 3000);
        }
      } else if (message.type === 'error') {
        setStatus('failed');
        if (message.error) {
          setErrors([{ file: 'system', error: message.error }]);
        }
        setIsLoading(false);
      }
    };

    apiClient.getIngestionStatus(taskId).then((statusData) => {
      console.log('Initial status:', statusData);
      setProgress(statusData.progress);
      setCurrentFile(statusData.current_file);
      setProcessedFiles(statusData.processed_files);
      setTotalFiles(statusData.total_files);
      setStatus(statusData.status);
      setErrors(statusData.errors);
      setIsLoading(false);

      // If already completed when we check, auto-return only if no errors
      if (statusData.status === 'completed' && (!statusData.errors || statusData.errors.length === 0)) {
        setTimeout(() => { onComplete(); }, 3000);
      }
    }).catch((error) => {
      console.error('Failed to fetch status:', error);
      setStatus('failed');
      setErrors([{ file: 'system', error: 'Failed to fetch upload status' }]);
      setIsLoading(false);
    });

    wsClient.connect(taskId, handleMessage);

    return () => {
      wsClient.disconnect();
    };
  }, [taskId]); // Removed onComplete from dependencies to prevent reconnection loop

  return (
    <div style={{
      backgroundColor: 'white',
      padding: '2rem',
      borderRadius: '0.5rem',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1.5rem', color: '#2d3748' }}>
        {isLoading ? 'Initializing Upload...' : 'Processing Documents'}
      </h3>

      {isLoading ? (
        <div style={{
          padding: '3rem',
          textAlign: 'center',
          color: '#4a5568'
        }}>
          <div style={{
            width: '3rem',
            height: '3rem',
            margin: '0 auto 1rem',
            border: '4px solid #e2e8f0',
            borderTop: '4px solid #4299e1',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          <div>Preparing to process your documents...</div>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      ) : (
        <React.Fragment>
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: '0.5rem',
              fontSize: '0.875rem',
              color: '#4a5568'
            }}>
              <span>Progress: {processedFiles} / {totalFiles} files</span>
              <span>{progress.toFixed(0)}%</span>
            </div>

            <div style={{
              width: '100%',
              height: '1.5rem',
              backgroundColor: '#e2e8f0',
              borderRadius: '9999px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${progress}%`,
                height: '100%',
                backgroundColor: status === 'failed'
                  ? '#f56565'
                  : status === 'completed' && errors.length > 0
                  ? '#f6ad55'
                  : status === 'completed'
                  ? '#48bb78'
                  : '#4299e1',
                transition: 'width 0.3s ease'
              }} />
            </div>
          </div>

      {currentFile && (status === 'processing' || status === 'queued') && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#ebf8ff',
          borderRadius: '0.375rem',
          marginBottom: '1rem'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#2c5282' }}>
            Currently processing: <strong>{currentFile}</strong>
          </div>
        </div>
      )}

      {status === 'completed' && errors.length === 0 && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#c6f6d5',
          borderRadius: '0.375rem',
          marginBottom: '1rem'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#22543d', fontWeight: 'bold' }}>
            ✓ All documents processed successfully!
          </div>
        </div>
      )}

      {status === 'completed' && errors.length > 0 && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#FEEBC8',
          borderRadius: '0.375rem',
          marginBottom: '1rem'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#7B341E', fontWeight: 'bold' }}>
            ⚠️ Completed with errors — some files failed to process. See details below.
          </div>
        </div>
      )}

      {status === 'failed' && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#fed7d7',
          borderRadius: '0.375rem',
          marginBottom: '1rem'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#c53030', fontWeight: 'bold' }}>
            ✗ Processing failed
          </div>
        </div>
      )}

      {errors.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 'bold', marginBottom: '0.5rem', color: '#c53030' }}>
            Errors:
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {errors.map((error, index) => (
              <div
                key={index}
                style={{
                  padding: '0.75rem',
                  backgroundColor: '#fff5f5',
                  borderLeft: '4px solid #fc8181',
                  borderRadius: '0.25rem',
                  fontSize: '0.875rem'
                }}
              >
                <div style={{ fontWeight: 'bold', color: '#742a2a' }}>{error.file}</div>
                <div style={{ color: '#c53030' }}>{error.error}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {(status === 'completed' || status === 'failed') && (
        <button
          onClick={onComplete}
          style={{
            width: '100%',
            padding: '0.75rem',
            backgroundColor: '#4299e1',
            color: 'white',
            border: 'none',
            borderRadius: '0.375rem',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '1rem'
          }}
        >
          Upload More Documents
        </button>
      )}
        </React.Fragment>
      )}
    </div>
  );
}
