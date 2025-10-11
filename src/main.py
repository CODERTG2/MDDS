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

def format_evaluation_results(results):
    if not results or "error" in results:
        return ""
    
    formatted_text = "\n\n---\n**Answer Quality Assessment:**\n\n"
    
    if "overall_score" in results:
        overall = results["overall_score"]
        formatted_text += f"**Overall Quality:** {overall['interpretation']} ({overall['score']:.1%})\n\n"
    
    if "metrics" in results:
        metrics = results["metrics"]
        formatted_text += "**Detailed Metrics:**\n"
        
        if "answer_top_chunk_similarity" in metrics:
            ans_chunk = metrics["answer_top_chunk_similarity"]
            formatted_text += f"• **Answer-Source Alignment:** {ans_chunk['interpretation']} ({ans_chunk['score']:.1%})\n"
            formatted_text += f"  *How well the answer is grounded in the most relevant research*\n\n"
        
        if "query_top_chunk_similarity" in metrics:
            query_chunk = metrics["query_top_chunk_similarity"]
            formatted_text += f"• **Source Relevance:** {query_chunk['interpretation']} ({query_chunk['score']:.1%})\n"
            formatted_text += f"  *How well the top source matches your question*\n\n"
        
        if "answer_query_similarity" in metrics:
            ans_query = metrics["answer_query_similarity"]
            formatted_text += f"• **Answer Relevance:** {ans_query['interpretation']} ({ans_query['score']:.1%})\n"
            formatted_text += f"  *How directly the answer addresses your question*\n\n"
    
    # Show which chunk was selected as most relevant
    if "top_chunk_index" in results:
        chunk_idx = results["top_chunk_index"]
        formatted_text += f"*Based on analysis of chunk #{chunk_idx + 1} as the most relevant source.*\n"
    
    # Add debug info if overall score is low
    if "overall_score" in results and results["overall_score"]["score"] < 0.5:
        if "debug_info" in results:
            debug = results["debug_info"]
            formatted_text += f"\n**Debug Info (Low Score Analysis):**\n"
            formatted_text += f"• Answer preview: {debug.get('answer_preview', 'N/A')[:100]}...\n"
            formatted_text += f"• Query: {debug.get('query', 'N/A')}\n"
            formatted_text += f"• Top chunk preview: {debug.get('top_chunk_preview', 'N/A')[:100]}...\n"
            formatted_text += f"• All similarities: {debug.get('all_answer_chunk_similarities', [])}\n"
    
    # Add evaluation type info
    if "evaluation_type" in results:
        eval_type = results["evaluation_type"]
        if "Top Chunk" in eval_type:
            formatted_text += "*Assessment focuses on the highest-quality source match.*"
        else:
            formatted_text += f"*Assessment method: {eval_type}*"
    
    return formatted_text

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
    
    def evaluation_results(rankings, input_query, answer, model):
        results = Evaluation(rankings, input_query, answer, model).evaluate_answer_chunk_relationship()
        return format_evaluation_results(results)
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        links_future = executor.submit(ScholarLink(answer).extract_scholar_links)
        results_future = executor.submit(evaluation_results, rankings, input_query, answer, model)

        links = links_future.result()
        evaluation_text = results_future.result()
    
    counter = 1
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

    links = ScholarLink(answer).extract_scholar_links()
    counter = 1
    for link in links:
        answer += f"\n\n [{counter}] {link}"
        counter += 1
    
    results = Evaluation(final_context, input_query, answer, model).evaluate_answer_chunk_relationship()
    evaluation_text = format_evaluation_results(results)
    answer += evaluation_text
    
    CacheDB(
        query=input_query,
        answer=answer,
        tag="deep"
    ).save()
    
    return answer

# result = deep_search("What is the best sugar monitoring device?")
# print(result)
