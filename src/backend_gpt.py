import openai
openai.api_key = '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'

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

