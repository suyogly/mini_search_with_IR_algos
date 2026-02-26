from pathlib import Path

path = Path("app/data")

def load_txts(path=path):
    doc = []
    for file in path.glob("*.txt"):
        doc.append({
            "doc_id": file.stem,
            "content": file.read_text(),
            "metadata": {
                "source": str(file)
            }
        })
    return doc


