'use client';

import { useState } from 'react';
import TopNav from './layout/TopNav';
import StoriesPage from './pages/StoriesPage';
import StoryDetailPage from './pages/StoryDetailPage';

export default function App() {
  const [view, setView] = useState<'stories' | 'reading'>('stories');
  const [selectedStoryId, setSelectedStoryId] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-[#faf8f5]">
      <TopNav />
      {view === 'stories' && <StoriesPage />}
      {view === 'reading' && selectedStoryId && (
        <StoryDetailPage storyId={selectedStoryId} />
      )}
    </div>
  );
}
