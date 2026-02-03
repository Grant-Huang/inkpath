import StoryDetailPage from '../../components/pages/StoryDetailPage'

export default function StoryPage({ params }: { params: { id: string } }) {
  return <StoryDetailPage storyId={params.id} />
}
