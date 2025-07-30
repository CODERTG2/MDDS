from UserQuery import UserQuery
from sentence_transformers import SentenceTransformer
from CacheHit import CacheHit
import faiss
from ContextRetrieval import ContextRetrieval
from Ranking import ranking
from openai import AzureOpenAI
from dotenv import load_dotenv
import json
import networkx as nx
from CacheDB import CacheDB
from DeepSearch import DeepSearch
from mongoengine import connect
import streamlit as st
from ScholarLink import ScholarLink

model = SentenceTransformer('pritamdeka/S-BioBert-snli-multinli-stsb', device='cpu')

vector_db = faiss.read_index("chunks(1).index")

load_dotenv()

endpoint = "https://aoai-camp.openai.azure.com/"
model_name = "gpt-4o-mini"
deployment = "abbott_researcher"
api_version = "2024-12-01-preview"

client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=st.secrets["AZURE_OPEN_AI_KEY"]
)

with open("chunks_with_entities(1).json", "r") as f:
    dictionary = json.load(f)

G = nx.read_gexf("knowledge_graph(3).gexf")

connect(host=st.secrets["MONGO_URI"])

def normal_search(input_query: str, temp=0.5):
    if CacheHit(input_query, model) is not False:
        return CacheHit(input_query, model)

    user_query = UserQuery(input_query, client, deployment)
    subqueries = user_query.multi_query()
    full_context = []
    disclaimers = []
    for subquery in subqueries:
        context, disclaimer = ContextRetrieval(model, G, vector_db, dictionary, subquery).retrieve()
        if disclaimer != "":
            disclaimers.append(disclaimer)
        for con in context:
            full_context.append(con)

    if "" in disclaimers:
        disclaimer = "No disclaimer"
    else:
        disclaimer = disclaimers[0]
    
    rankings = ranking(full_context, k=10)

    formatted_context = ""
    for i, chunk in enumerate(rankings, 1):
        metadata = chunk["metadata"]
        content = chunk["chunk_text"]
        
        metadata_str = ""
        for key, value in metadata.items():
            metadata_str += f"{key}: {value}, "
        metadata_str = metadata_str.rstrip(", ")
        
        formatted_context += f"[{i}] Metadata: {metadata_str}\nContent: {content}\n\n"

    prompt = f"""
You are a helpful AI assistant. Use the provided context to answer the user's question accurately and comprehensively.

Context:
{formatted_context}

Question: {input_query}

Disclaimer: {disclaimer}

Instructions:
- Base your answer primarily on the provided context
- Prioritize the most relevant and recent information. The context is sorted by relevance where the most relevant information appears first.
- When using information from the context, cite the source based on the metadata provided like author, year, title, etc. In the text you can use author and year. But then at the end of the answer, provide a list of sources with full metadata after saying 'Sources'. Put the disclaimer before the sources.
- If the context doesn't contain enough information, state this clearly
- Provide a clear, well-structured answer
- If there is a disclaimer, mention it in your answer.

Answer:"""
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are an expert in literature review for medical diagnostics devices."},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    
    answer = response.choices[0].message.content.strip()

    links = ScholarLink(answer).extract_scholar_links()
    print(links)
    counter = 1
    for link in links:
        answer += f"\n\n [{counter}] {link}"
        counter += 1
    print(answer)

    CacheDB(
        query=input_query,
        answer=answer,
        tag="normal"
    ).save()

    return answer
    
# result = normal_search("What is the best sugar monitoring device?")
# print(result)

def deep_search(input_query: str, temp: float):
    user_query = UserQuery(input_query, client, deployment)
    subqueries = user_query.multi_query()
    full_context = []

    deep_searcher = DeepSearch(input_query, model, k_articles=5, k_chunks=7)
    chunks = deep_searcher.get_context()

    for subquery in subqueries:
        context, disclaimer = ContextRetrieval(model, G, vector_db, dictionary, subquery, k=30).retrieve()
        for con in context:
            full_context.append(con)

    rankings = ranking(full_context, k=3)

    final_context = chunks + rankings

    formatted_context = ""
    for i, chunk in enumerate(final_context, 1):
        metadata = chunk["metadata"]
        content = chunk["chunk_text"]
        
        metadata_str = ""
        for key, value in metadata.items():
            metadata_str += f"{key}: {value}, "
        metadata_str = metadata_str.rstrip(", ")
        
        formatted_context += f"[{i}] Metadata: {metadata_str}\nContent: {content}\n\n"

    prompt = f"""
You are a helpful AI assistant. Use the provided context to answer the user's question accurately and comprehensively.

Context:
{formatted_context}

Question: {input_query}

Instructions:
- Base your answer primarily on the provided context
- Prioritize the most relevant and recent information. The context is sorted by relevance where the most relevant information appears first.
- When using information from the context, cite the source based on the metadata provided like author, year, title, etc. In the text you can use author and year. But then at the end of the answer, provide a list of sources with full metadata after saying 'Sources'. Put the disclaimer before the sources.
- Provide a clear, well-structured answer

Answer:"""
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are an expert in literature review for medical diagnostics devices."},
            {"role": "user", "content": prompt}
        ],
        temperature= temp
    )
    
    answer = response.choices[0].message.content.strip()

    links = ScholarLink(answer).extract_scholar_links()
    counter = 1
    for link in links:
        answer += f"\n\n [{counter}] {link}"
        counter += 1
    
    CacheDB(
        query=input_query,
        answer=answer,
        tag="deep"
    ).save()
    
    return answer

# result = deep_search("What is the best sugar monitoring device?")
# print(result)

