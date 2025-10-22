export interface SearchRequest {
  query: string;
  collection_name: string;
  top_k?: number;
  metadata_filter?: Record<string, any>;
  distance_metric?: string;
}

export interface ImageMetadata {
  width: number;
  height: number;
  format: string;
  file_size: number;
  thumbnail_url: string;
  full_image_url: string;
  mean_rgb: [number, number, number];
}

export interface SearchResult {
  id: string;
  score: number;
  document: string | null;
  metadata: Record<string, any>;
  result_type?: 'text' | 'image';
  image_metadata?: ImageMetadata;
}

export interface SearchResponse {
  results: SearchResult[];
  query: string;
  collection: string;
  total_results: number;
}

export interface CollectionInfo {
  name: string;
  count: number;
  metadata: Record<string, any>;
}

export interface CollectionsResponse {
  collections: CollectionInfo[];
}

export interface CollectionConfig {
  config_version: string;
  enable_layout_analysis: boolean;
  layout_ocr_enabled: boolean;
  layout_table_extraction: boolean;
  save_extracted_images: boolean;
  save_region_metadata: boolean;
  region_granularity: 'fine' | 'coarse';
  max_image_dimension: number;
}

export interface FileStatus {
  name: string;
  status: string;
  size: number;
  error?: string;
}

export interface IngestionResponse {
  task_id: string;
  files: FileStatus[];
}

export interface IngestionStatusResponse {
  task_id: string;
  status: string;
  progress: number;
  current_file: string | null;
  processed_files: number;
  total_files: number;
  errors: Array<{ file: string; error: string }>;
}

export interface SupportedFormatsResponse {
  formats: string[];
  max_file_size_mb: number;
}

export interface LessonDetailResponse {
  id: number;
  lesson_id: string;
  title: string;
  markdown_content: string;
  grade: string;
  subject: string;
  topic: string;
  learning_objective: string;
  duration_minutes: number;
  teaching_style: string;
  metadata_json: Record<string, any> | null;
  sources_count: number;
  images_count: number;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
}

export interface UpdateLessonRequest {
  markdown_content?: string;
  title?: string;
  duration_minutes?: number;
  teaching_style?: string;
  learning_objective?: string;
}

const API_BASE_URL = '/api';

export class APIClient {
  async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Search failed');
    }

    return response.json();
  }

  async searchByImage(
    image: File,
    collectionName: string,
    topK: number = 5,
    modalityFilter?: 'image' | 'text'
  ): Promise<SearchResponse> {
    const formData = new FormData();
    formData.append('image', image);
    formData.append('collection_name', collectionName);
    formData.append('top_k', topK.toString());
    if (modalityFilter) {
      formData.append('modality_filter', modalityFilter);
    }

    const response = await fetch(`${API_BASE_URL}/search/image`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Image search failed');
    }

    return response.json();
  }

  getThumbnailUrl(collection: string, imageId: string): string {
    return `${API_BASE_URL}/images/thumbnail/${collection}/${imageId}`;
  }

  getFullImageUrl(collection: string, imageId: string): string {
    return `${API_BASE_URL}/images/full/${collection}/${imageId}`;
  }

  async getCollections(): Promise<CollectionsResponse> {
    const response = await fetch(`${API_BASE_URL}/collections`);

    if (!response.ok) {
      throw new Error('Failed to fetch collections');
    }

    return response.json();
  }

  async uploadDocuments(
    files: File[],
    collectionName: string
  ): Promise<IngestionResponse> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('collection_name', collectionName);

    const response = await fetch(`${API_BASE_URL}/ingest/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  }

  async getIngestionStatus(taskId: string): Promise<IngestionStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/ingest/status/${taskId}`);

    if (!response.ok) {
      throw new Error('Failed to fetch ingestion status');
    }

    return response.json();
  }

  async getSupportedFormats(): Promise<SupportedFormatsResponse> {
    const response = await fetch(`${API_BASE_URL}/ingest/supported-formats`);

    if (!response.ok) {
      throw new Error('Failed to fetch supported formats');
    }

    return response.json();
  }

  async getCollectionConfig(collectionName: string): Promise<CollectionConfig> {
    const response = await fetch(`${API_BASE_URL}/collections/${encodeURIComponent(collectionName)}/config`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch collection config');
    }

    return response.json();
  }

  async updateCollectionConfig(
    collectionName: string,
    config: CollectionConfig
  ): Promise<CollectionConfig> {
    const response = await fetch(`${API_BASE_URL}/collections/${encodeURIComponent(collectionName)}/config`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update collection config');
    }

    return response.json();
  }

  async getLesson(lessonId: number): Promise<LessonDetailResponse> {
    const response = await fetch(`${API_BASE_URL}/lessons/${lessonId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch lesson');
    }

    return response.json();
  }

  async updateLesson(
    lessonId: number,
    updates: UpdateLessonRequest
  ): Promise<LessonDetailResponse> {
    const response = await fetch(`${API_BASE_URL}/lessons/${lessonId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update lesson');
    }

    return response.json();
  }
}

export const apiClient = new APIClient();
