from openai import AzureOpenAI

class UserQuery:
    def __init__(self, query: str, client, deployment):
        self.query = query
        self.multi_queries = None
        self.client = client
        self.deployment = deployment

    def multi_query(self):

        prompt = f"""
        You are a helpful assistant specialized in medical diagnostic devices.
        Given the following question, generate 3 diverse, search-optimized subqueries that could be used independently to retrieve 
        relevant information from a database of articles full of medical research.
        The retrieved information will then be searched for intersecting information and then summarized to answer the original question.
        Do not include years in the generated subqueries.
        Stay relevant to the question itself.

        The question to create subqueries based off of is:
        {self.query}

        Return the output as a list of 3 subqueries only with no punctuation or numbering. Just have the questions in separate lines.
        """
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are an expert in breaking down complex medical device queries into simpler subqueries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        output = response.choices[0].message.content
        self.multi_queries = output.split('\n')
        return self.multi_queries


        