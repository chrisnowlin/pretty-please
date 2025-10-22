import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LessonPlanForm, type LessonPlanRequest } from '../components/lessonPlan/LessonPlanForm';
import { ExportDropdown } from '../components/lessonPlan/ExportDropdown';
import { LessonDetail } from '../components/lessonPlan/LessonDetail';
import { apiClient } from '../services/api';

interface LessonPlanResponse {
  lesson_id: string;
  markdown: string;
  metadata: any;
  sources_count: number;
  images_count: number;
  generation_time_seconds: number;
}

interface LessonListItem {
  id: number;
  title: string;
  grade: string;
  subject: string;
  duration_minutes: number;
  created_at: string;
}

export const LessonPlansPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [lesson, setLesson] = useState<LessonPlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedLessonId, setSelectedLessonId] = useState<number | null>(null);
  const [showSavedLessons, setShowSavedLessons] = useState(false);

  const { data: savedLessons } = useQuery<LessonListItem[]>({
    queryKey: ['lessons'],
    queryFn: async () => {
      const response = await fetch('/api/lessons?limit=20');
      if (!response.ok) throw new Error('Failed to fetch lessons');
      return response.json();
    },
    enabled: showSavedLessons,
  });

  const handleGenerate = async (data: LessonPlanRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/lesson-plan/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate lesson: ${response.statusText}`);
      }

      const result = await response.json();
      setLesson(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  if (selectedLessonId) {
    return <LessonDetail lessonId={selectedLessonId} onBack={() => setSelectedLessonId(null)} />;
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Lesson Plan Generator</h1>
        <button
          onClick={() => setShowSavedLessons(!showSavedLessons)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {showSavedLessons ? 'Hide' : 'Show'} Saved Lessons
        </button>
      </div>

      {showSavedLessons && (
        <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-md">
          <h2 className="text-xl font-bold mb-4">Saved Lessons</h2>
          {savedLessons && savedLessons.length > 0 ? (
            <div className="space-y-2">
              {savedLessons.map((item) => (
                <div
                  key={item.id}
                  onClick={() => setSelectedLessonId(item.id)}
                  className="p-3 border rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 dark:border-gray-600"
                >
                  <div className="font-semibold">{item.title}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {item.grade} | {item.subject} | {item.duration_minutes} min
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600 dark:text-gray-400">No saved lessons yet</p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <LessonPlanForm onGenerate={handleGenerate} isLoading={isLoading} />
          {error && (
            <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">{error}</div>
          )}
        </div>

        <div>
          {lesson && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Sources: {lesson.sources_count} | Images: {lesson.images_count} |
                  Time: {lesson.generation_time_seconds}s
                </div>
                <ExportDropdown
                  lessonId={lesson.lesson_id}
                  lessonTitle={lesson.metadata.title}
                />
              </div>

              <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-auto max-h-screen">
                <pre className="whitespace-pre-wrap text-sm">{lesson.markdown}</pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
