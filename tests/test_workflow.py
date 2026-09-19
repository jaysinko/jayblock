from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def test_update_workflow(self) -> None:
        path = ROOT / ".github" / "workflows" / "update.yml"
        self.assertTrue(path.exists())
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertIn("schedule", data["on"])
        self.assertIn("workflow_dispatch", data["on"])
        cron = data["on"]["schedule"][0]["cron"]
        self.assertTrue(cron)
        jobs = data["jobs"]
        self.assertIn("build", jobs)
        script = str(jobs)
        self.assertIn("tools/build.py", script)
        self.assertIn("unittest", script)

    def test_sources_have_reasons(self) -> None:
        data = yaml.safe_load((ROOT / "config" / "sources.yml").read_text(encoding="utf-8"))
        for source in data["sources"]:
            self.assertTrue(source.get("reason"), source["id"])
            self.assertTrue(source.get("id"))
            self.assertTrue(source.get("url") or source.get("path"))


if __name__ == "__main__":
    unittest.main()
