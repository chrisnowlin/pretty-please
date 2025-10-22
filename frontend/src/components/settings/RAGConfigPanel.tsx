import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface RAGConfig {
  initial_retrieval_k: number;
  rerank_top_n: number;
  enable_reranking: boolean;
  rerank_model: string;
  enable_hybrid_search: boolean;
  hybrid_alpha: number;
  citation_style: string;
  include_relevance_scores: boolean;
}

interface RAGConfigResponse {
  config: RAGConfig;
  description?: string;
}

export default function RAGConfigPanel() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<RAGConfig>({
    initial_retrieval_k: 20,
    rerank_top_n: 5,
    enable_reranking: true,
    rerank_model: 'jinaai/jina-reranker-m0',
    enable_hybrid_search: false,
    hybrid_alpha: 0.5,
    citation_style: 'numbered',
    include_relevance_scores: true,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  // Fetch current RAG config
  const { data: configData, isLoading } = useQuery<RAGConfigResponse>({
    queryKey: ['rag-config'],
    queryFn: async () => {
      const res = await fetch('/api/config/rag');
      if (!res.ok) throw new Error('Failed to fetch RAG config');
      return res.json();
    },
  });

  // Update form data when config loads
  useEffect(() => {
    if (configData?.config) {
      setFormData(configData.config);
    }
  }, [configData]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async (config: RAGConfig) => {
      const res = await fetch('/api/config/rag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Failed to update config');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rag-config'] });
      setSuccessMessage('Configuration updated successfully');
      setErrorMessage('');
      setTimeout(() => setSuccessMessage(''), 3000);
    },
    onError: (error: Error) => {
      setErrorMessage(error.message);
      setSuccessMessage('');
    },
  });

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (formData.initial_retrieval_k < 1 || formData.initial_retrieval_k > 50) {
      newErrors.initial_retrieval_k = 'Must be between 1 and 50';
    }
    if (formData.rerank_top_n < 1 || formData.rerank_top_n > 20) {
      newErrors.rerank_top_n = 'Must be between 1 and 20';
    }
    if (formData.hybrid_alpha < 0 || formData.hybrid_alpha > 1) {
      newErrors.hybrid_alpha = 'Must be between 0 and 1';
    }
    if (!['numbered', 'inline', 'footnote'].includes(formData.citation_style)) {
      newErrors.citation_style = 'Must be numbered, inline, or footnote';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      updateMutation.mutate(formData);
    }
  };

  const handleChange = (field: keyof RAGConfig, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[field];
      return newErrors;
    });
  };

  if (isLoading) {
    return <div style={{ color: colors.text.secondary }}>Loading configuration...</div>;
  }

  const inputStyle = {
    width: '100%',
    padding: '0.5rem',
    border: `1px solid ${colors.border}`,
    borderRadius: '0.25rem',
    backgroundColor: colors.bg.primary,
    color: colors.text.primary,
    outline: 'none',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '0.875rem',
    fontWeight: '500' as const,
    marginBottom: '0.5rem',
    color: colors.text.primary,
  };

  const errorStyle = {
    color: colors.status.error,
    fontSize: '0.75rem',
    marginTop: '0.25rem',
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Success/Error Messages */}
      {successMessage && (
        <div style={{
          padding: '0.75rem',
          backgroundColor: '#10b98120',
          border: `1px solid #10b981`,
          borderRadius: '0.25rem',
          color: '#10b981',
        }}>
          {successMessage}
        </div>
      )}
      {errorMessage && (
        <div style={{
          padding: '0.75rem',
          backgroundColor: `${colors.status.error}20`,
          border: `1px solid ${colors.status.error}`,
          borderRadius: '0.25rem',
          color: colors.status.error,
        }}>
          {errorMessage}
        </div>
      )}

      {/* Retrieval Settings */}
      <div>
        <h3 style={{
          fontSize: '1rem',
          fontWeight: '600',
          marginBottom: '1rem',
          color: colors.text.primary
        }}>Retrieval Settings</h3>

        <div style={{ marginBottom: '1rem' }}>
          <label style={labelStyle}>
            Initial Retrieval Batch Size (1-50)
            <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
              - Number of documents to retrieve before reranking
            </span>
          </label>
          <input
            type="number"
            min="1"
            max="50"
            value={formData.initial_retrieval_k}
            onChange={(e) => handleChange('initial_retrieval_k', parseInt(e.target.value))}
            style={{
              ...inputStyle,
              borderColor: errors.initial_retrieval_k ? colors.status.error : colors.border
            }}
          />
          {errors.initial_retrieval_k && <div style={errorStyle}>{errors.initial_retrieval_k}</div>}
        </div>
      </div>

      {/* Reranking Settings */}
      <div>
        <h3 style={{
          fontSize: '1rem',
          fontWeight: '600',
          marginBottom: '1rem',
          color: colors.text.primary
        }}>Reranking Settings</h3>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.enable_reranking}
              onChange={(e) => handleChange('enable_reranking', e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ color: colors.text.primary }}>Enable Reranking</span>
          </label>
        </div>

        {formData.enable_reranking && (
          <React.Fragment>
            <div style={{ marginBottom: '1rem' }}>
              <label style={labelStyle}>Reranker Model</label>
              <select
                value={formData.rerank_model}
                onChange={(e) => handleChange('rerank_model', e.target.value)}
                style={inputStyle}
              >
                <option value="jinaai/jina-reranker-m0">jinaai/jina-reranker-m0</option>
                <option value="jinaai/jina-reranker-v1-turbo-en">jinaai/jina-reranker-v1-turbo-en</option>
              </select>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={labelStyle}>
                Top N After Reranking (1-20)
                <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                  - Number of documents to keep after reranking
                </span>
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={formData.rerank_top_n}
                onChange={(e) => handleChange('rerank_top_n', parseInt(e.target.value))}
                style={{
                  ...inputStyle,
                  borderColor: errors.rerank_top_n ? colors.status.error : colors.border
                }}
              />
              {errors.rerank_top_n && <div style={errorStyle}>{errors.rerank_top_n}</div>}
            </div>
          </React.Fragment>
        )}
      </div>

      {/* Citation Settings */}
      <div>
        <h3 style={{
          fontSize: '1rem',
          fontWeight: '600',
          marginBottom: '1rem',
          color: colors.text.primary
        }}>Citation Settings</h3>

        <div style={{ marginBottom: '1rem' }}>
          <label style={labelStyle}>Citation Style</label>
          <select
            value={formData.citation_style}
            onChange={(e) => handleChange('citation_style', e.target.value)}
            style={inputStyle}
          >
            <option value="numbered">Numbered ([1], [2], etc.)</option>
            <option value="inline">Inline (Source: document.pdf)</option>
            <option value="footnote">Footnote</option>
          </select>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.include_relevance_scores}
              onChange={(e) => handleChange('include_relevance_scores', e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ color: colors.text.primary }}>Include Relevance Scores in Context</span>
          </label>
        </div>
      </div>

      {/* Advanced Settings Section */}
      <div style={{
        borderTop: `1px solid ${colors.border}`,
        paddingTop: '1rem',
      }}>
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem',
            backgroundColor: 'transparent',
            border: 'none',
            color: colors.text.primary,
            fontSize: '1rem',
            fontWeight: '600',
            cursor: 'pointer',
            outline: 'none',
            transition: 'color 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.color = colors.button.active}
          onMouseLeave={(e) => e.currentTarget.style.color = colors.text.primary}
          title="Show advanced settings for hybrid search and compression"
        >
          <svg
            style={{
              width: '1rem',
              height: '1rem',
              transform: showAdvanced ? 'rotate(90deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s',
            }}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
          Advanced Settings
        </button>

        {showAdvanced && (
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            backgroundColor: colors.bg.secondary,
            borderRadius: '0.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}>
            {/* Hybrid Search Settings */}
            <div>
              <h4 style={{
                fontSize: '0.875rem',
                fontWeight: '600',
                marginBottom: '0.75rem',
                color: colors.text.primary
              }}>Hybrid Search (Experimental)</h4>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={formData.enable_hybrid_search}
                    onChange={(e) => handleChange('enable_hybrid_search', e.target.checked)}
                    style={{ cursor: 'pointer' }}
                  />
                  <span style={{ color: colors.text.primary }}>Enable Hybrid Search</span>
                </label>
                <p style={{
                  fontSize: '0.75rem',
                  color: colors.text.secondary,
                  marginTop: '0.25rem',
                  marginLeft: '1.5rem'
                }}>
                  Combines semantic search with keyword matching for improved results
                </p>
              </div>

              {formData.enable_hybrid_search && (
                <div>
                  <label style={labelStyle}>
                    Hybrid Alpha (0-1)
                    <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                      - Weight between semantic ({formData.hybrid_alpha.toFixed(2)}) and keyword ({(1 - formData.hybrid_alpha).toFixed(2)})
                    </span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={formData.hybrid_alpha}
                    onChange={(e) => handleChange('hybrid_alpha', parseFloat(e.target.value))}
                    style={{ width: '100%', cursor: 'pointer' }}
                  />
                  {errors.hybrid_alpha && <div style={errorStyle}>{errors.hybrid_alpha}</div>}
                </div>
              )}
            </div>

            <div style={{
              padding: '0.75rem',
              backgroundColor: `${colors.button.active}15`,
              borderLeft: `3px solid ${colors.button.active}`,
              borderRadius: '0.25rem',
            }}>
              <p style={{ fontSize: '0.75rem', color: colors.text.secondary, margin: 0 }}>
                <strong style={{ color: colors.text.primary }}>Note:</strong> Advanced settings are experimental.
                Compression features are currently under development and will be available in a future release.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={updateMutation.isPending || Object.keys(errors).length > 0}
        style={{
          padding: '0.75rem 1.5rem',
          backgroundColor: Object.keys(errors).length > 0 ? colors.button.inactive : colors.button.active,
          color: 'white',
          border: 'none',
          borderRadius: '0.25rem',
          fontWeight: '600',
          cursor: Object.keys(errors).length > 0 ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s',
          outline: 'none',
        }}
      >
        {updateMutation.isPending ? 'Saving...' : 'Save Configuration'}
      </button>
    </form>
  );
}
