import os
from dataclasses import dataclass

import openai

openai.api_key = os.environ["OPENAI_KEY"]

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

The user said: "{user_text}"\
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
    
    def __str__(self):
        return f"On slide {self.slide_num}, User text: {self.user_text}\nIndex query: {self.index_query}"


class RasaGPT:
    def __init__(self):
        self.query_items = []
    
    def get_index_query(self, slide_num, user_text, background_info):
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
    
    def coalesce_background_info(self):
        """
        Coalesce the background info into a single string
        """
        return " ".join([item.user_text for item in self.background_info])