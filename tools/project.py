"""Offline checks and deterministic example; does not spawn or call an LLM."""
import argparse
import json
import sys
import tomllib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from orchestration.protocol import read_json, validate_task, validate_result
from competition.demo.pipeline import run

def check(root=ROOT):
    root = Path(root)
    config = tomllib.loads((root/".codex/config.toml").read_text(encoding="utf-8"))
    legacy = "max_threads" in config.get("agents",{})
    if not legacy and config != {"agents":{"enabled":True,"max_concurrent_threads_per_session":3}}:
        raise ValueError("unexpected project config")
    routes = read_json(root/"orchestration/routes.json")["routes"]
    if set(routes) != {"prepare","solve","review"}:
        raise ValueError("missing routes")
    count = set()
    core_skills = set()
    conditional_by_mode = {}
    for mode, route in routes.items():
        agent = tomllib.loads((root/(".codex/agents/"+route["agent"]+".toml")).read_text(encoding="utf-8"))
        required = {"developer_instructions"} if legacy else {"name","description","developer_instructions"}
        if not required.issubset(agent) or set(agent)-required-{"sandbox_mode"}:
            raise ValueError("unsupported project agent fields")
        if not legacy and (agent["name"] != route["agent"] or not agent["description"]):
            raise ValueError("role identity mismatch")
        if legacy:
            declaration=config["agents"].get(route["agent"],{})
            if config["agents"].get("max_threads") != 3 or declaration.get("config_file") != "agents/"+route["agent"]+".toml" or not declaration.get("description"):
                raise ValueError("invalid legacy declaration")
        if route["prompt"] not in agent["developer_instructions"]:
            raise ValueError("missing prompt reference")
        prompt = root/route["prompt"]
        if not prompt.is_file() or not prompt.read_text(encoding="utf-8").strip():
            raise ValueError("missing prompt")
        conditional = route.get("conditional_skills", [])
        if not isinstance(conditional,list) or any(not isinstance(item,dict) or
                set(item) != {"skill","when"} or not isinstance(item["skill"],str) or
                not item["skill"] or not isinstance(item["when"],str) or
                not item["when"].strip() for item in conditional):
            raise ValueError("invalid conditional skill routing")
        conditional_names = [item["skill"] for item in conditional]
        if len(conditional_names) != len(set(conditional_names)) or set(conditional_names) & set(route["skills"]):
            raise ValueError("duplicate or unconditional skill routing")
        conditional_by_mode[mode] = set(conditional_names)
        core_skills.update(route["skills"])
        for skill in [*route["skills"],*conditional_names]:
            text = (root/f".agents/skills/{skill}/SKILL.md").read_text(encoding="utf-8")
            if not text.startswith("---\n") or text.count("---") < 2:
                raise ValueError("skill front matter missing")
            front = text.split("---",2)[1]
            if f"name: {skill}\n" not in front or "description:" not in front:
                raise ValueError("skill metadata missing")
            if "docs/protocol.md" not in text or "## 输出与验收" not in text:
                raise ValueError("skill contract missing")
            count.add(skill)
    expected_core = {"problem-analysis","data-processing","literature-evidence","model-selection",
                     "mathematical-modeling","algorithm-implementation","experiment-analysis",
                     "visualization","paper-writing"}
    expected_conditional = {"prepare":set(),"solve":{"eeg-c-task"},
                            "review":{"independent-validation","submission-audit"}}
    if core_skills != expected_core or conditional_by_mode != expected_conditional:
        raise ValueError("unexpected project skill routing")
    discovered = {path.parent.name for path in (root/".agents/skills").glob("*/SKILL.md")}
    if count != discovered:
        raise ValueError("unrouted or missing project skill: "+repr(sorted(count ^ discovered)))
    if any("literature-evidence" not in routes[mode]["skills"] for mode in routes):
        raise ValueError("literature evidence must be routed to every role")
    for f in ("AGENTS.md","docs/protocol.md","requirements.txt"):
        if not (root/f).is_file():
            raise ValueError("missing project file")
    for name,minimum in (("researcher",3000),("solver",8000)):
        if len((root/f"prompts/{name}.md").read_text(encoding="utf-8")) < minimum:
            raise ValueError("full prompt was truncated")
    return {"status":"passed","config_mode":"legacy" if legacy else "current","routes":3,"skills":len(count),"scope":"static project contract; not native Codex discovery"}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command",required=True)
    sub.add_parser("check")
    demo = sub.add_parser("demo")
    demo.add_argument("--run-id",default="demo")
    demo.add_argument("--config",default="competition/demo/config.json")
    route = sub.add_parser("route")
    route.add_argument("--task",required=True)
    route.add_argument("--completed",nargs="*",default=[])
    val = sub.add_parser("validate")
    val.add_argument("--task",required=True)
    val.add_argument("--result",required=True)
    val.add_argument("--completed",nargs="*",default=[])
    args = parser.parse_args()
    try:
        if args.command == "check":
            output = check()
        elif args.command == "demo":
            output = run(ROOT,args.run_id,args.config)
        elif args.command == "route":
            output = {"execution":"dry-run; no LLM",**validate_task(ROOT,read_json(ROOT/args.task),args.completed)}
        else:
            validate_result(ROOT,read_json(ROOT/args.task),read_json(ROOT/args.result),args.completed)
            output = {"status":"passed"}
        print(json.dumps(output,ensure_ascii=False,indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as error:
        print("ERROR: "+str(error),file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
