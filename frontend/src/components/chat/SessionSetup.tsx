import { useState } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';
import type { Collection, SessionConfig } from '../../types/chat';

interface SessionSetupProps {
  collections: Collection[] | undefined;
  selectedCollection: string;
  onCollectionChange: (collectionName: string) => void;
  onCreateSession: (config: SessionConfig) => void;
}

export function SessionSetup({
  collections,
  selectedCollection,
  onCollectionChange,
  onCreateSession
}: SessionSetupProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  // Advanced settings state
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [enableThinking, setEnableThinking] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [topP, setTopP] = useState(0.8);
  const [topK, setTopK] = useState(20);
  const [maxHistoryTurns, setMaxHistoryTurns] = useState(10);
  const [useGlobalRAG, setUseGlobalRAG] = useState(true);
  const [initialRetrievalK, setInitialRetrievalK] = useState(20);
  const [enableReranking, setEnableReranking] = useState(true);
  const [rerankTopN, setRerankTopN] = useState(5);

  // Apply thinking mode preset
  const handleThinkingToggle = (enabled: boolean) => {
    setEnableThinking(enabled);
    if (enabled) {
      // Thinking mode defaults
      setTemperature(0.6);
      setTopP(0.95);
    } else {
      // Non-thinking defaults
      setTemperature(0.4);
      setTopP(0.9);
    }
  };

  const handleCreateSession = () => {
    const config: SessionConfig = {
      temperature,
      top_p: topP,
      top_k: topK,
      max_history_turns: maxHistoryTurns,
      enable_thinking: enableThinking,
      max_tokens: 512,
      // Only include RAG settings if not using global
      ...(useGlobalRAG ? {} : {
        initial_retrieval_k: initialRetrievalK,
        enable_reranking: enableReranking,
        rerank_top_n: rerankTopN
      })
    };
    onCreateSession(config);
  };

  return (
    <div style={{
      backgroundColor: colors.bg.primary,
      borderRadius: '0.5rem',
      boxShadow: `0 1px 3px ${colors.shadow}`,
      padding: '1.5rem'
    }}>
      <h2 style={{
        fontSize: '1.25rem',
        fontWeight: '600',
        marginBottom: '1rem',
        color: colors.text.primary
      }}>Start a Chat Session</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: '500',
            marginBottom: '0.5rem',
            color: colors.text.primary
          }}>
            Select Collection
          </label>
          <select
            value={selectedCollection}
            onChange={(e) => onCollectionChange(e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: `1px solid ${colors.border}`,
              borderRadius: '0.25rem',
              outline: 'none',
              backgroundColor: colors.bg.primary,
              color: colors.text.primary,
              transition: 'border-color 0.2s, box-shadow 0.2s'
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = colors.button.active;
              e.currentTarget.style.boxShadow = `0 0 0 2px ${colors.button.active}33`;
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = colors.border;
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <option value="">Choose a collection...</option>
            {collections?.map((col) => (
              <option key={col.name} value={col.name}>
                {col.name} ({col.count} documents)
              </option>
            ))}
          </select>
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
              fontSize: '0.875rem',
              fontWeight: '600',
              cursor: 'pointer',
              outline: 'none',
              transition: 'color 0.2s',
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = colors.button.active}
            onMouseLeave={(e) => e.currentTarget.style.color = colors.text.primary}
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
              {/* Thinking Mode */}
              <div>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={enableThinking}
                    onChange={(e) => handleThinkingToggle(e.target.checked)}
                    style={{ cursor: 'pointer' }}
                  />
                  <span style={{ color: colors.text.primary, fontWeight: '500', fontSize: '0.875rem' }}>
                    Enable Thinking Mode
                  </span>
                </label>
                <p style={{
                  fontSize: '0.75rem',
                  color: colors.text.secondary,
                  marginTop: '0.25rem',
                  marginLeft: '1.5rem'
                }}>
                  Enables complex reasoning with preset parameters (temp: 0.6, top_p: 0.95)
                </p>
              </div>

              {/* Temperature */}
              <div>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  marginBottom: '0.5rem',
                  color: colors.text.primary
                }}>
                  Temperature: {temperature.toFixed(2)}
                  <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                    (0-2, controls randomness)
                  </span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  style={{ width: '100%', cursor: 'pointer' }}
                />
              </div>

              {/* Top P */}
              <div>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  marginBottom: '0.5rem',
                  color: colors.text.primary
                }}>
                  Top P: {topP.toFixed(2)}
                  <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                    (0-1, nucleus sampling)
                  </span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={topP}
                  onChange={(e) => setTopP(parseFloat(e.target.value))}
                  style={{ width: '100%', cursor: 'pointer' }}
                />
              </div>

              {/* Top K */}
              <div>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  marginBottom: '0.5rem',
                  color: colors.text.primary
                }}>
                  Top K
                  <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                    (min 1, limits vocabulary)
                  </span>
                </label>
                <input
                  type="number"
                  min="1"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value) || 1)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: `1px solid ${colors.border}`,
                    borderRadius: '0.25rem',
                    backgroundColor: colors.bg.primary,
                    color: colors.text.primary,
                    outline: 'none',
                  }}
                />
              </div>

              {/* Max History Turns */}
              <div>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  marginBottom: '0.5rem',
                  color: colors.text.primary
                }}>
                  Max History Turns
                  <span style={{ color: colors.text.secondary, fontWeight: 'normal', marginLeft: '0.5rem' }}>
                    (min 1, conversation memory)
                  </span>
                </label>
                <input
                  type="number"
                  min="1"
                  value={maxHistoryTurns}
                  onChange={(e) => setMaxHistoryTurns(parseInt(e.target.value) || 1)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: `1px solid ${colors.border}`,
                    borderRadius: '0.25rem',
                    backgroundColor: colors.bg.primary,
                    color: colors.text.primary,
                    outline: 'none',
                  }}
                />
              </div>

              {/* RAG Settings */}
              <div style={{
                borderTop: `1px solid ${colors.border}`,
                paddingTop: '1rem',
              }}>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={useGlobalRAG}
                      onChange={(e) => setUseGlobalRAG(e.target.checked)}
                      style={{ cursor: 'pointer' }}
                    />
                    <span style={{ color: colors.text.primary, fontWeight: '500', fontSize: '0.875rem' }}>
                      Use Global RAG Settings
                    </span>
                  </label>
                  <p style={{
                    fontSize: '0.75rem',
                    color: colors.text.secondary,
                    marginTop: '0.25rem',
                    marginLeft: '1.5rem'
                  }}>
                    When unchecked, configure session-specific retrieval settings
                  </p>
                </div>

                {!useGlobalRAG && (
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '1rem',
                    paddingLeft: '1rem',
                    borderLeft: `2px solid ${colors.border}`,
                  }}>
                    {/* Initial Retrieval K */}
                    <div>
                      <label style={{
                        display: 'block',
                        fontSize: '0.875rem',
                        fontWeight: '500',
                        marginBottom: '0.5rem',
                        color: colors.text.primary
                      }}>
                        Initial Retrieval K
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        value={initialRetrievalK}
                        onChange={(e) => setInitialRetrievalK(parseInt(e.target.value) || 1)}
                        style={{
                          width: '100%',
                          padding: '0.5rem',
                          border: `1px solid ${colors.border}`,
                          borderRadius: '0.25rem',
                          backgroundColor: colors.bg.primary,
                          color: colors.text.primary,
                          outline: 'none',
                        }}
                      />
                    </div>

                    {/* Enable Reranking */}
                    <div>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={enableReranking}
                          onChange={(e) => setEnableReranking(e.target.checked)}
                          style={{ cursor: 'pointer' }}
                        />
                        <span style={{ color: colors.text.primary, fontSize: '0.875rem' }}>
                          Enable Reranking
                        </span>
                      </label>
                    </div>

                    {/* Rerank Top N */}
                    {enableReranking && (
                      <div>
                        <label style={{
                          display: 'block',
                          fontSize: '0.875rem',
                          fontWeight: '500',
                          marginBottom: '0.5rem',
                          color: colors.text.primary
                        }}>
                          Rerank Top N
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="20"
                          value={rerankTopN}
                          onChange={(e) => setRerankTopN(parseInt(e.target.value) || 1)}
                          style={{
                            width: '100%',
                            padding: '0.5rem',
                            border: `1px solid ${colors.border}`,
                            borderRadius: '0.25rem',
                            backgroundColor: colors.bg.primary,
                            color: colors.text.primary,
                            outline: 'none',
                          }}
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <button
          onClick={handleCreateSession}
          disabled={!selectedCollection}
          style={{
            backgroundColor: !selectedCollection ? colors.button.inactive : colors.button.active,
            color: 'white',
            padding: '0.5rem 1.5rem',
            borderRadius: '0.25rem',
            border: 'none',
            outline: 'none',
            transition: 'background-color 0.2s',
            cursor: !selectedCollection ? 'not-allowed' : 'pointer',
            fontWeight: '500'
          }}
          onMouseEnter={(e) => {
            if (selectedCollection) {
              e.currentTarget.style.backgroundColor = colors.button.active;
            }
          }}
          onMouseLeave={(e) => {
            if (selectedCollection) {
              e.currentTarget.style.backgroundColor = colors.button.active;
            }
          }}
        >
          Start Chat
        </button>
      </div>
    </div>
  );
}
