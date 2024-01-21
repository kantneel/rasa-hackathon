import glob
import os
import re
from PIL import Image
from io import BytesIO
from openai import OpenAI
from llama_index.node_parser import MarkdownNodeParser
from llama_index import ServiceContext, VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings import OpenAIEmbedding
from llama_index import download_loader
from llama_index.indices.multi_modal.base import MultiModalVectorStoreIndex
from pathlib import Path
import requests
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
        self.text_retriever = index.as_retriever(similarity_top_k=3)
    
    def retrieve_text(self, text):
        return "\n\n".join([
            self.text_retriever.retrieve(text)[k].get_content()
            for k in range(3)
        ])


class HybridIndex2():
    def __init__(self, markdown_file, savedir):
        self.setup_text_retriever(markdown_file)
        self.setup_img_retriever(markdown_file, savedir)
        
    def setup_img_retriever(self, markdown_file, savedir):
        
        image_dir = os.path.join(savedir, 'images')
        with open(markdown_file, 'r') as file:
            text = file.read()
            images = re.findall(r"<img src=\"([^\s-]*)\"", text)
            print("images", images)
            idx = 0
            for image in images:
                response = requests.get(image)
                img = Image.open(BytesIO(response.content))
                os.makedirs(image_dir, exist_ok=True)
                img.save(os.path.join(image_dir, f"{idx}.png"))
                idx += 1

            glob.glob(os.path.join(savedir, '*.png'))
            documents = SimpleDirectoryReader(image_dir).load_data()
            
            index = MultiModalVectorStoreIndex.from_documents(documents)
            self.image_retriever = index.as_retriever()

    def setup_text_retriever(self, markdown_file):
        MarkdownReader = download_loader("MarkdownReader")
        loader = MarkdownReader()
        documents = loader.load_data(file=Path(markdown_file))
        embed_model = OpenAIEmbedding()
        ServiceContext.from_defaults(embed_model=embed_model)
        text_index = VectorStoreIndex.from_documents(documents)
        self.text_retriever = text_index.as_retriever(similarity_top_k=3)
        
        
    def retrieve_text(self, text, topk=3):
        return "\n\n".join([
            self.text_retriever.retrieve(text)[k].get_content()
            for k in range(3)
        ])

    def retrieve_img(self, text, topk=1):
        return self.image_retriever.retrieve(text)[0].to_dict()['node']['metadata']['file_path']


TEXT_INDEX = HybridIndex2(
    markdown_file="/Users/neel/Desktop/rasa-hackathon/data/reference_text.md", 
    savedir="/Users/neel/Desktop/rasa-hackathon/data"
)

        
SYSTEM_PROMPT = """\
You are an intelligent digital assistant working with a user who is preparing a presentation. They are iteratively using you to make calls to a retriever information to use in their presentation. You also take the retrieved information and synthesize that information with their text to make calls the frontend API to navigate between and create slides for the user. Your task is to interpret the user's intent and use the given tools as needed to accomplish the task."""


USER_PROMPT = """\
The user said "{user_text}"

Given the above user text, call the right tool for this task.
If you are using update_markdown_slide without providing an image, DO NOT attempt to include an image URL - remove it if needed.

When in doubt, choose the update_markdown_slide tool.   
"""

def choose_tool(whisper_prompt):
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT.format(user_text=whisper_prompt)}
        ],
        temperature=0,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "add_slide",
                    "description": "Choose this tool to add a new blank slide only if asked to.",
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
    return TEXT_INDEX.retrieve_img(image_prompt)


def make_slide(whisper_prompt, provide_image):
    if provide_image:
        return {'image': get_image(whisper_prompt), 'slide_index': 0}
    return {'markdown': generate_markdown(whisper_prompt), 'slide_index': 0}
    

GENERATE_MD_PROMPT = """\
Your task is to generate a markdown slide. The markdown you generate always starts with a title. This is an example.
# Slide 1
  This is some text
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
  

FEEDBACK_PROMPT = """
Here is what you have done so far:
    {response}

Tell me what you have done so far and ask what should be done next.
"""
def generate_feedback(response):
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": """You are a AI assistant responder."""},
            {"role": "user", "content": FEEDBACK_PROMPT.format(response=response)}
        ],
        temperature=0,
    )
    response = completion.choices[0].message.content
    return response

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
