import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import io
from PyPDF2 import PdfReader
import requests
import faiss

nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('punkt_tab')

sw_nltk = stopwords.words('english')
lemmatizer = WordNetLemmatizer()

class DeepSearch:
    def __init__(self, query, model, k_articles=5, k_chunks=7):
        self.query = query
        self.model = model
        self.keyword = self.extract_keyword()
        self.k_articles = k_articles
        self.k_chunks = k_chunks
        self.index = faiss.IndexFlatL2(768)

    def extract_keyword(self):
        question = self.query.lower()
        words = nltk.word_tokenize(question)
        words_no_punct = [re.sub(r'[^\w\s]', '', word) for word in words]
        words_no_punct = [word for word in words_no_punct if word]
        filtered_words = [word for word in words_no_punct if word not in sw_nltk]
        lemmatized_words = [lemmatizer.lemmatize(word) for word in filtered_words]
        keyword = ' '.join(lemmatized_words)
        return keyword

    def get_context(self):
        k=5
        encodingmethod = "utf-8"
        errortype = "strict"
        encoded_search_term = urllib.parse.quote(self.keyword, encoding=encodingmethod, errors=errortype)
        url = f'http://export.arxiv.org/api/query?search_query=all:{encoded_search_term}&start=0&max_results={self.k_articles}'

        try:
            response = urllib.request.urlopen(url)
            try:
                url_read = response.read().decode("utf-8")
            except UnicodeDecodeError:
                response = urllib.request.urlopen(url)
                url_read = response.read().decode("utf-8", errors="ignore")

            parse_xml = ET.fromstring(url_read)
        except Exception as e:
            raise

        ns = {"ns": "http://www.w3.org/2005/Atom"}
        entries = parse_xml.findall('ns:entry', ns)

        articles_data = []
        for entry in entries:
            link = entry.find('ns:link[@type="application/pdf"]', ns)
            if link is not None and "href" in link.attrib:
                pdf_url = link.attrib['href']

                title = entry.find('ns:title', ns)
                title_text = title.text.strip() if title is not None else "Unknown Title"

                authors = entry.findall('ns:author/ns:name', ns)
                author_names = [author.text for author in authors] if authors else ["Unknown Author"]

                published = entry.find('ns:published', ns)
                published_date = published.text[:10] if published is not None else "Unknown Date"

                summary = entry.find('ns:summary', ns)
                summary_text = summary.text.strip() if summary is not None else "No summary available"

                metadata = {
                    'title': title_text,
                    'authors': author_names,
                    'published': published_date,
                    'summary': summary_text
                }

                articles_data.append({
                    'pdf_url': pdf_url,
                    'metadata': metadata
                })

        chunks = []
        chunk_size_sentences = 50

        for i, article in enumerate(articles_data):
            try:
                pdf_response = requests.get(article['pdf_url'], timeout=30)
                pdf_response.raise_for_status()

                pdf_file = io.BytesIO(pdf_response.content)
                pdf_reader = PdfReader(pdf_file)
                pdf_text = ""

                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        pdf_text += page_text + " "

                pdf_text = re.sub(r' {2,}', ' ', pdf_text)
                pdf_text = re.sub(r'\n{3,}', '\n\n', pdf_text)
                pdf_text = re.sub(r'[\f\v\r]', ' ', pdf_text)
                pdf_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', pdf_text)
                pdf_text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', pdf_text)
                pdf_text = pdf_text.strip()

                sentences = nltk.sent_tokenize(pdf_text)
                num_sentences = len(sentences)

                for j in range(0, num_sentences, chunk_size_sentences):
                    chunk_sentences = sentences[j:j + chunk_size_sentences]
                    chunk_text = " ".join(chunk_sentences)

                    if chunk_text:
                        chunk_embedding = self.model.encode(chunk_text, convert_to_tensor=True)
                        chunk_embedding = chunk_embedding.cpu().numpy().astype('float32')

                        chunk_data = {
                            'chunk_text': chunk_text,
                            'embedding': chunk_embedding,
                            'metadata': article['metadata'],
                            'sentence_count': len(chunk_sentences)
                        }
                        embedding = chunk_data['embedding'].reshape(1, -1).astype("float32")
                        faiss.normalize_L2(embedding)
                        self.index.add(embedding)
                        chunks.append(chunk_data)

            except Exception as e:
                raise
        
        query_embedding = self.model.encode(self.query, convert_to_tensor=True)
        query_embedding = query_embedding.cpu().numpy().astype('float32')
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        distances, indices = self.index.search(query_embedding, k=self.k_chunks)

        chunks = [chunks[i] for i in indices[0]]
        return chunks
