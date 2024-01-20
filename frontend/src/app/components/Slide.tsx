import { cn } from '@/lib/utils'
import Markdown from 'react-markdown'

const colors = [
  'bg-red-50',
  'bg-blue-50',
  'bg-green-50',
  'bg-yellow-50',
  'bg-pink-50',
  'bg-purple-50',
  'bg-indigo-50',
  'bg-gray-50',
]

export function Slide({ markdown, index }: { markdown: string, index: number }) {
  return <Markdown className={cn(`slide h-screen w-screen text-left p-24 prose overflow-auto`, colors[index])}>{markdown}</Markdown>
}