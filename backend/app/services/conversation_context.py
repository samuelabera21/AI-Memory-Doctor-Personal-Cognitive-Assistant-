# simple in-memory context (per session later)
last_results = []


def save_context(results):
    global last_results
    last_results = results


def get_context():
    return last_results