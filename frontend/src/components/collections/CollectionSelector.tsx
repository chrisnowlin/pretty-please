import React, { useState } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';
import type { CollectionInfo } from '../../services/api';

interface CollectionSelectorProps {
  collections: CollectionInfo[];
  selectedCollection: string;
  onSelect: (collection: string) => void;
  onCollectionCreated?: (collectionName: string) => void;
}

export default function CollectionSelector({
  collections,
  selectedCollection,
  onSelect,
  onCollectionCreated,
}: CollectionSelectorProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [creatingCollection, setCreatingCollection] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateCollection = async () => {
    if (!newCollectionName.trim()) {
      setError('Collection name cannot be empty');
      return;
    }

    setCreatingCollection(true);
    setError(null);

    try {
      const response = await fetch('/api/collections/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `collection_name=${encodeURIComponent(newCollectionName)}`,
      });

      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create collection');
        return;
      }

      onSelect(newCollectionName);
      onCollectionCreated?.(newCollectionName);
      setNewCollectionName('');
      setShowCreateForm(false);
    } catch (err) {
      setError('Error creating collection');
      console.error(err);
    } finally {
      setCreatingCollection(false);
    }
  };

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <label style={{
        display: 'block',
        fontSize: '0.875rem',
        fontWeight: 'bold',
        marginBottom: '0.5rem',
        color: colors.text.secondary
      }}>
        Select Collection:
      </label>
      <select
        value={selectedCollection}
        onChange={(e) => onSelect(e.target.value)}
        style={{
          width: '100%',
          padding: '0.75rem',
          border: `1px solid ${colors.border}`,
          borderRadius: '0.375rem',
          fontSize: '1rem',
          backgroundColor: colors.bg.secondary,
          color: colors.text.primary,
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
      >
        <option value="">-- Choose a collection --</option>
        {collections && collections.map((collection) => (
          <option key={collection.name} value={collection.name}>
            {collection.name} ({collection.count} documents)
          </option>
        ))}
      </select>

      {!showCreateForm ? (
        <button
          onClick={() => setShowCreateForm(true)}
          style={{
            marginTop: '0.75rem',
            padding: '0.5rem 1rem',
            backgroundColor: colors.button.active,
            color: 'white',
            border: 'none',
            borderRadius: '0.375rem',
            cursor: 'pointer',
            fontSize: '0.875rem',
            fontWeight: 'bold',
            transition: 'all 0.2s',
          }}
        >
          + Create New Collection
        </button>
      ) : (
        <div style={{
          marginTop: '1rem',
          padding: '1rem',
          backgroundColor: colors.bg.tertiary,
          borderRadius: '0.375rem',
          border: `1px solid ${colors.border}`,
          transition: 'all 0.2s',
        }}>
          <input
            type="text"
            placeholder="Enter collection name..."
            value={newCollectionName}
            onChange={(e) => {
              setNewCollectionName(e.target.value);
              setError(null);
            }}
            disabled={creatingCollection}
            style={{
              width: '100%',
              padding: '0.75rem',
              border: `1px solid ${colors.border}`,
              borderRadius: '0.375rem',
              fontSize: '1rem',
              marginBottom: '0.75rem',
              boxSizing: 'border-box',
              backgroundColor: colors.bg.secondary,
              color: colors.text.primary,
              transition: 'all 0.2s',
            }}
          />
          {error && (
            <div style={{
              color: colors.status.error,
              fontSize: '0.875rem',
              marginBottom: '0.75rem'
            }}>
              {error}
            </div>
          )}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={handleCreateCollection}
              disabled={creatingCollection}
              style={{
                flex: 1,
                padding: '0.5rem',
                backgroundColor: colors.status.success,
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: creatingCollection ? 'not-allowed' : 'pointer',
                opacity: creatingCollection ? 0.7 : 1,
                fontWeight: 'bold',
                transition: 'all 0.2s',
              }}
            >
              {creatingCollection ? 'Creating...' : 'Create'}
            </button>
            <button
              onClick={() => setShowCreateForm(false)}
              disabled={creatingCollection}
              style={{
                flex: 1,
                padding: '0.5rem',
                backgroundColor: colors.button.inactive,
                color: colors.text.primary,
                border: 'none',
                borderRadius: '0.375rem',
                cursor: creatingCollection ? 'not-allowed' : 'pointer',
                opacity: creatingCollection ? 0.7 : 1,
                fontWeight: 'bold',
                transition: 'all 0.2s',
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
