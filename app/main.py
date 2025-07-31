

# Entry point
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core_agent import run_query
import markdown
from app.utils.history import load_history
app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# @app.post("/research", response_class=HTMLResponse)
# async def research(request: Request, query: str = Form(...)):
#     result = await run_query(query)

#     #  Convert Markdown to HTML so formatting appears correctly
#     final_html = markdown.markdown(result["final"])
#     timeline_html = [markdown.markdown(step) for step in result["timeline"]]

#     return templates.TemplateResponse("index.html", {
#         "request": request,
#         "timeline": timeline_html,
#         "final": final_html
#     })
# ...existing code...
from fastapi.responses import RedirectResponse

@app.post("/research", response_class=HTMLResponse)
async def research(request: Request, query: str = Form(...)):
    result = await run_query(query)

    # Check if feedback is required
    feedback_question = None
    final = result.get("final", "")
    if final.startswith("__AWAIT_FEEDBACK__::"):
        feedback_question = final.replace("__AWAIT_FEEDBACK__::", "")
        final = None  # Hide final until feedback is submitted

        # Store state in session
        request.session["pending_query"] = query
        request.session["feedback_prompt"] = feedback_question

    final_html = markdown.markdown(final) if final else ""
    timeline_html = [markdown.markdown(step) for step in result.get("timeline", [])]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "timeline": timeline_html,
        "final": final_html,
        "feedback_question": feedback_question
    })

@app.post("/submit-feedback", response_class=HTMLResponse)
async def submit_feedback(request: Request, feedback: str = Form(...)):
    pending_query = request.session.get("pending_query")
    # Resume processing with feedback
    result = await run_query(pending_query, feedback=feedback)

    # Clean up session
    request.session.pop("pending_query", None)
    request.session.pop("feedback_prompt", None)

    final_html = markdown.markdown(result.get("final", ""))
    timeline_html = [markdown.markdown(step) for step in result.get("timeline", [])]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "timeline": timeline_html,
        "final": final_html,
        "feedback_question": None
    })
# ...existing code...



@app.get("/history", response_class=HTMLResponse)
async def show_history(request: Request):
    history = load_history()
    return templates.TemplateResponse("history.html", {
        "request": request,
        "history": history
    })







###############################################################################################

# # # Entry point
# # from fastapi import FastAPI, Request, Form
# # from fastapi.responses import HTMLResponse
# # from fastapi.staticfiles import StaticFiles
# # from fastapi.templating import Jinja2Templates
# # from app.core_agent import run_query
# # import markdown

# # app = FastAPI()

# # app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
# # templates = Jinja2Templates(directory="frontend/templates")


# # @app.get("/", response_class=HTMLResponse)
# # async def home(request: Request):
# #     return templates.TemplateResponse("index.html", {"request": request})

# # @app.post("/research", response_class=HTMLResponse)
# # async def research(request: Request, query: str = Form(...)):
# #     result = await run_query(query)
# #     return templates.TemplateResponse("index.html", {
# #         "request": request,
# #         "timeline": result["timeline"],
# #         "final": result["final"]
# #     })

# # @app.post("/research", response_class=HTMLResponse)
# # async def research(request: Request, query: str = Form(...)):
# #     result = await run_query(query)
# #     # return templates.TemplateResponse("index.html", {"request": request, "result": result})
# #     html_result = markdown.markdown(result)
# #     return templates.TemplateResponse("index.html", {"request": request, "result": html_result})


# # @app.post("/research", response_class=HTMLResponse)
# # async def research(request: Request, query: str = Form(...)):
# #     result = await run_query(query)
# #     return templates.TemplateResponse("index.html", {
# #         "request": request,
# #         "timeline": result["timeline"],
# #         "final": result["final"]
# #     })










# # Entry point
# from fastapi import FastAPI, Request, Form
# from fastapi.responses import HTMLResponse, RedirectResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from app.core_agent import run_query
# from fastapi import FastAPI
# # from fastapi.middleware.sessions import SessionMiddleware
# from starlette.middleware.sessions import SessionMiddleware
# import markdown
# from app.utils.history import load_history
# from dotenv import load_dotenv
# import os
# load_dotenv()



# app = FastAPI()
# app.add_middleware(SessionMiddleware, secret_key=os.environ["SECRET_KEY"])
# app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
# templates = Jinja2Templates(directory="frontend/templates")


# # @app.get("/", response_class=HTMLResponse)
# # async def home(request: Request):
# #     return templates.TemplateResponse("index.html", {"request": request})
# @app.get("/", response_class=HTMLResponse)
# async def home(request: Request):
#     request.session.setdefault("chat", [])
#     return templates.TemplateResponse("index.html", {"request": request, "messages": request.session["chat"]})


# # @app.post("/research", response_class=HTMLResponse)
# # async def research(request: Request, query: str = Form(...)):
# #     result = await run_query(query)

# #     #  Convert Markdown to HTML so formatting appears correctly
# #     final_html = markdown.markdown(result["final"])
# #     timeline_html = [markdown.markdown(step) for step in result["timeline"]]

