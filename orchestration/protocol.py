"""Project-specific contract validation, not a general JSON Schema implementation."""
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

TASK_KEYS = {"schema_version","task_id","mode","inputs","depends_on","output_dir","acceptance","budget_minutes"}
RESULT_KEYS = {"schema_version","task_id","agent","status","summary","artifacts","commands","limitations"}
ID = re.compile(r"[A-Za-z0-9_-]+")
HEX = re.compile(r"[0-9a-f]{64}")

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def safe_path(root, value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("invalid relative path")
    pp = PurePosixPath(value)
    if pp.is_absolute() or ".." in pp.parts or "." == value:
        raise ValueError("path traversal or absolute path")
    root = Path(root).resolve()
    target = (root / value).resolve()
    if not target.is_relative_to(root):
        raise ValueError("resolved path escapes project")
    return target

def string_list(value, nonempty=False):
    if not isinstance(value,list) or (nonempty and not value):
        raise ValueError("expected list")
    if any(not isinstance(x,str) or not x.strip() for x in value):
        raise ValueError("expected nonempty strings")

def validate_task(root, task, completed=(), allow_unavailable=False):
    if not isinstance(task,dict) or set(task) != TASK_KEYS:
        raise ValueError("task fields do not match protocol")
    if type(task["schema_version"]) is not int or task["schema_version"] != 1:
        raise ValueError("unsupported schema_version")
    if not isinstance(task["task_id"],str) or not ID.fullmatch(task["task_id"]):
        raise ValueError("invalid task_id")
    routes = read_json(Path(root)/"orchestration/routes.json")["routes"]
    if not isinstance(task["mode"],str) or task["mode"] not in routes:
        raise ValueError("unknown mode")
    route = routes[task["mode"]]
    expected = route["output_base"]+"/"+task["task_id"]
    if task["output_dir"] != expected:
        raise ValueError("wrong output ownership")
    safe_path(root,task["output_dir"])
    for key in ("inputs","depends_on","acceptance"):
        string_list(task[key], nonempty=(key in ("inputs","acceptance")))
    if len(set(task["depends_on"])) != len(task["depends_on"]):
        raise ValueError("duplicate dependencies")
    if any(not ID.fullmatch(x) or x == task["task_id"] for x in task["depends_on"]):
        raise ValueError("invalid dependency")
    if not allow_unavailable and not set(task["depends_on"]).issubset(set(completed)):
        raise ValueError("dependencies are not completed")
    for value in task["inputs"]:
        path = safe_path(root,value)
        if not allow_unavailable and not path.is_file():
            raise ValueError("missing input: "+value)
    if type(task["budget_minutes"]) is not int or task["budget_minutes"] <= 0:
        raise ValueError("invalid budget")
    return route

def validate_result(root, task, result, completed=()):
    route = validate_task(root,task,completed,allow_unavailable=isinstance(result,dict) and result.get("status")=="blocked")
    if not isinstance(result,dict) or set(result) != RESULT_KEYS:
        raise ValueError("result fields do not match protocol")
    if type(result["schema_version"]) is not int or result["schema_version"] != 1:
        raise ValueError("unsupported result version")
    if result["task_id"] != task["task_id"] or result["agent"] != route["agent"]:
        raise ValueError("result identity mismatch")
    if result["status"] not in ("completed","partial","blocked","failed"):
        raise ValueError("unknown status")
    if not isinstance(result["summary"],str) or not result["summary"].strip():
        raise ValueError("missing summary")
    for key in ("commands","limitations"):
        string_list(result[key])
    if result["status"] != "completed" and not result["limitations"]:
        raise ValueError("incomplete result needs limitations")
    arts = result["artifacts"]
    if not isinstance(arts,list) or (result["status"] == "completed" and not arts):
        raise ValueError("missing artifacts")
    out = safe_path(root,task["output_dir"])
    seen = set()
    for artifact in arts:
        if not isinstance(artifact,dict) or set(artifact) != {"path","sha256"}:
            raise ValueError("bad artifact record")
        path = safe_path(root,artifact["path"])
        if not path.is_relative_to(out) or not path.is_file():
            raise ValueError("artifact missing or outside task")
        if path in seen or path == out/"result.json":
            raise ValueError("duplicate or self-referential artifact")
        seen.add(path)
        if not isinstance(artifact["sha256"],str) or not HEX.fullmatch(artifact["sha256"]):
            raise ValueError("invalid hash format")
        if sha256(path) != artifact["sha256"]:
            raise ValueError("artifact hash mismatch")
    return True
