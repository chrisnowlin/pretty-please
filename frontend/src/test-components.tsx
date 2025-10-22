#!/usr/bin/env bun
/**
 * Test that React components are rendering correctly
 */

import React from 'react';
import { renderToString } from 'react-dom/server';

// Import components
import Layout from './components/common/Layout';
import Navigation from './components/common/Navigation';
import LoadingSpinner from './components/common/LoadingSpinner';
import SearchBar from './components/search/SearchBar';
import ResultCard from './components/search/ResultCard';
import UploadZone from './components/ingestion/UploadZone';
import CollectionSelector from './components/collections/CollectionSelector';

console.log('🧪 Testing React Components Rendering\n');

const tests = [
  {
    name: 'Layout',
    component: <Layout>Test Content</Layout>,
    expectedContent: ['Jina RAG Pipeline', 'Test Content']
  },
  {
    name: 'Navigation',
    component: <Navigation currentPage="search" onNavigate={() => {}} />,
    expectedContent: ['Search', 'Upload Documents', 'Collections']
  },
  {
    name: 'LoadingSpinner',
    component: <LoadingSpinner />,
    expectedContent: ['spin']
  },
  {
    name: 'SearchBar',
    component: <SearchBar query="" onQueryChange={() => {}} onSearch={() => {}} topK={5} onTopKChange={() => {}} />,
    expectedContent: ['Enter your search query', 'Number of results']
  },
  {
    name: 'ResultCard',
    component: <ResultCard result={{
      id: 'test-1',
      score: 0.95,
      document: 'Test document content',
      metadata: { source: 'test' }
    }} />,
    expectedContent: ['95.0%', 'Test document content', 'Metadata']
  },
  {
    name: 'UploadZone',
    component: <UploadZone onUpload={() => {}} supportedFormats={['.txt', '.pdf']} />,
    expectedContent: ['Drag and drop files', 'click to browse']
  },
  {
    name: 'CollectionSelector',
    component: <CollectionSelector 
      collections={[{ name: 'test', count: 10, metadata: {} }]}
      selectedCollection=""
      onSelect={() => {}}
    />,
    expectedContent: ['Select Collection', 'test (10 documents)']
  }
];

let allPassed = true;

for (const test of tests) {
  try {
    const html = renderToString(test.component);
    const passed = test.expectedContent.every(content => html.includes(content));
    
    if (passed) {
      console.log(`✅ ${test.name}: Rendered successfully`);
    } else {
      console.log(`❌ ${test.name}: Missing expected content`);
      allPassed = false;
    }
  } catch (error) {
    console.log(`❌ ${test.name}: Failed to render - ${error.message}`);
    allPassed = false;
  }
}

console.log('\n' + '='.repeat(60));
if (allPassed) {
  console.log('✨ All components render correctly!');
} else {
  console.log('⚠️ Some components failed to render.');
}
console.log('='.repeat(60));

process.exit(allPassed ? 0 : 1);