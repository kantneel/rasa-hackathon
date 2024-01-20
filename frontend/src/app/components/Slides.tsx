'use client'
import * as React from 'react'

import { Card, CardContent } from '@/components/ui/card'
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
  type CarouselApi,
} from '@/components/ui/carousel'
import { cn } from '@/lib/utils'
import { Slide } from './Slide'


const markdownSlides = [
  `# Slide 1
  This is some text
  This is an image:
  ![image](https://images.unsplash.com/photo-1682685797277-f2bf89b24017?q=80&w=4140&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDF8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)
  ## This is a subheading
  - This is a list
  - This is a list
  - This is a list
  ### This is a subsubheading
  1. This is an ordered list
  2. This is an ordered list  
  `,
  `# Slide 2
  This is some text
  `,
  `# Slide 3
  This is some text
  `,
  `# Slide 4
  This is some text
  `,
]

export function Slides() {
  const [api, setApi] = React.useState<CarouselApi>()
  const [current, setCurrent] = React.useState(0)
  const [count, setCount] = React.useState(0)

  React.useEffect(() => {
    if (!api) {
      return
    }

    setCount(api.scrollSnapList().length)
    setCurrent(api.selectedScrollSnap() + 1)

    api.on('select', () => {
      setCurrent(api.selectedScrollSnap() + 1)
    })
  }, [api])


  return (
    <div>
      <Carousel
        setApi={setApi}
        className="w-screen h-screen overflow-hidden"
      >
        <CarouselContent>
          {markdownSlides.map((markdown, index) => (
            <CarouselItem key={index} className="basis-auto">
              <Slide markdown={markdown} index={index} />
            </CarouselItem>
          ))}
        </CarouselContent>
        <CarouselPrevious className='left-4' />
        <CarouselNext className='right-4' />
      </Carousel>
      <div className="py-2 text-center text-sm text-muted-foreground absolute bottom-4 mx-auto w-full text-black">
        Slide {current} of {count}
      </div>
    </div>
  )
}
