import json
import os
from dataclasses import dataclass
from rasa_tools import choose_tool, generate_markdown, get_image
from pusher_demo import add_slide, choose_slide, update_slide, set_image
import openai

def single_query_gpt4(system_prompt, prompt):
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt} 
        ]
    )
    response = response["choices"][0]["message"]["content"] # type: ignore
    return response


def chat_query_gpt4(prompt, messages):
    chat_messages = messages + [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=chat_messages
    )
    response = response["choices"][0]["message"]["content"] # type: ignore
    chat_messages.append({"role": "assistant", "content": response})
    return response, chat_messages
    


SYSTEM_PROMPT = """You are an intelligent assistant that helps the user with their data retrieval-related needs."""


INTENT_QUERY_PROMPT = """\
You are assisting a user who is preparing a presentation. They are iteratively using a voice assistant to make calls to a search engine to retrieve information to use in their presentation. Your task is to interpret the user's intent and create a query to retrieve the relevant information from the index. The query will be given to a learned vector retrieval model so optimize the query accordingly.

The output must be in JSON format and must contain the following fields:
- "query": The query text
- "endpoint": the endpoint to send the query to, options are ONLY "image" and "text"

An example well-formed query is:
```json
{
    "query": "information about the founding of Apple",
    "endpoint": "text"
}

another example well-formed query is:
```json
{
    "query": "a golden-retriever sitting on a lawn",
    "endpoint": "image"
}

Now, create a JSON query output for the following user utterance, inferring the endpoint type: "{user_text}"\
"""


GET_MARKDOWN_PROMPT = """\


An example would be:

```markdown
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
```

"""


INTENT_WITH_BACKGROUND_QUERY_PROMPT = """\
You are assisting a user who is preparing a presentation. They are iteratively using a voice assistant to make calls to a search engine to retrieve information to use in their presentation. Your task is to interpret the user's intent and create a query to retrieve the relevant information from the index. The query will be given to a learned vector retrieval model so optimize the query accordingly.

The user said: "{user_text}"

For context, the user has so far said: "{background_info}"\
"""


COALESCE_BACKGROUND_INFO_PROMPT = """\
You are assisting a user who is preparing a presentation. They are iteratively using a voice assistant to make calls to a search engine to retrieve information to use in their presentation. Your task is to interpret the user's intent and create a query to retrieve the relevant information from the index. The query will be given to a learned vector retrieval model so optimize the query accordingly.
    
So far, the user said the following things and the voice assistant has generated the respective queries:
{query_items}

Please coalesce the background information into a single string and generate a query to retrieve the relevant information from the index. The query will be given to a learned vector retrieval model so optimize the query accordingly.
"""


@dataclass
class QueryItem:
    """
    An item in the query
    """
    slide_num: int
    user_text: str
    index_query: str
    endpoint: str
    
    def __str__(self):
        return f"On slide {self.slide_num}, User text: {self.user_text}\nIndex query: {self.index_query}"


class RasaGPT:
    def __init__(self):
        self.history = []
        self.current_slide = -1
        self.total_slides = 0

    def process(self, query:str):
        function = choose_tool(query).function
        print(function)
        response = self.process_function_call(function, query)
        return response

    def process_function_call(self, function, query):
    # function = choose_tool("Make a slide with the title 'Hello World' and the content 'This is a slide.'").function
   
        match function.name:
            case 'add_slide':
                self.total_slides += 1
                add_slide()
                return {"response": "Added new slide"}
            case 'update_markdown_slide':
                print("Making a markdown slide", function.arguments)
                args = eval(function.arguments)
                if args["provide_image"]:
                    image_url = get_image(query)
                    set_image(image_url)
                    return {"response": image_url}
                else:
                    response = generate_markdown(query)
                    update_slide(response)
                return {"response": response}
            case 'choose_slide':
                print("Choosing a slide", function.arguments)
                self.current_slide = int(eval(function.arguments)["index"])
                choose_slide(self.current_slide)
                return {'response': f"Focus moved to slide: {self.current_slide}"}
            case _:
                print("Unknown function", function.arguments)
                return {"responsde": "Error Unknown Function"}
        
    def get_current_slide(self):
        # Ideally this should come from pusher
        return self.current_slide
    
    def get_index_query(self, slide_num, user_text, background_info=None):
        """
        Transform the audio transcription into a an intent query which will be sent to the index for retreival
        """
        if background_info is None:
            prompt = INTENT_QUERY_PROMPT.format(
                user_text=user_text
            )
        else:
            prompt = INTENT_WITH_BACKGROUND_QUERY_PROMPT.format(
                user_text=user_text,
                background_info=background_info
            )
            
        index_query = single_query_gpt4(SYSTEM_PROMPT, prompt)
        
        
        query_item = QueryItem(
            slide_num=slide_num,
            user_text=user_text, 
            index_query=index_query
        )
        self.query_items.append(query_item)
        return index_query