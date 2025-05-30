import aiohttp
import asyncio

PROFANITY_LIST_URL = "https://raw.githubusercontent.com/dsojevic/profanity-list/refs/heads/main/en.txt"
PROFANITY_WORDS = set()
PROFANITY_LOADED = False

async def fetch_profanity_list():
    global PROFANITY_WORDS, PROFANITY_LOADED
    if PROFANITY_LOADED:
        return PROFANITY_WORDS
    async with aiohttp.ClientSession() as session:
        async with session.get(PROFANITY_LIST_URL) as resp:
            text = await resp.text()
            PROFANITY_WORDS = set(word.strip().lower() for word in text.splitlines() if word.strip())
            PROFANITY_LOADED = True
            return PROFANITY_WORDS

async def censor_profanity(text):
    words = text.split()
    profanities = await fetch_profanity_list()
    censored = []
    for word in words:
        lower = word.lower()
        if lower in profanities:
            clean = word[0] + "*"*(len(word)-2) + word[-1] if len(word) > 2 else "*"*len(word)
            censored.append(clean)
        else:
            censored.append(word)
    return " ".join(censored)