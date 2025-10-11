from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

class Evaluation:
    def __init__(self, chunks, query, answer, sentence_transformer_model):
        self.chunks = chunks
        self.query = query
        self.answer = answer
        self.sentence_transformer_model = sentence_transformer_model
    
    def evaluate_answer_chunk_relationship(self):
        """
        Evaluate how closely related the answer is to the retrieved chunks using semantic similarity
        """
        return self._semantic_similarity_evaluation()
    
    def _semantic_similarity_evaluation(self):
        """Semantic similarity evaluation with 4 core metrics"""
        try:
            # Prepare chunks for embedding
            if isinstance(self.chunks, str):
                chunks_list = [self.chunks]
            elif isinstance(self.chunks, list):
                chunks_list = []
                for chunk in self.chunks:
                    if isinstance(chunk, dict):
                        if 'chunk_text' in chunk:
                            chunks_list.append(chunk['chunk_text'])
                        elif 'text' in chunk:
                            chunks_list.append(chunk['text'])
                        else:
                            chunks_list.append(str(chunk))
                    else:
                        chunks_list.append(str(chunk))
            else:
                chunks_list = [str(self.chunks)]
            
            # Prepare answer for embedding
            if isinstance(self.answer, dict):
                # Extract text content from dictionary
                if 'text' in self.answer:
                    answer_str = str(self.answer['text'])
                elif 'content' in self.answer:
                    answer_str = str(self.answer['content'])
                elif 'answer' in self.answer:
                    answer_str = str(self.answer['answer'])
                else:
                    answer_str = str(self.answer)
            elif isinstance(self.answer, list):
                answer_str = ' '.join(str(item) for item in self.answer)
            else:
                answer_str = str(self.answer)
            
            # Clean answer for better semantic matching
            answer_str = self._clean_answer_for_evaluation(answer_str)
            
            # Calculate semantic similarity between answer and each chunk
            answer_embedding = self.sentence_transformer_model.encode([answer_str])
            chunk_embeddings = self.sentence_transformer_model.encode(chunks_list)
            
            # Calculate query-chunk similarity for context precision
            query_embedding = self.sentence_transformer_model.encode([self.query])
            
            # Ensure proper shapes for cosine similarity
            if answer_embedding.ndim == 1:
                answer_embedding = answer_embedding.reshape(1, -1)
            if chunk_embeddings.ndim == 1:
                chunk_embeddings = chunk_embeddings.reshape(1, -1)
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # Calculate similarities
            answer_chunk_similarities = cosine_similarity(answer_embedding, chunk_embeddings)[0]
            query_chunk_similarities = cosine_similarity(query_embedding, chunk_embeddings)[0]
            answer_query_similarity = cosine_similarity(answer_embedding, query_embedding)[0][0]
            
            # Find the top-ranked chunk (highest similarity with answer)
            top_chunk_idx = np.argmax(answer_chunk_similarities)
            
            # Core metrics using top chunk only
            # 1. Answer-Top Chunk Similarity
            answer_top_chunk_similarity = float(answer_chunk_similarities[top_chunk_idx])
            
            # 2. Query-Top Chunk Similarity  
            query_top_chunk_similarity = float(query_chunk_similarities[top_chunk_idx])
            
            # 3. Answer-Query Similarity
            answer_query_score = float(answer_query_similarity)
            
            # Overall score - average of the 3 core metrics
            overall_score = (answer_top_chunk_similarity + query_top_chunk_similarity + answer_query_score) / 3
            
            # Debug information to understand low scores
            debug_info = {
                "answer_preview": answer_str[:200] + "..." if len(answer_str) > 200 else answer_str,
                "query": self.query,
                "top_chunk_preview": chunks_list[top_chunk_idx][:200] + "..." if len(chunks_list[top_chunk_idx]) > 200 else chunks_list[top_chunk_idx],
                "all_answer_chunk_similarities": [round(float(sim), 4) for sim in answer_chunk_similarities],
                "all_query_chunk_similarities": [round(float(sim), 4) for sim in query_chunk_similarities],
                "sentence_transformer_model": str(type(self.sentence_transformer_model).__name__)
            }
            
            results = {
                "evaluation_type": "Top Chunk Semantic Similarity Evaluation",
                "query": self.query,
                "answer_length": len(answer_str.split()),
                "num_chunks": len(chunks_list),
                "top_chunk_index": int(top_chunk_idx),
                "metrics": {
                    "answer_top_chunk_similarity": {
                        "score": round(answer_top_chunk_similarity, 4),
                        "interpretation": self._interpret_similarity_score(answer_top_chunk_similarity),
                        "description": "Similarity between answer and the top-ranked chunk"
                    },
                    "query_top_chunk_similarity": {
                        "score": round(query_top_chunk_similarity, 4),
                        "interpretation": self._interpret_similarity_score(query_top_chunk_similarity),
                        "description": "Similarity between query and the top-ranked chunk"
                    },
                    "answer_query_similarity": {
                        "score": round(answer_query_score, 4),
                        "interpretation": self._interpret_similarity_score(answer_query_score),
                        "description": "Similarity between answer and the original query"
                    }
                },
                "overall_score": {
                    "score": round(overall_score, 4),
                    "interpretation": self._interpret_overall_score(overall_score),
                    "description": "Average of the three core similarity metrics"
                },
                "debug_info": debug_info
            }
            
            return results
            
        except Exception as e:
            return {"error": str(e)}
    
    def _clean_answer_for_evaluation(self, answer_str):
        """Clean answer text to improve semantic similarity matching"""
        import re
        
        # Remove common answer formatting that doesn't help semantic matching
        # Remove source citations like "(Author, 2023)" or "[1]"
        answer_str = re.sub(r'\([^)]*\d{4}[^)]*\)', '', answer_str)  # (Author, 2023)
        answer_str = re.sub(r'\[\d+\]', '', answer_str)  # [1], [2], etc.
        
        # Remove "Sources:" section and everything after it
        sources_match = re.search(r'\n\s*Sources?\s*:?.*', answer_str, re.IGNORECASE | re.DOTALL)
        if sources_match:
            answer_str = answer_str[:sources_match.start()]
        
        # Remove "References:" section and everything after it
        refs_match = re.search(r'\n\s*References?\s*:?.*', answer_str, re.IGNORECASE | re.DOTALL)
        if refs_match:
            answer_str = answer_str[:refs_match.start()]
        
        # Remove disclaimer sections
        disclaimer_match = re.search(r'\n\s*Disclaimer\s*:?.*', answer_str, re.IGNORECASE | re.DOTALL)
        if disclaimer_match:
            answer_str = answer_str[:disclaimer_match.start()]
        
        # Remove excessive whitespace
        answer_str = re.sub(r'\s+', ' ', answer_str).strip()
        
        return answer_str
    
    def _interpret_score(self, metric_name, score):
        """Interpret individual metric scores"""
        if score >= 0.8:
            return "🟢 Excellent"
        elif score >= 0.6:
            return "🟡 Good"
        elif score >= 0.4:
            return "🟠 Fair"
        else:
            return "🔴 Needs Improvement"
    
    def _interpret_similarity_score(self, score):
        """Interpret semantic similarity scores"""
        if score >= 0.7:
            return "🟢 Highly Related"
        elif score >= 0.5:
            return "🟡 Moderately Related"
        elif score >= 0.3:
            return "🟠 Somewhat Related"
        else:
            return "🔴 Poorly Related"
    
    def _interpret_overall_score(self, score):
        """Interpret overall relationship score"""
        if score >= 0.8:
            return "🟢 Answer strongly grounded in chunks"
        elif score >= 0.6:
            return "🟡 Answer well supported by chunks"
        elif score >= 0.4:
            return "🟠 Answer partially supported by chunks"
        else:
            return "🔴 Answer poorly supported by chunks"
    
    def detailed_chunk_analysis(self):
        """Provide detailed analysis of each chunk's relationship to the answer"""
        try:
            # Prepare chunks for embedding
            if isinstance(self.chunks, str):
                chunks_list = [self.chunks]
            elif isinstance(self.chunks, list):
                chunks_list = []
                for chunk in self.chunks:
                    if isinstance(chunk, dict):
                        if 'chunk_text' in chunk:
                            chunks_list.append(chunk['chunk_text'])
                        elif 'text' in chunk:
                            chunks_list.append(chunk['text'])
                        else:
                            chunks_list.append(str(chunk))
                    else:
                        chunks_list.append(str(chunk))
            else:
                chunks_list = [str(self.chunks)]
            
            # Prepare answer for embedding
            if isinstance(self.answer, dict):
                # Extract text content from dictionary
                if 'text' in self.answer:
                    answer_str = str(self.answer['text'])
                elif 'content' in self.answer:
                    answer_str = str(self.answer['content'])
                elif 'answer' in self.answer:
                    answer_str = str(self.answer['answer'])
                else:
                    answer_str = str(self.answer)
            elif isinstance(self.answer, list):
                answer_str = ' '.join(str(item) for item in self.answer)
            else:
                answer_str = str(self.answer)
            
            answer_embedding = self.sentence_transformer_model.encode([answer_str])
            chunk_embeddings = self.sentence_transformer_model.encode(chunks_list)
            
            # Ensure proper shapes for cosine similarity
            if answer_embedding.ndim == 1:
                answer_embedding = answer_embedding.reshape(1, -1)
            if chunk_embeddings.ndim == 1:
                chunk_embeddings = chunk_embeddings.reshape(1, -1)
            
            similarities = cosine_similarity(answer_embedding, chunk_embeddings)[0]
            
            chunk_analysis = []
            for i, (chunk, similarity) in enumerate(zip(chunks_list, similarities)):
                analysis = {
                    "chunk_id": i + 1,
                    "similarity": round(float(similarity), 4),
                    "interpretation": self._interpret_similarity_score(similarity),
                    "chunk_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
                }
                chunk_analysis.append(analysis)
            
            # Sort by similarity
            chunk_analysis.sort(key=lambda x: x["similarity"], reverse=True)
            
            return chunk_analysis
            
        except Exception as e:
            return []
    
    def generate_evaluation_report(self):
        """Generate a comprehensive evaluation report"""
        # Main evaluation
        main_results = self.evaluate_answer_chunk_relationship()
        
        # Detailed chunk analysis
        chunk_analysis = self.detailed_chunk_analysis()
        
        # Compile full report
        report = {
            "query": self.query,
            "answer": self.answer,
            "chunks_count": len(self.chunks),
            "main_evaluation": main_results,
            "chunk_analysis": chunk_analysis,
            "recommendations": self._generate_recommendations(main_results)
        }
        
        return report
    
    def _generate_recommendations(self, results):
        """Generate actionable recommendations based on evaluation results"""
        recommendations = []
        
        if "overall_chunk_relationship" in results:
            score = results["overall_chunk_relationship"]["score"]
            
            if score < 0.4:
                recommendations.append("Consider improving chunk retrieval - answer seems poorly grounded")
                recommendations.append("Review query processing and similarity matching algorithms")
                recommendations.append("Check if chunks contain relevant information for this type of query")
            elif score < 0.6:
                recommendations.append("Moderate relationship detected - consider refining chunk selection")
                recommendations.append("May benefit from re-ranking retrieved chunks by relevance")
            elif score < 0.8:
                recommendations.append("Good relationship - minor optimizations could improve grounding")
            else:
                recommendations.append("Excellent answer-chunk relationship - system performing well")
        
        if "metrics" in results:
            metrics = results["metrics"]
            
            if "faithfulness" in metrics and metrics["faithfulness"]["score"] < 0.5:
                recommendations.append("Low faithfulness score - answer may contain hallucinations")
            
            if "context_precision" in metrics and metrics["context_precision"]["score"] < 0.5:
                recommendations.append("Low context precision - too many irrelevant chunks retrieved")
        
        return recommendations if recommendations else ["Evaluation completed successfully"]

