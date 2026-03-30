from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from github import Github, GithubException
import json
import re
import base64
import ollama

app = FastAPI(title="GitMind API (Ollama)", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_MODEL = "llama3"

# ─── Pydantic Models ───────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    instruction: str
    github_token: str
    ollama_model: Optional[str] = DEFAULT_MODEL

class RepoRequest(BaseModel):
    github_token: str
    repo_name: str
    description: Optional[str] = ""
    private: Optional[bool] = False
    ollama_model: Optional[str] = DEFAULT_MODEL

class DeleteRepoRequest(BaseModel):
    github_token: str
    repo_name: str

class AddFileRequest(BaseModel):
    github_token: str
    repo_name: str
    file_path: str
    content: str
    commit_message: Optional[str] = ""
    ollama_model: Optional[str] = DEFAULT_MODEL

class InsightRequest(BaseModel):
    github_token: str
    repo_name: str
    ollama_model: Optional[str] = DEFAULT_MODEL

class PRDraftRequest(BaseModel):
    github_token: str
    repo_name: str
    description: str
    ollama_model: Optional[str] = DEFAULT_MODEL

class ReadmeRequest(BaseModel):
    github_token: str
    repo_name: str
    ollama_model: Optional[str] = DEFAULT_MODEL
    extra_context: Optional[str] = ""
    push_to_repo: Optional[bool] = True

# ─── Helpers ───────────────────────────────────────────────────────────────────

def get_github(token: str) -> Github:
    return Github(token)

def ask_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"].strip()

def clean_json(raw: str) -> dict:
    raw = re.sub(r"```json|```", "", raw).strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]
    return json.loads(raw)

def parse_intent(text: str) -> str:
    text = text.lower()
    if "create" in text and "repo" in text:
        return "create_repo"
    elif "delete" in text and "repo" in text:
        return "delete_repo"
    elif "add file" in text or "push file" in text or "upload" in text:
        return "add_file"
    elif "readme" in text:
        return "generate_readme"
    elif "list" in text and "repo" in text:
        return "list_repos"
    elif "insight" in text or "analy" in text:
        return "insight"
    elif "pr" in text or "pull request" in text:
        return "pr_draft"
    else:
        return "chat"

# ─── Root ──────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "GitMind (Ollama) running", "version": "2.0.0"}

# ─── Ollama Status ─────────────────────────────────────────────────────────────

@app.get("/ollama/status")
def ollama_status():
    try:
        models_resp = ollama.list()
        raw_models = models_resp.get("models", []) if isinstance(models_resp, dict) else []
        model_names = [m.get("name", str(m)) if isinstance(m, dict) else str(m) for m in raw_models]
        return {"status": "ok", "models": model_names, "model": DEFAULT_MODEL}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama not reachable: {str(e)}")

# ─── Agent ─────────────────────────────────────────────────────────────────────

