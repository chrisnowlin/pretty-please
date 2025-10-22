import React, { useState } from 'react';
import { GRADE_LEVELS, SUBJECTS, TEACHING_STYLES, DEFAULT_DURATION, MIN_DURATION, MAX_DURATION } from '../../constants/educationOptions';

interface LessonPlanFormProps {
  onGenerate: (data: LessonPlanRequest) => void;
  isLoading: boolean;
}

export interface LessonPlanRequest {
  topic: string;
  learning_objective: string;
  grade_level: string;
  subject: string;
  duration_minutes: number;
  teaching_style: string;
}

export const LessonPlanForm: React.FC<LessonPlanFormProps> = ({ onGenerate, isLoading }) => {
  const [formData, setFormData] = useState<LessonPlanRequest>({
    topic: '',
    learning_objective: '',
    grade_level: '3',
    subject: 'Mathematics',
    duration_minutes: DEFAULT_DURATION,
    teaching_style: 'balanced',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onGenerate(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md">
      <div>
        <label className="block text-sm font-medium mb-1">Topic</label>
        <input
          type="text"
          value={formData.topic}
          onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
          className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
          required
          maxLength={200}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Learning Objective</label>
        <textarea
          value={formData.learning_objective}
          onChange={(e) => setFormData({ ...formData, learning_objective: e.target.value })}
          className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
          rows={3}
          required
          maxLength={500}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Grade Level</label>
          <select
            value={formData.grade_level}
            onChange={(e) => setFormData({ ...formData, grade_level: e.target.value })}
            className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
          >
            {GRADE_LEVELS.map((grade) => (
              <option key={grade.value} value={grade.value}>{grade.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Subject</label>
          <select
            value={formData.subject}
            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
            className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
          >
            {SUBJECTS.map((subject) => (
              <option key={subject.value} value={subject.value}>{subject.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">
          Duration: {formData.duration_minutes} minutes (default: {DEFAULT_DURATION})
        </label>
        <input
          type="range"
          min={MIN_DURATION}
          max={MAX_DURATION}
          value={formData.duration_minutes}
          onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })}
          className="w-full"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Teaching Style</label>
        <select
          value={formData.teaching_style}
          onChange={(e) => setFormData({ ...formData, teaching_style: e.target.value })}
          className="w-full p-2 border rounded dark:bg-gray-700 dark:border-gray-600"
        >
          {TEACHING_STYLES.map((style) => (
            <option key={style.value} value={style.value}>{style.label}</option>
          ))}
        </select>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
      >
        {isLoading ? 'Generating Lesson...' : 'Generate Lesson Plan'}
      </button>
    </form>
  );
};
