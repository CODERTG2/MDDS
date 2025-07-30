import urllib.parse

class ScholarLink:
    def __init__(self, llm_output):
        self.llm_output = llm_output
        self.scholar_links = []
    
    def llm_output_to_sources(self):
        split_output = self.llm_output.split("Sources")
        sources_section = self.llm_output.split("Sources")[-1].strip()
        return sources_section
    
    def extract_scholar_links(self):
        sources_section = self.llm_output_to_sources()
        sources = sources_section.split("\n")
        for source in sources:
            if source.strip() != "":
                encoded_search_term = urllib.parse.quote_plus(source)
                url = f"https://scholar.google.com/scholar?q={encoded_search_term}"
                self.scholar_links.append(url)
        
        return self.scholar_links[1:]

