import faiss
import spacy
import networkx as nx
from itertools import combinations
import concurrent.futures

nlp = spacy.load("en_core_web_sm")

class ContextRetrieval:
    def __init__(self, model, knowledge_graph, vector_db, dictionary, subquery, k=15, graph_search_method='one_hop'):
        self.model = model
        self.knowledge_graph = knowledge_graph
        self.vector_db = vector_db
        self.dictionary = dictionary
        self.subquery = subquery
        self.k = k
        self.graph_search_method = graph_search_method

    def retrieve(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            wide_net_future = executor.submit(self.retrieve_from_vector_db, self.model, self.subquery, self.vector_db)
            tags_future = executor.submit(self.retrieve_from_knowledge_graph, self.subquery, self.knowledge_graph)

            wide_net = wide_net_future.result()
            tags = tags_future.result()
        
        matched_chunks = {}
        for i, chunk in enumerate(wide_net):
            entities = chunk['entities']
            match_count = sum(entities.count(tag) for tag in tags)
            if match_count > 0:
                matched_chunks[i] = {
                    'chunk_text': chunk['text'],
                    'metadata': chunk['metadata'],
                    'match_count': match_count
                }

        if matched_chunks == {}:
            # Standardize key names for consistency
            standardized_chunks = []
            for chunk in wide_net:
                standardized_chunk = chunk.copy()
                if 'text' in standardized_chunk:
                    standardized_chunk['chunk_text'] = standardized_chunk.pop('text')
                standardized_chunks.append(standardized_chunk)
            return standardized_chunks, "Try using deep search for more accurate results."
    
        # Convert matched_chunks dict to list
        return list(matched_chunks.values()), ""
            
    def retrieve_from_vector_db(self, model, query, vector_db):
        # Use vector_db to retrieve relevant context based on the query
        embedding = model.encode(query).reshape(1, -1).astype('float32')
        faiss.normalize_L2(embedding)
        distances, indices = vector_db.search(embedding, self.k)
        results = []
        for i in indices[0]:
            results.append(self.dictionary[i])
        
        return results
    
    def retrieve_from_knowledge_graph(self, query, knowledge_graph):
        # .gitignore the graph file since its too big
        doc = nlp(query)
        start_tags = []
        for sent in doc.sents:
            subj, obj = None, None
            for tok in sent:
                if "subj" in tok.dep_:
                    subj = tok
                    start_tags.append(subj.text)
                if "obj" in tok.dep_:
                    obj = tok
                    start_tags.append(obj.text)
        
        if not start_tags:
            return []
        
        if self.graph_search_method == 'one_hop':
            tags = []
            for entity in start_tags:
                if knowledge_graph.has_node(entity):
                    immediate_neighbors = list(knowledge_graph.neighbors(entity))
                    tags.append(immediate_neighbors)
            return tags

        if self.graph_search_method == 'two_hop':
            shared = []
            for entity1, entity2 in combinations(start_tags, 2):
                if knowledge_graph.has_node(entity1) and knowledge_graph.has_node(entity2):
                    shared.append(nx.common_neighbors(knowledge_graph, entity1, entity2))
            return shared