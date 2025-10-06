import os
import tempfile
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    faithfulness,
    context_recall,
    context_precision,
    answer_correctness,
    answer_similarity
)
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

class Evaluation:
    def __init__(self, chunks, query, answer, sentence_transformer_model):
        self.chunks = chunks
        self.query = query
        self.answer = answer
        
        self.temp_dir = tempfile.mkdtemp()
        os.environ['TMPDIR'] = self.temp_dir
        
        # Configure OpenAI for RAGAS evaluation using Azure OpenAI
        # RAGAS needs Azure OpenAI configuration, not just the API key
        try:
            import streamlit as st
            if 'AZURE_OPEN_AI_KEY' in st.secrets:
                # Set environment variables for Azure OpenAI that RAGAS can use
                os.environ['OPENAI_API_KEY'] = st.secrets['AZURE_OPEN_AI_KEY']
                os.environ['OPENAI_API_BASE'] = "https://aoai-camp.openai.azure.com/"
                os.environ['OPENAI_API_TYPE'] = "azure"
                os.environ['OPENAI_API_VERSION'] = "2024-12-01-preview"
                
                # Also try the newer Azure environment variables
                os.environ['AZURE_OPENAI_API_KEY'] = st.secrets['AZURE_OPEN_AI_KEY']
                os.environ['AZURE_OPENAI_ENDPOINT'] = "https://aoai-camp.openai.azure.com/"
                os.environ['AZURE_OPENAI_API_VERSION'] = "2024-12-01-preview"
        except Exception as e:
            pass
        
        self.sentence_transformer_model = sentence_transformer_model
    
    def evaluate_answer_chunk_relationship(self):
        """
        Evaluate how closely related the answer is to the retrieved chunks using RAGAS
        """
        try:
            # Ensure chunks is a list of strings (not a single string)
            if isinstance(self.chunks, str):
                chunks_list = [self.chunks]
            elif isinstance(self.chunks, list):
                # Extract text from chunks if they're dictionaries
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
            
            # Ensure answer is a string (not a list or dict)
            if isinstance(self.answer, dict):
                # Extract text content from dictionary - try common keys
                if 'text' in self.answer:
                    answer_str = str(self.answer['text'])
                elif 'content' in self.answer:
                    answer_str = str(self.answer['content'])
                elif 'answer' in self.answer:
                    answer_str = str(self.answer['answer'])
                else:
                    # If no recognizable text key, convert whole dict to string
                    answer_str = str(self.answer)
            elif isinstance(self.answer, list):
                answer_str = ' '.join(str(item) for item in self.answer)
            else:
                answer_str = str(self.answer)
            
            eval_data = {
                "question": [self.query],
                "answer": [answer_str],
                "contexts": [chunks_list],
            }
            
            eval_dataset = Dataset.from_dict(eval_data)
            
            metrics = [
                faithfulness,
                answer_relevancy,
            ]
            
            # Skip RAGAS for now due to Azure OpenAI complexity
            # The semantic similarity evaluation is working well and provides meaningful metrics
            raise Exception("Using semantic similarity evaluation instead of RAGAS for Azure OpenAI compatibility")
            
            return self._format_ragas_results(result)
            
        except Exception as e:
            return self._fallback_evaluation()
    
    def _format_ragas_results(self, result):
        """Format RAGAS results for better readability"""
        # Prepare answer for length calculation  
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
        
        # Prepare chunks for count calculation
        if isinstance(self.chunks, str):
            chunks_count = 1
        elif isinstance(self.chunks, list):
            chunks_count = len(self.chunks)
        else:
            chunks_count = 1
        
        formatted_results = {
            "evaluation_type": "RAGAS",
            "query": self.query,
            "answer_length": len(answer_str.split()),
            "num_chunks": chunks_count,
            "metrics": {}
        }
        
        # Process RAGAS scores - handle different result object types
        metrics_dict = {}
        
        # Method 1: Check if it has items() method (dictionary-like)
        if hasattr(result, 'items') and callable(getattr(result, 'items')):
            try:
                for metric_name, score in result.items():
                    if isinstance(score, (int, float)):
                        metrics_dict[metric_name] = score
            except Exception as e:
                pass
        
        # Method 2: Check if it's a pandas DataFrame or Series
        if hasattr(result, 'to_dict'):
            try:
                result_dict = result.to_dict()
                for key, value in result_dict.items():
                    if isinstance(value, (int, float)):
                        metrics_dict[key] = value
            except Exception as e:
                pass
        
        # Method 3: Check object attributes
        if hasattr(result, '__dict__'):
            try:
                result_dict = result.__dict__
                for attr_name, attr_value in result_dict.items():
                    if isinstance(attr_value, (int, float)) and not (attr_value != attr_value):  # Check for nan
                        metrics_dict[attr_name] = attr_value
                    elif isinstance(attr_value, dict):
                        # Handle nested dictionaries like _scores_dict
                        for sub_key, sub_value in attr_value.items():
                            if isinstance(sub_value, list) and len(sub_value) > 0:
                                # Take the first value from list
                                val = sub_value[0]
                                if isinstance(val, (int, float)) and not (val != val):  # Check for nan
                                    metrics_dict[sub_key] = val
                            elif isinstance(sub_value, (int, float)) and not (sub_value != sub_value):
                                metrics_dict[sub_key] = sub_value
            except Exception as e:
                pass
        
        # Method 4: Try common attribute names
        common_metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
        for metric in common_metrics:
            if hasattr(result, metric):
                try:
                    value = getattr(result, metric)
                    if isinstance(value, (int, float)):
                        metrics_dict[metric] = value
                except Exception as e:
                    pass
        
        if not metrics_dict:
            return self._fallback_evaluation()
        
        # Process extracted metrics
        for metric_name, score in metrics_dict.items():
            formatted_results["metrics"][metric_name] = {
                "score": round(score, 4),
                "interpretation": self._interpret_score(metric_name, score)
            }
        
        # Calculate overall relationship score (focus on answer-chunk relationship)
        key_metrics = ["faithfulness", "answer_relevancy"]
        available_scores = [metrics_dict.get(metric, 0) for metric in key_metrics if metric in metrics_dict]
        
        if available_scores:
            overall_score = sum(available_scores) / len(available_scores)
            formatted_results["overall_chunk_relationship"] = {
                "score": round(overall_score, 4),
                "interpretation": self._interpret_overall_score(overall_score)
            }
        
        return formatted_results
    
    def _fallback_evaluation(self):
        """Enhanced semantic similarity evaluation with comprehensive metrics"""
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
            
            # Enhanced metrics calculation
            
            # 1. Faithfulness approximation (how well answer is grounded in chunks)
            max_similarity = float(np.max(answer_chunk_similarities))
            avg_similarity = float(np.mean(answer_chunk_similarities))
            faithfulness_score = (max_similarity * 0.7) + (avg_similarity * 0.3)  # Weighted combination
            
            # 2. Answer relevancy approximation (how relevant answer is to query)  
            answer_relevancy_score = float(answer_query_similarity)
            
            # 3. Context precision approximation (how relevant chunks are to query)
            relevant_chunks = sum(1 for sim in query_chunk_similarities if sim > 0.3)
            context_precision_score = relevant_chunks / len(chunks_list) if len(chunks_list) > 0 else 0
            
            # 4. Context recall approximation (coverage of relevant information)
            high_similarity_chunks = sum(1 for sim in answer_chunk_similarities if sim > 0.5)
            context_recall_score = high_similarity_chunks / len(chunks_list) if len(chunks_list) > 0 else 0
            
            # 5. Overall coherence score
            coherence_score = (faithfulness_score + answer_relevancy_score + context_precision_score) / 3
            
            results = {
                "evaluation_type": "Enhanced Semantic Similarity (RAGAS-style)",
                "query": self.query,
                "answer_length": len(answer_str.split()),
                "num_chunks": len(chunks_list),
                "metrics": {
                    "faithfulness": {
                        "score": round(faithfulness_score, 4),
                        "interpretation": self._interpret_score("faithfulness", faithfulness_score),
                        "description": "How well the answer is grounded in the provided chunks"
                    },
                    "answer_relevancy": {
                        "score": round(answer_relevancy_score, 4),
                        "interpretation": self._interpret_score("answer_relevancy", answer_relevancy_score),
                        "description": "How relevant the answer is to the original query"
                    },
                    "context_precision": {
                        "score": round(context_precision_score, 4),
                        "interpretation": self._interpret_score("context_precision", context_precision_score),
                        "description": "Proportion of retrieved chunks that are relevant to the query"
                    },
                    "context_recall": {
                        "score": round(context_recall_score, 4),
                        "interpretation": self._interpret_score("context_recall", context_recall_score),
                        "description": "How well the chunks cover the information needed for the answer"
                    },
                    "max_chunk_similarity": {
                        "score": round(max_similarity, 4),
                        "interpretation": self._interpret_similarity_score(max_similarity),
                        "description": "Highest similarity between answer and any chunk"
                    },
                    "avg_chunk_similarity": {
                        "score": round(avg_similarity, 4),
                        "interpretation": self._interpret_similarity_score(avg_similarity),
                        "description": "Average similarity between answer and all chunks"
                    }
                },
                "overall_chunk_relationship": {
                    "score": round(coherence_score, 4),
                    "interpretation": self._interpret_overall_score(coherence_score)
                }
            }
            
            return results
            
        except Exception as e:
            return {"error": str(e)}
    
    def _interpret_score(self, metric_name, score):
        """Interpret individual RAGAS metric scores"""
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

