import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { getThemeColors } from '../styles/theme';
import { useQuery } from '@tanstack/react-query';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { apiClient } from '../services/api';

export default function CollectionsPage() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const { data: collections, isLoading, error, refetch } = useQuery({
    queryKey: ['collections'],
    queryFn: () => apiClient.getCollections(),
  });

  if (isLoading) return <LoadingSpinner />;

   if (error) {
     return (
       <div style={{
         backgroundColor: colors.bg.tertiary,
         color: colors.text.primary,
         padding: '1rem',
         borderRadius: '0.5rem',
         border: `1px solid ${colors.border}`,
       }}>
         Error: {error instanceof Error ? error.message : 'Failed to load collections'}
       </div>
     );
   }

   return (
     <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
       <div style={{
         backgroundColor: colors.bg.secondary,
         padding: '2rem',
         borderRadius: '0.5rem',
         boxShadow: `0 2px 4px ${colors.shadow}`,
         transition: 'all 0.2s',
       }}>
         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
           <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: colors.text.primary }}>Collections</h2>
           <button
             onClick={() => refetch()}
             style={{
               padding: '0.5rem 1rem',
               backgroundColor: colors.button.active,
               color: 'white',
               border: 'none',
               borderRadius: '0.375rem',
               cursor: 'pointer',
               fontSize: '0.875rem',
               transition: 'background-color 0.2s'
             }}
             onMouseEnter={(e) => e.currentTarget.style.backgroundColor = colors.button.active}
             onMouseLeave={(e) => e.currentTarget.style.backgroundColor = colors.button.active}
           >
            Refresh
          </button>
        </div>

        {collections && collections.collections.length === 0 ? (
           <div style={{
             textAlign: 'center',
             padding: '3rem',
             color: colors.text.secondary
           }}>
             No collections found. Upload some documents to create your first collection.
           </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {collections?.collections.map((collection) => (
               <div
                 key={collection.name}
                 style={{
                   padding: '1.5rem',
                   border: `1px solid ${colors.border}`,
                   borderRadius: '0.5rem',
                   backgroundColor: colors.bg.secondary,
                   transition: 'all 0.2s'
                 }}
                 onMouseEnter={(e) => {
                   e.currentTarget.style.borderColor = colors.button.active;
                   e.currentTarget.style.boxShadow = `0 2px 8px ${colors.shadow}`;
                 }}
                 onMouseLeave={(e) => {
                   e.currentTarget.style.borderColor = colors.border;
                   e.currentTarget.style.boxShadow = 'none';
                 }}
               >
                 <h3 style={{ fontSize: '1.125rem', fontWeight: 'bold', marginBottom: '1rem', color: colors.text.primary }}>
                   {collection.name}
                 </h3>

                 <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.875rem' }}>
                   <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                     <span style={{ color: colors.text.secondary }}>Documents:</span>
                     <span style={{ fontWeight: 'bold', color: colors.text.primary }}>{collection.count}</span>
                   </div>

                  {Object.keys(collection.metadata).length > 0 && (
                     <details style={{ marginTop: '0.5rem' }}>
                       <summary style={{ cursor: 'pointer', color: colors.text.secondary, fontWeight: 'bold' }}>
                         Metadata
                       </summary>
                       <pre style={{
                         marginTop: '0.5rem',
                         padding: '0.5rem',
                         backgroundColor: colors.bg.primary,
                         border: `1px solid ${colors.border}`,
                         borderRadius: '0.25rem',
                         overflow: 'auto',
                         fontSize: '0.75rem',
                         color: colors.text.primary
                       }}>
                         {JSON.stringify(collection.metadata, null, 2)}
                       </pre>
                     </details>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
