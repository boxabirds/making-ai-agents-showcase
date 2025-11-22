import os
from pathlib import Path

import tempfile
from fastapi import FastAPI, HTTPException, Request, Form
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from dotenv import load_dotenv
from common.utils import configure_code_base_source, read_prompt_file

from infinite_scalability.orchestrator import run_pipeline
from infinite_scalability.store import Store
from infinite_scalability.validation import validate_summary

load_dotenv(".env.test")

app = FastAPI()
templates = Jinja2Templates(directory="web/templates")


class BaseRequest(BaseModel):
    store_path: str | None = None
    persist_store: bool = True


class DraftRequest(BaseRequest):
    prompt_path: str | None = None
    prompt_text: str | None = None
    repo: str | None = None
    directory: str | None = None


class IngestRequest(BaseRequest):
    directory: str | None = None
    repo: str | None = None
    ingest_file_limit: int | None = None


class SummariesRequest(BaseRequest):
    directory: str | None = None
    repo: str | None = None


class RetrievalRequest(BaseRequest):
    directory: str | None = None
    repo: str | None = None
    query: str = "main"


def _ensure_store(req: BaseRequest) -> tuple[Store, Path]:
    if req.store_path:
        store_path = Path(req.store_path)
        store_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        fd, tmp = tempfile.mkstemp(prefix="tech-writer-", suffix=".db")
        store_path = Path(tmp)
    store = Store(db_path=store_path, persist=req.persist_store)
    return store, store_path


@app.post("/ingest")
def ingest(req: IngestRequest):
    store, store_path = _ensure_store(req)
    try:
        if req.ingest_file_limit:
            os.environ["INGEST_FILE_LIMIT"] = str(req.ingest_file_limit)
        from infinite_scalability.ingest import ingest_repo

        repo_url, directory_path = configure_code_base_source(req.repo, req.directory, cache_dir="~/.cache/github")
        ingest_repo(Path(directory_path), store)
        cur = store.conn.execute("SELECT COUNT(*) FROM files")
        files = cur.fetchone()[0]
        cur = store.conn.execute("SELECT COUNT(*) FROM chunks")
        chunks = cur.fetchone()[0]
        cur = store.conn.execute("SELECT COUNT(*) FROM symbols")
        symbols = cur.fetchone()[0]
        return {"files": files, "chunks": chunks, "symbols": symbols, "store_path": str(store_path)}
    finally:
        store.close()


@app.post("/summaries")
def summaries(req: SummariesRequest):
    store, store_path = _ensure_store(req)
    try:
        from infinite_scalability.summarize import summarize_all_files, summarize_module
        from infinite_scalability.validation import validate_summary

        repo_url, directory_path = configure_code_base_source(req.repo, req.directory, cache_dir="~/.cache/github")

        summaries = summarize_all_files(store)
        for s in summaries:
            validate_summary(store, s)
        module_summary = summarize_module(store, directory_path, summaries)
        validate_summary(store, module_summary)
        return {"file_summaries": len(summaries), "module_summary": module_summary.text, "store_path": str(store_path)}
    finally:
        store.close()


@app.post("/retrieval")
def retrieval(req: RetrievalRequest):
    store, store_path = _ensure_store(req)
    try:
        from infinite_scalability.retrieval import retrieve_context
        repo_url, directory_path = configure_code_base_source(req.repo, req.directory, cache_dir="~/.cache/github")
        ctx = retrieve_context(store, req.query)
        return {
            "chunks": len(ctx.chunks),
            "summaries": len(ctx.summaries),
            "symbols": len(ctx.symbols),
            "edges": len(ctx.edges),
            "store_path": str(store_path),
        }
    finally:
        store.close()


@app.post("/draft")
def draft(req: DraftRequest):
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    store, store_path = _ensure_store(req)
    try:
        if req.prompt_text:
            prompt = req.prompt_text
        else:
            try:
                with open(req.prompt_path, "r", encoding="utf-8") as f:
                    prompt = f.read().strip()
            except OSError:
                raise HTTPException(status_code=400, detail="Prompt file not found")

        repo_url, directory_path = configure_code_base_source(req.repo, req.directory, cache_dir="~/.cache/github")
        report, rv = run_pipeline(Path(directory_path), prompt, store, gate=None)
        return {"report": report, "report_version": rv.id, "store_path": str(store_path)}
    finally:
        store.close()


