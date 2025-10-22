import React, { useEffect, useRef } from 'react';
import type { CitationMetadata } from '../../types/chat';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface SourceViewerProps {
  citationId: string;
  citationData: CitationMetadata;
  onClose: () => void;
}

/**
 * Slide-in panel to display source content for citations
 * Supports both text documents and images with accessibility features
 */
export function SourceViewer({ citationId, citationData, onClose }: SourceViewerProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const panelRef = useRef<HTMLDivElement>(null);

  // Handle ESC key to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Focus panel on mount for keyboard navigation
  useEffect(() => {
    panelRef.current?.focus();
  }, []);

  // Handle click outside to close
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const isImage = citationData.type === 'image';
  const isText = citationData.type === 'text';

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end'
      }}
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="source-viewer-title"
    >
      <div
        ref={panelRef}
        className="bg-white h-full w-full sm:w-[600px] md:w-[700px] shadow-2xl overflow-hidden flex flex-col animate-slide-in-right"
        style={{
          backgroundColor: colors.bg.primary,
          borderLeft: `1px solid ${colors.border}`
        }}
        tabIndex={-1}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between p-4 border-b"
          style={{ borderColor: colors.border }}
        >
          <div className="flex-1 min-w-0">
            <h2
              id="source-viewer-title"
              className="text-lg font-semibold truncate"
              style={{ color: colors.text.primary }}
            >
              {citationId} - {citationData.source}
            </h2>
            <p
              className="text-sm mt-1"
              style={{ color: colors.text.secondary }}
            >
              Relevance: {(citationData.score * 100).toFixed(1)}% • {isImage ? 'Image' : 'Document'}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              marginLeft: '1rem',
              padding: '0.5rem',
              borderRadius: '0.25rem',
              border: 'none',
              outline: 'none',
              backgroundColor: 'transparent',
              transition: 'background-color 0.2s',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = colors.bg.tertiary}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            aria-label="Close source viewer"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {isImage && citationData.image_urls && (
            <div className="flex flex-col items-center">
              <img
                src={citationData.image_urls.full_image_url}
                alt={citationData.metadata.description || citationData.source}
                className="max-w-full h-auto rounded shadow-lg"
              />
              {citationData.metadata.description && (
                <p
                  className="mt-4 text-sm text-center"
                  style={{ color: colors.text.secondary }}
                >
                  {citationData.metadata.description}
                </p>
              )}
              <div
                className="mt-4 p-3 rounded text-sm w-full"
                style={{ backgroundColor: colors.bg.secondary }}
              >
                <p className="font-medium mb-2" style={{ color: colors.text.primary }}>
                  Image Details
                </p>
                <ul className="space-y-1" style={{ color: colors.text.secondary }}>
                  {citationData.metadata.width && citationData.metadata.height && (
                    <li>Dimensions: {citationData.metadata.width} × {citationData.metadata.height}px</li>
                  )}
                  {citationData.metadata.format && (
                    <li>Format: {citationData.metadata.format.toUpperCase()}</li>
                  )}
                  {citationData.metadata.file_size && (
                    <li>Size: {(citationData.metadata.file_size / 1024).toFixed(1)} KB</li>
                  )}
                </ul>
              </div>
            </div>
          )}

          {isText && citationData.document_url && (
            <div className="space-y-4">
              <div
                className="p-4 rounded border"
                style={{
                  backgroundColor: colors.bg.secondary,
                  borderColor: colors.border
                }}
              >
                <p className="text-sm font-medium mb-2" style={{ color: colors.text.primary }}>
                  Document Preview
                </p>
                <p className="text-sm" style={{ color: colors.text.secondary }}>
                  This document can be viewed in your browser or downloaded.
                </p>
                <div className="mt-3 flex gap-2">
                  <a
                    href={citationData.document_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      padding: '0.5rem 1rem',
                      backgroundColor: colors.button.active,
                      color: 'white',
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      borderRadius: '0.25rem',
                      textDecoration: 'none',
                      transition: 'background-color 0.2s',
                      outline: 'none'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = colors.button.active}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = colors.button.active}
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    Open Document
                  </a>
                </div>
              </div>

              {/* Metadata */}
              {citationData.metadata && Object.keys(citationData.metadata).length > 0 && (
                <div
                  className="p-4 rounded border"
                  style={{
                    backgroundColor: colors.bg.secondary,
                    borderColor: colors.border
                  }}
                >
                  <p className="text-sm font-medium mb-2" style={{ color: colors.text.primary }}>
                    Metadata
                  </p>
                  <ul className="space-y-1 text-sm" style={{ color: colors.text.secondary }}>
                    {citationData.metadata.page && (
                      <li>Page: {citationData.metadata.page}</li>
                    )}
                    {citationData.metadata.chunk_index !== undefined && (
                      <li>Section: {citationData.metadata.chunk_index + 1}</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer with keyboard hint */}
        <div
          style={{
            padding: '0.75rem',
            borderTop: `1px solid ${colors.border}`,
            fontSize: '0.75rem',
            textAlign: 'center',
            color: colors.text.secondary
          }}
        >
          Press <kbd style={{
            padding: '0.125rem 0.5rem',
            backgroundColor: colors.bg.tertiary,
            borderRadius: '0.25rem',
            border: `1px solid ${colors.border}`,
            fontFamily: 'monospace',
            fontSize: '0.75rem'
          }}>ESC</kbd> to close
        </div>
      </div>
    </div>
  );
}
