import copy
import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from algorithms.linear import fit,predict,metrics
from competition.demo.pipeline import evaluate,load_data,make_task,run
from orchestration.protocol import safe_path,sha256,read_json,validate_task,validate_result
from tools.project import check

class ModelTests(unittest.TestCase):
    def test_exact_line(self):
        p=fit([(1,5),(2,8),(3,11)],"linear")
        self.assertAlmostEqual(p["slope"],3)
        self.assertAlmostEqual(p["intercept"],2)
        self.assertEqual(predict(p,[4]),[14])
    def test_baselines(self):
        self.assertEqual(predict(fit([(1,2),(2,6)],"mean"),[9]),[4])
        self.assertEqual(predict(fit([(1,2),(2,6)],"last"),[9]),[6])
    def test_singular(self):
        with self.assertRaises(ValueError): fit([(1,2),(1,4)],"linear")
    def test_nonfinite(self):
        with self.assertRaises(ValueError): fit([(1,2),(2,math.nan)],"linear")
    def test_extreme_finite_linear_fit_is_scaled(self):
        model=fit([(1e154,1e154),(-1e154,-1e154)],"linear")
        self.assertTrue(all(math.isfinite(value) for value in model.values()))
        self.assertAlmostEqual(model["slope"],1.0)
        self.assertAlmostEqual(model["intercept"],0.0)
    def test_mean_baseline_avoids_sum_overflow(self):
        model=fit([(0,1e308),(1,1e308)],"mean")
        self.assertEqual(model,{"intercept":1e308,"slope":0.0})
    def test_unrepresentable_slope_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"finite float range"):
            fit([(0.0,0.0),(5e-324,1.0)],"linear")
    def test_malformed_and_boolean_rows_are_rejected_consistently(self):
        invalid=([1,2],[(0,"x"),(1,2)],[(False,0),(True,1)])
        for rows in invalid:
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                fit(rows,"linear")
    def test_metrics_hand_calculation(self):
        result=metrics([2,4],[1,7])
        self.assertEqual(result["mae"],2)
        self.assertAlmostEqual(result["rmse"],math.sqrt(5))
    def test_metrics_avoid_square_overflow(self):
        result=metrics([1e200,-1e200],[0.0,0.0])
        self.assertTrue(math.isfinite(result["mae"]))
        self.assertTrue(math.isfinite(result["rmse"]))
        self.assertEqual(result["mae"],1e200)
        self.assertEqual(result["rmse"],1e200)
    def test_unrepresentable_metric_error_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"finite float range"):
            metrics([1e308],[-1e308])
    def test_prediction_overflow_and_boolean_input_are_rejected(self):
        with self.assertRaisesRegex(ValueError,"finite float range"):
            predict({"intercept":0.0,"slope":1e308},[2.0])
        with self.assertRaises(ValueError):
            predict({"intercept":0.0,"slope":1.0},[True])
    def test_metric_length(self):
        with self.assertRaises(ValueError): metrics([1],[])
    def test_test_targets_do_not_affect_selection(self):
        rows=load_data(ROOT/"competition/demo/demand.csv")
        config=read_json(ROOT/"competition/demo/config.json")
        first=evaluate(rows,config)
        altered=rows[:24]+[(x,y+10000) for x,y in rows[24:]]
        second=evaluate(altered,config)
        self.assertEqual(first["chosen"],second["chosen"])
        self.assertEqual(first["validation"],second["validation"])
        self.assertEqual(first["parameters"],second["parameters"])
        self.assertEqual(first["predictions"],second["predictions"])
        self.assertNotEqual(first["test"],second["test"])
    def test_invalid_split(self):
        config=read_json(ROOT/"competition/demo/config.json")
        config["train_end"]=24
        with self.assertRaises(ValueError):
            evaluate(load_data(ROOT/"competition/demo/demand.csv"),config)

