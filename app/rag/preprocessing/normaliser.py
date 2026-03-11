from loader import load_txts
import re
import string

def lower_txt(data):
    lowered = []
    for file in data:
        file["content"] = file["content"].lower()
        lowered.append(file)
    return lowered


_PUNCT_RE = re.compile(r"[!\"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~]")

def remove_punctuation_regex(data):
    result = []
    for file in data:
        file["content"] = _PUNCT_RE.sub("", file["content"])
        result.append(file)
    return result

def remove_numbers(data):
    result = []
    for file in data:
        file["content"] = re.sub(r'\d+', '', file["content"])
        result.append(file)
    return result

def remove_extra_whitespace(data):
    result = []
    for file in data:
        file["content"] = re.sub(r'\s+', ' ', file["content"]).strip()
        result.append(file)
    return result

def tokenize(data):
    result = []
    for file in data:
        file["tokens"] = file["content"].split()
        result.append(file)
    return result

def remove_stopwords(data):
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "is", "it", "of", "with"}
    result = []
    for file in data:
        file["tokens"] = [word for word in file["tokens"] if word not in stopwords]
        result.append(file)
    return result

def normalize():
    raw_data     = load_txts()
    lowered      = lower_txt(raw_data)
    no_punct     = remove_punctuation_regex(lowered)
    no_numbers   = remove_numbers(no_punct)
    no_spaces    = remove_extra_whitespace(no_numbers)
    tokenized    = tokenize(no_spaces)
    final        = remove_stopwords(tokenized)
    return final

if __name__ == "__main__":
    result = normalize()
    for doc in result:
        print(doc)
