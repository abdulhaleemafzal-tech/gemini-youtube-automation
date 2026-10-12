import json
from pathlib import Path
import unittest

from agent import check_plan, make_flow_prompts
from producer import srt_time

ROOT = Path(__file__).resolve().parent


class HindiKidsAgentTests(unittest.TestCase):
    def test_sample_story_has_five_clips_and_hindi_voice(self):
        plan = json.loads((ROOT / "sample_episode.json").read_text(encoding="utf-8"))
        check_plan(plan)
        self.assertEqual(len(plan["scenes"]), 5)
        self.assertTrue(all(any("\u0900" <= ch <= "\u097f" for ch in s["narration_hi"])
                            for s in plan["scenes"]))

    def test_prompt_package_names_five_clips(self):
        plan = json.loads((ROOT / "sample_episode.json").read_text(encoding="utf-8"))
        prompts = make_flow_prompts(plan)
        for n in range(1, 6):
            self.assertIn("scene_%02d.mp4" % n, prompts)
        self.assertIn(plan["characters"], prompts)

    def test_bad_plan_rejected(self):
        plan = json.loads((ROOT / "sample_episode.json").read_text(encoding="utf-8"))
        plan["scenes"] = plan["scenes"][:4]
        with self.assertRaises(ValueError):
            check_plan(plan)

    def test_srt_timing(self):
        self.assertEqual(srt_time(8.5), "00:00:08,500")


if __name__ == "__main__":
    unittest.main()
