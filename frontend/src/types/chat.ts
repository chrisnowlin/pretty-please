export interface CitationMetadata {
  source: string;
  type: 'text' | 'image';
  score: number;
  metadata: Record<string, any>;
  document_url?: string;  // For text citations - URL to retrieve document
  document_id?: string;  // For image citations
  image_urls?: {
    thumbnail_url: string;
    full_image_url: string;
  };
}

export interface CitationMap {
  [citationId: string]: CitationMetadata;
}

export interface RetrievalMetrics {
  documents_retrieved: number;
  images_retrieved: number;
  documents_after_rerank: number;
  vector_search_time_ms: number;
  reranking_time_ms: number;
  total_time_ms: number;
  reranking_enabled: boolean;
  hybrid_search_used: boolean;
  compression_enabled: boolean;
}

export interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date | null;
  citationMap?: CitationMap;  // Optional citation map for this message
  retrievalMetrics?: RetrievalMetrics;  // Optional retrieval metrics for this message
}

export interface SessionConfig {
  temperature: number;
  top_p: number;
  top_k: number;
  max_history_turns: number;
  enable_thinking: boolean;
  max_tokens: number;
  // Optional RAG settings (only set if not using global)
  initial_retrieval_k?: number;
  enable_reranking?: boolean;
  rerank_top_n?: number;
}

export interface ChatSession {
  session_id: string;
  collection_name: string;
  config?: SessionConfig;
}

export interface Collection {
  name: string;
  count: number;
}
