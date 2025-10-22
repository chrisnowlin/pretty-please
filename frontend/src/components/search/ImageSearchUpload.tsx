import React, { useState, useRef } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface ImageSearchUploadProps {
  onImageSelect: (file: File) => void;
  disabled?: boolean;
}

const MAX_IMAGE_SIZE_MB = 20;
const SUPPORTED_IMAGE_TYPES = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'];

export default function ImageSearchUpload({ onImageSelect, disabled }: ImageSearchUploadProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateImage = (file: File): string | null => {
    // Check file type
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED_IMAGE_TYPES.includes(extension)) {
      return `Unsupported file type. Please upload one of: ${SUPPORTED_IMAGE_TYPES.join(', ')}`;
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > MAX_IMAGE_SIZE_MB) {
      return `File size exceeds ${MAX_IMAGE_SIZE_MB}MB limit. Current size: ${fileSizeMB.toFixed(2)}MB`;
    }

    return null;
  };

  const handleFileSelect = async (file: File) => {
    setError(null);

    const validationError = validateImage(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setSelectedImage(file);

    // Create preview
    try {
      const reader = new FileReader();
      reader.onload = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    } catch (err) {
      console.error('Failed to create preview:', err);
      setError('Failed to create image preview');
    }

    // Notify parent component
    onImageSelect(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]); // Only take the first file
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleClear = () => {
    setSelectedImage(null);
    setPreview(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div style={{ marginBottom: '1rem' }}>
      {!selectedImage ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={disabled ? undefined : handleBrowseClick}
          style={{
            border: `2px dashed ${isDragging ? colors.button.active : colors.border}`,
            borderRadius: '0.5rem',
            padding: '2rem',
            textAlign: 'center',
            backgroundColor: isDragging ? colors.bg.secondary : colors.bg.tertiary,
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.5 : 1,
            transition: 'all 0.2s',
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={SUPPORTED_IMAGE_TYPES.join(',')}
            onChange={handleInputChange}
            style={{ display: 'none' }}
            disabled={disabled}
          />

          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🖼️</div>
          <div style={{ fontSize: '1.125rem', fontWeight: 'bold', marginBottom: '0.5rem', color: colors.text.primary }}>
            {disabled ? 'Select a collection first' : 'Drop an image here'}
          </div>
          <div style={{ color: colors.text.secondary, marginBottom: '1rem' }}>
            or click to browse
          </div>
          <div style={{ fontSize: '0.875rem', color: colors.text.tertiary }}>
            Supported formats: {SUPPORTED_IMAGE_TYPES.join(', ')}
            <br />
            Maximum size: {MAX_IMAGE_SIZE_MB}MB
          </div>
        </div>
      ) : (
        <div
          style={{
            backgroundColor: colors.bg.tertiary,
            borderRadius: '0.5rem',
            border: `1px solid ${colors.border}`,
            overflow: 'hidden',
          }}
        >
          {/* Image Preview */}
          {preview && (
            <div
              style={{
                width: '100%',
                maxHeight: '300px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: colors.bg.secondary,
                padding: '1rem',
              }}
            >
              <img
                src={preview}
                alt={selectedImage.name}
                style={{
                  maxWidth: '100%',
                  maxHeight: '300px',
                  objectFit: 'contain',
                  borderRadius: '0.25rem',
                }}
              />
            </div>
          )}

          {/* Image Info */}
          <div style={{ padding: '1rem' }}>
            <div
              style={{
                fontSize: '0.875rem',
                fontWeight: 'bold',
                color: colors.text.primary,
                marginBottom: '0.5rem',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
              title={selectedImage.name}
            >
              {selectedImage.name}
            </div>
            <div style={{ fontSize: '0.75rem', color: colors.text.secondary, marginBottom: '1rem' }}>
              {formatFileSize(selectedImage.size)}
            </div>

            {/* Clear Button */}
            <button
              onClick={handleClear}
              style={{
                width: '100%',
                padding: '0.5rem',
                backgroundColor: colors.status.error,
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '0.875rem',
                transition: 'opacity 0.2s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.9')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
            >
              Clear Image
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div
          style={{
            marginTop: '1rem',
            backgroundColor: '#fed7d7',
            color: '#c53030',
            padding: '0.75rem',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
          }}
        >
          {error}
        </div>
      )}
    </div>
  );
}
