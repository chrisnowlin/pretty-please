import React from 'react';
import ReactMarkdown from 'react-markdown';
import { MessageAvatar } from './MessageAvatar';
import { CitationLink } from './CitationLink';
import type { Message, CitationMetadata } from '../../types/chat';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeColors } from '../../styles/theme';

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
  showTimestamp?: boolean;
  onCitationClick?: (citationId: string, citationData: CitationMetadata) => void;
}

/**
 * Parse text content to replace citation markers with CitationLink components
 * Matches patterns: [1], [2], [IMG-1], [IMG-2], etc.
 */
function parseCitationsInText(
  text: string,
  citationMap: Record<string, CitationMetadata> | undefined,
  onCitationClick: ((citationId: string, citationData: CitationMetadata) => void) | undefined
): React.ReactNode[] {
  if (!citationMap || !onCitationClick) {
    return [text];
  }

  // Regex to match citation patterns: [1], [2], [IMG-1], etc.
  const citationRegex = /(\[(?:IMG-)?(\d+)\])/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;

  while ((match = citationRegex.exec(text)) !== null) {
    const fullMatch = match[1]; // e.g., "[1]" or "[IMG-1]"
    const matchIndex = match.index;

    // Add text before citation
    if (matchIndex > lastIndex) {
      parts.push(text.substring(lastIndex, matchIndex));
    }

    // Check if this citation exists in the map
    const citationData = citationMap[fullMatch];
    if (citationData) {
      // Add citation link
      parts.push(
        <CitationLink
          key={`citation-${fullMatch}-${matchIndex}`}
          citationId={fullMatch}
          citationData={citationData}
          onClick={onCitationClick}
        />
      );
    } else {
      // Citation not in map, render as plain text
      parts.push(fullMatch);
    }

    lastIndex = citationRegex.lastIndex;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
}

/**
 * Process React children to find and replace citation text with CitationLink components
 * This function flattens the children array and processes each text node for citations
 */
function processChildrenForCitations(
  children: React.ReactNode,
  citationMap: Record<string, CitationMetadata> | undefined,
  onCitationClick: ((citationId: string, citationData: CitationMetadata) => void) | undefined
): React.ReactNode {
  if (!citationMap || !onCitationClick) {
    return children;
  }

  const result: React.ReactNode[] = [];

  React.Children.forEach(children, (child) => {
    // If child is a string, parse for citations and add all parts
    if (typeof child === 'string') {
      const parsed = parseCitationsInText(child, citationMap, onCitationClick);
      result.push(...parsed);
    }
    // If child is a React element with children, recursively process
    else if (React.isValidElement(child) && child.props.children) {
      const processedChild = React.cloneElement(child, {
        ...child.props,
        children: processChildrenForCitations(child.props.children, citationMap, onCitationClick)
      } as any);
      result.push(processedChild);
    }
    // Otherwise add as-is
    else {
      result.push(child);
    }
  });

  return result;
}

export function ChatMessage({ message, showTimestamp = true, isStreaming = false, onCitationClick }: ChatMessageProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const messageStyle = {
    maxWidth: '85%',
    borderRadius: '1rem',
    padding: '0.75rem 1rem',
    boxShadow: `0 1px 2px ${colors.shadow}`,
    transition: 'all 0.15s',
    backgroundColor: message.role === 'user' ? colors.button.active : colors.bg.secondary,
    color: message.role === 'user' ? 'white' : colors.text.primary,
    border: message.role === 'assistant' ? `1px solid ${colors.border}` : 'none',
  };

  const containerStyle = {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '0.75rem',
    justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
    flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
  };

  return (
    <div style={containerStyle}>
      <MessageAvatar role={message.role} />

      <div
        style={messageStyle}
        aria-label={`${message.role === 'user' ? 'You' : 'Assistant'}: ${String(message.content).substring(0, 50)}${String(message.content).length > 50 ? '...' : ''}`}
      >
        <div style={{
          fontSize: '1rem',
          lineHeight: '1.5',
          color: 'inherit',
        }}>
          {message.role === 'assistant' ? (
            <ReactMarkdown
              components={{
                p: ({children}) => (
                  <p style={{ margin: '0.5rem 0', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {processChildrenForCitations(children, message.citationMap, onCitationClick)}
                  </p>
                ),
                strong: ({children}) => <strong style={{ fontWeight: 'bold' }}>{children}</strong>,
                em: ({children}) => <em style={{ fontStyle: 'italic' }}>{children}</em>,
                ul: ({children}) => <ul style={{ listStyleType: 'disc', marginLeft: '1rem', margin: '0.5rem 0' }}>{children}</ul>,
                ol: ({children}) => <ol style={{ listStyleType: 'decimal', marginLeft: '1rem', margin: '0.5rem 0' }}>{children}</ol>,
                li: ({children}) => (
                  <li style={{ margin: '0.25rem 0', whiteSpace: 'normal' }}>
                    {processChildrenForCitations(children, message.citationMap, onCitationClick)}
                  </li>
                ),
                code: ({children}) => <code style={{
                  backgroundColor: colors.bg.tertiary,
                  padding: '0.125rem 0.25rem',
                  borderRadius: '0.25rem',
                  fontSize: '0.875rem',
                  color: colors.text.primary,
                }}>{children}</code>,
                h1: ({children}) => <h1 style={{ fontSize: '1.25rem', fontWeight: 'bold', margin: '0.5rem 0' }}>{children}</h1>,
                h2: ({children}) => <h2 style={{ fontSize: '1.125rem', fontWeight: 'bold', margin: '0.5rem 0' }}>{children}</h2>,
                h3: ({children}) => <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', margin: '0.5rem 0' }}>{children}</h3>,
              }}
            >{message.content}</ReactMarkdown>
          ) : (
            <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
          )}
          {isStreaming && message.role === 'assistant' && (
            <span
              style={{
                display: 'inline-block',
                width: '0.125rem',
                height: '1.25rem',
                backgroundColor: 'currentColor',
                marginLeft: '0.125rem',
                animation: 'pulse 1s ease-in-out infinite',
              }}
              aria-hidden="true"
            />
          )}
        </div>
        {showTimestamp && message.timestamp && !isStreaming && (
          <p style={{
            fontSize: '0.75rem',
            lineHeight: '1.25',
            fontWeight: '500',
            opacity: 0.7,
            marginTop: '0.375rem',
            color: colors.text.secondary,
          }}>
            {message.timestamp.toLocaleTimeString()}
          </p>
        )}
      </div>
    </div>
  );
}
