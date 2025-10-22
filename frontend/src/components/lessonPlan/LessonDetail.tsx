import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { apiClient, type LessonDetailResponse, type UpdateLessonRequest } from '../../services/api';
import { TEACHING_STYLES, MIN_DURATION, MAX_DURATION } from '../../constants/educationOptions';

interface LessonDetailProps {
  lessonId: number;
  onBack?: () => void;
}

export const LessonDetail: React.FC<LessonDetailProps> = ({ lessonId, onBack }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [editedTitle, setEditedTitle] = useState('');
  const [editedDuration, setEditedDuration] = useState(50);
  const [editedTeachingStyle, setEditedTeachingStyle] = useState('balanced');
  const [editedObjective, setEditedObjective] = useState('');
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const { data: lesson, isLoading } = useQuery({
    queryKey: ['lessons', lessonId],
    queryFn: () => apiClient.getLesson(lessonId),
  });

  const updateMutation = useMutation({
    mutationFn: (updates: UpdateLessonRequest) => apiClient.updateLesson(lessonId, updates),
    onSuccess: (updatedLesson) => {
      queryClient.invalidateQueries({ queryKey: ['lessons', lessonId] });
      queryClient.invalidateQueries({ queryKey: ['lessons'] });
      setIsEditing(false);
      setError(null);
    },
    onError: (error: Error) => {
      setError(error.message);
    },
  });

  const isDirty = useMemo(() => {
    if (!lesson) return false;
    return (
      editedContent !== lesson.markdown_content ||
      editedTitle !== lesson.title ||
      editedDuration !== lesson.duration_minutes ||
      editedTeachingStyle !== lesson.teaching_style ||
      editedObjective !== lesson.learning_objective
    );
  }, [lesson, editedContent, editedTitle, editedDuration, editedTeachingStyle, editedObjective]);

  const handleEdit = () => {
    if (lesson) {
      setEditedContent(lesson.markdown_content);
      setEditedTitle(lesson.title);
      setEditedDuration(lesson.duration_minutes);
      setEditedTeachingStyle(lesson.teaching_style);
      setEditedObjective(lesson.learning_objective);
      setIsEditing(true);
      setError(null);
    }
  };

  const handleCancel = () => {
    if (isDirty) {
      if (window.confirm('Discard unsaved changes?')) {
        setIsEditing(false);
        setError(null);
      }
    } else {
      setIsEditing(false);
      setError(null);
    }
  };

  const handleSave = () => {
    if (!lesson) return;

    const updates: UpdateLessonRequest = {};
    if (editedContent !== lesson.markdown_content) {
      updates.markdown_content = editedContent;
    }
    if (editedTitle !== lesson.title) {
      updates.title = editedTitle;
    }
    if (editedDuration !== lesson.duration_minutes) {
      updates.duration_minutes = editedDuration;
    }
    if (editedTeachingStyle !== lesson.teaching_style) {
      updates.teaching_style = editedTeachingStyle;
    }
    if (editedObjective !== lesson.learning_objective) {
      updates.learning_objective = editedObjective;
    }

    if (Object.keys(updates).length === 0) {
      setError('No changes to save');
      return;
    }

    updateMutation.mutate(updates);
  };

  if (isLoading) {
    return <div className="p-6">Loading...</div>;
  }

  if (!lesson) {
    return <div className="p-6">Lesson not found</div>;
  }

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleString();
  };

  return (
    <div className="container mx-auto p-6">
      {onBack && (
        <button
          onClick={onBack}
          className="mb-4 text-blue-600 hover:text-blue-800"
        >
          ← Back to list
        </button>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
        <div className="p-6 border-b dark:border-gray-700 flex justify-between items-center">
          <h1 className="text-2xl font-bold">{isEditing ? 'Edit Lesson' : lesson.title}</h1>
          {!isEditing && (
            <button
              onClick={handleEdit}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Edit
            </button>
          )}
        </div>

        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
        )}

        {isEditing ? (
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Title ({editedTitle.length}/500)
              </label>
              <input
                type="text"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
                maxLength={500}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Duration (minutes)</label>
                <input
                  type="number"
                  value={editedDuration}
                  onChange={(e) => setEditedDuration(parseInt(e.target.value) || MIN_DURATION)}
                  className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
                  min={MIN_DURATION}
                  max={MAX_DURATION}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Teaching Style</label>
                <select
                  value={editedTeachingStyle}
                  onChange={(e) => setEditedTeachingStyle(e.target.value)}
                  className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
                >
                  {TEACHING_STYLES.map((style) => (
                    <option key={style.value} value={style.value}>{style.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Learning Objective ({editedObjective.length}/500)
              </label>
              <textarea
                value={editedObjective}
                onChange={(e) => setEditedObjective(e.target.value)}
                className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
                rows={3}
                maxLength={500}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Markdown Content ({editedContent.length}/100000)
              </label>
              <textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                className="w-full p-4 border rounded font-mono text-sm dark:bg-gray-700 dark:border-gray-600 resize-y"
                rows={20}
                maxLength={100000}
              />
            </div>

            <div className="flex gap-4">
              <button
                onClick={handleSave}
                disabled={updateMutation.isPending || !isDirty}
                className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
              >
                {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                onClick={handleCancel}
                disabled={updateMutation.isPending}
                className="px-6 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded">
              <div>
                <span className="font-semibold">Grade:</span> {lesson.grade}
              </div>
              <div>
                <span className="font-semibold">Subject:</span> {lesson.subject}
              </div>
              <div>
                <span className="font-semibold">Duration:</span> {lesson.duration_minutes} minutes
              </div>
              <div>
                <span className="font-semibold">Teaching Style:</span> {lesson.teaching_style}
              </div>
              <div className="md:col-span-2">
                <span className="font-semibold">Topic:</span> {lesson.topic}
              </div>
              <div className="md:col-span-2">
                <span className="font-semibold">Learning Objective:</span> {lesson.learning_objective}
              </div>
              <div>
                <span className="font-semibold">Sources:</span> {lesson.sources_count}
              </div>
              <div>
                <span className="font-semibold">Images:</span> {lesson.images_count}
              </div>
            </div>

            <div className="prose dark:prose-invert max-w-none">
              <ReactMarkdown>{lesson.markdown_content}</ReactMarkdown>
            </div>

            <div className="mt-6 pt-4 border-t dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400">
              <p>Created: {formatDate(lesson.created_at)}</p>
              <p>Last updated: {formatDate(lesson.updated_at)}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
