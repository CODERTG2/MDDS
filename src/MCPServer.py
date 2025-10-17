from mcp.server.fastmcp import FastMCP
from sentence_transformers import SentenceTransformer
import faiss
import json
import networkx as nx
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import concurrent.futures
from datetime import datetime
import logging
import time
import mongoengine

from CacheHit import CacheHit
from UserQuery import UserQuery
from ContextRetrieval import ContextRetrieval
from Ranking import ranking
from Evaluation import Evaluation
from ScholarLink import ScholarLink
from CacheDB import CacheDB
from DeepSearch import DeepSearch

# TODO: UI for the user to choose between the 3 diff search methods - normal, deep, intelligent

mcp = FastMCP("MDDS")

endpoint = "https://aoai-camp.openai.azure.com/"
model_name = "gpt-4o-mini"
deployment = "medical-device-research-model"
api_version = "2024-12-01-preview"

load_dotenv()

try:
    mongodb_uri = os.environ["MONGO_URI"]
    logging.info(f"Connecting to MongoDB at {mongodb_uri}")
    mongoengine.connect(host=mongodb_uri)
    logging.info("MongoDB connection established")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")

model = SentenceTransformer('pritamdeka/S-BioBert-snli-multinli-stsb', device='cpu')
vector_db = faiss.read_index("data/chunks(1).index")
with open("data/chunks_with_entities(1).json", "r") as f:
    dictionary = json.load(f)
G = nx.read_gexf("data/knowledge_graph(3).gexf")
client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=os.environ["AZURE_OPEN_AI_KEY"]
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler()
    ]
)

@mcp.tool()
def normal_search(input_query: str, temp=0.1):
    start_time = datetime.now()
    logging.info("Starting normal search..." + datetime.now().strftime("%H:%M:%S.%f")[:-3])
    
    def UserQuery_multi_query(input_query, client, deployment):
        user_query = UserQuery(input_query, client, deployment)
        return user_query.multi_query()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        cache_future = executor.submit(CacheHit, input_query, model)
        user_query_future = executor.submit(UserQuery_multi_query, input_query, client, deployment)

        logging.info("Waiting for cache result...")
        cache_result = cache_future.result()
        logging.info("Cache check complete")
        
        logging.info("Waiting for subqueries...")
        subqueries = user_query_future.result()
        logging.info(f"Generated {len(subqueries)} subqueries")

        if cache_result is not False:
            logging.info("Cache hit found, returning result")
            return cache_result

    full_context = []
    disclaimers = []
    
    logging.info("Starting context retrieval")
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(ContextRetrieval(model, G, vector_db, dictionary, subquery).retrieve): subquery for subquery in subqueries}
        completed = 0
        total = len(futures)
        
        for future in concurrent.futures.as_completed(futures):
            context, disclaimer = future.result()
            completed += 1
            logging.info(f"Context retrieval: {completed}/{total} completed")
            
            if disclaimer != "":
                disclaimers.append(disclaimer)
            for con in context:
                full_context.append(con)

    if "" in disclaimers:
        disclaimer = "Don't give disclaimer"
    else:
        disclaimer = disclaimers[0]
    
    logging.info(f"Starting ranking with {len(full_context)} context items")
    start_ranking = time.time()
    rankings = ranking(full_context, k=10)
    logging.info(f"Ranking completed in {time.time() - start_ranking:.2f} seconds")
    
    prompt = f"""
You are a helpful AI assistant. Use the provided context to answer the user's question accurately and comprehensively.

Context:
{format_context_for_prompt(rankings)}

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
    logging.info("Starting LLM call")
    start_llm = time.time()
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are an expert in literature review for medical diagnostics devices."},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    
    answer = response.choices[0].message.content.strip()
    logging.info(f"LLM call completed in {time.time() - start_llm:.2f} seconds")
    
    logging.info("Starting evaluation")
    start_eval = time.time()
    evaluator = Evaluation(rankings, input_query, model, client)
    initial_metrics = evaluator.evaluate(answer)
    
    if initial_metrics < 0.7:
        logging.info("Low evaluation score, redrafting answer")
        answer = evaluator.drafting(answer)
        evaluator.evaluate(answer)

    evaluation_text = evaluator.format_evaluation_results()
    logging.info(f"Evaluation completed in {time.time() - start_eval:.2f} seconds")

    logging.info("Extracting scholar links")
    start_links = time.time()
    counter = 1
    links = ScholarLink(answer).extract_scholar_links()
    for link in links:
        answer += f"\n\n [{counter}] {link}"
        counter += 1
    
    answer += evaluation_text
    logging.info(f"Scholar links extracted in {time.time() - start_links:.2f} seconds")

    logging.info("Saving to cache")
    try:
        CacheDB(
            query=input_query,
            answer=answer,
            tag="normal"
        ).save()
        logging.info("Successfully saved to cache")
    except Exception as e:
        logging.error(f"Failed to save to cache: {e}")
        # Continue execution even if cache save fails

    logging.info("Finished normal search..." + datetime.now().strftime("%H:%M:%S.%f")[:-3])
    end_time = datetime.now()
    logging.info(f"Normal search duration: {end_time - start_time}")

    return answer

@mcp.tool()
def deep_search(input_query: str, temp=0.1):
    start_time = datetime.now()
    logging.info("Starting deep search..." + datetime.now().strftime("%H:%M:%S.%f")[:-3])
    
    logging.info("Generating subqueries")
    user_query = UserQuery(input_query, client, deployment)
    subqueries = user_query.multi_query()
    logging.info(f"Generated {len(subqueries)} subqueries")
    full_context = []

    logging.info("Starting deep search and context retrieval")
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        logging.info("Submitting DeepSearch job")
        deep_searcher_future = executor.submit(DeepSearch(input_query, model, k_articles=5, k_chunks=7).get_context)
        
        logging.info("Submitting ContextRetrieval jobs")
        futures = {executor.submit(ContextRetrieval(model, G, vector_db, dictionary, subquery, k=30).retrieve): subquery for subquery in subqueries}
        
        logging.info("Waiting for DeepSearch results...")
        start_deep = time.time()
        chunks = deep_searcher_future.result()
        logging.info(f"DeepSearch completed in {time.time() - start_deep:.2f} seconds, found {len(chunks)} chunks")

        completed = 0
        total = len(futures)
        logging.info(f"Processing {total} context retrieval jobs")
        
        for future in concurrent.futures.as_completed(futures):
            context, disclaimer = future.result()
            completed += 1
            logging.info(f"Context retrieval: {completed}/{total} completed")
            
            for con in context:
                full_context.append(con)

    logging.info(f"Starting ranking with {len(full_context)} context items")
    start_ranking = time.time()
    rankings = ranking(full_context, k=3)
    logging.info(f"Ranking completed in {time.time() - start_ranking:.2f} seconds")

    final_context = chunks + rankings
    logging.info(f"Combined context has {len(final_context)} items")

    prompt = f"""
