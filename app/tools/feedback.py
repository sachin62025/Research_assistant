# app/tools/feedback.py
# def ask_human_feedback(question: str) -> str:
#     return input(question)     ## this is work perfect 
# ...existing code...
def ask_human_feedback(question: str) -> str:
    # This function should now raise or return a marker for web feedback
    return f"__AWAIT_FEEDBACK__::{question}"
# ...existing code...