from loader import load_txts


loader = load_txts()

def lower_txt(data = loader):
    lowered = []
    for files in data:
        files["content"] = files["content"].lower()
        lowered.append(files)
    return lowered

def remove_puntuation(data = lower_txt()):
    