@app.post("/agent")
async def agent(req: AgentRequest):
    try:
        gh = get_github(req.github_token)
        user = gh.get_user()
        username = user.login
        model = req.ollama_model or DEFAULT_MODEL
        intent = parse_intent(req.instruction)

        prompt = f"""You are GitMind AI, a GitHub assistant.
User instruction: "{req.instruction}"
Detected intent: {intent}

Return ONLY valid JSON, no explanation, no markdown fences:
{{
  "action": "{intent}",
  "repo_name": "<repo name if mentioned, else empty string>",
  "file_path": "<file path if mentioned, else empty string>",
  "file_content": "<file content if needed, else empty string>",
  "description": "<repo description if needed, else empty string>",
  "private": false
}}"""

        raw = ask_ollama(prompt, model=model)
        try:
            parsed = clean_json(raw)
        except Exception:
            parsed = {"action": intent, "repo_name": "", "file_path": "",
                      "file_content": "", "description": "", "private": False}

        action = parsed.get("action", intent)
        result = {"action": action, "status": "ok", "details": {}}

        if action == "create_repo":
            repo_name = parsed.get("repo_name") or "gitmind-repo"
            repo = user.create_repo(
                repo_name,
                description=parsed.get("description", ""),
                private=parsed.get("private", False),
                auto_init=True
            )
            result["details"] = {
                "message": f"Repository '{repo.full_name}' created!",
                "repo": repo.full_name,
                "url": repo.html_url
            }

        elif action == "delete_repo":
            repo_name = parsed.get("repo_name", "")
            if not repo_name:
                raise HTTPException(status_code=400, detail="Could not determine repo name.")
            repo = gh.get_repo(f"{username}/{repo_name}")
            repo.delete()
            result["details"] = {"message": f"Deleted '{repo_name}'."}

        elif action == "add_file":
            repo_name = parsed.get("repo_name", "")
            if not repo_name:
                raise HTTPException(status_code=400, detail="Could not determine repo name.")
            repo = gh.get_repo(f"{username}/{repo_name}")
            file_path = parsed.get("file_path", "README.md")
            content = parsed.get("file_content", "# GitMind File")
            commit_msg = ask_ollama(
                f"Write a concise git commit message (one line, max 72 chars) for adding '{file_path}'.",
                model=model
            ).strip().strip('"').strip("'").split("\n")[0]
            try:
                existing = repo.get_contents(file_path)
                repo.update_file(file_path, commit_msg, content, existing.sha)
                action_word = "updated"
            except Exception:
                repo.create_file(file_path, commit_msg, content)
                action_word = "created"
            result["details"] = {"message": f"File '{file_path}' {action_word}.", "action": action_word, "commit": commit_msg}

        elif action == "list_repos":
            repos = list(user.get_repos())
            result["details"] = {
                "message": f"Found {len(repos)} repositories.",
                "repos": [
                    {"name": r.name, "url": r.html_url, "private": r.private,
                     "language": r.language, "stars": r.stargazers_count,
                     "updated": r.updated_at.strftime("%Y-%m-%d") if r.updated_at else "—"}
                    for r in repos
                ]
            }

        elif action == "generate_readme":
            repo_name = parsed.get("repo_name", "")
            if not repo_name:
                raise HTTPException(status_code=400, detail="Could not determine repo name.")
            repo = gh.get_repo(f"{username}/{repo_name}")
            try:
                tree = repo.get_git_tree(repo.default_branch, recursive=True)
                file_list = [f.path for f in tree.tree if f.type == "blob"][:40]
            except Exception:
                file_list = []
            readme_content = ask_ollama(
                f"Write a professional README.md for GitHub repo '{repo_name}'.\n"
                f"Files: {', '.join(file_list) or 'unknown'}\n"
                "Include: title, badges, description, features, installation, usage, tech stack, contributing, license.",
                model=model
            )
            try:
                existing = repo.get_contents("README.md")
                repo.update_file("README.md", "docs: update README via GitMind", readme_content, existing.sha)
            except Exception:
                repo.create_file("README.md", "docs: add README via GitMind", readme_content)
            result["details"] = {
                "message": f"README pushed to '{repo_name}'.",
                "readme": readme_content,
                "url": f"{repo.html_url}/blob/{repo.default_branch}/README.md",
                "pushed": True
            }

        elif action == "insight":
            repo_name = parsed.get("repo_name", "")
            if not repo_name:
                raise HTTPException(status_code=400, detail="Repo name required.")
            repo = gh.get_repo(f"{username}/{repo_name}")
            try:
                commit_msgs = [c.commit.message.split("\n")[0] for c in list(repo.get_commits()[:10])]
            except Exception:
                commit_msgs = []
            summary = ask_ollama(
                f"Analyze GitHub repo '{repo_name}'. Language: {repo.language}. "
                f"Stars: {repo.stargazers_count}, Forks: {repo.forks_count}, Issues: {repo.open_issues_count}. "
                f"Recent commits: {commit_msgs}. Give code health, patterns, suggestions, next steps.",
                model=model
            )
            result["action"] = "insight"
            result["stars"] = repo.stargazers_count
            result["forks"] = repo.forks_count
            result["open_issues"] = repo.open_issues_count
            result["details"] = {"repo": repo_name, "summary": summary, "message": f"Insights for '{repo_name}'."}

        elif action == "pr_draft":
            pr_text = ask_ollama(
                f"Write a professional GitHub PR description for: {req.instruction}\n"
                "Include: ## Summary, ## Changes Made, ## Testing, ## Breaking Changes. Use Markdown.",
                model=model
            )
            result["action"] = "pr_draft"
            result["details"] = {"pr_draft": pr_text, "message": "PR draft generated."}

        else:
            result["details"] = {"message": ask_ollama(req.instruction, model=model)}

        return result

    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e.data) if hasattr(e, "data") else str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Repos: Create ─────────────────────────────────────────────────────────────

@app.post("/repos/create")
def create_repo(req: RepoRequest):
    try:
        gh = get_github(req.github_token)
        user = gh.get_user()
        repo = user.create_repo(
            req.repo_name,
            description=req.description or "",
            private=req.private or False,
            auto_init=True
        )
        return {"repo": repo.full_name, "url": repo.html_url}
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e.data) if hasattr(e, "data") else str(e))

# ─── Repos: Delete ─────────────────────────────────────────────────────────────

@app.post("/repos/delete")
def delete_repo(req: DeleteRepoRequest):
    try:
        gh = get_github(req.github_token)
        user = gh.get_user()
        repo = gh.get_repo(f"{user.login}/{req.repo_name}")
        repo.delete()
        return {"deleted": req.repo_name}
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e.data) if hasattr(e, "data") else str(e))

