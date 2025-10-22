import React, { useEffect, useRef, useState } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';
import { apiClient, GlobalConfig } from '../../services/api';
import { useQueryClient } from '@tanstack/react-query';

type ToastState = { type: 'success' | 'error'; message: string } | null;

export default function ConfigurationActions() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [toast, setToast] = useState<ToastState>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const config = await apiClient.exportConfig();
      const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      const timestamp = new Date().toISOString().split('T')[0];
      anchor.href = url;
      anchor.download = `global-config-${timestamp}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setToast({ type: 'success', message: 'Exported configuration to JSON file' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to export configuration';
      setToast({ type: 'error', message });
    } finally {
      setIsExporting(false);
    }
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleImportFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    try {
      const text = await file.text();
      const parsed = JSON.parse(text) as GlobalConfig;
      await apiClient.importConfig(parsed);
      await queryClient.invalidateQueries({ queryKey: ['embedding-config'] });
      await queryClient.invalidateQueries({ queryKey: ['ocr-config'] });
      setToast({ type: 'success', message: 'Imported configuration successfully' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to import configuration';
      setToast({ type: 'error', message });
    } finally {
      setIsImporting(false);
      event.target.value = '';
    }
  };

  const toastBackground = toast?.type === 'success' ? colors.status.success : colors.status.error;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
      marginBottom: '2rem',
      backgroundColor: colors.bg.secondary,
      borderRadius: '0.75rem',
      padding: '1.25rem',
      border: `1px solid ${colors.border}`,
    }}>
      {toast && (
        <div
          style={{
            position: 'fixed',
            bottom: '2rem',
            right: '2rem',
            padding: '0.75rem 1rem',
            borderRadius: '0.5rem',
            backgroundColor: toastBackground,
            color: '#ffffff',
            boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
            zIndex: 60,
            minWidth: '16rem',
            textAlign: 'center',
          }}
        >
          {toast.message}
        </div>
      )}

      <div>
        <h2 style={{ color: colors.text.primary, fontSize: '1.1rem', fontWeight: 600, margin: 0 }}>
          Configuration Management
        </h2>
        <p style={{ color: colors.text.secondary, fontSize: '0.9rem', marginTop: '0.35rem', marginBottom: '0.75rem' }}>
          Export your current global configuration or import a saved JSON file to share presets across environments.
        </p>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
        <button
          type="button"
          onClick={handleExport}
          disabled={isExporting}
          style={{
            padding: '0.5rem 1.25rem',
            backgroundColor: colors.button.active,
            color: '#ffffff',
            border: 'none',
            borderRadius: '0.25rem',
            cursor: isExporting ? 'not-allowed' : 'pointer',
            fontSize: '0.9rem',
            fontWeight: 500,
            opacity: isExporting ? 0.7 : 1,
          }}
        >
          {isExporting ? 'Exporting…' : 'Export Configuration'}
        </button>

        <button
          type="button"
          onClick={handleImportClick}
          disabled={isImporting}
          style={{
            padding: '0.5rem 1.25rem',
            backgroundColor: 'transparent',
            color: colors.button.active,
            border: `1px solid ${colors.button.active}`,
            borderRadius: '0.25rem',
            cursor: isImporting ? 'not-allowed' : 'pointer',
            fontSize: '0.9rem',
            fontWeight: 500,
            opacity: isImporting ? 0.7 : 1,
          }}
        >
          {isImporting ? 'Importing…' : 'Import Configuration'}
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept="application/json"
          style={{ display: 'none' }}
          onChange={handleImportFile}
        />
      </div>

      <ul style={{ margin: 0, paddingLeft: '1.25rem', color: colors.text.secondary, fontSize: '0.8rem' }}>
        <li>Exported files include both embedding and OCR presets.</li>
        <li>Import expects JSON matching the export format; validation is performed on the server.</li>
      </ul>
    </div>
  );
}
