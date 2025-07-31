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
from Evaluation import Evaluation

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

def format_evaluation_results(results):
    """Format evaluation results in a user-friendly way"""
    if not results or "error" in results:
        return ""
    
    formatted_text = "\n\n---\n**Answer Quality Assessment:**\n\n"
    
    if "metrics" in results:
        metrics = results["metrics"]
        
        # Overall assessment
        if "overall_chunk_relationship" in results:
            overall = results["overall_chunk_relationship"]
            formatted_text += f"**Overall Quality:** {overall['interpretation']} ({overall['score']:.1%})\n\n"
        
        # Key metrics explanation
        formatted_text += "**Detailed Metrics:**\n"
        
        if "faithfulness" in metrics:
            faith = metrics["faithfulness"]
            formatted_text += f"• **Answer Accuracy:** {faith['interpretation']} ({faith['score']:.1%})\n"
            formatted_text += f"  *How well the answer is supported by the provided research*\n\n"
        
        if "answer_relevancy" in metrics:
            rel = metrics["answer_relevancy"]
            formatted_text += f"• **Answer Relevancy:** {rel['interpretation']} ({rel['score']:.1%})\n"
            formatted_text += f"  *How well the answer addresses your specific question*\n\n"
        
        if "context_precision" in metrics:
            prec = metrics["context_precision"]
            formatted_text += f"• **Source Quality:** {prec['interpretation']} ({prec['score']:.1%})\n"
            formatted_text += f"  *Relevance of the research sources used*\n\n"
        
        if "context_recall" in metrics:
            recall = metrics["context_recall"]
            formatted_text += f"• **Information Coverage:** {recall['interpretation']} ({recall['score']:.1%})\n"
            formatted_text += f"  *Completeness of information from available sources*\n\n"
    
    # Add evaluation type info
    if "evaluation_type" in results:
        eval_type = results["evaluation_type"]
        if "Enhanced Semantic Similarity" in eval_type:
            formatted_text += "*Assessment based on advanced semantic analysis of answer quality and source relevance.*"
        else:
            formatted_text += f"*Assessment method: {eval_type}*"
    
    return formatted_text

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

    links = ScholarLink(answer).extract_scholar_links()
    counter = 1
    for link in links:
        answer += f"\n\n [{counter}] {link}"
        counter += 1

    results = Evaluation(rankings, input_query, answer, model).evaluate_answer_chunk_relationship()
    evaluation_text = format_evaluation_results(results)
    answer += evaluation_text

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

