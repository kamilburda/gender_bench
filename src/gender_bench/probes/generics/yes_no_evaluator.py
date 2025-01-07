from typing import Any

import nltk
from nltk.tokenize import word_tokenize

from gender_bench.probing.attempt import Attempt
from gender_bench.probing.evaluator import ClosedSetEvaluator


class YesNoEvaluator(ClosedSetEvaluator):
    """
    Detect Yes or No.
    """

    def __init__(self, probe):
        super().__init__(probe=probe, options=["yes", "no"], undetected=None)
        nltk.download("punkt", quiet=True)

    def calculate_evaluation(self, attempt: Attempt) -> Any:
        tokens = word_tokenize(attempt.answer.lower())
        contains_yes, contains_no = "yes" in tokens, "no" in tokens
        if contains_yes == contains_no:
            return None
        if contains_yes:
            return "yes"
        return "no"
