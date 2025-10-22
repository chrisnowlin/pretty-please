import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';
import { apiClient } from '../../services/api';
import type { CollectionConfig } from '../../services/api';

interface CollectionConfigPanelProps {
  collectionName: string;
  onClose: () => void;
}

export default function CollectionConfigPanel({ collectionName, onClose }: CollectionConfigPanelProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<CollectionConfig>({
    config_version: '1.0',
    enable_layout_analysis: true,
    layout_ocr_enabled: true,
    layout_table_extraction: true,
    save_extracted_images: true,
    save_region_metadata: true,
    region_granularity: 'fine',
    max_image_dimension: 2048,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  // Fetch current collection config
  const { data: configData, isLoading } = useQuery<CollectionConfig>({
    queryKey: ['collection-config', collectionName],
    queryFn: () => apiClient.getCollectionConfig(collectionName),
  });

  // Update form data when config loads
  useEffect(() => {
    if (configData) {
      setFormData(configData);
    }
  }, [configData]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (config: CollectionConfig) => apiClient.updateCollectionConfig(collectionName, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection-config', collectionName] });
      queryClient.invalidateQueries({ queryKey: ['collections'] });
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

    if (formData.max_image_dimension < 256 || formData.max_image_dimension > 4096) {
      newErrors.max_image_dimension = 'Must be between 256 and 4096';
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

  const handleChange = (field: keyof CollectionConfig, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[field];
      return newErrors;
    });
  };

  const modalOverlayStyle: React.CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  };

  const modalContentStyle: React.CSSProperties = {
    backgroundColor: colors.bg.primary,
    borderRadius: '0.5rem',
    padding: '2rem',
    maxWidth: '600px',
    width: '90%',
    maxHeight: '90vh',
    overflow: 'auto',
    boxShadow: `0 4px 6px ${colors.shadow}`,
  };

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

  if (isLoading) {
    return (
      <div style={modalOverlayStyle} onClick={onClose}>
        <div style={modalContentStyle} onClick={e => e.stopPropagation()}>
          <div style={{ color: colors.text.secondary }}>Loading configuration...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={modalOverlayStyle} onClick={onClose}>
      <div style={modalContentStyle} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: colors.text.primary, margin: 0 }}>
            Configure Collection: {collectionName}
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: colors.text.secondary,
              padding: '0.25rem',
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = colors.text.primary}
            onMouseLeave={(e) => e.currentTarget.style.color = colors.text.secondary}
          >
            ×
          </button>
        </div>

        {/* Warning message */}
        <div style={{
          padding: '0.75rem',
          backgroundColor: `${colors.button.active}15`,
          borderLeft: `3px solid ${colors.button.active}`,
          borderRadius: '0.25rem',
          marginBottom: '1.5rem',
        }}>
          <p style={{ fontSize: '0.875rem', color: colors.text.primary, margin: 0 }}>
            <strong>Note:</strong> Configuration changes only affect future document uploads.
            Existing documents in this collection will not be reprocessed.
          </p>
        </div>

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

          {/* Layout Analysis Settings */}
          <div>
            <h3 style={{
              fontSize: '1rem',
              fontWeight: '600',
              marginBottom: '1rem',
              color: colors.text.primary
            }}>Layout Analysis Settings</h3>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={formData.enable_layout_analysis}
                  onChange={(e) => handleChange('enable_layout_analysis', e.target.checked)}
                  style={{ cursor: 'pointer' }}
                />
                <span style={{ color: colors.text.primary }}>Enable Layout Analysis</span>
              </label>
              <p style={{
                fontSize: '0.75rem',
                color: colors.text.secondary,
                marginTop: '0.25rem',
                marginLeft: '1.5rem'
              }}>
                Analyze document structure to extract regions like images, tables, and text blocks
              </p>
            </div>

            {formData.enable_layout_analysis && (
              <React.Fragment>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={formData.layout_ocr_enabled}
                      onChange={(e) => handleChange('layout_ocr_enabled', e.target.checked)}
                      style={{ cursor: 'pointer' }}
                    />
                    <span style={{ color: colors.text.primary }}>Enable OCR for Images</span>
                  </label>
                  <p style={{
                    fontSize: '0.75rem',
                    color: colors.text.secondary,
                    marginTop: '0.25rem',
                    marginLeft: '1.5rem'
                  }}>
                    Extract text from scanned documents and images using OCR
                  </p>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={formData.layout_table_extraction}
                      onChange={(e) => handleChange('layout_table_extraction', e.target.checked)}
                      style={{ cursor: 'pointer' }}
                    />
                    <span style={{ color: colors.text.primary }}>Enable Table Extraction</span>
                  </label>
                  <p style={{
                    fontSize: '0.75rem',
                    color: colors.text.secondary,
                    marginTop: '0.25rem',
                    marginLeft: '1.5rem'
                  }}>
                    Extract and structure tables as HTML/JSON for better searchability
                  </p>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={labelStyle}>Region Granularity</label>
                  <select
                    value={formData.region_granularity}
                    onChange={(e) => handleChange('region_granularity', e.target.value as 'fine' | 'coarse')}
                    style={inputStyle}
                  >
                    <option value="fine">Fine (Maximum precision, more regions)</option>
                    <option value="coarse">Coarse (Fewer regions, faster processing)</option>
                  </select>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={labelStyle}>
                    Maximum Image Dimension (256-4096 pixels)
                    <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                      - Larger images will be resized
                    </span>
                  </label>
                  <input
                    type="number"
                    min="256"
                    max="4096"
                    step="128"
                    value={formData.max_image_dimension}
                    onChange={(e) => handleChange('max_image_dimension', parseInt(e.target.value))}
                    style={{
                      ...inputStyle,
                      borderColor: errors.max_image_dimension ? colors.status.error : colors.border
                    }}
                  />
                  {errors.max_image_dimension && <div style={errorStyle}>{errors.max_image_dimension}</div>}
                </div>
              </React.Fragment>
            )}
          </div>

          {/* Storage Settings */}
          <div>
            <h3 style={{
              fontSize: '1rem',
              fontWeight: '600',
              marginBottom: '1rem',
              color: colors.text.primary
            }}>Storage Settings</h3>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={formData.save_extracted_images}
                  onChange={(e) => handleChange('save_extracted_images', e.target.checked)}
                  style={{ cursor: 'pointer' }}
                />
                <span style={{ color: colors.text.primary }}>Save Extracted Images</span>
              </label>
              <p style={{
                fontSize: '0.75rem',
                color: colors.text.secondary,
                marginTop: '0.25rem',
                marginLeft: '1.5rem'
              }}>
                Store images extracted from documents for future reference
              </p>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={formData.save_region_metadata}
                  onChange={(e) => handleChange('save_region_metadata', e.target.checked)}
                  style={{ cursor: 'pointer' }}
                />
                <span style={{ color: colors.text.primary }}>Save Region Metadata</span>
              </label>
              <p style={{
                fontSize: '0.75rem',
                color: colors.text.secondary,
                marginTop: '0.25rem',
                marginLeft: '1.5rem'
              }}>
                Store detailed metadata about each extracted region (bounding boxes, types, etc.)
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', paddingTop: '1rem', borderTop: `1px solid ${colors.border}` }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: colors.bg.secondary,
                color: colors.text.primary,
                border: `1px solid ${colors.border}`,
                borderRadius: '0.25rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'background-color 0.2s',
                outline: 'none',
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = colors.bg.tertiary}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = colors.bg.secondary}
            >
              Cancel
            </button>
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
          </div>
        </form>
      </div>
    </div>
  );
}
