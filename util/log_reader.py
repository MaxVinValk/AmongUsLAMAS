import matplotlib.pyplot as plt
import numpy as np
import pickle
import os

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


def find_log_around(log, sentence_to_find, num_context=3):
    for i in range(len(log["logs"])):
        if log["logs"][i].__contains__(sentence_to_find):
            print("--------------------")
            for j in range(i-num_context, min(i+num_context+1, len(log["logs"]))):
                print(f"{j}| {log['logs'][j]}")


def find_trust(log):

    trusts = set()
    i = 0

    while i < len(log["logs"]):
        # We found a discussion phase
        if log["logs"][i].__contains__("Phase.DISCUSS"):
            i += 1
            while not log["logs"][i].__contains__("Phase.VOTE"):
                s = log["logs"][i]
                if s.__contains__("trusts"):
                    #Parse sentence
                    first_crew = int(s[:s.find("trusts")])
                    second_crew = int(s[s.find("trusts") + 6: s.index("On")])
                    trusts.add(f"{first_crew}_{second_crew}")
                i += 1
        else:
            i += 1

    return trusts


def plot_variable(name_of_variable, log_file_paths):

    loaded_logs = []

    for file_path in os.listdir(log_file_paths):
        if file_path.endswith(".amongus"):
            loaded_logs.append(load_log(f"{log_file_paths}/{file_path}"))

    results = {}
    for log in loaded_logs:
        results[log["run_info"][name_of_variable]] = get_wins(log)

    sorted_keys = sorted(results.keys())

    wins_crew_vote = [results[k][0] for k in sorted_keys]
    wins_crew_tasks = [results[k][1] for k in sorted_keys]
    wins_impostors = [results[k][2] for k in sorted_keys]

    y_pos = np.arange(len(sorted_keys))
    plt.rcdefaults()
    fig, ax = plt.subplots()

    h = 1

    ax.barh(y_pos - h/4, wins_crew_vote, height=h/5, label="crew (vote)")
    ax.barh(y_pos, wins_crew_tasks, height=h/5, label="crew (task)")
    ax.barh(y_pos + h/4, wins_impostors, height=h/5, label="imps")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_keys)
    ax.invert_yaxis()

    ax.set_xlabel("Count")
    ax.set_title(f"Outcomes of wins for varying {name_of_variable}")

    ax.legend()

    plt.show()

