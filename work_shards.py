#!/usr/bin/env python3
"""Prepare named application sessions; keep application loops and transcripts intact."""
from __future__ import annotations

import argparse
import json
import math
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class WorkShardError(Exception):
    """A short diagnostic that is safe to write to a preparation receipt."""


def expand(value: Any, env: dict[str, str]) -> Any:
    if isinstance(value, str):
        def replace(match):
            key = match.group(1)
            if key not in env:
                raise WorkShardError(f"missing environment variable: {key}")
            return env[key]
        return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", replace, value)
    if isinstance(value, list):
        return [expand(item, env) for item in value]
    if isinstance(value, dict):
        return {key: expand(item, env) for key, item in value.items()}
    return value


def load_config(path: Path) -> dict[str, Any]:
    try:
        config = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise WorkShardError("cannot read configuration JSON") from exc
    if not isinstance(config, dict) or config.get("version") != 1:
        raise WorkShardError("configuration version must be 1")
    if not isinstance(config.get("profiles"), dict) or not isinstance(config.get("sets", {}), dict):
        raise WorkShardError("profiles and sets must be objects")
    return config


def select(config, names, set_name):
    if set_name and names:
        raise WorkShardError("select profile names or one saved set")
    if set_name:
        names = config.get("sets", {}).get(set_name)
    if not isinstance(names, list) or not names or not all(isinstance(n, str) for n in names):
        raise WorkShardError("select existing profiles or a nonempty saved set")
    chosen = []
    for name in dict.fromkeys(names):
        profile = config["profiles"].get(name)
        if not isinstance(profile, dict):
            raise WorkShardError("selected profile does not exist")
        chosen.append((name, profile))
    return chosen


def argv_list(value, field):
    if not isinstance(value, list) or not value or not all(isinstance(v, str) for v in value) or not value[0]:
        raise WorkShardError(f"{field} must be a nonempty argv array")
    return value.copy()


def validated(profile):
    environment = profile.get("env", {})
    if not isinstance(environment, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in environment.items()):
        raise WorkShardError("env must map names to strings")
    env = dict(os.environ)
    env.update(expand(environment, env))
    profile = expand(profile, env)
    workspace = profile.get("workspace")
    if not isinstance(workspace, str) or not workspace:
        raise WorkShardError("workspace is required")
    workspace = Path(workspace).expanduser().resolve()
    if not workspace.is_dir():
        raise WorkShardError("workspace does not exist")
    timeout = profile.get("timeout_s", 120)
    if isinstance(timeout, bool) or not isinstance(timeout, (float, int)) or not math.isfinite(timeout) or timeout <= 0:
        raise WorkShardError("timeout_s must be a positive finite number")
    return profile, workspace, env, timeout


def stop_child(proc):
    if proc.stdin:
        try:
            proc.stdin.close()
        except OSError:
            pass
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        for hard in (False, True):
            try:
                if os.name == "posix":
                    os.killpg(proc.pid, signal.SIGKILL if hard else signal.SIGTERM)
                else:
                    proc.kill() if hard else proc.terminate()
                proc.wait(timeout=1)
                break
            except ProcessLookupError:
                break
            except subprocess.TimeoutExpired:
                continue
    if proc.stdout:
        proc.stdout.close()


class DSH:
    def __init__(self, profile, check):
        self.profile, self.workspace, self.env, self.timeout = validated(profile)
        self.check = check
        for field in ("session_id", "provider", "model"):
            if not isinstance(self.profile.get(field), str) or not self.profile[field].strip():
                raise WorkShardError(f"{field} is required")
        cap = self.profile.get("max_tokens", 256)
        if isinstance(cap, bool) or not isinstance(cap, int) or cap <= 0:
            raise WorkShardError("max_tokens must be a positive integer")
        prompt = self.profile.get("prompt", "Preparation only. Do not use tools or modify files. Reply READY.")
        if not isinstance(prompt, str) or not prompt.strip():
            raise WorkShardError("prompt must be nonempty text")
        self.prompt = prompt
        self.command = argv_list(self.profile.get("command", ["dsh", "--profile", "sdk"]), "command")
        self.command[0] = os.path.expanduser(self.command[0])
        if self.profile.get("patch"):
            patch = Path(self.profile["patch"]).expanduser().resolve()
            if not patch.is_file():
                raise WorkShardError("DSH patch file does not exist")
            self.command += ["--patch", str(patch)]

    def run(self):
        proc = subprocess.Popen(self.command, cwd=self.workspace, env=self.env, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                start_new_session=(os.name == "posix"))
        responses = queue.Queue()
        # A reader thread keeps partial lines and notification bursts off the timeout path.
        def read():
            try:
                for line in proc.stdout:
                    try:
                        frame = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(frame, dict) and "id" in frame:
                        responses.put(frame)
            finally:
                responses.put(None)
        threading.Thread(target=read, daemon=True).start()
        deadline = time.monotonic() + self.timeout
        counter = 0
        shut_down = False

        def rpc(method, params, until=None):
            nonlocal counter
            counter += 1
            try:
                proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": counter, "method": method, "params": params}) + "\n")
                proc.stdin.flush()
            except OSError as exc:
                raise WorkShardError("DSH exited before completing the request") from exc
            limit = deadline if until is None else until
            while True:
                left = limit - time.monotonic()
                if left <= 0:
                    raise WorkShardError("DSH operation timed out")
                try:
                    frame = responses.get(timeout=left)
                except queue.Empty as exc:
                    raise WorkShardError("DSH operation timed out") from exc
                if frame is None:
                    raise WorkShardError("DSH exited before completing the request")
                if frame.get("id") != counter:
                    continue
                if "error" in frame:
                    raise WorkShardError(f"DSH rejected {method}")
                if "result" not in frame:
                    raise WorkShardError("DSH returned an invalid response")
                return frame["result"]
        try:
            rpc("initialize", {"cwd": str(self.workspace), "provider": self.profile["provider"],
                               "model": self.profile["model"], "maxTokens": self.profile.get("max_tokens", 256)})
            session = {"sessionId": self.profile["session_id"]}
            rpc("session/resume", session)
            result = rpc("session/working-directory/get", session)
            cwd = result.get("cwd") if isinstance(result, dict) else None
            if not isinstance(cwd, str) or Path(cwd).resolve() != self.workspace:
                raise WorkShardError("saved session workspace does not match profile")
            if not self.check:
                result = rpc("session/prompt", {**session, "contentBlocks": [{"type": "text", "text": self.prompt}]})
                if not isinstance(result, dict) or not result.get("messageId"):
                    raise WorkShardError("DSH did not acknowledge the preparation prompt")
                rpc("session/wait", session)
            rpc("shutdown", {})
            shut_down = True
        finally:
            if not shut_down and proc.poll() is None and time.monotonic() < deadline:
                try:
                    rpc("shutdown", {}, min(deadline, time.monotonic() + 0.5))
                except WorkShardError:
                    pass
            stop_child(proc)
        if proc.returncode != 0:
            raise WorkShardError("DSH exited with a failure status")


