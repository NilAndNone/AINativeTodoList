from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import os
from pathlib import Path
import subprocess
from typing import Any

from .config import CloseDayGitConfig


GIT_EXECUTABLE_ENV_VAR = "AINATIVE_TODO_GIT_BIN"


@dataclass(frozen=True)
class GitCommandResult:
    command: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def as_dict(self) -> dict[str, object]:
        return {
            "command": self.command,
            "cwd": self.cwd,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


def _git_executable() -> str:
    return os.getenv(GIT_EXECUTABLE_ENV_VAR, "git")


def _run_git(data_repo: Path, *args: str) -> GitCommandResult:
    command = [_git_executable(), *args]
    completed = subprocess.run(
        command,
        cwd=str(data_repo),
        text=True,
        capture_output=True,
        check=False,
    )
    return GitCommandResult(
        command=command,
        cwd=str(data_repo),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _git_error(message: str, result: GitCommandResult) -> str:
    detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
    return f"{message}: {detail}"


def _failure_payload(payload: dict[str, Any], *, error: str) -> dict[str, Any]:
    payload["ok"] = False
    payload["error"] = error
    return payload


def run_close_day_git_automation(
    *,
    data_repo: Path,
    git_config: CloseDayGitConfig,
    date: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": True,
        "enabled": git_config.auto_commit_on_close_day or git_config.auto_push_on_close_day,
        "repo": str(data_repo.resolve()),
        "auto_commit_on_close_day": git_config.auto_commit_on_close_day,
        "auto_push_on_close_day": git_config.auto_push_on_close_day,
        "commit_message": None,
        "commit_hash": None,
        "commit_status": "disabled",
        "push_status": "disabled",
        "commands": [],
    }
    if not payload["enabled"]:
        return payload
    if git_config.auto_push_on_close_day and not git_config.auto_commit_on_close_day:
        return _failure_payload(
            payload,
            error="Invalid git config: auto_push_on_close_day requires auto_commit_on_close_day=true.",
        )

    repo_check = _run_git(data_repo, "rev-parse", "--is-inside-work-tree")
    payload["commands"].append(repo_check.as_dict())
    if not repo_check.ok or repo_check.stdout.strip().lower() != "true":
        return _failure_payload(payload, error=f"Data repo is not a git repository: {data_repo.resolve()}")

    effective_date = date or dt.date.today().isoformat()
    commit_performed = False
    if git_config.auto_commit_on_close_day:
        try:
            commit_message = git_config.commit_message.format(date=effective_date)
        except KeyError as exc:
            return _failure_payload(
                payload,
                error=f"Invalid git commit_message template in data repo config: missing placeholder '{exc.args[0]}'",
            )
        payload["commit_message"] = commit_message

        add_result = _run_git(data_repo, "add", "-A")
        payload["commands"].append(add_result.as_dict())
        if not add_result.ok:
            return _failure_payload(payload, error=_git_error("git add failed in data repo", add_result))

        diff_check = _run_git(data_repo, "diff", "--cached", "--quiet")
        payload["commands"].append(diff_check.as_dict())
        if diff_check.returncode not in (0, 1):
            return _failure_payload(payload, error=_git_error("git diff --cached failed in data repo", diff_check))

        if diff_check.returncode == 1:
            commit_result = _run_git(data_repo, "commit", "-m", commit_message)
            payload["commands"].append(commit_result.as_dict())
            if not commit_result.ok:
                return _failure_payload(payload, error=_git_error("git commit failed in data repo", commit_result))

            rev_parse = _run_git(data_repo, "rev-parse", "HEAD")
            payload["commands"].append(rev_parse.as_dict())
            if not rev_parse.ok:
                return _failure_payload(payload, error=_git_error("git rev-parse HEAD failed in data repo", rev_parse))

            payload["commit_hash"] = rev_parse.stdout.strip()
            payload["commit_status"] = "created"
            commit_performed = True
        else:
            payload["commit_status"] = "noop"

    if git_config.auto_push_on_close_day:
        if git_config.auto_commit_on_close_day and not commit_performed:
            payload["push_status"] = "skipped_no_new_commit"
            return payload

        push_result = _run_git(data_repo, "push")
        payload["commands"].append(push_result.as_dict())
        if not push_result.ok:
            return _failure_payload(payload, error=_git_error("git push failed in data repo", push_result))
        payload["push_status"] = "pushed"

    return payload