# ─── Repos: List ───────────────────────────────────────────────────────────────

@app.post("/repos/list")
def list_repos(req: RepoRequest):
    try:
        gh = get_github(req.github_token)
        user = gh.get_user()
        repos = list(user.get_repos())
        return {
            "repos": [
                {
                    "name": r.name,
                    "url": r.html_url,
                    "private": r.private,
                    "language": r.language,
                    "stars": r.stargazers_count,
                    "updated": r.updated_at.strftime("%Y-%m-%d") if r.updated_at else "—"
                }
                for r in repos
            ]
        }
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e.data) if hasattr(e, "data") else str(e))

# ─── Repos: Insight ────────────────────────────────────────────────────────────

@app.post("/repos/insight")
def repo_insight(req: InsightRequest):
    try:
        gh = get_github(req.github_token)
        user = gh.get_user()
        repo = gh.get_repo(f"{user.login}/{req.repo_name}")
        model = req.ollama_model or DEFAULT_MODEL
        try:
            commit_msgs = [c.commit.message.split("\n")[0] for c in list(repo.get_commits()[:10])]
        except Exception:
            commit_msgs = []
        summary = ask_ollama(
            f"Analyze GitHub repo '{req.repo_name}'. Language: {repo.language}. "
            f"Stars: {repo.stargazers_count}, Forks: {repo.forks_count}, Issues: {repo.open_issues_count}. "
            f"Recent commits: {commit_msgs}. Give code health, activity summary, suggestions, next steps.",
            model=model
        )
        return {
            "repo": req.repo_name,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "summary": summary
        }
    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e.data) if hasattr(e, "data") else str(e))

# ─── Files: Add / Update (text) ────────────────────────────────────────────────

@app.post("/files/add")
def add_file(req: AddFileRequest):
    try:
        gh = get_github(req.github_token)
        user = gh.get_user()
        username = user.login
        model = req.ollama_model or DEFAULT_MODEL

        repo = gh.get_repo(f"{username}/{req.repo_name}")

        if req.commit_message and req.commit_message.strip():
            commit_msg = req.commit_message.strip()
        else:
            commit_msg = ask_ollama(
                f"Write a concise git commit message (one line, max 72 chars) for adding or updating '{req.file_path}'.",
                model=model
            ).strip().strip('"').strip("'").split("\n")[0]

        try:
            existing = repo.get_contents(req.file_path)
            repo.update_file(req.file_path, commit_msg, req.content, existing.sha)
            action = "updated"
        except GithubException:
            repo.create_file(req.file_path, commit_msg, req.content)
            action = "created"

        return {"status": "done", "action": action, "commit": commit_msg}

    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e.data) if hasattr(e, "data") else str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Files: Upload Binary (images, datasets, any file) ────────────────────────

@app.post("/files/upload")
async def upload_binary_file(
    file: UploadFile = File(...),
    github_token: str = Form(...),
    repo_name: str = Form(...),
    file_path: str = Form(...),
    commit_message: str = Form(""),
    ollama_model: str = Form(DEFAULT_MODEL),
):
    """
    Upload any file (binary or text) to a GitHub repo using base64 encoding.
    Supports images (.png, .jpg, .gif, .svg), datasets (.csv, .json, .parquet, .xlsx),
    PDFs, zips, and any other file type.
    GitHub's file size limit via API is 100 MB.
    """
    try:
        gh = get_github(github_token)
        user = gh.get_user()
        username = user.login
        model = ollama_model or DEFAULT_MODEL

        # Read raw bytes
        file_bytes = await file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)

        if file_size_mb > 100:
            raise HTTPException(
                status_code=400,
                detail=f"File too large ({file_size_mb:.1f} MB). GitHub API limit is 100 MB."
            )

        # Base64 encode for GitHub API
        encoded_content = base64.b64encode(file_bytes).decode("utf-8")

        # Generate commit message if not provided
        if commit_message and commit_message.strip():
            commit_msg = commit_message.strip()
        else:
            commit_msg = ask_ollama(
                f"Write a concise git commit message (one line, max 72 chars) for uploading '{file_path}' "
                f"({file_size_mb:.2f} MB, type: {file.content_type or 'unknown'}).",
                model=model
            ).strip().strip('"').strip("'").split("\n")[0]

        repo = gh.get_repo(f"{username}/{repo_name}")

        # Use the GitHub API directly with base64 content for binary files
        try:
            existing = repo.get_contents(file_path)
            # update_file accepts base64 content directly via the underlying API
            repo.update_file(
                file_path,
                commit_msg,
                file_bytes,          # PyGithub handles encoding internally
                existing.sha
            )
            action = "updated"
        except GithubException:
            repo.create_file(
                file_path,
                commit_msg,
                file_bytes           # PyGithub handles encoding internally
            )
            action = "created"

        file_url = f"{repo.html_url}/blob/{repo.default_branch}/{file_path}"

        return {
            "status": "done",
            "action": action,
            "commit": commit_msg,
            "file_path": file_path,
            "file_size_mb": round(file_size_mb, 3),
            "url": file_url
        }

    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e.data) if hasattr(e, "data") else str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── PR Draft ──────────────────────────────────────────────────────────────────