def command_profile(profile, check):
    profile, workspace, env, timeout = validated(profile)
    field = "check_command" if check else "command"
    command = argv_list(profile.get(field), field)
    command[0] = os.path.expanduser(command[0])
    return command, workspace, env, timeout


def run_command(profile, check):
    command, workspace, env, timeout = command_profile(profile, check)
    proc = subprocess.Popen(command, cwd=workspace, env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=(os.name == "posix"))
    try:
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise WorkShardError("application command timed out") from exc
    finally:
        stop_child(proc)
    if proc.returncode != 0:
        raise WorkShardError("application command failed")


def receipt_path(config_path):
    return config_path.parent / ".work-shards" / "receipts.json"


def save_receipts(path, records):
    previous = json.loads(path.read_text()) if path.exists() else []
    combined = {record["name"]: record for record in previous}
    combined.update({record["name"]: record for record in records})
    path.parent.mkdir(mode=0o700, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as stream:
        json.dump(list(combined.values()), stream, indent=2)
        stream.write("\n")
    temporary.replace(path)


def execute(config_path, chosen, check, dry_run):
    records = []
    for name, profile in chosen:
        started = time.monotonic()
        status = "validated" if dry_run else "checked" if check else "prepared"
        error = None
        try:
            adapter = profile.get("adapter")
            if adapter == "dsh":
                instance = DSH(profile, check)
                if not dry_run:
                    instance.run()
            elif adapter == "command":
                command_profile(profile, check)
                if not dry_run:
                    run_command(profile, check)
            else:
                raise WorkShardError("adapter must be dsh or command")
        except (WorkShardError, OSError, ValueError, TypeError) as exc:
            status = "failed"
            error = str(exc) if isinstance(exc, WorkShardError) else "application launch or configuration failed"
        records.append({"name": name, "adapter": profile.get("adapter"), "status": status,
                        "time": datetime.now(timezone.utc).isoformat(),
                        "duration_s": round(time.monotonic() - started, 3), "error": error,
                        "cache_residency": "unknown"})
        print(f"{name}: {status}" + (f" ({error})" if error else ""))
    if not dry_run:
        save_receipts(receipt_path(config_path), records)
    return int(any(record["status"] == "failed" for record in records))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="work-shards.local.json", help="private profile JSON")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("init", help="create private profiles from the example")
    sub.add_parser("list", help="list profiles and saved sets")
    for action in ("prepare", "check"):
        command = sub.add_parser(action)
        command.add_argument("profiles", nargs="*")
        command.add_argument("--set", help="saved set of profiles")
        command.add_argument("--dry-run", action="store_true", help="validate without launching applications")
    sub.add_parser("status", help="show last operations; not current cache residency")
    args = parser.parse_args(argv)
    config_path = Path(args.config).expanduser()
    try:
        if args.action == "init":
            template = Path(__file__).with_name("work-shards.example.json").read_text()
            with os.fdopen(os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
                stream.write(template)
            print("Created private profile configuration.")
            return 0
        if args.action == "status":
            path = receipt_path(config_path)
            if not path.exists():
                print("No preparation receipts yet.")
                return 0
            for record in json.loads(path.read_text()):
                print(f"LAST {record['status'].upper()}: {record['name']} at {record['time']} ({record['duration_s']} s); cache residency unknown")
            return 0
        config = load_config(config_path)
        if args.action == "list":
            for name in config["profiles"]:
                print(f"profile: {name}")
            for name, members in config.get("sets", {}).items():
                print(f"set: {name}: {', '.join(members)}")
            return 0
        return execute(config_path, select(config, args.profiles, args.set), args.action == "check", args.dry_run)
    except WorkShardError as exc:
        print(str(exc), file=sys.stderr)
    except FileExistsError:
        print("Configuration already exists; preserved it.", file=sys.stderr)
    except (OSError, ValueError, TypeError, KeyError):
        print("Cannot read or write local configuration or receipts.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
