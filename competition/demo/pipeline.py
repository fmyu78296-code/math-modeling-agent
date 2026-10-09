"""Deterministic, non-LLM pipeline for a synthetic forecasting problem."""
import csv
import io
import json
import math
import platform
import sys
from pathlib import Path
from statistics import fmean
from xml.sax.saxutils import escape
from algorithms.linear import fit, predict, metrics
from orchestration.protocol import read_json, safe_path, sha256, validate_task, validate_result

def write_json(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")

def write_csv(path, columns, rows):
    with path.open("w",encoding="utf-8",newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)

def load_data(path):
    with path.open(encoding="utf-8-sig",newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["day","demand"]:
            raise ValueError("expected day,demand columns")
        rows = []
        for row in reader:
            try:
                x,y = float(row["day"]),float(row["demand"])
            except (ValueError,TypeError):
                raise ValueError("missing or nonnumeric data") from None
            if not math.isfinite(x) or not math.isfinite(y) or y < 0:
                raise ValueError("invalid data range")
            rows.append((x,y))
    if any(a[0] >= b[0] for a,b in zip(rows,rows[1:])):
        raise ValueError("days must be unique and increasing")
    return rows

def validate_config(config, count):
    expected = {"seed","train_end","validation_end","candidates","selection_metric","sensitivity_factors"}
    if not isinstance(config,dict) or set(config) != expected:
        raise ValueError("invalid demo configuration fields")
    a,b = config["train_end"],config["validation_end"]
    if type(a) is not int or type(b) is not int or not 2 <= a < b < count:
        raise ValueError("invalid chronological split")
    if type(config["seed"]) is not int:
        raise ValueError("invalid seed")
    if config["selection_metric"] != "rmse":
        raise ValueError("only RMSE selection supported by this demo")
    candidates = config["candidates"]
    if not isinstance(candidates,list) or len(candidates) < 2 or len(set(candidates)) != len(candidates):
        raise ValueError("need distinct baseline and candidate")
    if any(c not in ("mean","last","linear") for c in candidates) or "linear" not in candidates:
        raise ValueError("unsupported candidates")
    factors = config["sensitivity_factors"]
    if not isinstance(factors,list) or not factors or any(type(f) not in (int,float) or not math.isfinite(f) or f <= 0 for f in factors):
        raise ValueError("invalid sensitivity factors")

def evaluate(rows, config):
    validate_config(config,len(rows))
    a,b = config["train_end"],config["validation_end"]
    train, val, test = rows[:a],rows[a:b],rows[b:]
    scores = {}
    for model in config["candidates"]:
        pars = fit(train,model)
        pred = predict(pars,[r[0] for r in val])
        scores[model] = metrics([r[1] for r in val],pred)
    # Stable tie break uses config order; test data cannot influence selection.
    chosen = min(config["candidates"],key=lambda name:scores[name]["rmse"])
    frozen = {name:fit(rows[:b],name) for name in config["candidates"]}
    predictions = {name:predict(p,[r[0] for r in test]) for name,p in frozen.items()}
    final = {name:metrics([r[1] for r in test],predictions[name]) for name in config["candidates"]}
    sensitivity = []
    base = fit(train,"linear")
    xm,ym = fmean(r[0] for r in train),fmean(r[1] for r in train)
    for factor in config["sensitivity_factors"]:
        slope = base["slope"]*factor
        pars = {"intercept":ym-slope*xm,"slope":slope}
        sensitivity.append({"factor":factor,**metrics([r[1] for r in val],predict(pars,[r[0] for r in val]))})
    return {"chosen":chosen,"validation":scores,"test":final,"parameters":frozen,
            "predictions":predictions,"sensitivity":sensitivity,
            "split":{"train_count":a,"validation_count":b-a,"test_count":len(rows)-b}}

def make_svg(rows, xs, ys):
    # Standalone scientific plot with explicit units, ticks, legend and no fabricated intervals.
    width,height = 900,480
    left,right,top,bottom = 75,860,50,405
    xmin,xmax = rows[0][0],rows[-1][0]
    ymin,ymax = 0,max([r[1] for r in rows]+ys)*1.1
    px = lambda x:left+(x-xmin)/(xmax-xmin)*(right-left)
    py = lambda y:bottom-(y-ymin)/(ymax-ymin)*(bottom-top)
    points = lambda data:" ".join(f"{px(x):.2f},{py(y):.2f}" for x,y in data)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="Arial,sans-serif" font-size="14" fill="#18212f">',
             '<text x="75" y="28" font-size="20">Synthetic demand: observations and frozen test forecast</text>',
             f'<path d="M {left} {top} V {bottom} H {right}" fill="none" stroke="#334155"/>']
    for index in range(6):
        y=ymax*index/5
        parts.append(f'<text x="63" y="{py(y)+5:.2f}" text-anchor="end">{y:.1f}</text>')
        parts.append(f'<line x1="{left}" y1="{py(y):.2f}" x2="{right}" y2="{py(y):.2f}" stroke="#e2e8f0"/>')
    for x in (1,6,12,18,24,30):
        parts.append(f'<text x="{px(x):.2f}" y="428" text-anchor="middle">{x}</text>')
    parts += [f'<polyline points="{points(rows)}" fill="none" stroke="#1d4ed8" stroke-width="2"/>',
              f'<polyline points="{points(list(zip(xs,ys)))}" fill="none" stroke="#c2410c" stroke-width="3" stroke-dasharray="7 4"/>',
              '<text x="460" y="455">Time (day)</text>',
              '<text transform="translate(20,260) rotate(-90)">Demand (items)</text>',
              '<text x="110" y="70" fill="#1d4ed8">Observed</text>',
              '<text x="240" y="70" fill="#c2410c">Test forecast</text>',
              '<text x="75" y="475" font-size="12">Source: synthetic demand.csv; no confidence interval estimated.</text>',
              '</g></svg>']
    return "\n".join(parts)+"\n"

def make_task(run_id, config_path):
    return {"schema_version":1,"task_id":run_id,"mode":"solve",
            "inputs":["competition/demo/problem.md","competition/demo/demand.csv",config_path],
            "depends_on":[],"output_dir":"competition/runs/"+run_id,
            "acceptance":["真实运行三种候选并冻结验证选型","保存预测、指标、图表与证据哈希"],
            "budget_minutes":5}

def run(root, run_id, config_path="competition/demo/config.json"):
    root = Path(root)
    task = make_task(run_id,config_path)
    route = validate_task(root,task)
    config = read_json(safe_path(root,config_path))
    rows = load_data(root/"competition/demo/demand.csv")
    calculated = evaluate(rows,config)
    out = safe_path(root,task["output_dir"])
    # Reserve a fresh directory only after inputs have passed checks.
    out.mkdir(parents=True,exist_ok=False)
    command = f"python tools/project.py demo --run-id {run_id} --config {config_path}"
    try:
        write_json(out/"task.json",task)
        write_json(out/"config.json",config)
        write_json(out/"metrics.json",{k:calculated[k] for k in ("chosen","validation","test","parameters","split")})
        b=config["validation_end"]
        test=rows[b:]
        models=config["candidates"]
        write_csv(out/"predictions.csv",["day","actual",*models],
                  [[x,y,*[calculated["predictions"][name][i] for name in models]] for i,(x,y) in enumerate(test)])
        write_csv(out/"sensitivity.csv",["factor","mae","rmse"],
                  [[r["factor"],r["mae"],r["rmse"]] for r in calculated["sensitivity"]])
        write_csv(out/"processed.csv",["day","demand"],rows)
        (out/"forecast.svg").write_text(make_svg(rows,[r[0] for r in test],calculated["predictions"][calculated["chosen"]]),encoding="utf-8")
        (out/"problem_analysis.md").write_text("# 题目分析\n用已知前24天预测后6天，预测不是因果估计。输出预测值、指标和适用范围。\n",encoding="utf-8")
        (out/"task_breakdown.md").write_text("# 拆解\n输入审计 → 时间划分 → 候选比较 → 验证选型 → 冻结重拟合 → 测试评价 → 图表与文字。\n",encoding="utf-8")
        (out/"assumptions.md").write_text("# 假设\n短期趋势近似持续，时间间隔一致，需求单位为件。合成数据无外部事件和季节性，不能推广到真实需求。\n",encoding="utf-8")
        (out/"data_report.md").write_text(f"# 数据报告\n{len(rows)}行，字段day/demand。无缺失、重复时间、负需求或非有限值。严格检查后不插补、不删值、不缩放。\n划分：{calculated['split']}。所有预处理和拟合均不访问未来目标。\n",encoding="utf-8")
        (out/"model.md").write_text("# 模型\n均值基线、末值基线和OLS趋势 y=a+bt。b=sum((t-tbar)(y-ybar))/sum((t-tbar)^2)，a=ybar-b*tbar。a单位件，b单位件/天。\n算法见 algorithms/linear.py；验证选型后只用前24天重拟合，测试目标不参与。\n",encoding="utf-8")
        m=calculated["test"][calculated["chosen"]]
        (out/"paper.md").write_text(
            f"# 合成数据结果素材\n本示例在30天合成需求上，以前18天训练、第19—24天验证。验证RMSE选择 {calculated['chosen']}，再用前24天重拟合，预测末6天。\n"
            f"测试MAE={m['mae']:.6f}件，RMSE={m['rmse']:.6f}件。数据见 predictions.csv，指标见 metrics.json，图见 forecast.svg。\n"
            f"斜率在训练均值处保持预测锚点，按配置因子 {config['sensitivity_factors']} 扰动，在验证集评价，见 sensitivity.csv。此结果不是置信区间。\n"
            "没有运行Bootstrap、随机稳健性或消融；模型没有组合模块。不证明真实需求预测能力，不代表正式赛题答案。\n",encoding="utf-8")
        write_csv(out/"claim_evidence.csv",["claim","evidence"],
                  [["chosen model","metrics.json: chosen"],["test MAE/RMSE","metrics.json: test"],
                   ["test forecast","predictions.csv"],["validation slope sensitivity","sensitivity.csv"]])
        write_json(out/"figure_manifest.json",{"figure":"forecast.svg","source":"predictions.csv",
                   "source_sha256":sha256(out/"predictions.csv"),"command":command})
        write_json(out/"environment.json",{"python":sys.version,"platform":platform.platform(),
                   "dependencies":"standard library only","seed":config["seed"],
                   "seed_note":"deterministic formulas; random number generator not used"})
        sources = [*task["inputs"],"algorithms/linear.py","competition/demo/pipeline.py","orchestration/protocol.py"]
        write_json(out/"provenance.json",{p:sha256(root/p) for p in sources})
        write_json(out/"stage_trace.json",{"execution":"offline deterministic demonstration, NOT native agent/skill calls",
                   "route":route["agent"],"planned_skill_order":route["skills"],
                   "implemented_steps":["input audit","chronological split","candidate fitting","validation selection",
                                        "frozen refit","test scoring","sensitivity","SVG and evidence writing"]})
        (out/"run_log.txt").write_text(command+"\nstatus=completed\nexecution=offline, no LLM\n",encoding="utf-8")
        artifacts = [{"path":p.relative_to(root).as_posix(),"sha256":sha256(p)} for p in sorted(out.iterdir()) if p.is_file()]
        result={"schema_version":1,"task_id":run_id,"agent":"solver","status":"completed",
                "summary":"合成预测示例及文件协议联调完成；无真实Agent调用。",
                "artifacts":artifacts,"commands":[command],
                "limitations":["仅合成示例，不是正式赛题","未调用LLM或原生子Agent","未运行可选依赖、MATLAB或论文排版"]}
        write_json(out/"result.json",result)
        validate_result(root,task,result)
        return {"status":"passed","output_dir":task["output_dir"],"chosen":calculated["chosen"],"test":m,"execution":"offline; no LLM"}
    except Exception as error:
        (out/"failure.txt").write_text(type(error).__name__+": "+str(error),encoding="utf-8")
        raise
