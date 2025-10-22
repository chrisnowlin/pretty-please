import React from 'react';
import { ChatMessage } from './ChatMessage';
import { TypingIndicator } from './TypingIndicator';
import { PromptSuggestions } from './PromptSuggestions';
import MetricsDisplay from './MetricsDisplay';
import type { Message, CitationMetadata } from '../../types/chat';

interface MessageListProps {
  messages: Message[];
  isGenerating: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  onSelectSuggestion?: (suggestion: string) => void;
  onCitationClick?: (citationId: string, citationData: CitationMetadata) => void;
}

const DEFAULT_SUGGESTIONS = [
  "Summarize the key findings from the documents",
  "What are the main themes across these documents?",
  "Find information about the latest updates",
  "What questions can I ask about this collection?"
];

export function MessageList({ messages, isGenerating, messagesEndRef, onSelectSuggestion, onCitationClick }: MessageListProps) {
  const isEmpty = messages.length === 0 && !isGenerating;

  return (
    <div
      className="h-80 sm:h-96 overflow-y-auto p-2 sm:p-4 space-y-3 sm:space-y-4 flex flex-col"
      role="log"
      aria-live="polite"
      aria-label="Chat messages"
    >
      {isEmpty ? (
        <PromptSuggestions
          suggestions={DEFAULT_SUGGESTIONS}
          onSelect={onSelectSuggestion || (() => {})}
        />
      ) : (
        <React.Fragment>
          {messages.map((msg, idx) => {
            const isLastMessage = idx === messages.length - 1;
            const streamingThisMessage = isGenerating && isLastMessage && msg.role === 'assistant' && !msg.timestamp;
            return (
              <React.Fragment key={msg.id || `${msg.role}-${idx}`}>
                <ChatMessage
                  message={msg}
                  showTimestamp={!!msg.timestamp}
                  isStreaming={streamingThisMessage}
                  onCitationClick={onCitationClick}
                />
                {/* Show retrieval metrics for assistant messages that have them */}
                {msg.role === 'assistant' && msg.retrievalMetrics && (
                  <MetricsDisplay metrics={msg.retrievalMetrics} />
                )}
              </React.Fragment>
            );
          })}

          {isGenerating && <TypingIndicator />}
        </React.Fragment>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}