class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="math-model-")
        self.root=Path(self.temp.name)/"项目 with spaces"
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns("__pycache__","runs","work",".venv","input","refs"))
        self.task=make_task("test-run","competition/demo/config.json")
    def tearDown(self):
        self.temp.cleanup()
    def test_static_config_skills_and_full_prompts(self):
        self.assertEqual(check(self.root)["skills"],12)
        routes=read_json(self.root/"orchestration/routes.json")["routes"]
        self.assertEqual(routes["prepare"]["conditional_skills"],[])
        self.assertEqual([item["skill"] for item in routes["solve"]["conditional_skills"]],["eeg-c-task"])
        self.assertEqual({item["skill"] for item in routes["review"]["conditional_skills"]},
                         {"independent-validation","submission-audit"})
    def test_all_role_routes(self):
        for mode,agent,base in (("prepare","researcher","knowledge"),("solve","solver","competition"),("review","reviewer","validation")):
            task=copy.deepcopy(self.task)
            task.update(mode=mode,output_dir=base+"/runs/test-run")
            self.assertEqual(validate_task(self.root,task)["agent"],agent)
    def test_config_switch_and_backup(self):
        from tools.config_mode import switch
        files=("config.toml","agents/researcher.toml","agents/solver.toml","agents/reviewer.toml")
        initial_mode=check(self.root)["config_mode"]
        target_mode="current" if initial_mode=="legacy" else "legacy"
        original={name:(self.root/".codex"/name).read_bytes() for name in files}
        outcome=switch(self.root,target_mode)
        self.assertEqual(check(self.root)["config_mode"],target_mode)
        for name,content in original.items():
            self.assertEqual((self.root/outcome["backup"]/name).read_bytes(),content)
        switch(self.root,initial_mode)
        self.assertEqual(check(self.root)["config_mode"],initial_mode)
        for name in files:
            self.assertEqual((self.root/".codex"/name).read_bytes(),
                             (self.root/"compat"/initial_mode/".codex"/name).read_bytes())
    def test_blocked_missing_input_is_reportable(self):
        self.task["inputs"]=["competition/not-yet-provided.csv"]
        result={"schema_version":1,"task_id":"test-run","agent":"solver","status":"blocked",
                "summary":"missing attachment","artifacts":[],"commands":[],
                "limitations":["required attachment absent"]}
        validate_result(self.root,self.task,result)
        self.task["inputs"]=["../outside.csv"]
        with self.assertRaises(ValueError): validate_result(self.root,self.task,result)
    def test_missing_input(self):
        self.task["inputs"]=["competition/missing.csv"]
        with self.assertRaises(ValueError): validate_task(self.root,self.task)
    def test_path_escape_variants(self):
        for value in ("../secret","/tmp/secret","C:/secret","a\\b","a/../../secret"):
            with self.subTest(value=value),self.assertRaises(ValueError):
                safe_path(self.root,value)
    def test_symlink_escape_if_supported(self):
        target=Path(self.temp.name)/"outside"
        target.mkdir()
        try:
            (self.root/"escape").symlink_to(target,target_is_directory=True)
        except OSError:
            self.skipTest("OS does not permit unprivileged symlink creation")
        with self.assertRaises(ValueError): safe_path(self.root,"escape/file")
    def test_wrong_output_owner(self):
        self.task["output_dir"]="knowledge/runs/test-run"
        with self.assertRaises(ValueError): validate_task(self.root,self.task)
    def test_incomplete_dependency(self):
        self.task["depends_on"]=["upstream"]
        with self.assertRaises(ValueError): validate_task(self.root,self.task)
        validate_task(self.root,self.task,completed=["upstream"])
    def test_wrong_budget_type(self):
        self.task["budget_minutes"]=True
        with self.assertRaises(ValueError): validate_task(self.root,self.task)
    def test_full_pipeline_and_evidence(self):
        answer=run(self.root,"test-run")
        out=self.root/"competition/runs/test-run"
        result=read_json(out/"result.json")
        validate_result(self.root,self.task,result)
        self.assertEqual(answer["chosen"],"linear")
        self.assertLess(answer["test"]["rmse"],2)
        ET.parse(out/"forecast.svg")
        self.assertTrue({"metrics.json","predictions.csv","forecast.svg","paper.md","provenance.json"}.issubset({Path(a["path"]).name for a in result["artifacts"]}))
        self.assertEqual(read_json(out/"stage_trace.json")["route"],"solver")
    def test_repeat_is_deterministic(self):
        run(self.root,"a")
        run(self.root,"b")
        for name in ("metrics.json","predictions.csv","sensitivity.csv","forecast.svg"):
            self.assertEqual((self.root/"competition/runs/a"/name).read_bytes(),
                             (self.root/"competition/runs/b"/name).read_bytes())
    def test_refuses_overwrite(self):
        run(self.root,"test-run")
        with self.assertRaises(FileExistsError): run(self.root,"test-run")
    def test_tampering_detected(self):
        run(self.root,"test-run")
        out=self.root/"competition/runs/test-run"
        result=read_json(out/"result.json")
        (out/"metrics.json").write_text("tampered",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"hash mismatch"): validate_result(self.root,self.task,result)
    def test_role_mismatch(self):
        run(self.root,"test-run")
        result=read_json(self.root/"competition/runs/test-run/result.json")
        result["agent"]="researcher"
        with self.assertRaisesRegex(ValueError,"identity"): validate_result(self.root,self.task,result)
    def test_fake_completion(self):
        result={"schema_version":1,"task_id":"test-run","agent":"solver","status":"completed",
                "summary":"claim","artifacts":[],"commands":[],"limitations":[]}
        with self.assertRaises(ValueError): validate_result(self.root,self.task,result)
    def test_bad_csv(self):
        path=self.root/"bad.csv"
        for contents in ("day,demand\n1,2\n1,3\n","day,demand\n1,nan\n","day,demand\n1,\n"):
            path.write_text(contents,encoding="utf-8")
            with self.assertRaises(ValueError): load_data(path)
    def test_cli_from_unrelated_working_directory(self):
        proc=subprocess.run([sys.executable,str(self.root/"tools/project.py"),"check"],
                            cwd=self.temp.name,capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(proc.returncode,0,proc.stderr)
    def test_handoff_prepare_solve_review(self):
        # File protocol integration only: these records do not represent LLM calls.
        completed=[]
        for mode,agent,base in (("prepare","researcher","knowledge"),("solve","solver","competition"),("review","reviewer","validation")):
            task=copy.deepcopy(self.task)
            task.update(task_id=mode,mode=mode,output_dir=base+"/runs/"+mode,depends_on=completed[-1:])
            if completed:
                task["inputs"]=[previous]
            validate_task(self.root,task,completed)
            out=self.root/task["output_dir"]
            out.mkdir(parents=True)
            evidence=out/"handoff.txt"
            evidence.write_text("offline contract fixture",encoding="utf-8")
            previous=evidence.relative_to(self.root).as_posix()
            result={"schema_version":1,"task_id":mode,"agent":agent,"status":"completed",
                    "summary":"offline fixture","artifacts":[{"path":previous,"sha256":sha256(evidence)}],
                    "commands":[],"limitations":["not a native agent call"]}
            validate_result(self.root,task,result,completed)
            completed.append(mode)
        self.assertEqual(completed,["prepare","solve","review"])

if __name__ == "__main__":
    unittest.main()