# UI pages
@app.get("/", response_class=HTMLResponse)
def ui_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Harness"})


@app.get("/ui/ingest", response_class=HTMLResponse)
def ui_ingest_form(request: Request):
    fields = [
        {"label": "Store Path", "name": "store_path", "type": "text", "help": "Path to SQLite store", "required": True},
        {"label": "Directory", "name": "directory", "type": "text", "help": "Directory to ingest", "required": True},
        {"label": "File Limit", "name": "ingest_file_limit", "type": "number", "help": "Optional cap on files", "required": False},
    ]
    return templates.TemplateResponse("form.html", {"request": request, "title": "Ingest", "heading": "Task 2: Ingest", "action": "/ui/ingest", "fields": fields, "submit_label": "Ingest", "result": None})


@app.post("/ui/ingest", response_class=HTMLResponse)
def ui_ingest(request: Request, store_path: str = Form(""), directory: str = Form(""), ingest_file_limit: str = Form(""), repo: str = Form("")):
    req = IngestRequest(
        store_path=store_path or None,
        directory=directory or None,
        repo=repo or None,
        ingest_file_limit=int(ingest_file_limit) if ingest_file_limit else None,
    )
    resp = ingest(req)
    return templates.TemplateResponse("form.html", {"request": request, "title": "Ingest", "heading": "Task 2: Ingest", "action": "/ui/ingest", "fields": [
        {"label": "Store Path", "name": "store_path", "type": "text", "help": "Optional path to SQLite store (blank => temp)", "required": False, "value": resp.get("store_path")},
        {"label": "Repo URL", "name": "repo", "type": "text", "help": "Optional GitHub repo (e.g., https://github.com/owner/repo)", "required": False, "value": repo},
        {"label": "Directory", "name": "directory", "type": "text", "help": "Local directory (if no repo)", "required": False, "value": directory},
        {"label": "File Limit", "name": "ingest_file_limit", "type": "number", "help": "Optional cap on files", "required": False, "value": ingest_file_limit},
    ], "submit_label": "Ingest", "result": resp})


@app.get("/ui/summaries", response_class=HTMLResponse)
def ui_summaries_form(request: Request):
    fields = [
        {"label": "Store Path", "name": "store_path", "type": "text", "help": "Optional path to SQLite store (blank => temp)", "required": False},
        {"label": "Repo URL", "name": "repo", "type": "text", "help": "Optional GitHub repo", "required": False},
        {"label": "Directory", "name": "directory", "type": "text", "help": "Local directory (if no repo)", "required": False},
    ]
    return templates.TemplateResponse("form.html", {"request": request, "title": "Summaries", "heading": "Task 3: Summaries", "action": "/ui/summaries", "fields": fields, "submit_label": "Summarize", "result": None})


@app.post("/ui/summaries", response_class=HTMLResponse)
def ui_summaries(request: Request, store_path: str = Form(""), directory: str = Form(""), repo: str = Form("")):
    req = SummariesRequest(store_path=store_path or None, directory=directory or None, repo=repo or None)
    resp = summaries(req)
    return templates.TemplateResponse("form.html", {"request": request, "title": "Summaries", "heading": "Task 3: Summaries", "action": "/ui/summaries", "fields": [
        {"label": "Store Path", "name": "store_path", "type": "text", "help": "Optional path to SQLite store (blank => temp)", "required": False, "value": resp.get("store_path")},
        {"label": "Repo URL", "name": "repo", "type": "text", "help": "Optional GitHub repo", "required": False, "value": repo},
        {"label": "Directory", "name": "directory", "type": "text", "help": "Local directory (if no repo)", "required": False, "value": directory},
    ], "submit_label": "Summarize", "result": resp})


