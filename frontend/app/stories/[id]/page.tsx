import StoryDetailPage from '@/components/pages/StoryDetailPage'

export default async function StoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return <StoryDetailPage storyId={id} />
}
