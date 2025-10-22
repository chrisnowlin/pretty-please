import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { getThemeColors } from '../styles/theme';
import { useQuery } from '@tanstack/react-query';
import { MessageList, MessageInput, SessionSetup, ConnectionStatus, SourceViewer, ConfigSummaryBadge } from '../components/chat';
import type { Message, ChatSession, CitationMap, CitationMetadata, RetrievalMetrics, SessionConfig } from '../types/chat';

export default function ChatPage() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [selectedCollection, setSelectedCollection] = useState('');
   const [session, setSession] = useState<ChatSession | null>(null);
   const [messages, setMessages] = useState<Message[]>([]);
   const [input, setInput] = useState('');
   const [isConnected, setIsConnected] = useState(false);
   const [isGenerating, setIsGenerating] = useState(false);
   const [error, setError] = useState<string | null>(null);
   const [selectedCitation, setSelectedCitation] = useState<{ id: string; data: CitationMetadata } | null>(null);
   const currentCitationMapRef = useRef<CitationMap | null>(null);
   const currentRetrievalMetricsRef = useRef<RetrievalMetrics | null>(null);
   const wsRef = useRef<WebSocket | null>(null);
   const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch collections
  const { data: collections } = useQuery({
    queryKey: ['collections'],
    queryFn: async () => {
      const res = await fetch('/api/collections');
      return res.json();
    },
  });

   // Auto-scroll to bottom
   useEffect(() => {
     messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
   }, [messages]);

   // Cleanup WebSocket on unmount
   useEffect(() => {
     return () => {
       if (wsRef.current?.readyState === WebSocket.OPEN) {
         wsRef.current.close();
       }
     };
   }, []);

  // Create session and connect WebSocket
   const createSession = async (config: SessionConfig) => {
     if (!selectedCollection) {
       setError('Please select a collection');
       return;
     }

     setError(null);
     try {
      const res = await fetch('/api/chat/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collection_name: selectedCollection,
          config,
        }),
      });

       if (!res.ok) {
         throw new Error(`Failed to create session: HTTP ${res.status}`);
       }
       const data = await res.json();
       // Store session with config
       setSession({ ...data, config });

      // Connect WebSocket
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // In development, connect to backend on port 8000
      const backendHost = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host;
      const wsUrl = `${protocol}//${backendHost}/api/chat/ws/${data.session_id}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === 'context') {
          // Store citation map and retrieval metrics for the current conversation turn
          if (message.citation_map) {
            currentCitationMapRef.current = message.citation_map;
            console.log('Received citation map:', message.citation_map);
          }
          if (message.retrieval_metrics) {
            currentRetrievalMetricsRef.current = message.retrieval_metrics;
            console.log('Received retrieval metrics:', message.retrieval_metrics);
          }
        } else if (message.type === 'assistant_chunk') {
           setMessages((prev) => {
             const last = prev[prev.length - 1];
             if (last && last.role === 'assistant' && !last.timestamp) {
               // Append to current assistant message
               return [
                 ...prev.slice(0, -1),
                 { ...last, content: last.content + message.content },
               ];
             } else {
               // Start new assistant message with citation map and retrieval metrics
               return [...prev, {
                 id: `assistant-${Date.now()}`,
                 role: 'assistant' as const,
                 content: message.content,
                 timestamp: null,
                 citationMap: currentCitationMapRef.current || undefined,
                 retrievalMetrics: currentRetrievalMetricsRef.current || undefined
               }];
             }
           });
        } else if (message.type === 'complete') {
          setIsGenerating(false);
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.role === 'assistant') {
              return [...prev.slice(0, -1), { ...last, timestamp: new Date() }];
            }
            return prev;
          });
          // Clear citation map and retrieval metrics after response is complete
          currentCitationMapRef.current = null;
          currentRetrievalMetricsRef.current = null;
         } else if (message.type === 'error') {
           setIsGenerating(false);
           setError(message.content);
           currentCitationMapRef.current = null;
           currentRetrievalMetricsRef.current = null;
         }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');
      };

      wsRef.current = ws;
     } catch (error) {
       const message = error instanceof Error ? error.message : 'Failed to create chat session';
       setError(message);
       console.error('Failed to create session:', error);
     }
  };

   const sendMessage = (messageContent?: string) => {
     const content = messageContent || input.trim();
     if (!content || !wsRef.current || !isConnected || isGenerating) {
       return;
     }

      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date(),
      };

     setMessages((prev) => [...prev, userMessage]);
     setIsGenerating(true);

     wsRef.current.send(JSON.stringify({
       type: 'user_message',
       content,
     }));

     setInput('');
   };

   const handleSelectSuggestion = (suggestion: string) => {
     sendMessage(suggestion);
   };

   const handleCitationClick = (citationId: string, citationData: CitationMetadata) => {
     setSelectedCitation({ id: citationId, data: citationData });
   };

   const handleCloseSourceViewer = () => {
     setSelectedCitation(null);
   };

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
         }}>Chat</h1>

         {error && (
           <div style={{
             marginBottom: '1rem',
             padding: '1rem',
             backgroundColor: colors.bg.secondary,
             border: `1px solid ${colors.status.error}`,
             borderRadius: '0.5rem',
             display: 'flex',
             alignItems: 'flex-start',
             gap: '0.75rem'
           }}>
             <svg style={{
               width: '1.25rem',
               height: '1.25rem',
               color: colors.status.error,
               flexShrink: 0,
               marginTop: '0.125rem'
             }} fill="currentColor" viewBox="0 0 20 20">
               <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
             </svg>
             <div style={{ flex: 1 }}>
               <p style={{
                 fontSize: '0.875rem',
                 fontWeight: '500',
                 color: colors.status.error
               }}>{error}</p>
             </div>
             <button
               onClick={() => setError(null)}
               style={{
                 color: colors.status.error,
                 transition: 'color 0.2s',
                 flexShrink: 0
               }}
               onMouseEnter={(e) => e.currentTarget.style.color = colors.text.primary}
               onMouseLeave={(e) => e.currentTarget.style.color = colors.status.error}
               aria-label="Dismiss error"
             >
               <svg style={{ width: '1.25rem', height: '1.25rem' }} fill="currentColor" viewBox="0 0 20 20">
                 <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
               </svg>
             </button>
           </div>
         )}

       {!session ? (
         <SessionSetup
           collections={collections?.collections}
           selectedCollection={selectedCollection}
           onCollectionChange={setSelectedCollection}
           onCreateSession={createSession}
         />
       ) : (
         <div style={{
           backgroundColor: colors.bg.primary,
           borderRadius: '0.5rem',
           boxShadow: `0 1px 3px ${colors.shadow}`
         }}>
            {/* Header */}
            <div style={{
              borderBottom: `1px solid ${colors.border}`,
              padding: '1rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: colors.bg.primary
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div>
                  <h2 style={{
                    fontSize: '1.125rem',
                    fontWeight: '600',
                    lineHeight: '1.25',
                    color: colors.text.primary
                  }}>{session.collection_name}</h2>
                </div>
                <ConnectionStatus isConnected={isConnected} />
                {session.config && <ConfigSummaryBadge config={session.config} />}
              </div>
               <button
                onClick={() => {
                  wsRef.current?.close();
                  setSession(null);
                  setMessages([]);
                }}
                style={{
                  fontSize: '0.875rem',
                  color: colors.text.secondary,
                  border: 'none',
                  outline: 'none',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '0.25rem',
                  transition: 'all 0.2s',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = colors.text.primary}
                onMouseLeave={(e) => e.currentTarget.style.color = colors.text.secondary}
              >
                End Session
              </button>
           </div>

            <MessageList
              messages={messages}
              isGenerating={isGenerating}
              messagesEndRef={messagesEndRef}
              onSelectSuggestion={handleSelectSuggestion}
              onCitationClick={handleCitationClick}
            />

            {/* Source Viewer for citations */}
            {selectedCitation && (
              <SourceViewer
                citationId={selectedCitation.id}
                citationData={selectedCitation.data}
                onClose={handleCloseSourceViewer}
              />
            )}

           <MessageInput
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onSubmit={() => sendMessage()}
              disabled={!isConnected}
              isGenerating={isGenerating}
            />
        </div>
      )}
    </div>
  );
}
