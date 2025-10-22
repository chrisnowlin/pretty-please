import React, { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

type ResolutionMode = 'tiny' | 'small' | 'base' | 'large' | 'gundam';

interface OCRConfig {
  batch_size: number;
  render_workers: number;
  analysis_workers: number;
  pre_render_batches: number;
  checkpoint_enabled: boolean;
  resolution_mode: ResolutionMode;
  enable_grounding: boolean;
  enable_compression: boolean;
  use_vllm: boolean;
}

interface OCRConfigResponse {
  config: OCRConfig;
  preset: string;
}

interface PresetInfo {
  name: string;
  display_name?: string;
  description: string;
  performance_characteristics?: Record<string, string>;
}

const RESOLUTION_OPTIONS: Array<{
  value: ResolutionMode;
  label: string;
  description: string;
}> = [
  {
    value: 'tiny',
    label: 'Tiny (512×512)',
    description: 'Fastest option for simple, text-heavy documents. Grounding disabled for speed.',
  },
  {
    value: 'small',
    label: 'Small (640×640)',
    description: 'Balanced speed and quality. Good default for mixed but moderate complexity documents.',
  },
  {
    value: 'base',
    label: 'Base (1024×1024)',
    description: 'Default Deepseek quality. Recommended general-purpose configuration.',
  },
  {
    value: 'large',
    label: 'Large (1280×1280)',
    description: 'High fidelity rendering. Best choice for dense tables, equations, and diagrams.',
  },
  {
    value: 'gundam',
    label: 'Gundam (Dynamic)',
    description: 'Multi-resolution pipeline that adapts per page. Ideal for complex mixed-layout documents.',
  },
];

export default function OCRConfigPanel() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<OCRConfig>({
    batch_size: 30,
    render_workers: 20,
    analysis_workers: 2,
    pre_render_batches: 4,
    checkpoint_enabled: true,
    resolution_mode: 'base',
    enable_grounding: true,
    enable_compression: true,
    use_vllm: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [selectedPreset, setSelectedPreset] = useState<string>('custom');

  // Fetch current OCR config
  const { data: configData, isLoading } = useQuery<OCRConfigResponse>({
    queryKey: ['ocr-config'],
    queryFn: async () => {
      const res = await fetch('/api/config/ocr');
      if (!res.ok) throw new Error('Failed to fetch OCR config');
      return res.json();
    },
  });

  // Fetch available presets
  const { data: presetsData } = useQuery<PresetInfo[]>({
    queryKey: ['ocr-presets'],
    queryFn: async () => {
      const res = await fetch('/api/config/ocr/presets');
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
    mutationFn: async (config: OCRConfig) => {
      const res = await fetch('/api/config/ocr', {
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
      queryClient.invalidateQueries({ queryKey: ['ocr-config'] });
      setSuccessMessage('OCR configuration updated successfully');
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

    if (formData.batch_size < 1 || formData.batch_size > 100) {
      newErrors.batch_size = 'Must be between 1 and 100';
    }
    if (formData.render_workers < 1 || formData.render_workers > 50) {
      newErrors.render_workers = 'Must be between 1 and 50';
    }
    if (formData.analysis_workers < 1 || formData.analysis_workers > 10) {
      newErrors.analysis_workers = 'Must be between 1 and 10';
    }
    if (formData.pre_render_batches < 1 || formData.pre_render_batches > 10) {
      newErrors.pre_render_batches = 'Must be between 1 and 10';
    }
    if (!RESOLUTION_OPTIONS.some(option => option.value === formData.resolution_mode)) {
      newErrors.resolution_mode = 'Select a valid resolution mode';
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

  const handleChange = (field: keyof OCRConfig, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[field];
      return newErrors;
    });
  };

  const handlePresetChange = async (presetName: string) => {
    setErrorMessage('');
    setSelectedPreset(presetName);
    if (presetName === 'custom') return;

    // Apply preset by fetching its configuration
    // For now, we'll just refetch the current config
    // In a production system, you'd have a preset endpoint that returns the preset config
    queryClient.invalidateQueries({ queryKey: ['ocr-config'] });
  };

  if (isLoading) {
    return <div style={{ color: colors.text.secondary }}>Loading OCR configuration...</div>;
  }

  const selectedResolution = useMemo(
    () => RESOLUTION_OPTIONS.find(option => option.value === formData.resolution_mode),
    [formData.resolution_mode],
  );

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
              {(preset.display_name ?? preset.name) }
            </option>
          ))}
        </select>
        {selectedPreset !== 'custom' && (
          <p style={{ color: colors.text.secondary, marginTop: '0.5rem', fontSize: '0.75rem' }}>
            {presetsData?.find(p => p.name === selectedPreset)?.description}
          </p>
        )}
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
            Batch Size (1-100)
            <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
              - Pages per processing batch
            </span>
          </label>
          <input
            type="number"
            min="1"
            max="100"
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
            Render Workers (1-50)
            <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
              - Concurrent rendering threads
            </span>
          </label>
          <input
            type="number"
            min="1"
            max="50"
            value={formData.render_workers}
            onChange={(e) => handleChange('render_workers', parseInt(e.target.value))}
            style={{
              ...inputStyle,
              borderColor: errors.render_workers ? colors.status.error : colors.border
            }}
          />
          {errors.render_workers && <div style={errorStyle}>{errors.render_workers}</div>}
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={labelStyle}>
            Analysis Workers (1-10)
            <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
              - Concurrent analysis threads
            </span>
          </label>
          <input
            type="number"
            min="1"
            max="10"
            value={formData.analysis_workers}
            onChange={(e) => handleChange('analysis_workers', parseInt(e.target.value))}
            style={{
              ...inputStyle,
              borderColor: errors.analysis_workers ? colors.status.error : colors.border
            }}
          />
          {errors.analysis_workers && <div style={errorStyle}>{errors.analysis_workers}</div>}
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={labelStyle}>
            Pre-render Batches (1-10)
            <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
              - Number of batches to pre-render ahead
            </span>
          </label>
          <input
            type="number"
            min="1"
            max="10"
            value={formData.pre_render_batches}
            onChange={(e) => handleChange('pre_render_batches', parseInt(e.target.value))}
            style={{
              ...inputStyle,
              borderColor: errors.pre_render_batches ? colors.status.error : colors.border
            }}
          />
          {errors.pre_render_batches && <div style={errorStyle}>{errors.pre_render_batches}</div>}
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.checkpoint_enabled}
              onChange={(e) => handleChange('checkpoint_enabled', e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ color: colors.text.primary }}>
              Enable Checkpoint Saving
              <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                - Save progress for crash recovery
              </span>
            </span>
          </label>
        </div>
      </div>

      {/* Deepseek-Specific Options */}
      <div>
        <h3 style={{
          fontSize: '1rem',
          fontWeight: '600',
          marginBottom: '1rem',
          color: colors.text.primary,
        }}>Deepseek Rendering Options</h3>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={labelStyle}>
            Resolution Mode
            <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
              - Controls render size, speed, and grounding detail
            </span>
          </label>
          <select
            value={formData.resolution_mode}
            onChange={(e) => handleChange('resolution_mode', e.target.value as ResolutionMode)}
            style={{
              ...inputStyle,
              borderColor: errors.resolution_mode ? colors.status.error : colors.border,
            }}
          >
            {RESOLUTION_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {selectedResolution && (
            <p style={{ color: colors.text.secondary, marginTop: '0.5rem', fontSize: '0.75rem' }}>
              {selectedResolution.description}
            </p>
          )}
          {errors.resolution_mode && <div style={errorStyle}>{errors.resolution_mode}</div>}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.enable_grounding}
              onChange={(e) => handleChange('enable_grounding', e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ color: colors.text.primary }}>
              Enable Grounding (Bounding Boxes)
              <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                - Required for spatial citations and layout-aware retrieval
              </span>
            </span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.enable_compression}
              onChange={(e) => handleChange('enable_compression', e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ color: colors.text.primary }}>
              Enable Optical Compression
              <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                - Reduces tokens by ~10× with minimal quality loss
              </span>
            </span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.use_vllm}
              onChange={(e) => handleChange('use_vllm', e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ color: colors.text.primary }}>
              Use vLLM Backend
              <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                - High-throughput inference for A100-class GPUs (optional)
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
          {showAdvanced ? '▼ Hide' : '▶ Show'} Advanced Information
        </button>
      </div>

      {/* Advanced Information */}
      {showAdvanced && (
        <div style={{
          padding: '1rem',
          backgroundColor: colors.bg.secondary,
          borderRadius: '0.25rem',
          border: `1px solid ${colors.border}`,
        }}>
          <h3 style={{
            fontSize: '1rem',
            fontWeight: '600',
            marginBottom: '1rem',
            color: colors.text.primary
          }}>Deepseek Performance Guidelines</h3>

          <div style={{ fontSize: '0.875rem', color: colors.text.secondary, lineHeight: '1.6' }}>
            <p style={{ marginBottom: '0.75rem' }}>
              <strong style={{ color: colors.text.primary }}>Resolution Mode:</strong> Start with <code>base</code> for most workloads. Use <code>tiny</code> for throughput-sensitive tasks or <code>large</code>/<code>gundam</code> when precise layout fidelity is critical.
            </p>
            <p style={{ marginBottom: '0.75rem' }}>
              <strong style={{ color: colors.text.primary }}>Grounding:</strong> Keep enabled to capture bounding boxes. You may disable for purely textual ingestion when speed matters more than spatial metadata.
            </p>
            <p style={{ marginBottom: '0.75rem' }}>
              <strong style={{ color: colors.text.primary }}>Compression:</strong> Deepseek&apos;s optical compression reduces token counts by ~90%. Disable only when debugging raw markdown output.
            </p>
            <p style={{ marginBottom: '0.75rem' }}>
              <strong style={{ color: colors.text.primary }}>vLLM:</strong> Requires a dedicated GPU with ≥24GB VRAM. Provides 5–10× throughput. Leave disabled for local development or CPU/MPS environments.
            </p>
            {selectedPreset !== 'custom' && presetsData?.length ? (
              <div style={{ marginTop: '1rem' }}>
                <strong style={{ color: colors.text.primary }}>Preset Characteristics:</strong>
                <ul style={{ margin: '0.5rem 0 0 1.25rem', padding: 0 }}>
                  {Object.entries(presetsData.find(p => p.name === selectedPreset)?.performance_characteristics ?? {}).map(([key, value]) => (
                    <li key={key} style={{ marginBottom: '0.25rem' }}>
                      <span style={{ color: colors.text.primary }}>{key}:</span> {value}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
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
