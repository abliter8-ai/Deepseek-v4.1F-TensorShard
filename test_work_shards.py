import contextlib
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
import io

import work_shards

FAKE_SDK = r'''
import json, os, sys, time
log = os.environ.get("FAKE_LOG"); mode = os.environ.get("FAKE_MODE", "ok")
cwd = os.environ.get("FAKE_CWD", os.getcwd())
def record(x):
    if log:
        with open(log, "a") as f: f.write(json.dumps(x) + "\n")
def reply(req, result=None, error=False):
    out = {"jsonrpc":"2.0", "id":req.get("id")}
    if error: out["error"] = {"code":-1,"message":"synthetic"}
    else: out["result"] = result or {}
    sys.stdout.write(json.dumps(out) + "\n"); sys.stdout.flush()
for line in sys.stdin:
    req = json.loads(line); method = req.get("method"); record({"method":method,"params":req.get("params"),"cwd":os.getcwd()})
    if mode == "premature": sys.exit(3)
    if mode == "error" and method == os.environ.get("FAKE_ERROR_METHOD", "session/resume"):
        reply(req, error=True); continue
    if mode == "timeout" and method == "initialize":
        sys.stdout.write('{"jsonrpc":"2.0"'); sys.stdout.flush(); time.sleep(5); continue
    if mode == "burst":
        for i in range(4): sys.stdout.write(json.dumps({"jsonrpc":"2.0","method":"notice","params":{"n":i}})+"\n")
        sys.stdout.flush()
    if method == "session/working-directory/get": reply(req, {"cwd":os.environ.get("FAKE_SESSION_CWD", cwd)})
    elif method == "session/prompt": reply(req, {"messageId":"m1"})
    else: reply(req)
if mode == "nonzero": sys.exit(9)
'''

COMMAND = "import json, os, sys; open(os.environ['COMMAND_LOG'], 'w').write(json.dumps(sys.argv[1:]))"


class WorkShardsSubprocessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.workspace = self.root / "workspace"; self.workspace.mkdir()
        self.fake = self.root / "fake_sdk.py"; self.fake.write_text(FAKE_SDK)
        self.command = self.root / "command.py"; self.command.write_text(COMMAND)

    def tearDown(self): self.tmp.cleanup()

    def profile(self, **overrides):
        p = {"adapter":"dsh", "workspace":str(self.workspace), "session_id":"saved-1",
             "provider":"test-provider", "model":"test-model", "command":[sys.executable,str(self.fake)], "timeout_s":1}
        p.update(overrides); return p

    def run_profile(self, profile, check=False, dry_run=False, extra_profiles=None):
        config = {"version":1,"profiles":{"one":profile},"sets":{}}
        if extra_profiles: config["profiles"].update(extra_profiles)
        path = self.root / "work-shards.json"; path.write_text(json.dumps(config))
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = work_shards.main(["--config",str(path),"check" if check else "prepare","one"] + (["--dry-run"] if dry_run else []))
        return code, out.getvalue(), err.getvalue(), path

    def fake_env(self, mode="ok", **extra):
        env = os.environ.copy(); env.update({"FAKE_LOG":str(self.root/"sdk.log"),"FAKE_MODE":mode,"FAKE_CWD":str(self.workspace)})
        env.update({k:str(v) for k,v in extra.items()}); return env

    def test_prepare_protocol_order_and_workspace(self):
        old=os.environ.copy(); os.environ.update(self.fake_env())
        try: code, _, err, _ = self.run_profile(self.profile())
        finally: os.environ.clear(); os.environ.update(old)
        self.assertEqual((code,err),(0,""))
        frames=[json.loads(x) for x in (self.root/"sdk.log").read_text().splitlines()]
        methods=[frame["method"] for frame in frames]
        self.assertEqual(methods,["initialize","session/resume","session/working-directory/get","session/prompt","session/wait","shutdown"])
        self.assertEqual(Path(frames[0]["params"]["cwd"]).resolve(), self.workspace.resolve())
        for frame in frames:
            self.assertEqual(Path(frame["cwd"]).resolve(), self.workspace.resolve())
            if frame["method"].startswith("session/"):
                self.assertEqual(frame["params"]["sessionId"], "saved-1")
        receipt=json.loads((self.root/".work-shards/receipts.json").read_text())[0]
        self.assertEqual(receipt["status"],"prepared"); self.assertEqual(receipt["cache_residency"],"unknown")
        self.assertNotIn("test-provider",json.dumps(receipt))

    def test_check_has_no_prompt_or_wait(self):
        old=os.environ.copy(); os.environ.update(self.fake_env())
        try: code, _, _, _ = self.run_profile(self.profile(), check=True)
        finally: os.environ.clear(); os.environ.update(old)
        self.assertEqual(code,0)
        methods=[json.loads(x)["method"] for x in (self.root/"sdk.log").read_text().splitlines()]
        self.assertEqual(methods,["initialize","session/resume","session/working-directory/get","shutdown"])

    def test_workspace_mismatch_prevents_prompt(self):
        old=os.environ.copy(); os.environ.update(self.fake_env(FAKE_SESSION_CWD=str(self.root/"other")))
        try: code,out,_,_=self.run_profile(self.profile())
        finally: os.environ.clear(); os.environ.update(old)
        self.assertNotEqual(code,0); self.assertIn("failed",out)
        methods=[json.loads(x)["method"] for x in (self.root/"sdk.log").read_text().splitlines()]
        self.assertNotIn("session/prompt",methods)

    def test_jsonrpc_error_and_premature_exit(self):
        for mode in ("error","premature"):
            with self.subTest(mode=mode):
                old=os.environ.copy(); os.environ.update(self.fake_env(mode))
                try: code,_,_,_=self.run_profile(self.profile())
                finally: os.environ.clear(); os.environ.update(old)
                self.assertNotEqual(code,0)

    def test_nonzero_after_shutdown_is_failure(self):
        old=os.environ.copy(); os.environ.update(self.fake_env("nonzero"))
        try: code,_,_,_=self.run_profile(self.profile(),check=True)
        finally: os.environ.clear(); os.environ.update(old)
        self.assertNotEqual(code,0)

    def test_timeout_is_bounded_with_partial_line(self):
        old=os.environ.copy(); os.environ.update(self.fake_env("timeout"))
        try:
            started=time.monotonic(); code,_,_,_=self.run_profile(self.profile(timeout_s=.1))
        finally: os.environ.clear(); os.environ.update(old)
        self.assertNotEqual(code,0); self.assertLess(time.monotonic()-started,2)

    def test_notifications_do_not_break_response_matching(self):
        old=os.environ.copy(); os.environ.update(self.fake_env("burst"))
        try: code,_,_,_=self.run_profile(self.profile(),check=True)
        finally: os.environ.clear(); os.environ.update(old)
        self.assertEqual(code,0)

    def test_continue_after_missing_profile_command(self):
        good=self.profile(adapter="command",command=[sys.executable,str(self.command)],env={"COMMAND_LOG":str(self.root/"command.log")})
        bad=self.profile(command=[str(self.root/"does-not-exist")])
        path=self.root/"work-shards.json"; path.write_text(json.dumps({"version":1,"profiles":{"bad":bad,"good":good},"sets":{}}))
        out,err=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err): code=work_shards.main(["--config",str(path),"prepare","bad","good"])
        self.assertNotEqual(code,0); self.assertIn("good: prepared",out.getvalue()); self.assertTrue((self.root/"command.log").exists())

    def test_dry_run_validates_without_child_or_receipt(self):
        profile=self.profile(command=[str(self.root/"missing")]); code,out,_,_=self.run_profile(profile,dry_run=True)
        self.assertEqual(code,0); self.assertIn("one: validated",out); self.assertFalse((self.root/".work-shards").exists())
        self.assertNotIn("prepared",out.lower())

    def test_receipts_keep_previous_profile_state(self):
        p1=self.profile(); p2={"adapter":"command","workspace":str(self.workspace),"command":[sys.executable,str(self.command)],"env":{"COMMAND_LOG":str(self.root/"command.log")}}
        path=self.root/"work-shards.json"; path.write_text(json.dumps({"version":1,"profiles":{"one":p1,"two":p2},"sets":{}}))
        old=os.environ.copy(); os.environ.update(self.fake_env())
        try: self.assertEqual(work_shards.main(["--config",str(path),"check","one"]),0)
        finally: os.environ.clear(); os.environ.update(old)
        self.assertEqual(work_shards.main(["--config",str(path),"prepare","two"]),0)
        names={r["name"] for r in json.loads((self.root/".work-shards/receipts.json").read_text())}; self.assertEqual(names,{"one","two"})

    def test_command_argv_is_literal_and_no_shell(self):
        marker=self.root/"literal.json"
        profile={"adapter":"command","workspace":str(self.workspace),"command":[sys.executable,str(self.command),"$(touch SHOULD_NOT_EXIST)"],"env":{"COMMAND_LOG":str(marker)}}
        code,_,_,_=self.run_profile(profile); self.assertEqual(code,0)
        self.assertEqual(json.loads(marker.read_text())[-1],"$(touch SHOULD_NOT_EXIST)"); self.assertFalse((self.workspace/"SHOULD_NOT_EXIST").exists())


class ConfigValidationTests(unittest.TestCase):
    def test_unknown_env_substitution_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"c.json"; path.write_text(json.dumps({"version":1,"profiles":{"x":{"workspace":"${DEFINITELY_MISSING}"}},"sets":{}}))
            with self.assertRaises(work_shards.WorkShardError): work_shards.expand("${DEFINITELY_MISSING}", {})

    def test_selection_deduplicates_and_rejects_unknown(self):
        config={"profiles":{"a":{},"b":{}},"sets":{"daily":["a","a","b"]}}
        self.assertEqual([n for n,_ in work_shards.select(config,[],"daily")],["a","b"])
        with self.assertRaises(work_shards.WorkShardError): work_shards.select(config,["nope"],None)


if __name__ == "__main__": unittest.main(verbosity=2)