@app.post("/pr/draft")
def pr_draft(req: PRDraftRequest):
    model = req.ollama_model or DEFAULT_MODEL
    pr_text = ask_ollama(
        f"Write a professional GitHub PR description for repo '{req.repo_name}'.\n"
        f"Developer's changes: {req.description}\n"
        "Sections: ## Summary, ## Changes Made, ## Testing, ## Breaking Changes. Use Markdown.",
        model=model
    )
    return {"pr_draft": pr_text}

# ─── README Generator ──────────────────────────────────────────────────────────

@app.post("/readme/generate")
def generate_readme(req: ReadmeRequest):
    try:
        gh = get_github(req.github_token)
        user = gh.get_user()
        username = user.login

        repo = gh.get_repo(f"{username}/{req.repo_name}")
        model = req.ollama_model or DEFAULT_MODEL

        try:
            tree = repo.get_git_tree(repo.default_branch, recursive=True)
            all_files = [f.path for f in tree.tree if f.type == "blob"]
            file_list = all_files[:50]
            file_count = len(all_files)
        except Exception:
            file_list = []
            file_count = 0

        key_files = ["package.json", "requirements.txt", "setup.py", "Cargo.toml",
                     "go.mod", "pom.xml", "build.gradle", "pyproject.toml"]
        dep_info = {}
        for kf in key_files:
            if kf in file_list:
                try:
                    fc = repo.get_contents(kf)
                    dep_info[kf] = fc.decoded_content.decode("utf-8", errors="ignore")[:800]
                except Exception:
                    pass

        try:
            commit_msgs = [c.commit.message.split("\n")[0] for c in list(repo.get_commits()[:8])]
        except Exception:
            commit_msgs = []

        prompt = f"""Write a comprehensive, professional README.md for the GitHub repository '{req.repo_name}'.

Repository details:
- Language: {repo.language or 'unknown'}
- Description: {repo.description or 'not provided'}
- Stars: {repo.stargazers_count} | Forks: {repo.forks_count}
- File structure ({file_count} files total): {', '.join(file_list[:30])}
- Recent commits: {commit_msgs}
- Dependency files: {json.dumps(dep_info, indent=2) if dep_info else 'none found'}
{('- Extra context: ' + req.extra_context) if req.extra_context else ''}

Write a world-class README.md with:
1. Project title + badges
2. Short tagline / description
3. Features (bullet list)
4. Quick Start / Installation
5. Usage with code examples
6. Project Structure
7. Tech Stack
8. Contributing
9. License

Use proper Markdown."""

        readme_content = ask_ollama(prompt, model=model)

        pushed = False
        url = ""
        if req.push_to_repo:
            try:
                try:
                    existing = repo.get_contents("README.md")
                    repo.update_file(
                        "README.md",
                        "docs: update README via GitMind AI",
                        readme_content,
                        existing.sha
                    )
                except GithubException:
                    repo.create_file(
                        "README.md",
                        "docs: add README via GitMind AI",
                        readme_content
                    )
                pushed = True
                url = f"{repo.html_url}/blob/{repo.default_branch}/README.md"
            except Exception:
                pushed = False

        return {
            "readme": readme_content,
            "pushed": pushed,
            "url": url,
            "language": repo.language or "—",
            "file_count": file_count
        }

    except GithubException as e:
        raise HTTPException(status_code=400, detail=str(e.data) if hasattr(e, "data") else str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Voice Transcribe ──────────────────────────────────────────────────────────

@app.post("/voice/transcribe")
async def voice_transcribe(
    audio: UploadFile = File(...),
    ollama_model: str = Form(DEFAULT_MODEL)
):
    try:
        audio_bytes = await audio.read()
        try:
            import whisper
            import tempfile, os
            suffix = "." + (audio.filename.split(".")[-1] if "." in audio.filename else "webm")
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            wmodel = whisper.load_model("base")
            result = wmodel.transcribe(tmp_path)
            os.unlink(tmp_path)
            return {"transcript": result["text"].strip()}
        except ImportError:
            pass
        return {
            "transcript": "",
            "error": "Install openai-whisper to enable transcription: pip install openai-whisper"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))