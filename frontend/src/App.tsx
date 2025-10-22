import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './contexts/ThemeContext';
import SearchPage from './pages/SearchPage';
import IngestionPage from './pages/IngestionPage';
import CollectionsPage from './pages/CollectionsPage';
import ChatPage from './pages/ChatPage';
import SettingsPage from './pages/SettingsPage';
import { LessonPlansPage } from './pages/LessonPlansPage';
import Navigation from './components/common/Navigation';
import Layout from './components/common/Layout';

const queryClient = new QueryClient();

export default function App() {
  const [currentPage, setCurrentPage] = useState<'search' | 'ingest' | 'collections' | 'chat' | 'lesson-plans' | 'settings'>('search');

  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <Layout>
          <Navigation currentPage={currentPage} onNavigate={setCurrentPage} />
          {currentPage === 'search' && <SearchPage />}
          {currentPage === 'ingest' && <IngestionPage />}
          {currentPage === 'collections' && <CollectionsPage />}
          {currentPage === 'chat' && <ChatPage />}
          {currentPage === 'lesson-plans' && <LessonPlansPage />}
          {currentPage === 'settings' && <SettingsPage />}
        </Layout>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
