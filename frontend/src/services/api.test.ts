import { describe, test, expect } from 'bun:test';
import { APIClient } from './api';

describe('APIClient', () => {
  const client = new APIClient();

  test('should create API client instance', () => {
    expect(client).toBeDefined();
    expect(client).toBeInstanceOf(APIClient);
  });

  test('should have search method', () => {
    expect(typeof client.search).toBe('function');
  });

  test('should have getCollections method', () => {
    expect(typeof client.getCollections).toBe('function');
  });

  test('should have uploadDocuments method', () => {
    expect(typeof client.uploadDocuments).toBe('function');
  });

  test('should have getIngestionStatus method', () => {
    expect(typeof client.getIngestionStatus).toBe('function');
  });

  test('should have getSupportedFormats method', () => {
    expect(typeof client.getSupportedFormats).toBe('function');
  });
});
