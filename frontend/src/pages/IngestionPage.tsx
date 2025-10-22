import React, { useState, useCallback } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { getThemeColors } from '../styles/theme';
import { useQuery } from '@tanstack/react-query';
import UploadZone from '../components/ingestion/UploadZone';
import ProgressTracker from '../components/ingestion/ProgressTracker';
import CollectionSelector from '../components/collections/CollectionSelector';
import { apiClient } from '../services/api';

export default function IngestionPage() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [selectedCollection, setSelectedCollection] = useState('');
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data: collections, refetch: refetchCollections } = useQuery({
    queryKey: ['collections'],
    queryFn: () => apiClient.getCollections(),
  });

  const { data: supportedFormats } = useQuery({
    queryKey: ['supported-formats'],
    queryFn: () => apiClient.getSupportedFormats(),
  });

  const handleCollectionCreated = (collectionName: string) => {
    // Refresh collections list
    refetchCollections();
  };

  const handleUpload = async (files: File[]) => {
    if (!selectedCollection) {
      setErrorMessage('Please select a collection first');
      return;
    }

    // Clear any previous errors
    setErrorMessage(null);

    console.log('Starting upload, files:', files);
    try {
      setIsUploading(true);
      console.log('Set isUploading=true');
      setUploadedFiles(files);
      const response = await apiClient.uploadDocuments(files, selectedCollection);
      console.log('Upload response:', response);
      setCurrentTaskId(response.task_id);
      setIsUploading(false);
      console.log('Set isUploading=false, taskId:', response.task_id);
    } catch (error) {
      console.error('Upload error:', error);
      setIsUploading(false);
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      setErrorMessage(`Upload failed: ${errorMsg}`);
    }
  };

  const handleComplete = useCallback(() => {
    setCurrentTaskId(null);
    setUploadedFiles([]);
    setErrorMessage(null);
  }, []); // Empty dependency array since setState functions never change

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Error Message Banner */}
      {errorMessage && (
        <div style={{
          backgroundColor: '#FEE2E2',
          border: '1px solid #EF4444',
          borderRadius: '0.5rem',
          padding: '1rem',
          marginBottom: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.25rem' }}>⚠️</span>
            <span style={{ color: '#991B1B', fontWeight: '500' }}>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            style={{
              background: 'none',
              border: 'none',
              color: '#991B1B',
              fontSize: '1.25rem',
              cursor: 'pointer',
              padding: '0.25rem 0.5rem',
            }}
          >
            ✕
          </button>
        </div>
      )}

      <div style={{
        backgroundColor: colors.bg.secondary,
        padding: '2rem',
        borderRadius: '0.5rem',
        boxShadow: `0 2px 4px ${colors.shadow}`,
        marginBottom: '2rem',
        transition: 'all 0.2s',
      }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem', color: colors.text.primary }}>
          Upload Documents
        </h2>

        {collections && (
          <CollectionSelector
            collections={collections.collections}
            selectedCollection={selectedCollection}
            onSelect={setSelectedCollection}
            onCollectionCreated={handleCollectionCreated}
          />
        )}

         {supportedFormats && (
           <div style={{
             marginTop: '1rem',
             padding: '1rem',
             backgroundColor: colors.bg.tertiary,
             borderRadius: '0.375rem',
             fontSize: '0.875rem',
             color: colors.text.secondary
          }}>
            <div><strong>Supported formats:</strong> {supportedFormats.formats.join(', ')}</div>
            <div><strong>Maximum file size:</strong> {supportedFormats.max_file_size_mb}MB</div>
          </div>
        )}
      </div>

      {isUploading ? (
        <div style={{
          backgroundColor: 'white',
          padding: '3rem',
          borderRadius: '0.5rem',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center'
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
          <div style={{ color: '#4a5568', fontSize: '1rem' }}>
            Uploading files...
          </div>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      ) : currentTaskId ? (
        <ProgressTracker taskId={currentTaskId} onComplete={handleComplete} />
      ) : (
        <UploadZone
          onUpload={handleUpload}
          supportedFormats={supportedFormats?.formats}
          maxFileSizeMB={supportedFormats?.max_file_size_mb}
          disabled={!selectedCollection}
        />
      )}
    </div>
  );
}
