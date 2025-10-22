import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { getThemeColors } from '../styles/theme';
import RAGConfigPanel from '../components/settings/RAGConfigPanel';
import CollectionsConfigPage from '../components/settings/CollectionsConfigPage';
import EmbeddingConfigPanel from '../components/settings/EmbeddingConfigPanel';
import OCRConfigPanel from '../components/settings/OCRConfigPanel';

type Tab = 'rag' | 'embeddings' | 'ocr' | 'collections' | 'system';

export default function SettingsPage() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [activeTab, setActiveTab] = useState<Tab>('rag');

  const tabButtonStyle = (tab: Tab) => ({
    padding: '0.75rem 1.5rem',
    backgroundColor: activeTab === tab ? colors.bg.secondary : 'transparent',
    color: activeTab === tab ? colors.text.primary : colors.text.secondary,
    border: 'none',
    borderBottom: activeTab === tab ? `2px solid ${colors.button.active}` : `2px solid transparent`,
    cursor: 'pointer',
    fontWeight: activeTab === tab ? '600' : 'normal',
    transition: 'all 0.2s',
    outline: 'none',
  });

  return (
    <div style={{
      width: '100%',
      maxWidth: '80rem',
      margin: '0 auto',
      padding: '0.5rem 1rem',
    }}>
      <h1 style={{
        fontSize: '1.875rem',
        fontWeight: 'bold',
        lineHeight: '1.25',
        color: colors.text.primary,
        marginBottom: '1.5rem'
      }}>Settings</h1>

      {/* Tab Navigation */}
      <div style={{
        borderBottom: `1px solid ${colors.border}`,
        marginBottom: '2rem',
      }}>
        <div style={{
          display: 'flex',
          gap: '0.5rem',
        }}>
          <button
            style={tabButtonStyle('rag')}
            onClick={() => setActiveTab('rag')}
            onMouseEnter={(e) => {
              if (activeTab !== 'rag') {
                e.currentTarget.style.color = colors.text.primary;
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== 'rag') {
                e.currentTarget.style.color = colors.text.secondary;
              }
            }}
          >
            RAG
          </button>
          <button
            style={tabButtonStyle('embeddings')}
            onClick={() => setActiveTab('embeddings')}
            onMouseEnter={(e) => {
              if (activeTab !== 'embeddings') {
                e.currentTarget.style.color = colors.text.primary;
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== 'embeddings') {
                e.currentTarget.style.color = colors.text.secondary;
              }
            }}
          >
            Embeddings
          </button>
          <button
            style={tabButtonStyle('ocr')}
            onClick={() => setActiveTab('ocr')}
            onMouseEnter={(e) => {
              if (activeTab !== 'ocr') {
                e.currentTarget.style.color = colors.text.primary;
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== 'ocr') {
                e.currentTarget.style.color = colors.text.secondary;
              }
            }}
          >
            OCR
          </button>
          <button
            style={tabButtonStyle('collections')}
            onClick={() => setActiveTab('collections')}
            onMouseEnter={(e) => {
              if (activeTab !== 'collections') {
                e.currentTarget.style.color = colors.text.primary;
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== 'collections') {
                e.currentTarget.style.color = colors.text.secondary;
              }
            }}
          >
            Collections
          </button>
          <button
            style={tabButtonStyle('system')}
            onClick={() => setActiveTab('system')}
            onMouseEnter={(e) => {
              if (activeTab !== 'system') {
                e.currentTarget.style.color = colors.text.primary;
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== 'system') {
                e.currentTarget.style.color = colors.text.secondary;
              }
            }}
          >
            System
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div style={{
        backgroundColor: colors.bg.primary,
        borderRadius: '0.5rem',
        padding: '1.5rem',
        boxShadow: `0 1px 3px ${colors.shadow}`
      }}>
        {activeTab === 'rag' && (
          <div>
            <h2 style={{
              fontSize: '1.25rem',
              fontWeight: '600',
              marginBottom: '1rem',
              color: colors.text.primary
            }}>RAG Configuration</h2>
            <p style={{
              color: colors.text.secondary,
              marginBottom: '1.5rem'
            }}>
              Configure global RAG settings for retrieval, reranking, and citation formatting.
              These settings apply to all new chat sessions.
            </p>
            <RAGConfigPanel />
          </div>
        )}

        {activeTab === 'embeddings' && (
          <div>
            <h2 style={{
              fontSize: '1.25rem',
              fontWeight: '600',
              marginBottom: '1rem',
              color: colors.text.primary
            }}>Embedding Configuration</h2>
            <p style={{
              color: colors.text.secondary,
              marginBottom: '1.5rem'
            }}>
              Configure Jina AI v4 embedding model settings. These settings control embedding quality,
              storage efficiency, and processing performance. Changes take effect for new documents.
            </p>
            <EmbeddingConfigPanel />
          </div>
        )}

        {activeTab === 'ocr' && (
          <div>
            <h2 style={{
              fontSize: '1.25rem',
              fontWeight: '600',
              marginBottom: '1rem',
              color: colors.text.primary
            }}>OCR Configuration</h2>
            <p style={{
              color: colors.text.secondary,
              marginBottom: '1.5rem'
            }}>
              Configure PDF OCR processing pipeline settings. Adjust batch sizes, parallelism,
              and two-tier hybrid mode for optimal speed/quality tradeoff. Changes take effect for new uploads.
            </p>
            <OCRConfigPanel />
          </div>
        )}

        {activeTab === 'collections' && (
          <div>
            <h2 style={{
              fontSize: '1.25rem',
              fontWeight: '600',
              marginBottom: '1rem',
              color: colors.text.primary
            }}>Collection Configuration</h2>
            <CollectionsConfigPage />
          </div>
        )}

        {activeTab === 'system' && (
          <div>
            <h2 style={{
              fontSize: '1.25rem',
              fontWeight: '600',
              marginBottom: '1rem',
              color: colors.text.primary
            }}>System Information</h2>
            <p style={{ color: colors.text.secondary }}>
              System health and statistics will be displayed here.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
