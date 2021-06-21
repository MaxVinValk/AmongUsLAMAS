import pickle

def load_log(file_path):
    with open(file_path, "rb") as f:
        return pickle.load(f)

def get_wins(log):
    win_crew_vote = 0
    win_crew_tasks = 0
    win_imp = 0
    for line in log["logs"]:
        if line.startswith("Crewmates win!"):
            if line.__contains__("(tasks)"):
                win_crew_tasks += 1
            else:
                win_crew_vote += 1
        elif line.startswith("Impostors win!"):
            win_imp += 1

    return win_crew_vote, win_crew_tasks, win_imp
