import pickle

def load_log(file_path):
    with open(file_path, "rb") as f:
        return pickle.load(f)

def get_wins(log):
    win_crew = 0
    win_imp = 0
    for line in log:
        if line.startswith("Crewmates win!"):
            win_crew += 1
        elif line.startswith("Impostors win!"):
            win_imp += 1

    return win_crew, win_imp