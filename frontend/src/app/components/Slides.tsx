'use client'
import * as React from 'react'

import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
  type CarouselApi,
} from '@/components/ui/carousel'
import { Slide } from './Slide'
import Pusher from 'pusher-js'

export type Slide = {
  markdown: string
  image?: string
}

const markdownSlides: Slide[] = [
  {
    markdown: `# Rasa
  ![rasa](/rasa.png)
  ### The Voice Presentation Tool
  ---
  *At [UI AGI House Hackathon Jan 20, 2024](https://partiful.com/e/1antxX3cgLArJFGRNKg4)*
  `,
    // image: 'https://github.com/zrannie/rasa/blob/main/teamphoto.png?raw=true'
  },
  // {
  //   markdown: `# Problem Statement\n\nIn the realm of presentations, speakers often face the challenge of managing their slides while maintaining engagement with their audience. Traditional presentation methods require physical interaction with the computer, disrupting the flow and visual continuity of the presentation. Rasa addresses these issues by offering a hands-free, voice-controlled presentation experience.`
  // }
  // {
  //   markdown: `# Empty Slide
  // `,
  // },
  // {
  //   markdown: `# Rasa 2
  // ![rasa](/rasa.png)
  // ## The Voice Presentation Tool
  // ---
  // *At UI AGI House Hackathon Jan 20, 2024*
  // `,
  // }
]

const ADD_SLIDE = 'add_slide'
const CHOOSE_SLIDE = 'choose_slide'
const UPDATE_SLIDE = 'update_slide'
const SET_IMAGE = 'set_image'

type AddSlidePayload = {
}

type ChooseSlidePayload = {
  index: number
}

type UpdateSlidePayload = {
  markdown: string
}

type SetImagePayload = {
  image_url: string
}

export function Slides() {
  const [api, setApi] = React.useState<CarouselApi>()
  const [current, setCurrent] = React.useState(0)
  const [count, setCount] = React.useState(1)
  const [slides, setSlides] = React.useState(markdownSlides)

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

  React.useEffect(() => {
    if (!api) {
      return
    }


    const pusher = new Pusher('1e429e2648755b45004d', {
      cluster: 'us3'
    })

    const channel = pusher.subscribe('rasa');

    channel.bind(ADD_SLIDE, (data: AddSlidePayload) => {
      console.log('add slide', data)
      // insert slide after current slide
      setSlides([
        ...slides.slice(0, current),
        { markdown: '# New slide' },
        ...slides.slice(current)
      ])
      // api.scrollTo(count)
      setCount(count + 1)
    })

    channel.bind(UPDATE_SLIDE, (data: UpdateSlidePayload) => {
      console.log('make slide', data)
      // update current slide based on current
      setSlides([
        ...slides.slice(0, current - 1),
        { markdown: data.markdown },
        ...slides.slice(current)
      ])
      api.reInit()
    })

    channel.bind(CHOOSE_SLIDE, (data: ChooseSlidePayload) => {
      console.log(`choose slide ${data.index}`)
      api.scrollTo(data.index)
    })

    channel.bind(SET_IMAGE, (data: SetImagePayload) => {
      // update current slide based on current
      setSlides([
        ...slides.slice(0, current - 1),
        { markdown: slides[current - 1].markdown, image: data.image_url },
        ...slides.slice(current)
      ])
    })

    return () => {
      channel.unbind(ADD_SLIDE)
      channel.unbind(UPDATE_SLIDE)
      channel.unbind(CHOOSE_SLIDE)
      channel.unbind(SET_IMAGE)
      pusher.unsubscribe('rasa')
    }
  }, [current, slides, api, count])

  return (
    <div>
      <Carousel
        setApi={setApi}
        className="w-screen h-screen overflow-hidden"
        key={`${count}-slides`}
      >
        <CarouselContent>
          {slides.map((slide, index) => (
            <CarouselItem key={index} className="basis-auto">
              <Slide slide={slide} index={index} />
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
