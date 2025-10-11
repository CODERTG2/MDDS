from src.UserQuery import UserQuery
from sentence_transformers import SentenceTransformer
from src.CacheHit import CacheHit
import faiss
from src.ContextRetrieval import ContextRetrieval
from src.Ranking import ranking
from openai import AzureOpenAI
from dotenv import load_dotenv
import json
import networkx as nx
from src.CacheDB import CacheDB
from src.DeepSearch import DeepSearch
from mongoengine import connect
import streamlit as st
from src.ScholarLink import ScholarLink
from src.Evaluation import Evaluation
import concurrent.futures
from datetime import datetime

model = SentenceTransformer('pritamdeka/S-BioBert-snli-multinli-stsb', device='cpu')

vector_db = faiss.read_index("data/chunks(1).index")

load_dotenv()

endpoint = "https://aoai-camp.openai.azure.com/"
model_name = "gpt-4o-mini"
deployment = "medical-device-research-model"
api_version = "2024-12-01-preview"

client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=st.secrets["AZURE_OPEN_AI_KEY"]
)

with open("data/chunks_with_entities(1).json", "r") as f:
    dictionary = json.load(f)

G = nx.read_gexf("data/knowledge_graph(3).gexf")

connect(host=st.secrets["MONGO_URI"])

def normal_search(input_query: str, temp=0.5):
    start_time = datetime.now()
    print("Starting normal search..." + datetime.now().strftime("%H:%M:%S.%f")[:-3])
    def UserQuery_multi_query(input_query, client, deployment):
        user_query = UserQuery(input_query, client, deployment)
        return user_query.multi_query()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        cache_future = executor.submit(CacheHit, input_query, model)
        user_query_future = executor.submit(UserQuery_multi_query, input_query, client, deployment)

        cache_result = cache_future.result()
        subqueries = user_query_future.result()

        if cache_result is not False:
            return cache_result

    full_context = []
    disclaimers = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(ContextRetrieval(model, G, vector_db, dictionary, subquery).retrieve): subquery for subquery in subqueries}
        for future in concurrent.futures.as_completed(futures):
            context, disclaimer = future.result()
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
- When using information from the context, cite the source based on the metadata provided like author, year, title, etc. In the text you can use author and year. But then at the end of the answer, provide a list of sources with full metadata after saying 'Sources'.
- If the context doesn't contain enough information, state this clearly
- Provide a clear, well-structured answer
- If there is a disclaimer, mention it in your answer. Put the disclaimer before the sources.

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
    
    evaluator = Evaluation(rankings, input_query, model, client)
    initial_metrics = evaluator.evaluate(answer)
    if initial_metrics < 0.7:
        answer = evaluator.drafting(answer)
        evaluator.evaluate(answer)

    evaluation_text = evaluator.format_evaluation_results()

    counter = 1
    links = ScholarLink(answer).extract_scholar_links()
    for link in links:
        answer += f"\n\n [{counter}] {link}"
        counter += 1
    
    answer += evaluation_text

    CacheDB(
        query=input_query,
        answer=answer,
        tag="normal"
    ).save()

    print("Finished normal search..." + datetime.now().strftime("%H:%M:%S.%f")[:-3])
    end_time = datetime.now()
    print(f"Normal search duration: {end_time - start_time}")

    return answer
    
# result = normal_search("What is the best sugar monitoring device?")
# print(result)

def deep_search(input_query: str, temp: float):
    start_time = datetime.now()
    print("Starting deep search..." + datetime.now().strftime("%H:%M:%S.%f")[:-3])
    user_query = UserQuery(input_query, client, deployment)
    subqueries = user_query.multi_query()
    full_context = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        deep_searcher_future = executor.submit(DeepSearch(input_query, model, k_articles=5, k_chunks=7).get_context)
        futures = {executor.submit(ContextRetrieval(model, G, vector_db, dictionary, subquery, k=30).retrieve): subquery for subquery in subqueries}
        
        chunks = deep_searcher_future.result()

        for future in concurrent.futures.as_completed(futures):
            context, disclaimer = future.result()
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
- When using information from the context, cite the source based on the metadata provided like author, year, title, etc. In the text you can use author and year. But then at the end of the answer, provide a list of sources with full metadata after saying 'Sources'.
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

    evaluator = Evaluation(final_context, input_query, model, client)
    initial_metrics = evaluator.evaluate(answer)
    if initial_metrics < 0.7:
        answer = evaluator.drafting(answer)
        evaluator.evaluate(answer)

    evaluation_text = evaluator.format_evaluation_results()

    counter = 1
    links = ScholarLink(answer).extract_scholar_links()
    for link in links:
        answer += f"\n\n [{counter}] {link}"
        counter += 1

    answer += evaluation_text
    
    CacheDB(
        query=input_query,
        answer=answer,
        tag="deep"
    ).save()

    print("Finished deep search..." + datetime.now().strftime("%H:%M:%S.%f")[:-3])
    end_time = datetime.now()
    print(f"Deep search duration: {end_time - start_time}")

    return answer

# result = deep_search("What is the best sugar monitoring device?")
# print(result)
