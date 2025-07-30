def ranking(chunks):
    counterlist = [chunk["metadata"]["title"] for chunk in chunks]

    for chunk in chunks:
        chunk["repeat_count"] = counterlist.count(chunk["metadata"]["title"])

    unique_chunks = {}
    
    for chunk in chunks:
        title = chunk["metadata"]["title"]
        
        if title not in unique_chunks or chunk["repeat_count"] > unique_chunks[title]["repeat_count"]:
            unique_chunks[title] = {
                "metadata": chunk["metadata"],
                "chunk_text": chunk.get("chunk_text", chunk.get("text", chunk.get("content", ""))),
                "match_count": chunk.get("match_count", 0),
                "repeat_count": chunk["repeat_count"]
            }

    unique_chunks = list(unique_chunks.values())
    unique_chunks.sort(key=lambda x: (0.7 * x["repeat_count"] + 0.3 * x["match_count"]), reverse=True)
    return unique_chunks[:7]