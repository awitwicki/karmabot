import cachetools.func
from googlesearch import search
from googletrans import Translator


@cachetools.func.ttl_cache(maxsize=100, ttl=60 * 60)
def translate_text(msg_text, dest = 'en', silent_mode = False) -> str:
    try:
        translator = Translator()
        result = translator.translate(msg_text, dest=dest)

        return result.text
    except:
        return None


@cachetools.func.ttl_cache(maxsize=100, ttl=60 * 60)
def google_search(text: str) -> str:
    try:
        search_question = f'cite: stackoverflow.com {text}'

        result = search(search_question, num_results=1)
        result = result[0].replace('https://','').replace('http://','')
        return result
    except Exception as e:
        return 'Даже гугл не знает 🤷‍♂️'


@cachetools.func.ttl_cache(maxsize=100, ttl=60 * 60)
def stackoverflow_search(text: str) -> str:
    search_question = translate_text(text)
    if not search_question:
        return 'Произошла ошибка :('

    search_question = f'cite: stackoverflow.com {search_question}'

    result = search(search_question, num_results=1)
    result = result[0].replace('https://','').replace('http://','')
    return result