@app.get("/ui/retrieval", response_class=HTMLResponse)
def ui_retrieval_form(request: Request):
    fields = [
        {"label": "Store Path", "name": "store_path", "type": "text", "help": "Optional path to SQLite store (blank => temp)", "required": False},
        {"label": "Repo URL", "name": "repo", "type": "text", "help": "Optional GitHub repo", "required": False},
        {"label": "Directory", "name": "directory", "type": "text", "help": "Local directory (if no repo)", "required": False},
        {"label": "Query", "name": "query", "type": "text", "help": "Query/topic", "required": True, "value": "main"},
    ]
    return templates.TemplateResponse("form.html", {"request": request, "title": "Retrieval", "heading": "Task 4: Retrieval", "action": "/ui/retrieval", "fields": fields, "submit_label": "Retrieve", "result": None})


@app.post("/ui/retrieval", response_class=HTMLResponse)
def ui_retrieval(request: Request, store_path: str = Form(""), directory: str = Form(""), repo: str = Form(""), query: str = Form(...)):
    req = RetrievalRequest(store_path=store_path or None, directory=directory or None, repo=repo or None, query=query)
    resp = retrieval(req)
    return templates.TemplateResponse("form.html", {"request": request, "title": "Retrieval", "heading": "Task 4: Retrieval", "action": "/ui/retrieval", "fields": [
        {"label": "Store Path", "name": "store_path", "type": "text", "help": "Optional path to SQLite store (blank => temp)", "required": False, "value": resp.get("store_path")},
        {"label": "Repo URL", "name": "repo", "type": "text", "help": "Optional GitHub repo", "required": False, "value": repo},
        {"label": "Directory", "name": "directory", "type": "text", "help": "Local directory (if no repo)", "required": False, "value": directory},
        {"label": "Query", "name": "query", "type": "text", "help": "Query/topic", "required": True, "value": query},
    ], "submit_label": "Retrieve", "result": resp})


@app.get("/ui/draft", response_class=HTMLResponse)
def ui_draft_form(request: Request):
    fields = [
        {"label": "Store Path", "name": "store_path", "type": "text", "help": "Optional path to SQLite store (blank => temp)", "required": False},
        {"label": "Repo URL", "name": "repo", "type": "text", "help": "Optional GitHub repo", "required": False},
        {"label": "Directory", "name": "directory", "type": "text", "help": "Local directory (if no repo)", "required": False},
        {"label": "Prompt Path", "name": "prompt_path", "type": "text", "help": "Path to prompt file", "required": False},
        {"label": "Prompt Text", "name": "prompt_text", "type": "text", "help": "Inline prompt text", "required": False},
    ]
    return templates.TemplateResponse("form.html", {"request": request, "title": "Draft", "heading": "Task 5: Draft", "action": "/ui/draft", "fields": fields, "submit_label": "Draft", "result": None})


@app.post("/ui/draft", response_class=HTMLResponse)
def ui_draft(request: Request, store_path: str = Form(""), directory: str = Form(""), repo: str = Form(""), prompt_path: str = Form(""), prompt_text: str = Form("")):
    req = DraftRequest(store_path=store_path or None, directory=directory or None, repo=repo or None, prompt_path=prompt_path or None, prompt_text=prompt_text or None)
    resp = draft(req)
    return templates.TemplateResponse("form.html", {"request": request, "title": "Draft", "heading": "Task 5: Draft", "action": "/ui/draft", "fields": [
        {"label": "Store Path", "name": "store_path", "type": "text", "help": "Optional path to SQLite store (blank => temp)", "required": False, "value": resp.get("store_path")},
        {"label": "Repo URL", "name": "repo", "type": "text", "help": "Optional GitHub repo", "required": False, "value": repo},
        {"label": "Directory", "name": "directory", "type": "text", "help": "Local directory (if no repo)", "required": False, "value": directory},
        {"label": "Prompt Path", "name": "prompt_path", "type": "text", "help": "Path to prompt file", "required": False, "value": prompt_path},
        {"label": "Prompt Text", "name": "prompt_text", "type": "text", "help": "Inline prompt text", "required": False, "value": prompt_text},
    ], "submit_label": "Draft", "result": resp})
