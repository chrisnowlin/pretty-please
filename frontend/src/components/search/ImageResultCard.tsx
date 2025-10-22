import React, { useState } from 'react';
import type { SearchResult } from '../../services/api';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface ImageResultCardProps {
  result: SearchResult;
}

export default function ImageResultCard({ result }: ImageResultCardProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [showModal, setShowModal] = useState(false);
  const [imageError, setImageError] = useState(false);

  if (!result.image_metadata) {
    return null;
  }

  const { thumbnail_url, full_image_url, width, height, format, file_size } = result.image_metadata;
  const fileSizeKB = Math.round(file_size / 1024);

  const handleImageError = () => {
    setImageError(true);
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = full_image_url;
    link.download = result.metadata.source || 'image';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <React.Fragment>
      <div
        style={{
          backgroundColor: colors.bg.secondary,
          borderRadius: '0.5rem',
          boxShadow: `0 2px 4px ${colors.shadow}`,
          overflow: 'hidden',
          cursor: 'pointer',
          transition: 'transform 0.2s, box-shadow 0.2s',
          position: 'relative',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = `0 4px 8px ${colors.shadow}`;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = `0 2px 4px ${colors.shadow}`;
        }}
        onClick={() => setShowModal(true)}
      >
        {/* Thumbnail Image */}
        <div
          style={{
            width: '100%',
            height: '200px',
            backgroundColor: colors.bg.tertiary,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
          }}
        >
          {imageError ? (
            <div style={{ textAlign: 'center', color: colors.text.tertiary }}>
              <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>🖼️</div>
              <div style={{ fontSize: '0.875rem' }}>Image not available</div>
            </div>
          ) : (
            <img
              src={thumbnail_url}
              alt={result.metadata.source || 'Image'}
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
              }}
              onError={handleImageError}
            />
          )}
        </div>

        {/* Relevance Score Badge */}
         <div
           style={{
             position: 'absolute',
             top: '0.5rem',
             right: '0.5rem',
             backgroundColor: colors.button.active,
             color: 'white',
             padding: '0.25rem 0.5rem',
             borderRadius: '0.25rem',
             fontSize: '0.75rem',
             fontWeight: 'bold',
           }}
         >
          {Math.round(result.score * 100)}% match
        </div>

        {/* Image Info Footer */}
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
          >
            {result.metadata.source || 'Unknown'}
          </div>

          <div
            style={{
              fontSize: '0.75rem',
              color: colors.text.tertiary,
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: '0.5rem',
            }}
          >
            <span>{width} × {height}px</span>
            <span>{format.toUpperCase()}</span>
            <span>{fileSizeKB} KB</span>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowModal(true);
              }}
              style={{
                flex: 1,
                padding: '0.5rem',
                backgroundColor: colors.button.active,
                color: 'white',
                border: 'none',
                borderRadius: '0.25rem',
                fontSize: '0.75rem',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
            >
              View Full Size
            </button>
             <button
               onClick={(e) => {
                 e.stopPropagation();
                 handleDownload();
               }}
               style={{
                 flex: 1,
                 padding: '0.5rem',
                 backgroundColor: colors.status.success,
                 color: 'white',
                 border: 'none',
                 borderRadius: '0.25rem',
                 fontSize: '0.75rem',
                 fontWeight: 'bold',
                 cursor: 'pointer',
               }}
             >
              Download
            </button>
          </div>
        </div>
      </div>

      {/* Full-Size Image Modal */}
      {showModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
             backgroundColor: 'rgba(0, 0, 0, 0.9)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '2rem',
          }}
          onClick={() => setShowModal(false)}
        >
          <div
             style={{
               maxWidth: '90vw',
               maxHeight: '90vh',
               backgroundColor: colors.bg.primary,
               borderRadius: '0.5rem',
               overflow: 'hidden',
               position: 'relative',
             }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={() => setShowModal(false)}
              style={{
                position: 'absolute',
                top: '1rem',
                right: '1rem',
                width: '2.5rem',
                height: '2.5rem',
                 backgroundColor: colors.bg.tertiary,
                color: 'white',
                border: 'none',
                borderRadius: '50%',
                fontSize: '1.5rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1001,
              }}
            >
              ×
            </button>

            {/* Full-Size Image */}
            <img
              src={full_image_url}
              alt={result.metadata.source || 'Image'}
              style={{
                maxWidth: '100%',
                maxHeight: '90vh',
                objectFit: 'contain',
              }}
            />

            {/* Image Details */}
            <div
              style={{
                padding: '1rem',
                backgroundColor: colors.bg.tertiary,
                borderTop: `1px solid ${colors.border}`,
              }}
            >
              <div style={{ fontSize: '0.875rem', color: colors.text.primary, marginBottom: '0.5rem' }}>
                <strong>{result.metadata.source || 'Unknown'}</strong>
              </div>
              <div style={{ fontSize: '0.75rem', color: colors.text.tertiary }}>
                {width} × {height}px • {format.toUpperCase()} • {fileSizeKB} KB • {Math.round(result.score * 100)}% relevance
              </div>
            </div>
          </div>
        </div>
         )}
      </React.Fragment>
    );
}
