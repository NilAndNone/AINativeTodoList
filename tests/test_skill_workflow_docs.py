from __future__ import annotations

import unittest
from pathlib import Path

from ainative_todo_service.mcp_tool_contracts import SUPPORTED_WRITE_ACTIONS


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "todo-local-workflow"


class SkillWorkflowDocsTests(unittest.TestCase):
    def test_codex_skill_files_exist(self) -> None:
        expected = [
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "agents" / "openai.yaml",
            SKILL_ROOT / "references" / "morning.md",
            SKILL_ROOT / "references" / "during-day.md",
            SKILL_ROOT / "references" / "close-day.md",
            SKILL_ROOT / "references" / "review.md",
            REPO_ROOT / "docs" / "human-workflow.md",
            REPO_ROOT / "docs" / "agent-workflow.md",
        ]
        for path in expected:
            self.assertTrue(path.exists(), path)

    def test_skill_enforces_plan_confirm_apply_rules(self) -> None:
        content = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("todo_plan_write", content)
        self.assertIn("todo_apply", content)
        self.assertIn("needs_input", content)
        self.assertIn("missing_fields", content)
        self.assertIn("ambiguous", content)
        self.assertIn("ready_for_confirm", content)
        self.assertIn("不得直接编辑文件", content)

    def test_human_workflow_matches_service_contract(self) -> None:
        content = (REPO_ROOT / "docs" / "human-workflow.md").read_text(encoding="utf-8")
        self.assertIn("todo_plan_write", content)
        self.assertIn("todo_apply", content)
        self.assertIn("开工", content)
        self.assertIn("收工", content)
        self.assertIn("白天更新", content)
        self.assertIn("周期总结", content)
        for field in ("title", "project", "priority", "due_date", "deliverable", "status", "notes"):
            self.assertIn(field, content)
        self.assertIn("只手改 `状态` 和 `备注`", content)

    def test_agent_workflow_lists_supported_actions(self) -> None:
        content = (REPO_ROOT / "docs" / "agent-workflow.md").read_text(encoding="utf-8")
        for action in SUPPORTED_WRITE_ACTIONS:
            self.assertIn(f"`{action}`", content)
        self.assertIn("todo_get_overview", content)
        self.assertIn("todo_search_tasks", content)

    def test_claude_guidance_points_to_new_skill(self) -> None:
        content = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn(".agents/skills/todo-local-workflow/SKILL.md", content)
        self.assertIn("todo_plan_write", content)
        self.assertIn("todo_apply", content)


if __name__ == "__main__":
    unittest.main()
