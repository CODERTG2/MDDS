from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
import concurrent.futures
from src.util import cosine_similarity

class Evaluation:
    def __init__(self, chunks, query, answer, sentence_transformer_model):
        self.chunks = chunks
        self.query = query
        self.answer = answer
        self.sentence_transformer_model = sentence_transformer_model
    
    def evaluate(self):
        query_embedding = self.sentence_transformer_model.encode(self.query, convert_to_tensor=True).cpu().numpy().astype('float32')
        answer_embedding = self.sentence_transformer_model.encode(self.answer, convert_to_tensor=True).cpu().numpy().astype('float32')

        with concurrent.futures.ThreadPoolExecutor() as executor:
            chunk_query_futures = {executor.submit(cosine_similarity, self.sentence_transformer_model.encode(chunk["chunk_text"], convert_to_tensor=True).cpu().numpy().astype('float32'), query_embedding) for chunk in self.chunks}
            chunk_answer_futures = {executor.submit(cosine_similarity, self.sentence_transformer_model.encode(chunk["chunk_text"], convert_to_tensor=True).cpu().numpy().astype('float32'), answer_embedding) for chunk in self.chunks}
            query_answer_future = executor.submit(cosine_similarity, query_embedding, answer_embedding)

            chunk_query_similarities = [future.result() for future in concurrent.futures.as_completed(chunk_query_futures)]
            chunk_answer_similarities = [future.result() for future in concurrent.futures.as_completed(chunk_answer_futures)]
            query_answer_similarity = query_answer_future.result()

        return self.format_evaluation_results({
            "chunk_query_similarities": chunk_query_similarities,
            "chunk_answer_similarities": chunk_answer_similarities,
            "query_answer_similarity": query_answer_similarity
        })
    
    def format_evaluation_results(self, results):
        if not results or "error" in results:
            return ""
        
        formatted_text = "\n\n---\n**Evaluation Scores:**\n\n"
        chunk_answer_similarity = max(results['chunk_answer_similarities'])
        chunk_query_similarity = max(results['chunk_query_similarities'])
        query_answer_similarity = results['query_answer_similarity']

        if chunk_answer_similarity >= 0.8:
            formatted_text += f"**Grounded in source:** 🟢 Excellent - {chunk_answer_similarity:.3f}\n"
        elif chunk_answer_similarity >= 0.5:
            formatted_text += f"**Grounded in source:** 🟡 Good - {chunk_answer_similarity:.3f}\n"
        elif chunk_answer_similarity >= 0.3:
            formatted_text += f"**Grounded in source:** 🟠 Fair - {chunk_answer_similarity:.3f}\n"
        else:
            formatted_text += f"**Grounded in source:** 🔴 Poor - {chunk_answer_similarity:.3f}\n"
        
        if chunk_query_similarity >= 0.8:
            formatted_text += f"**Relevance to query:** 🟢 Excellent - {chunk_query_similarity:.3f}\n"
        elif chunk_query_similarity >= 0.5:
            formatted_text += f"**Relevance to query:** 🟡 Good - {chunk_query_similarity:.3f}\n"
        elif chunk_query_similarity >= 0.3:
            formatted_text += f"**Relevance to query:** 🟠 Fair - {chunk_query_similarity:.3f}\n"
        else:
            formatted_text += f"**Relevance to query:** 🔴 Poor - {chunk_query_similarity:.3f}\n"

        if query_answer_similarity >= 0.8:
            formatted_text += f"**Answer Quality:** 🟢 Excellent - {query_answer_similarity:.3f}\n"
        elif query_answer_similarity >= 0.5:
            formatted_text += f"**Answer Quality:** 🟡 Good - {query_answer_similarity:.3f}\n"
        elif query_answer_similarity >= 0.3:
            formatted_text += f"**Answer Quality:** 🟠 Fair - {query_answer_similarity:.3f}\n"
        else:
            formatted_text += f"**Answer Quality:** 🔴 Poor - {query_answer_similarity:.3f}\n"

        return formatted_text

