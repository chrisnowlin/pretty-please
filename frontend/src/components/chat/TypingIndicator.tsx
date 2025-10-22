import React from 'react';
import { MessageAvatar } from './MessageAvatar';

export const TypingIndicator = React.memo(function TypingIndicator() {
  return (
    <div
      className="flex items-start gap-2 justify-start"
      role="status"
      aria-live="polite"
      aria-label="Assistant is typing"
    >
      <MessageAvatar role="assistant" />

      <div className="bg-gray-100 border border-gray-200 rounded-2xl p-3 md:p-4 shadow-sm">
        <div className="flex items-center gap-1" aria-hidden="true">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
        </div>
        <span className="sr-only">Assistant is typing</span>
      </div>
    </div>
  );
});
