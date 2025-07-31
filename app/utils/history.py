import json
import os
from hashlib import sha256

HISTORY_PATH = "data/history.json"

def load_history():
    if not os.path.exists(HISTORY_PATH):
        return []
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_entry(question, timeline, final_answer):
    history = load_history()
    entry = {
        "id": sha256(question.encode()).hexdigest(),
        "question": question.strip(),
        "timeline": timeline,
        "final_answer": final_answer.strip()
    }
    # Avoid duplicate
    if not any(h["id"] == entry["id"] for h in history):
        history.append(entry)
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

def get_cached_answer(question):
    qid = sha256(question.encode()).hexdigest()
    history = load_history()
    for h in history:
        if h["id"] == qid:
            return {
                "timeline": h["timeline"],
                "final": h["final_answer"]
            }
    return None
def search_history(term: str):
    return [h for h in load_history() if term.lower() in h["question"].lower()]
