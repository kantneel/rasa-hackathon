import os
import openai

openai.api_key = os.environ["OPENAI_KEY"]

def query_gpt4(system_prompt, prompt):
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt} 
        ]
    )
    response = response["choices"][0]["message"]["content"] # type: ignore
    return response

