import json

class DrafterAgent:
    def __init__(self, client, chunks, query, answer, temperature=0.1, deployment="medical-device-research-model"):
        self.client = client
        self.chunks = chunks
        self.query = query
        self.answer = answer
        self.temperature = temperature
        self.deployment = deployment

    def assess(self):
        chunks_text = '\n'.join([f"- {chunk['chunk_text'][:200]}..." for chunk in self.chunks])
        
        prompt = f"""Analyze this Q&A and determine what improvements are needed. Respond with a JSON object containing boolean flags:

Query: {self.query}
Answer: {self.answer}
Available Context: {chunks_text}

Assess:
1. Is the answer well-grounded in the provided context? 
2. Does the answer directly address the query?
3. Is the context sufficient to answer the query?
4. Any other brief suggestions for improvement?

Respond ONLY with JSON:
{{
    "needs_grounding": true/false,
    "needs_query_focus": true/false,
    "insufficient_context": true/false,
    "assessment_summary": "brief explanation"
}}"""
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are an expert evaluator. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature
        )

        try:
            return json.loads(response.choices[0].message.content.strip())
        except:
            return {"needs_grounding": False, "needs_query_focus": False, "sufficient_context": True}
    
    def draft(self, assessment):
        if not any([assessment.get("needs_grounding"), assessment.get("needs_query_focus"), assessment.get("insufficient_context")]):
            return self.answer
                    
        chunks_text = '\n'.join([f"- {chunk['chunk_text']}\nSource: {chunk.get('source', 'Unknown')}" 
                                for chunk in self.chunks])
        
        improvement_focus = []
        if assessment.get("needs_grounding"):
            improvement_focus.append("Better ground the answer in the provided context")
        if assessment.get("needs_query_focus"): 
            improvement_focus.append("Make the answer more directly responsive to the query")
        if assessment.get("assessment_summary"):
            improvement_focus.append(assessment["assessment_summary"])
            
        prompt = f"""Improve this answer focusing on: {', '.join(improvement_focus)}

Query: {self.query}
Current Answer: {self.answer}

Available Context:
{chunks_text}

Guidelines:
- Base your answer primarily on the provided context
- Prioritize the most relevant and recent information. The context is sorted by relevance where the most relevant information appears first.
- When using information from the context, cite the source based on the metadata provided like author, year, title, etc. In the text you can use author and year. But then at the end of the answer, provide a list of sources with full metadata after saying 'Sources'.
- If the context doesn't contain enough information, state this clearly
- Provide a clear, well-structured answer

Improved Answer:"""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are an expert in medical diagnostic devices. Provide clear, well-grounded answers."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature
        )
        
        return response.choices[0].message.content.strip()