You are a helpful AI assistant. Use the provided context to answer the user's question accurately and comprehensively.

Context: {format_context_for_prompt(final_context)}

Question: {input_query}

Instructions:
- Base your answer primarily on the provided context
- Prioritize the most relevant and recent information. The context is sorted by relevance where the most relevant information appears first.
- When using information from the context, cite the source based on the metadata provided like author, year, title, etc. In the text you can use author and year. But then at the end of the answer, provide a list of sources with full metadata after saying 'Sources'.
- Provide a clear, well-structured answer

Answer:"""
    logging.info("Starting LLM call")
    start_llm = time.time()
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are an expert in literature review for medical diagnostics devices."},
            {"role": "user", "content": prompt}
        ],
        temperature= temp
    )
    
    answer = response.choices[0].message.content.strip()
    logging.info(f"LLM call completed in {time.time() - start_llm:.2f} seconds")

    logging.info("Starting evaluation")
    start_eval = time.time()
    evaluator = Evaluation(final_context, input_query, model, client)
    initial_metrics = evaluator.evaluate(answer)
    
    if initial_metrics < 0.7:
        logging.info("Low evaluation score, redrafting answer")
        answer = evaluator.drafting(answer)
        evaluator.evaluate(answer)

    evaluation_text = evaluator.format_evaluation_results()
    logging.info(f"Evaluation completed in {time.time() - start_eval:.2f} seconds")

    logging.info("Extracting scholar links")
    start_links = time.time()
    counter = 1
    links = ScholarLink(answer).extract_scholar_links()
    for link in links:
        answer += f"\n\n [{counter}] {link}"
        counter += 1

    answer += evaluation_text
    logging.info(f"Scholar links extracted in {time.time() - start_links:.2f} seconds")
    
    logging.info("Saving to cache")
    try:
        CacheDB(
            query=input_query,
            answer=answer,
            tag="deep"
        ).save()
        logging.info("Successfully saved to cache")
    except Exception as e:
        logging.error(f"Failed to save to cache: {e}")
        # Continue execution even if cache save fails

    logging.info("Finished deep search..." + datetime.now().strftime("%H:%M:%S.%f")[:-3])
    end_time = datetime.now()
    logging.info(f"Deep search duration: {end_time - start_time}")

    return answer

@mcp.tool()
def intelligent_search(query: str) -> str:
    """Intelligent search that chooses between normal and deep search based on query complexity"""
    logging.info(f"Starting intelligent search with query: {query}")
    
    prompt = f"""
You are an expert agent that decides whether to use normal search or deep search based on the user's query.
The normal search is faster and works well for straightforward queries, while the deep search is more thorough and suited for complex or nuanced questions.
If the query solely focuses on applications of AI and mobile for medical devices, the normal search would be better.
Given the query: "{query}", decide which search method is more appropriate.
Respond with either "normal" or "deep" only.
"""
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are an expert in selecting appropriate search methods."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    decision = response.choices[0].message.content.strip().lower()
    logging.info(f"Search decision: {decision}")
    
    if "deep" in decision:
        return deep_search(query)
    else:
        return normal_search(query)

def format_context_for_prompt(context):
    formatted_context = ""
    for i, chunk in enumerate(context, 1):
        metadata = chunk["metadata"]
        content = chunk["chunk_text"]
        
        metadata_str = ""
        for key, value in metadata.items():
            metadata_str += f"{key}: {value}, "
        metadata_str = metadata_str.rstrip(", ")
        
        formatted_context += f"[{i}] Metadata: {metadata_str}\nContent: {content}\n\n"
    return formatted_context

@mcp.tool()
def test_search(input_query: str) -> str:
    """A lightweight search for testing connectivity"""
    logging.info(f"Running test search with query: {input_query}")
    return f"Successfully received query: '{input_query}'. This is a test response to verify the MCP connection works."

if __name__ == "__main__":
    logging.info("Starting MCP server...")
    print("Starting MCP server...")
    mcp.run(transport="stdio")