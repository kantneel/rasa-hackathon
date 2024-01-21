import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["OPENAI_KEY"]
)

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
        # tool_choice={
        #     "type": "function", 
        #     "function": {
        #         "name": None
        #     }
        # },
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "choose_slide",
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
                    "description": """
This is a tool that can choose a slide.
""",
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_slide",
                    "description": """
Choose this tool to add a slide.
""",
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_markdown_slide",
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
                                "title": "Should provide an image to fullfill the request",
                                "description": "Choose True if you want to provide an image to fullfill the request"
                            },
                        }
                    },
                    "description": """
This is a tool that can update a markdown slide.
                    """
                }
            },
        ]
    )

    return completion.choices[0].message.tool_calls[0]




def process_whisper_prompt(whisper_prompt):
    pusher_command = get_pusher_command(whisper_prompt)

    # push to pusher


def get_pusher_command(whisper_prompt):
    # function = choose_tool("Make a slide with the title 'Hello World' and the content 'This is a slide.'").function
    function = choose_tool(whisper_prompt).function

    print(function)

    match function.name:
        case 'make_markdown_slide':
            print("Making a markdown slide", function.arguments)
            return make_slide(whisper_prompt, False)
        case 'choose_slide':
            print("Choosing a slide", function.arguments)
            return {'slide_index': function.arguments['index']}
        case 'add_slide':
            return add_slide()
        case _:
            print("Unknown function", function.arguments)


def add_slide():
    return {'add_slide': True}

def make_slide(whisper_prompt, provide_image):
    if provide_image:
        return {'image': get_image(whisper_prompt), 'slide_index': 0}

    return {'markdown': generate_markdown(whisper_prompt), 'slide_index': 0}
    

def generate_markdown(whisper_prompt):
    context = retrieve_context(whisper_prompt)

    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": """
                You are a markdown slides generation pro.
             """},
            {"role": "user", "content": f"""
               Generate a markdown slide.

            This is the context:
             ---
             {context}
             ---

            This is the prompt:
            ---
            {whisper_prompt}
            --- 

            The markdown you generate always starts with a title. This is an example.

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
             
             """}
        ],
        temperature=0,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "make_markdown_slide",
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
                    "description": """
This is a tool that can make a markdown slide.
                    """
                }
            },
        ]
    )

    return completion.choices[0].message.tool_calls[0].function.arguments['markdown']

def get_image(image_prompt):
    return 'https://images.dog.ceo/breeds/terrier-norwich/n02094258_100.jpg'

def retrieve_context(query):
    return 'lorem ipsum'


def main():
    res = process_whisper_prompt("Add a title to the slide 'Hello World'")
    print(res)

main()
