import os
from openai import OpenAI
from llama_index.node_parser import MarkdownNodeParser
from llama_index import ServiceContext, VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings import OpenAIEmbedding
from pathlib import Path
from llama_index import download_loader
parser = MarkdownNodeParser(include_metadata=True, include_prev_next_rel=True)

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)


class HybridIndex():
    def __init__(self, markdown_file):
        
        MarkdownReader = download_loader("MarkdownReader")
        loader = MarkdownReader()
        documents = loader.load_data(file=Path(markdown_file))
        embed_model = OpenAIEmbedding()
        ServiceContext.from_defaults(embed_model=embed_model)
        index = VectorStoreIndex.from_documents(documents)
        self.text_retriever = index.as_retriever()
    
    def retrieve_text(self, text):
        return self.text_retriever.retrieve(text)[0].get_content()
    

TEXT_INDEX = HybridIndex("/Users/neel/Desktop/rasa-hackathon/data/reference_text.md")

        
SYSTEM_PROMPT = """\
You are an intelligent digital assistant working with a user who is preparing a presentation. They are iteratively using you to make calls to a retriever information to use in their presentation. You also take the retrieved information and synthesize that information with their text to make calls the frontend API to navigate between and create slides for the user. Your task is to interpret the user's intent and use the given tools as needed to accomplish the task."""


def choose_tool(whisper_prompt):
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": whisper_prompt}
        ],
        temperature=0,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "add_slide",
                    "description": "Choose this tool to add a slide.",
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "choose_slide",
                    "description": "This is a tool that can choose a slide.",
                    "parameters": {
                        "type": "object",
                        "title": "SlideInputs",
                        "required": ["index"],
                        "properties": {
                            "index": {
                                "type": "integer",
                                "title": "index",
                                "description": "Slide to choose"
                            }
                        }
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_markdown_slide",
                    "description": "This is a tool that can update a markdown slide.",
                    "parameters": {
                        "type": "object",
                        "title": "MarkdownSlideInput",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "title": "Query",
                                "description": "The query to generate the slide from"
                            },
                            "provide_image": {
                                "type": "boolean",
                                "title": "Should provide an image to fulfill the request",
                                "description": "Choose True if you want to provide an image to fullfill the request"
                            },
                        }
                    },
                }
            },
        ]
    )

    return completion.choices[0].message.tool_calls[0]



def get_image(image_prompt):
    return 'https://images.dog.ceo/breeds/terrier-norwich/n02094258_100.jpg'


def make_slide(whisper_prompt, provide_image):
    if provide_image:
        return {'image': get_image(whisper_prompt), 'slide_index': 0}
    return {'markdown': generate_markdown(whisper_prompt), 'slide_index': 0}
    

GENERATE_MD_PROMPT = """\
Your task is to generate a markdown slide. The markdown you generate always starts with a title. This is an example.
# Slide 1
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

Now do this by synthesizing the following context with the prompt:

This is the context:
---
{context}
---

This is the prompt:
---
{whisper_prompt}
---\
"""
  

def generate_markdown(whisper_prompt):
    context = TEXT_INDEX.retrieve_text(whisper_prompt)
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": """You are a markdown slides generation pro."""},
            {"role": "user", "content": GENERATE_MD_PROMPT.format(context=context, whisper_prompt=whisper_prompt)}
        ],
        temperature=0,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "make_markdown_slide",
                    "description": "This is a tool that can make a markdown slide.",
                    "parameters": {
                        "type": "object",
                        "title": "MarkdownSlideInput",
                        "required": ["markdown"],
                        "properties": {
                            "markdown": {
                                "type": "string",
                                "title": "Markdown",
                                "description": "The markdown for the slide"
                            }
                        }
                    },
                }
            },
        ]
    )
    return eval(completion.choices[0].message.tool_calls[0].function.arguments)['markdown']


def main():
    #res = process_whisper_prompt("Add a title to the slide 'Hello World'")
    res = generate_markdown("Let's get the founding story")
    print(res)
