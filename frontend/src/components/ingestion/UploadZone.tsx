import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface UploadZoneProps {
  onUpload: (files: File[]) => void;
  supportedFormats?: string[];
  disabled?: boolean;
  maxFileSizeMB?: number;
}

interface FileWithPreview {
  file: File;
  preview?: string;
  isImage: boolean;
}

export default function UploadZone({ onUpload, supportedFormats, disabled, maxFileSizeMB = 1024 }: UploadZoneProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<FileWithPreview[]>([]);
  const [fileSizeWarnings, setFileSizeWarnings] = useState<Map<string, string>>(new Map());
  const fileInputRef = useRef<HTMLInputElement>(null);

  const IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'];
  const MAX_IMAGE_SIZE_MB = 100; // 100MB for images

  const isImageFile = (file: File): boolean => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    return IMAGE_FORMATS.includes(extension);
  };

  const createPreviews = async (files: File[]) => {
    const warnings = new Map<string, string>();

    const filesWithPreview: FileWithPreview[] = await Promise.all(
      files.map(async (file) => {
        const isImage = isImageFile(file);
        let preview: string | undefined;

        // Check file size and add warnings
        const fileSizeMB = file.size / (1024 * 1024);
        const maxSize = isImage ? MAX_IMAGE_SIZE_MB : maxFileSizeMB;

        if (fileSizeMB > maxSize) {
          warnings.set(file.name, `File size (${fileSizeMB.toFixed(1)}MB) exceeds maximum allowed size (${maxSize}MB)`);
        } else if (fileSizeMB > maxSize * 0.8) {
          warnings.set(file.name, `Large file (${fileSizeMB.toFixed(1)}MB) - upload may take longer`);
        }

        if (isImage) {
          try {
            preview = await new Promise<string>((resolve, reject) => {
              const reader = new FileReader();
              reader.onload = () => resolve(reader.result as string);
              reader.onerror = reject;
              reader.readAsDataURL(file);
            });
          } catch (error) {
            console.error('Failed to create preview for', file.name, error);
          }
        }

        return { file, preview, isImage };
      })
    );

    setFileSizeWarnings(warnings);
    return filesWithPreview;
  };

  // Cleanup preview URLs when component unmounts or files change
  useEffect(() => {
    return () => {
      selectedFiles.forEach((fileWithPreview) => {
        if (fileWithPreview.preview && fileWithPreview.preview.startsWith('blob:')) {
          URL.revokeObjectURL(fileWithPreview.preview);
        }
      });
    };
  }, [selectedFiles]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    const filesWithPreview = await createPreviews(files);
    setSelectedFiles(filesWithPreview);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      const filesWithPreview = await createPreviews(files);
      setSelectedFiles(filesWithPreview);
    }
  };

  const handleUploadClick = () => {
    if (selectedFiles.length > 0) {
      // Check if any files exceed the size limit
      const oversizedFiles = selectedFiles.filter((f) => {
        const isImage = isImageFile(f.file);
        const maxSize = isImage ? MAX_IMAGE_SIZE_MB : maxFileSizeMB;
        return f.file.size > maxSize * 1024 * 1024;
      });

      if (oversizedFiles.length > 0) {
        const fileNames = oversizedFiles.map(f => f.file.name).join(', ');
        if (!confirm(`Warning: ${oversizedFiles.length} file(s) exceed the size limit (${fileNames}). These files will likely fail to upload. Continue anyway?`)) {
          return;
        }
      }

      const files = selectedFiles.map((f) => f.file);
      onUpload(files);
      setSelectedFiles([]);
      setFileSizeWarnings(new Map());
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleRemoveFile = (index: number) => {
    const fileToRemove = selectedFiles[index];
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));

    // Remove warning for this file
    if (fileToRemove) {
      setFileSizeWarnings((prev) => {
        const newWarnings = new Map(prev);
        newWarnings.delete(fileToRemove.file.name);
        return newWarnings;
      });
    }
  };

  const handleBrowseClick = (e?: React.MouseEvent) => {
    if (e) {
      e.stopPropagation();
    }
    fileInputRef.current?.click();
  };

  // Generate accept attribute from supported formats
  const acceptAttribute = supportedFormats?.join(',') || '*';

  return (
     <div style={{
       backgroundColor: colors.bg.primary,
       padding: '2rem',
       borderRadius: '0.5rem',
       boxShadow: `0 2px 4px ${colors.shadow}`
     }}>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
         style={{
           border: `2px dashed ${isDragging ? colors.button.active : colors.border}`,
           borderRadius: '0.5rem',
           padding: '3rem',
           textAlign: 'center',
           backgroundColor: isDragging ? colors.bg.secondary : colors.bg.tertiary,
           cursor: disabled ? 'not-allowed' : 'pointer',
           opacity: disabled ? 0.5 : 1,
           transition: 'all 0.2s'
         }}
        onClick={disabled ? undefined : handleBrowseClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptAttribute}
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          disabled={disabled}
        />

        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📁</div>
        <div style={{ fontSize: '1.125rem', fontWeight: 'bold', marginBottom: '0.5rem', color: colors.text.primary }}>
          {disabled ? 'Select a collection first' : 'Drag and drop files here'}
        </div>
        <div style={{ color: colors.text.secondary, marginBottom: '1rem' }}>
          or
        </div>
        <button
          onClick={handleBrowseClick}
          disabled={disabled}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: disabled ? colors.bg.tertiary : colors.button.active,
            color: disabled ? colors.text.tertiary : 'white',
            border: 'none',
            borderRadius: '0.375rem',
            cursor: disabled ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            fontSize: '1rem',
            transition: 'all 0.2s',
          }}
        >
          Browse Files
        </button>
        {supportedFormats && (
          <div style={{ fontSize: '0.875rem', color: colors.text.tertiary, marginTop: '1rem' }}>
            Accepted formats: {supportedFormats.join(', ')}
          </div>
        )}
      </div>

      {selectedFiles.length > 0 && (
        <div style={{ marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 'bold', marginBottom: '1rem', color: colors.text.primary }}>
            Selected Files ({selectedFiles.length})
          </h3>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
              gap: '1rem',
              marginBottom: '1.5rem',
            }}
          >
            {selectedFiles.map((fileWithPreview, index) => (
              <div
                key={index}
                style={{
                  position: 'relative',
                  backgroundColor: colors.bg.tertiary,
                  borderRadius: '0.375rem',
                  overflow: 'hidden',
                  border: `1px solid ${colors.border}`,
                }}
              >
                {/* Remove button */}
                <button
                  onClick={() => handleRemoveFile(index)}
                  style={{
                    position: 'absolute',
                    top: '0.25rem',
                    right: '0.25rem',
                    width: '1.5rem',
                    height: '1.5rem',
                    backgroundColor: colors.status.error,
                    color: 'white',
                    border: 'none',
                    borderRadius: '50%',
                    cursor: 'pointer',
                    fontSize: '1rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 10,
                  }}
                >
                  ×
                </button>

                {/* Preview or icon */}
                {fileWithPreview.isImage && fileWithPreview.preview ? (
                  <div
                    style={{
                      width: '100%',
                      height: '120px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: colors.bg.secondary,
                      position: 'relative',
                    }}
                  >
                    <img
                      src={fileWithPreview.preview}
                      alt={fileWithPreview.file.name}
                      style={{
                        maxWidth: '100%',
                        maxHeight: '100%',
                        objectFit: 'contain',
                      }}
                    />
                    {/* Image indicator badge */}
                    <div
                      style={{
                        position: 'absolute',
                        bottom: '0.25rem',
                        left: '0.25rem',
                        backgroundColor: colors.button.active,
                        color: 'white',
                        padding: '0.125rem 0.375rem',
                        borderRadius: '0.25rem',
                        fontSize: '0.625rem',
                        fontWeight: 'bold',
                      }}
                    >
                      🖼️ IMAGE
                    </div>
                  </div>
                ) : (
                  <div
                    style={{
                      width: '100%',
                      height: '120px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '3rem',
                    }}
                  >
                    📄
                  </div>
                )}

                {/* File info */}
                <div style={{ padding: '0.5rem' }}>
                  <div
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                      color: colors.text.primary,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                    title={fileWithPreview.file.name}
                  >
                    {fileWithPreview.file.name}
                  </div>
                  <div style={{ fontSize: '0.625rem', color: colors.text.secondary, marginTop: '0.25rem' }}>
                    {fileWithPreview.file.size < 1024 * 1024
                      ? `${(fileWithPreview.file.size / 1024).toFixed(1)} KB`
                      : `${(fileWithPreview.file.size / (1024 * 1024)).toFixed(1)} MB`
                    }
                  </div>
                  {/* Size warning */}
                  {fileSizeWarnings.has(fileWithPreview.file.name) && (
                    <div style={{
                      fontSize: '0.625rem',
                      color: fileSizeWarnings.get(fileWithPreview.file.name)?.includes('exceeds') ? '#DC2626' : '#F59E0B',
                      marginTop: '0.25rem',
                      fontWeight: '500',
                    }}>
                      {fileSizeWarnings.get(fileWithPreview.file.name)?.includes('exceeds') ? '⚠️ ' : '⏱️ '}
                      {fileSizeWarnings.get(fileWithPreview.file.name)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={handleUploadClick}
            style={{
              width: '100%',
              padding: '0.75rem',
              backgroundColor: colors.status.success,
              color: 'white',
              border: 'none',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              fontWeight: 'bold',
              fontSize: '1rem',
            }}
          >
            Upload & Process {selectedFiles.length} File{selectedFiles.length !== 1 ? 's' : ''}
          </button>
        </div>
      )}
    </div>
  );
}
