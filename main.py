from UserQuery import UserQuery
from sentence_transformers import SentenceTransformer
from CacheHit import CacheHit
import faiss
from ContextRetrieval import ContextRetrieval
from Ranking import ranking
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import json
import networkx as nx
from CacheDB import CacheDB

model = SentenceTransformer('./content/sentence_transformer_model', device='cpu')

vector_db = faiss.read_index("chunks(1).index")

load_dotenv()

endpoint = "https://aoai-camp.openai.azure.com/"
model_name = "gpt-4o-mini"
deployment = "abbott_researcher"
api_version = "2024-12-01-preview"

client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=os.getenv("AZURE_OPEN_AI_KEY")
)

with open("chunks_with_entities(1).json", "r") as f:
    dictionary = json.load(f)

G = nx.read_gexf("knowledge_graph(3).gexf")

def normal_search(input_query: str):
    if CacheHit(input_query, model) is not False:
        return CacheHit(input_query, model)

    user_query = UserQuery(input_query, client, deployment)
    subqueries = user_query.multi_query()
    full_context = []
    for subquery in subqueries:
        context, disclaimer = ContextRetrieval(model, G, vector_db, dictionary, subquery).retrieve()
        if disclaimer != "":
            pass
        for con in context:
            full_context.append(con)
        
    rankings = ranking(full_context)

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
- When using information from the context, cite the source based on the metadata provided.
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
        temperature=0.5
    )
    
    answer = response.choices[0].message.content.strip()

    CacheDB(
        query=input_query,
        answer=answer
    ).save()
    
    return answer
    
result = normal_search("What are some glucose monitoring devices for athletes?")
print(result)

def deep_search(input_query: str):
    user_query = UserQuery(input_query, client, deployment)
    subqueries = user_query.multi_query()
    full_context = []
    for subquery in subqueries:
        context, disclaimer = ContextRetrieval(model, G, vector_db, dictionary, subquery, k=30).retrieve()
        if disclaimer != "":
            pass
        for con in context:
            full_context.append(con)
    
        
    rankings = ranking(full_context)

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
- When using information from the context, cite the source based on the metadata provided.
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
        temperature=0.5
    )
    
    answer = response.choices[0].message.content.strip()

    CacheDB(
        query=input_query,
        answer=answer
    ).save()
    
    return answer