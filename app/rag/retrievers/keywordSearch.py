from app.rag.preprocessing.normaliser import normalize, normalize_query

def keyword_search(query, data):
    search_intent = normalize_query(query)
    results = []
    for file in data:
        for word in file["tokens"]:
            if word in search_intent:
                results.append(file)
    return results

print(keyword_search("structure", normalize()))