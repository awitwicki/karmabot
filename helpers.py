import cachetools.func
from googlesearch import search

@cachetools.func.ttl_cache(maxsize=100, ttl=60 * 60)
def google_search(text: str) -> str:
    try:
        search_question = f'cite: stackoverflow.com {text}'

        result = search(search_question, num_results=1)
        result = result[0].replace('https://','').replace('http://','')
        return result
    except Exception as e:
        return 'Даже гугл не знает 🤷‍♂️'
