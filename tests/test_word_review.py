"""Missing confidence scores do not hide unfinished words or suspect timing."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class WordReviewTests(unittest.TestCase):
    def test_unfinished_word_and_suspicious_timing_require_review_without_confidence(self):
        words = [
            {"type": "word", "text": "النصوص", "start": 0, "end": .4},
            {"type": "word", "text": "ال-", "start": .5, "end": .7},
            {"type": "word", "text": "وتعالى.", "start": .8, "end": 5.1},
        ]
        segments = server.words_to_segments(words)
        self.assertTrue(segments[0]["needs_review"])
        self.assertEqual([w["text"] for w in segments[0]["unclear_words"]], ["ال-", "وتعالى."])
        self.assertEqual(segments[0]["ar"], "النصوص ال- وتعالى.")
        self.assertEqual(segments[0]["end"], 5.1)  # Do not fabricate corrected timing.
        self.assertEqual(segments[0]["unclear_words"][0]["reasons"], ["unfinished_word"])
        self.assertEqual(segments[0]["unclear_words"][1]["reasons"], ["long_word_timing"])

    def test_low_confidence_and_timing_hints_coexist_without_changing_speech(self):
        flags = server.questionable_words([
            {"text": "عادي", "start": 0, "end": .4},
            {"text": "مقطع-", "start": .5, "end": 3.5, "logprob": -2},
        ])
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]["reasons"], ["low_confidence", "unfinished_word", "long_word_timing"])


if __name__ == "__main__":
    unittest.main()
