import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface EmbeddingConfig {
  task: string;
  dimensions: number;
  late_chunking: boolean;
  return_multivector: boolean;
  embedding_format: string;
  batch_size: number;
  max_tokens_per_batch: number;
}

interface EmbeddingConfigResponse {
  config: EmbeddingConfig;
  preset: string;
}

interface PresetInfo {
  name: string;
  description: string;
}

const TASK_OPTIONS = [
  { value: 'retrieval.query', label: 'Retrieval Query' },
  { value: 'retrieval.passage', label: 'Retrieval Passage' },
  { value: 'text-matching', label: 'Text Matching' },
  { value: 'classification', label: 'Classification' },
  { value: 'separation', label: 'Separation' },
];

const DIMENSION_OPTIONS = [128, 256, 512, 1024, 2048];

const FORMAT_OPTIONS = [
  { value: 'float', label: 'Float (Full precision)' },
  { value: 'binary', label: 'Binary (1-bit)' },
  { value: 'ubinary', label: 'Unsigned Binary' },
];

export default function EmbeddingConfigPanel() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<EmbeddingConfig>({
    task: 'retrieval.passage',
    dimensions: 1024,
    late_chunking: true,
    return_multivector: false,
    embedding_format: 'float',
    batch_size: 32,
    max_tokens_per_batch: 8192,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [selectedPreset, setSelectedPreset] = useState<string>('custom');

  // Fetch current embedding config
  const { data: configData, isLoading } = useQuery<EmbeddingConfigResponse>({
    queryKey: ['embedding-config'],
    queryFn: async () => {
      const res = await fetch('/api/config/embeddings');
      if (!res.ok) throw new Error('Failed to fetch embedding config');
      return res.json();
    },
  });

  // Fetch available presets
  const { data: presetsData } = useQuery<PresetInfo[]>({
    queryKey: ['embedding-presets'],
    queryFn: async () => {
      const res = await fetch('/api/config/embeddings/presets');
      if (!res.ok) throw new Error('Failed to fetch presets');
      return res.json();
    },
  });

  // Update form data when config loads
  useEffect(() => {
    if (configData?.config) {
      setFormData(configData.config);
      setSelectedPreset(configData.preset || 'custom');
    }
  }, [configData]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async (config: EmbeddingConfig) => {
      const res = await fetch('/api/config/embeddings', {
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
      queryClient.invalidateQueries({ queryKey: ['embedding-config'] });
      setSuccessMessage('Embedding configuration updated successfully');
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

    if (!DIMENSION_OPTIONS.includes(formData.dimensions)) {
      newErrors.dimensions = 'Must be one of: 128, 256, 512, 1024, 2048';
    }
    if (formData.batch_size < 1 || formData.batch_size > 256) {
      newErrors.batch_size = 'Must be between 1 and 256';
    }
    if (formData.max_tokens_per_batch < 512 || formData.max_tokens_per_batch > 32768) {
      newErrors.max_tokens_per_batch = 'Must be between 512 and 32768';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      updateMutation.mutate(formData);
      setSelectedPreset('custom');
    }
  };

  const handleChange = (field: keyof EmbeddingConfig, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[field];
      return newErrors;
    });
  };

  const handlePresetChange = async (presetName: string) => {
    setSelectedPreset(presetName);
    if (presetName === 'custom') return;

    // Apply preset by fetching its configuration
    // For now, we'll just refetch the current config
    // In a production system, you'd have a preset endpoint that returns the preset config
    queryClient.invalidateQueries({ queryKey: ['embedding-config'] });
  };

  if (isLoading) {
    return <div style={{ color: colors.text.secondary }}>Loading embedding configuration...</div>;
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

      {/* Preset Selector */}
      <div>
        <label style={labelStyle}>
          Configuration Preset
          <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
            - Quick configurations for common use cases
          </span>
        </label>
        <select
          value={selectedPreset}
          onChange={(e) => handlePresetChange(e.target.value)}
          style={inputStyle}
        >
          <option value="custom">Custom Configuration</option>
          {presetsData?.map(preset => (
            <option key={preset.name} value={preset.name}>
              {preset.name} - {preset.description}
            </option>
          ))}
        </select>
      </div>

      {/* Basic Settings */}
      <div>
        <h3 style={{
          fontSize: '1rem',
          fontWeight: '600',
          marginBottom: '1rem',
          color: colors.text.primary
        }}>Basic Settings</h3>

        <div style={{ marginBottom: '1rem' }}>
          <label style={labelStyle}>
            Task Type
            <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
              - Optimizes embeddings for specific use case
            </span>
          </label>
          <select
            value={formData.task}
            onChange={(e) => handleChange('task', e.target.value)}
            style={inputStyle}
          >
            {TASK_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={labelStyle}>
            Embedding Dimensions
            <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
              - Higher = better quality, slower; Lower = faster, more storage efficient
            </span>
          </label>
          <select
            value={formData.dimensions}
            onChange={(e) => handleChange('dimensions', parseInt(e.target.value))}
            style={{
              ...inputStyle,
              borderColor: errors.dimensions ? colors.status.error : colors.border
            }}
          >
            {DIMENSION_OPTIONS.map(dim => (
              <option key={dim} value={dim}>{dim} dimensions</option>
            ))}
          </select>
          {errors.dimensions && <div style={errorStyle}>{errors.dimensions}</div>}
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={labelStyle}>
            Embedding Format
            <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
              - Binary formats use less storage but may reduce quality
            </span>
          </label>
          <select
            value={formData.embedding_format}
            onChange={(e) => handleChange('embedding_format', e.target.value)}
            style={inputStyle}
          >
            {FORMAT_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.late_chunking}
              onChange={(e) => handleChange('late_chunking', e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ color: colors.text.primary }}>
              Enable Late Chunking
              <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                - Improves quality by preserving context
              </span>
            </span>
          </label>
        </div>
      </div>

      {/* Advanced Settings Toggle */}
      <div>
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: 'transparent',
            color: colors.accent.primary,
            border: `1px solid ${colors.accent.primary}`,
            borderRadius: '0.25rem',
            cursor: 'pointer',
            fontSize: '0.875rem',
          }}
        >
          {showAdvanced ? '▼ Hide' : '▶ Show'} Advanced Settings
        </button>
      </div>

      {/* Advanced Settings */}
      {showAdvanced && (
        <div>
          <h3 style={{
            fontSize: '1rem',
            fontWeight: '600',
            marginBottom: '1rem',
            color: colors.text.primary
          }}>Advanced Settings</h3>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={formData.return_multivector}
                onChange={(e) => handleChange('return_multivector', e.target.checked)}
                style={{ cursor: 'pointer' }}
              />
              <span style={{ color: colors.text.primary }}>
                Enable Multi-Vector Embeddings
                <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                  - Returns multiple embeddings per document (experimental)
                </span>
              </span>
            </label>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={labelStyle}>
              Batch Size (1-256)
              <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                - Number of texts to process at once
              </span>
            </label>
            <input
              type="number"
              min="1"
              max="256"
              value={formData.batch_size}
              onChange={(e) => handleChange('batch_size', parseInt(e.target.value))}
              style={{
                ...inputStyle,
                borderColor: errors.batch_size ? colors.status.error : colors.border
              }}
            />
            {errors.batch_size && <div style={errorStyle}>{errors.batch_size}</div>}
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={labelStyle}>
              Max Tokens Per Batch (512-32768)
              <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                - Maximum total tokens to process in one batch
              </span>
            </label>
            <input
              type="number"
              min="512"
              max="32768"
              step="512"
              value={formData.max_tokens_per_batch}
              onChange={(e) => handleChange('max_tokens_per_batch', parseInt(e.target.value))}
              style={{
                ...inputStyle,
                borderColor: errors.max_tokens_per_batch ? colors.status.error : colors.border
              }}
            />
            {errors.max_tokens_per_batch && <div style={errorStyle}>{errors.max_tokens_per_batch}</div>}
          </div>
        </div>
      )}

      {/* Submit Button */}
      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
        <button
          type="submit"
          disabled={updateMutation.isPending}
          style={{
            padding: '0.5rem 1.5rem',
            backgroundColor: colors.accent.primary,
            color: 'white',
            border: 'none',
            borderRadius: '0.25rem',
            cursor: updateMutation.isPending ? 'not-allowed' : 'pointer',
            fontSize: '0.875rem',
            fontWeight: '500',
            opacity: updateMutation.isPending ? 0.6 : 1,
          }}
        >
          {updateMutation.isPending ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </form>
  );
}
