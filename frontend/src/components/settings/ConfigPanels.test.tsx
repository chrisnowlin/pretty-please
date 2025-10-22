import { describe, test, expect, beforeEach, afterEach } from 'bun:test';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Window } from 'happy-dom';

import EmbeddingConfigPanel from './EmbeddingConfigPanel';
import OCRConfigPanel from './OCRConfigPanel';
import { ThemeContext } from '../../contexts/ThemeContext';

type FetchCall = { input: RequestInfo | URL; init?: RequestInit };

const windowInstance = new Window();
(globalThis as any).window = windowInstance as unknown as Window;
(globalThis as any).document = windowInstance.document;
(globalThis as any).navigator = windowInstance.navigator;

const testingLibrary = await import('@testing-library/react');
const { render, screen, cleanup, waitFor, fireEvent } = testingLibrary;

const embeddingConfigResponse = {
  config: {
    task: 'retrieval.passage',
    dimensions: 1024,
    late_chunking: true,
    return_multivector: false,
    embedding_format: 'float',
    batch_size: 32,
    max_tokens_per_batch: 8192,
  },
  preset: 'for_documents',
};

const embeddingPresetsResponse = [
  {
    name: 'for_documents',
    display_name: 'Document Optimized',
    description: 'Preserves context with late chunking',
    performance_characteristics: {
      speed: 'Standard',
      quality: 'High',
    },
  },
  {
    name: 'fast',
    display_name: 'Fast',
    description: 'Lower dimensions for quicker throughput',
    performance_characteristics: {
      speed: '4× faster',
      dimensions: '512',
    },
  },
];

const ocrConfigResponse = {
  config: {
    batch_size: 20,
    render_workers: 4,
    analysis_workers: 2,
    pre_render_batches: 3,
    checkpoint_enabled: true,
    use_two_tier: false,
    complexity_table_threshold: 1,
    complexity_equation_threshold: 1,
    complexity_image_threshold: 2,
    complexity_min_text_length: 100,
  },
  preset: 'balanced',
};

const ocrPresetsResponse = [
  {
    name: 'balanced',
    display_name: 'Balanced',
    description: 'Balanced speed and quality',
    performance_characteristics: {
      speed: 'Standard',
      memory: '~8 GB',
    },
  },
  {
    name: 'two_tier',
    display_name: 'Two-tier Hybrid',
    description: 'Routes complex pages for higher quality',
    performance_characteristics: {
      speed: '2× faster',
      routing: 'Complexity-based',
    },
  },
];

let fetchCalls: FetchCall[] = [];

function createFetchResponse(data: unknown): ResponseLike {
  return {
    ok: true,
    json: async () => data,
  } as ResponseLike;
}

type ResponseLike = { ok: boolean; json: () => Promise<unknown> };

beforeEach(() => {
  fetchCalls = [];
  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<ResponseLike> => {
    fetchCalls.push({ input, init });
    const url = typeof input === 'string' ? input : input.toString();
    const method = init?.method?.toUpperCase() || 'GET';

    if (url.endsWith('/api/config/embeddings') && method === 'GET') {
      return createFetchResponse(embeddingConfigResponse);
    }

    if (url.endsWith('/api/config/embeddings/presets')) {
      return createFetchResponse(embeddingPresetsResponse);
    }

    if (url.endsWith('/api/config/embeddings') && method === 'POST') {
      const body = init?.body ? JSON.parse(init.body.toString()) : {};
      return createFetchResponse({ config: body, preset: 'custom' });
    }

    if (url.endsWith('/api/config/recommendations')) {
      return createFetchResponse({
        system: 'Darwin',
        architecture: 'arm64',
        total_memory_gb: 32,
        embeddings: {
          preset: 'for_documents',
          display_name: 'Document Optimized',
          reason: 'Balanced preset for document indexing.',
          estimated_memory_gb: 8,
          speed_hint: 'Standard',
        },
        ocr: {
          preset: 'mlx_optimized',
          display_name: 'MLX Optimized',
          reason: 'Apple Silicon detected; MLX uses ~2.2 GB vs ~8 GB.',
          estimated_memory_gb: 2.2,
          speed_hint: 'Fastest on Apple Silicon',
        },
      });
    }

    if (url.endsWith('/api/config/ocr') && method === 'GET') {
      return createFetchResponse(ocrConfigResponse);
    }

    if (url.endsWith('/api/config/ocr/presets')) {
      return createFetchResponse(ocrPresetsResponse);
    }

    if (url.endsWith('/api/config/ocr') && method === 'POST') {
      const body = init?.body ? JSON.parse(init.body.toString()) : {};
      return createFetchResponse({ config: body, preset: 'custom' });
    }

    throw new Error(`Unhandled fetch: ${method} ${url}`);
  };
});

afterEach(() => {
  cleanup();
});

function renderWithProviders(element: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeContext.Provider value={{ theme: 'light', mode: 'light', setMode: () => {} }}>
        {element}
      </ThemeContext.Provider>
    </QueryClientProvider>
  );
}

describe('EmbeddingConfigPanel', () => {
  test('renders current configuration and submits updates', async () => {
    renderWithProviders(<EmbeddingConfigPanel />);

    await screen.findByText(/Basic Settings/i);

    const dimensionSelect = await screen.findByDisplayValue('1024');
    fireEvent.change(dimensionSelect, { target: { value: '512' } });

    const saveButton = screen.getByRole('button', { name: /save configuration/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(fetchCalls.some(({ input, init }) => {
        const url = typeof input === 'string' ? input : input.toString();
        return url.endsWith('/api/config/embeddings') && init?.method === 'POST';
      })).toBe(true);
    });

    await screen.findByText(/Embedding configuration updated successfully/i);
  });
});

describe('OCRConfigPanel', () => {
  test('renders current configuration and submits updates', async () => {
    renderWithProviders(<OCRConfigPanel />);

    await screen.findByText(/Basic Settings/i);

    const batchInput = await screen.findByDisplayValue('20');
    fireEvent.change(batchInput, { target: { value: '18' } });

    const saveButton = screen.getByRole('button', { name: /save configuration/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(fetchCalls.some(({ input, init }) => {
        const url = typeof input === 'string' ? input : input.toString();
        return url.endsWith('/api/config/ocr') && init?.method === 'POST';
      })).toBe(true);
    });

    await screen.findByText(/OCR configuration updated successfully/i);
  });
});
