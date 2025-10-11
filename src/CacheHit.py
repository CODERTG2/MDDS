from sentence_transformers import SentenceTransformer
from src.CacheDB import CacheDB
from mongoengine import connect
import os
from dotenv import load_dotenv
from src.util import cosine_similarity
import concurrent.futures

def check_cache_deep(query, model, query_embedding):
    for cached_query in CacheDB.objects(tag="deep"):
        cached_embedding = model.encode(cached_query.query)
        similarity = cosine_similarity(query_embedding, cached_embedding)
        if similarity > 0.8:
            return cached_query.answer

def check_cache_normal(query, model, query_embedding):
    for cached_query in CacheDB.objects(tag="normal"):
        cached_embedding = model.encode(cached_query.query)
        similarity = cosine_similarity(query_embedding, cached_embedding)
        if similarity > 0.8:
            return cached_query.answer

def CacheHit(query: str, model: SentenceTransformer):
    load_dotenv()
    connect(host=os.getenv("MONGO_URI"))

    query_embedding = model.encode(query)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        deep_future = executor.submit(check_cache_deep, query, model, query_embedding)
        normal_future = executor.submit(check_cache_normal, query, model, query_embedding)

        deep_result = deep_future.result()
        if deep_result:
            return deep_result

        normal_result = normal_future.result()
        if normal_result:
            return normal_result

    return False