# #     return templates.TemplateResponse("index.html", {
# #         "request": request,
# #         "timeline": timeline_html,
# #         "final": final_html
# #     })

# def build_messages(question: str, timeline: list[str], final: str = None) -> list[dict]:
#     messages = []

#     # User question
#     messages.append({
#         "role": "user",
#         "content": question
#     })

#     # Timeline messages (usually system or tool/AI updates)
#     for step in timeline:
#         role = "ai" if "AIMessage" in step else "tool"
#         messages.append({
#             "role": role,
#             "content": step.replace("<b>AIMessage:</b>", "").replace("<b>ToolMessage:</b>", "")
#         })

#     # Final answer, if available
#     if final:
#         messages.append({
#             "role": "ai",
#             "content": final
#         })

#     return messages


# @app.post("/research")
# async def research(request: Request, query: str = Form(...)):
#     result = await run_query(query)

#     timeline = result.get("timeline", [])
#     final = result.get("final", "")

#     feedback_question = None
#     if final.startswith("__AWAIT_FEEDBACK__::"):
#         feedback_question = final.replace("__AWAIT_FEEDBACK__::", "")
#         final = None  # Don’t render final until feedback is submitted

#         # Store question in session or memory
#         request.session["pending_question"] = query
#         request.session["feedback_prompt"] = feedback_question

#     return templates.TemplateResponse("index.html", {
#         "request": request,
#         "messages": build_messages(query, timeline, final),
#         "feedback_question": feedback_question
#     })


# @app.post("/submit-feedback")
# async def submit_feedback(request: Request, feedback: str = Form(...)):
#     pending_question = request.session.get("pending_question")
#     # Here you can log feedback or store it

#     # Resume processing: You can re-run the query with feedback if needed
#     result = await run_query(pending_question, feedback=feedback)

#     timeline = result.get("timeline", [])
#     final = result.get("final", "")

#     request.session.pop("pending_question", None)
#     request.session.pop("feedback_prompt", None)

#     return templates.TemplateResponse("index.html", {
#         "request": request,
#         "messages": build_messages(pending_question, timeline, final)
#     })

# # @app.post("/research", response_class=HTMLResponse)
# # async def research(request: Request, query: str = Form(...)):
# #     messages = request.session.get("chat", [])

# #     # Save user question
# #     messages.append({"type": "user", "content": query})

# #     # Run the query, possibly using cache
# #     result = await run_query(query)

# #     # Whether from cache or fresh, add to session
# #     timeline = "<br>".join(result["timeline"])
# #     final = f"<b>Final Answer:</b><br>{result['final']}"

# #     messages.append({"type": "ai", "content": timeline})
# #     messages.append({"type": "ai", "content": final})

# #     # Save back to session
# #     request.session["chat"] = messages
# #     return RedirectResponse("/", status_code=303)


# @app.get("/history", response_class=HTMLResponse)
# async def show_history(request: Request):
#     history = load_history()
#     return templates.TemplateResponse("history.html", {
#         "request": request,
#         "history": history
#     })


# @app.get("/clear")
# async def clear_chat(request: Request):
#     request.session["chat"] = []
#     return RedirectResponse("/", status_code=303)


# ###################################################################################################################################################
# # from app.tools.feedback import get_pending_feedback_question, submit_feedback_response

# # @app.get("/get_feedback")
# # async def get_feedback():
# #     question = get_pending_feedback_question()
# #     return JSONResponse(content={"feedback_question": question})

# # @app.post("/submit_feedback")
# # async def submit_feedback(request: Request):
# #     data = await request.json()
# #     submit_feedback_response(data["feedback"])
# #     return {"status": "ok"}
# # from fastapi.responses import JSONResponse





# # Entry point
# from fastapi import FastAPI, Request, Form
# from fastapi.responses import HTMLResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from app.core_agent import run_query
# import markdown

# app = FastAPI()

# app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
# templates = Jinja2Templates(directory="frontend/templates")


# @app.get("/", response_class=HTMLResponse)
# async def home(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

# @app.post("/research", response_class=HTMLResponse)
# async def research(request: Request, query: str = Form(...)):
#     result = await run_query(query)
#     return templates.TemplateResponse("index.html", {
#         "request": request,
#         "timeline": result["timeline"],
#         "final": result["final"]
#     })

# @app.post("/research", response_class=HTMLResponse)
# async def research(request: Request, query: str = Form(...)):
#     result = await run_query(query)
#     # return templates.TemplateResponse("index.html", {"request": request, "result": result})
#     html_result = markdown.markdown(result)
#     return templates.TemplateResponse("index.html", {"request": request, "result": html_result})


# @app.post("/research", response_class=HTMLResponse)
# async def research(request: Request, query: str = Form(...)):
#     result = await run_query(query)
#     return templates.TemplateResponse("index.html", {
#         "request": request,
#         "timeline": result["timeline"],
#         "final": result["final"]
#     })








