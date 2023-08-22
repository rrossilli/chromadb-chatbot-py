from chromadb.config import Settings
from time import time, sleep
from utils import save_yaml
import openai

from consts import (
    OPENAI_MODEL,
    PATH_API_LOGS,
)
from consts import OPENAI_MODEL


def chatbot(messages, model=OPENAI_MODEL, temperature=0):
    max_retry = 7
    retry = 0

    while True:
        try:
            response = openai.ChatCompletion.create(
                model=model, messages=messages, temperature=temperature)
            text = response['choices'][0]['message']['content']

            # trim message object
            debug_object = [i['content'] for i in messages]
            debug_object.append(text)
            save_yaml(PATH_API_LOGS + '/convo_%s.yaml' % time(), debug_object)
            if response['usage']['total_tokens'] >= 7000:
                a = messages.pop(1)

            return text
        except Exception as oops:
            print(f'\n\nError communicating with OpenAI: "{oops}"')
            if 'maximum context length' in str(oops):
                a = messages.pop(1)
                print('\n\n DEBUG: Trimming oldest message')
                continue
            retry += 1
            if retry >= max_retry:
                print(f"\n\nExiting due to excessive errors in API: {oops}")
                exit(1)
            print(f'\n\nRetrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)
