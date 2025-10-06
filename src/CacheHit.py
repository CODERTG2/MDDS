from sentence_transformers import SentenceTransformer

from src.CacheDB import CacheDB
from mongoengine import connect
import os
from dotenv import load_dotenv


def CacheHit(query: str, model: SentenceTransformer):
    load_dotenv()
    connect(host=os.getenv("MONGO_URI"))

    query_embedding = model.encode(query)

    for cached_query in CacheDB.objects(tag="deep"):
        cached_embedding = model.encode(cached_query.query)
        similarity = cosine_similarity(query_embedding, cached_embedding)
        if similarity > 0.8:
            return cached_query.answer
        
    for cached_query in CacheDB.objects(tag="normal"):
        cached_embedding = model.encode(cached_query.query)
        similarity = cosine_similarity(query_embedding, cached_embedding)
        if similarity > 0.8:
            return cached_query.answer

    return False

def cosine_similarity(vec1, vec2):
    from numpy import dot
    from numpy.linalg import norm
    return dot(vec1, vec2) / (norm(vec1) * norm(vec2))