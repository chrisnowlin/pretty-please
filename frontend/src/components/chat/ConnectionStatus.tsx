interface ConnectionStatusProps {
  isConnected: boolean;
  isConnecting?: boolean;
}

export function ConnectionStatus({ isConnected, isConnecting = false }: ConnectionStatusProps) {
  if (isConnecting) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-50 border border-yellow-200">
        <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
        <span className="text-sm font-medium text-yellow-800">
          Connecting...
        </span>
      </div>
    );
  }

  if (isConnected) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-50 border border-green-200">
        <div className="w-2 h-2 rounded-full bg-green-500" />
        <span className="text-sm font-medium text-green-800">
          Connected
        </span>
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-50 border border-red-200">
      <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
      </svg>
      <span className="text-sm font-medium text-red-800">
        Disconnected
      </span>
    </div>
  );
}
