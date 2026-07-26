import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ClaudeReviewLoopIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(
        os.environ.get("RUN_CLAUDE_REVIEW_INTEGRATION") == "1",
        "실제 Claude 호출은 RUN_CLAUDE_REVIEW_INTEGRATION=1일 때만 실행",
    )
    def test_real_claude_review_round(self):
        claude = shutil.which("claude")
        if claude is None and os.name == "nt":
            candidate = Path(os.environ.get("USERPROFILE", "")) / ".local" / "bin" / "claude.exe"
            claude = str(candidate) if candidate.is_file() else None
        if claude is None:
            self.skipTest("Claude Code CLI가 설치되어 있지 않음")
        skill_root = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "claude-review-loop"
        script = skill_root / "scripts" / "run_review.py"
        config = skill_root / "config.json"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            (root / "sample.txt").write_text("small review target\n", encoding="utf-8")
            review_dir = root / ".review"
            review_dir.mkdir()
            (review_dir / "request.json").write_text(
                json.dumps(
                    {
                        "iteration": 1,
                        "user_request": "Review this small repository change.",
                        "objective": "Confirm the review loop can complete one round.",
                        "acceptance_criteria": ["Return the required JSON review."],
                        "implementation_summary": ["Added sample.txt."],
                        "tests_executed": [],
                        "known_risks": [],
                        "review_focus": ["No code defect in the sample file."],
                        "previous_review": {"findings": [], "changes_made": []},
                    }
                ),
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["CLAUDE_BIN"] = claude
            result = subprocess.run(
                [sys.executable, str(script), "--repo-root", str(root), "--config", str(config)],
                cwd=root,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertIn(result.returncode, (0, 2))
            response = json.loads((review_dir / "response.json").read_text(encoding="utf-8"))
            self.assertIn(response.get("decision"), ("approved", "changes_requested"))


if __name__ == "__main__":
    unittest.main()
