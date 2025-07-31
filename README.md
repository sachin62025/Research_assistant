# Scientific Research Assistant using LangGraph
An AI-powered web application that assists users in scientific research by retrieving, reasoning over, and summarizing academic papers using LangGraph Agents and FastAPI. It supports chat-like interaction, dynamic tool reasoning, and tracks question-answer history.

---

## Features

- Ask complex research questions in natural language
- LangGraph agent plans, searches, and synthesizes answers from research papers
- Step-by-step timeline of what AI is doing
- Final synthesized answer with citations
- Saves questions, answers, and AI steps in `history.json`
- Supports human feedback collection (via web popup)

---

##  Project Structure
```
Research_assistant/
├── app/
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── core_api.py
│   │   ├── download.py
│   │   └── feedback.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── core_agent.py
│   │   ├── format.py
│   │   ├── history.py
│   │   └── prompts.py
│   ├── core_agent.py   
│   └── main.py
├── data/
│   └── history.json
├── frontend/
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── history.html
│       └── index.html
├── notebook/ 
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── run.py
```
```bash
git clone https://github.com/sachin62025/Research_assistant.git
cd Research_assistant
```
```bash
python -m venv venv
source venv/bin/activate   # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```
```bash
python run.py
```

