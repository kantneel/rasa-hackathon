import { cn } from '@/lib/utils'
import Markdown from 'react-markdown'
import { Slide } from './Slides'
import Image from 'next/image'

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

export function Slide({ slide, index }: { slide: Slide, index: number }) {
  return <div className={cn("py-24 px-32 h-screen w-screen overflow-auto flex items-center")} style={{ background: 'rgb(246,248,245)' }}>
    <Markdown className={cn(`slide h-full w-full text-left prose prose-2xl overflow-auto`)}>{slide.markdown}</Markdown>
    {slide.image && <img className="object-center pr-20 rounded-lg w-1/2 ml-4" src={slide.image} alt='image' width={800} height={400} />}
  </div>

}

