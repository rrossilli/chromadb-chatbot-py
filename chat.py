from chromadb.config import Settings
from utils import save_file, open_file
from helpers import chatbot
from uuid import uuid4
from time import time
import chromadb
import openai

from consts import (
    CHROMADB_COLLECTION,
    EXAMPLE_PROFILE,
    PATH_CHAT_LOGS,
    PATH_CHROMADB,
    PATH_USER_PROFILE,
    PATH_USER_OPENAI_KEY,
    PATH_SYSTEM_DEFAULT,
    PATH_SYSTEM_UPDATE_USER_PROFILE,
    PATH_SYSTEM_SUBSTANTIATE_NEW_KB,
    PATH_SYSTEM_UPDATE_EXISTING_KB,
    PATH_SYSTEM_SPLIT_KB,
    PATH_API_LOGS,
    PATH_DB_LOGS,
    PATH_USER_PROFILE_BACKUP,
    SLUG_KB,
    SLUG_PROFILE,
    SLUG_WORDS,
    SLUG_UPD
)


def initialize_profile():
    profile_data = []
    for field, example in EXAMPLE_PROFILE.items():
        user_input = input(f"{field} (e.g., {example}): ")
        profile_data.append(f"- {field}: {user_input}")

    # Save the collected data to PATH_USER_PROFILE
    save_file(PATH_USER_PROFILE, '\n'.join(profile_data))
    # save a backup file in case of corruption
    save_file(PATH_USER_PROFILE_BACKUP, profile)


def initialize_openai_key():
    """
    Prompt the user to enter their OpenAI key.
    """
    openai_key = input("Enter your OpenAI API key: ")
    save_file(PATH_USER_OPENAI_KEY, openai_key)


if __name__ == '__main__':

    # Check if user_profile.txt exists, if not, initialize profile
    try:
        with open(PATH_USER_PROFILE, 'r', encoding='utf-8'):
            pass
    except FileNotFoundError:
        print("\n\nNo user profile found. Help me create one.")
        initialize_profile()

    # Check if key_openai.txt exists, if not, initialize OpenAI key
    try:
        with open(PATH_USER_OPENAI_KEY, 'r', encoding='utf-8'):
            pass
    except FileNotFoundError:
        print("\n\nNo OpenAI API key found.")
        initialize_openai_key()

    # instantiate ChromaDB
    chroma_client = chromadb.PersistentClient(path=PATH_CHROMADB)
    collection = chroma_client.get_or_create_collection(
        name=CHROMADB_COLLECTION)

    # instantiate chatbot
    openai.api_key = open_file(PATH_USER_OPENAI_KEY)
    conversation = list()
    conversation.append(
        {'role': 'system', 'content': open_file(PATH_SYSTEM_DEFAULT)})
    user_messages = list()
    all_messages = list()

    while True:
        # get user input
        text = input('\n\nUSER: ')
        user_messages.append(text)
        all_messages.append('USER: %s' % text)
        conversation.append({'role': 'user', 'content': text})
        save_file(PATH_CHAT_LOGS + '/chat_%s_user.txt' % time(), text)

        # update main scratchpad
        if len(all_messages) > 5:
            all_messages.pop(0)
        main_scratchpad = '\n\n'.join(all_messages).strip()

        # search KB, update default system
        current_profile = open_file(PATH_USER_PROFILE)
        kb = 'No KB articles yet'
        if collection.count() > 0:
            results = collection.query(
                query_texts=[main_scratchpad], n_results=1)
            kb = results['documents'][0][0]
            # print('\n\nDEBUG: Found results %s' % results)
        default_system = open_file(PATH_SYSTEM_DEFAULT).replace(
            SLUG_PROFILE, current_profile).replace(SLUG_KB, kb)
        # print('SYSTEM: %s' % default_system)
        conversation[0]['content'] = default_system

        # generate a response
        response = chatbot(conversation)
        save_file(PATH_CHAT_LOGS + '/chat_%s_chatbot.txt' % time(), response)
        conversation.append({'role': 'assistant', 'content': response})
        all_messages.append('CHATBOT: %s' % response)
        print('\n\nCHATBOT: %s' % response)

        # update user scratchpad
        if len(user_messages) > 3:
            user_messages.pop(0)
        user_scratchpad = '\n'.join(user_messages).strip()

        # update user profile
        print('\n\nUpdating user profile...')
        profile_length = len(current_profile.split(' '))
        profile_conversation = list()
        profile_conversation.append({'role': 'system', 'content': open_file(PATH_SYSTEM_UPDATE_USER_PROFILE).replace(
            SLUG_UPD, current_profile).replace(SLUG_WORDS, str(profile_length))})
        profile_conversation.append(
            {'role': 'user', 'content': user_scratchpad})
        profile = chatbot(profile_conversation)
        save_file(PATH_USER_PROFILE, profile)

        # update main scratchpad
        if len(all_messages) > 5:
            all_messages.pop(0)
        main_scratchpad = '\n\n'.join(all_messages).strip()

        # Update the knowledge base
        print('\n\nUpdating KB...')
        if collection.count() == 0:
            # yay first KB!
            kb_convo = list()
            kb_convo.append({'role': 'system', 'content': open_file(
                PATH_SYSTEM_SUBSTANTIATE_NEW_KB)})
            kb_convo.append({'role': 'user', 'content': main_scratchpad})
            article = chatbot(kb_convo)
            new_id = str(uuid4())
            collection.add(documents=[article], ids=[new_id])
            save_file(PATH_DB_LOGS + '/log_%s_add.txt' %
                      time(), 'Added document %s:\n%s' % (new_id, article))
        else:
            results = collection.query(
                query_texts=[main_scratchpad], n_results=1)
            kb = results['documents'][0][0]
            kb_id = results['ids'][0][0]

            # Expand current KB
            kb_convo = list()
            kb_convo.append({'role': 'system', 'content': open_file(
                PATH_SYSTEM_UPDATE_EXISTING_KB).replace(SLUG_KB, kb)})
            kb_convo.append({'role': 'user', 'content': main_scratchpad})
            article = chatbot(kb_convo)
            collection.update(ids=[kb_id], documents=[article])
            save_file(PATH_DB_LOGS + '/log_%s_update.txt' %
                      time(), 'Updated document %s:\n%s' % (kb_id, article))
            # TODO - save more info in DB logs, probably as YAML file (original article, new info, final article)

            # Split KB if too large
            kb_len = len(article.split(' '))
            if kb_len > 1000:
                print('\n\nSplitting KB...')
                kb_convo = list()
                kb_convo.append(
                    {'role': 'system', 'content': open_file(PATH_SYSTEM_SPLIT_KB)})
                kb_convo.append({'role': 'user', 'content': article})
                articles = chatbot(kb_convo).split('ARTICLE 2:')
                a1 = articles[0].replace('ARTICLE 1:', '').strip()
                a2 = articles[1].strip()
                collection.update(ids=[kb_id], documents=[a1])
                new_id = str(uuid4())
                collection.add(documents=[a2], ids=[new_id])
                save_file(PATH_DB_LOGS + '/log_%s_split.txt' % time(),
                          'Split document %s, added %s:\n%s\n\n%s' % (kb_id, new_id, a1, a2))
