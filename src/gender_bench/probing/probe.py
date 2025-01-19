import json
import os
import random
import typing
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Literal, Optional

import numpy as np
from scipy.stats import norm
from tqdm import tqdm

from gender_bench.config import LOG_DIR
from gender_bench.generators.generator import Generator
from gender_bench.probing.attempt import Attempt
from gender_bench.probing.evaluator import Evaluator
from gender_bench.probing.metric_calculator import MetricCalculator
from gender_bench.probing.probe_item import ProbeItem

status = Enum("status", ["NEW", "POPULATED", "GENERATED", "EVALUATED", "FINISHED"])


class Probe(ABC):
    """`Probes` are capable of orchestrating the entire probing pipeline to
    calculate `metrics` and `marks` for text generators. Each `Probe` is
    designed to quantify one or more harmful behaviors that such text generators
    might manifest.

    The lifecycle of `Probe` consists of four main steps:

        1. Creating `ProbeItems` and their `Attempts`.
        2. Running `generator` on all the created `Attempts`
        3. Evaluating the generated answers with `evaluator`.
        4. Calculating metrics and marks based on the evaluations.

    Args:
        evaluator (Evaluator): `Evaluator` used to evaluate generated answers in
            `attempts`.
        metric_calculator (MetricCalculator): `MetricCalculator` used to
            calculate metrics from the evaluated `Attempts`.
        num_repetitions (int): How many `Attempts` are created for each
            `Prompt`. Useful to increase the precision of measurments. Defaults
            to 1.
        sample_k (Optional[int], optional): How many `ProbeItems` are sampled
            from the full dataset. When set to None, all the samples are used.
            Defaults to None.
        calculate_cis (bool, optional): Whether to calculate confidence
            intervals (via bootstrapping) for metrics or use the raw values.
            Defaults to True.
        bootstrap_cycles (int, optional): How many resamplings of `ProbeItems`
            are done for confidence interval calculations. Defaults to 1000.
        bootstrap_alpha (float, optional): The *alpha* level for confidence
            interval calculations. Defaults to 0.95.
        random_seed (int, optional): Random seed used when we create
            `ProbeItems`. Defaults to 123.
        log_strategy (Literal["after", "during", "no"], optional): How often is
            the state of the probe logged into a file as a JSON line:

                - "after" - After the entire `run` lifecycle.
                - "during" - After each of the 4 steps in the `run` lifecycle.
                - "no" - Never.

            Defaults to "no".
        log_dir (str, optional): Path to the logging directory. If None,
            LOG_DIR environment variable is used. Defaults to None.

    Attributes:
        metrics (dict[str, float]): Calculated metrics. Available only in
            ``status.FINISHED``.
        marks (dict[str, dict]): Calculated marks. Available only in
            ``status.FINISHED``.
        status (status): Current status of the `Probe`, one of ``status.NEW``,
            ``status.POPULATED``, ``status.GENERATED``, ``status.EVALUATED``,
            ``status.FINISHED``. Status is changed after each of the four steps.
        uuid (uuid.UUID): UUID identifier.
        probe_items (list[ProbeItem]): List of current `ProbeItems`. Available
            starting from ``status.POPULATED``.
    """

    mark_definitions = list()

    def __init__(
        self,
        evaluator: Evaluator,
        metric_calculator: MetricCalculator,
        num_repetitions: int = 1,
        sample_k: Optional[int] = None,
        calculate_cis: bool = True,
        bootstrap_cycles: int = 1000,
        bootstrap_alpha: float = 0.95,
        random_seed: int = 123,
        log_strategy: Literal["no", "during", "after"] = "no",
        log_dir: str = None,
    ):
        self.evaluator = evaluator
        self.metric_calculator = metric_calculator

        self.num_repetitions = num_repetitions
        self.sample_k = sample_k
        self.random_seed = random_seed

        self.calculate_cis = calculate_cis
        self.bootstrap_cycles = bootstrap_cycles
        self.bootstrap_alpha = bootstrap_alpha

        self.metrics = dict()
        self.marks = dict()
        self.status = status.NEW
        self.uuid = uuid.uuid4()
        self.log_strategy = log_strategy

        if log_dir is None:
            log_dir = LOG_DIR
        self.log_dir = Path(log_dir)

        self.probe_items = list()

    def __repr__(self):
        num_items = len(self.probe_items)
        num_attempts = sum(len(item.attempts) for item in self.probe_items)
        return f"<{self.__class__.__name__}: {num_items=}, {num_attempts=}>"

    @property
    def attempts(self) -> typing.Generator[Attempt, None, None]:
        """Generator of all the attempts that belong to this `Probe`.

        Yields:
            Attempt
        """
        for item in self.probe_items:
            for attempt in item.attempts:
                yield attempt

    def create_probe_items(self):
        """Populate `probe_items` with corrensponding prepared `ProbeItems`.
        This is the first step in the `run` lifecycle. Moves the `status` from
        ``NEW`` to ``POPULATED``.
        """
        assert self.status == status.NEW
        self.create_probe_items_random_generator = random.Random(self.random_seed)
        self.probe_items = self._create_probe_items()
        if self.sample_k is not None:
            self.probe_items = self.sample(k=self.sample_k)
        self.status = status.POPULATED
        if self.log_strategy == "during":
            self.log_current_state()

    @abstractmethod
    def _create_probe_items(self) -> list[ProbeItem]:
        """The core method that creates a list of all the necessary
            `ProbeItems`.

        Returns:
            list[ProbeItem]
        """
        raise NotImplementedError

    def generate(self, generator: Generator):
        """Use text `generator` to generate texts based on all the `Attempts`
        from this `Probe`, and populate their `answer` field. This is the second
        step in the `run` lifecycle. Moves the `status` from ``POPULATED`` to
        ``GENERATED``.

        Args:
            generator (Generator): Text generator that is being probed.
        """
        assert self.status == status.POPULATED
        texts = [attempt.prompt.text for attempt in self.attempts]

        answers = generator.generate(texts)
        answers_iterator = iter(answers)

        for item in self.probe_items:
            for attempt in item.attempts:
                attempt.answer = next(answers_iterator)

        if self.log_strategy == "during":
            self.log_current_state()
        self.status = status.GENERATED

    def evaluate(self):
        """Use `evaluator` to evaluate the generated texts and populate the
        `evaluation` field in all the `Attempts`. This is the third step in the
        `run` lifecycle. Moves the `status` from ``GENERATED`` to ``EVALUATED``.
        """
        assert self.status == status.GENERATED
        for attempt in self.attempts:
            attempt.evaluate(self.evaluator)
        if self.log_strategy == "during":
            self.log_current_state()
        self.status = status.EVALUATED

    def calculate_metrics(self):
        """Calculate `metrics` and `marks` based on the results of evaluation.
        This is the fourth and final step in the `run` lifecycle. Moves the
        `status` from ``EVALUATED`` to ``FINISHED``.
        """
        assert self.status == status.EVALUATED

        # Bootstrapping
        if self.calculate_cis:
            random.seed(self.random_seed)
            metric_buffer = defaultdict(lambda: list())
            for _ in tqdm(
                range(self.bootstrap_cycles), desc="Bootstrapping"
            ):  # 1000 could be a hyperparameter
                sample_items = random.choices(self.probe_items, k=len(self.probe_items))
                sample_metrics = self.metric_calculator(sample_items)
                for metric, value in sample_metrics.items():
                    metric_buffer[metric].append(value)

            metrics = dict()
            for metric_name, values in metric_buffer.items():
                if all(np.isnan(value) for value in values):
                    interval = (np.nan, np.nan)
                elif len(set(values)) == 1:
                    interval = (values[0], values[0])
                else:
                    values = [value for value in values if not np.isnan(value)]
                    interval = norm.interval(self.bootstrap_alpha, *norm.fit(values))
                    interval = tuple(map(float, interval))
                metrics[metric_name] = interval

        # No bootstrapping
        else:
            metrics = self.metric_calculator(self.probe_items)

        self.metrics = metrics
        self.marks = self.calculate_marks()
        self.status = status.FINISHED

        if self.log_strategy in ("during", "after"):
            self.log_current_state()

    def calculate_marks(self):
        """Calculate `marks` and prepare output mark dictionary.

        Returns:
            dict[str, dict]: Assessment of the mark based on coressponding
                metric value.
        """
        return {
            mark.metric_name: mark.prepare_mark_output(self)
            for mark in self.mark_definitions
        }

    def run(self, generator: Generator) -> tuple[dict[str, dict], dict[str, float]]:
        """This is the main process being used to probe `generator` for harmful
        behavior.

        Args:
            generator (Generator): Evaluated text generator.

        Returns:
            tuple[dict[str, dict]], dict[str, float]: A tuple containing:

                - Dictionary describing the calculated marks.
                - Dictionary with metrics and their values.
        """
        self.create_probe_items()
        self.generate(generator)
        self.evaluate()
        self.calculate_metrics()
        return self.marks, self.metrics

    def sample(self, k: int) -> list[ProbeItem]:
        """Sample `k` existing `ProbeItems`.

        Args:
            k (int): How many `ProbeItems` are sampled.

        Returns:
            list[ProbeItem]: Sampled `ProbeItems`.
        """
        random.seed(self.random_seed)
        return random.sample(self.probe_items, k=k)

    def to_json_dict(self) -> dict:
        """Prepare a JSON-serializable dictionary representation. Used for
        logging.

        Returns:
            dict: JSON-serializable dictionary.
        """
        parameters = [
            "uuid",
            "status",
            "metrics",
            "marks",
            "calculate_cis",
            "bootstrap_cycles",
            "bootstrap_alpha",
            "random_seed",
            "sample_k",
            "num_repetitions",
        ]
        d = {parameter: getattr(self, parameter) for parameter in parameters}
        d["probe_items"] = [
            probe_item.to_json_dict() for probe_item in self.probe_items
        ]
        return {"probe_state": d}

    def log_current_state(self):
        """Log current state of `Probe` into a file."""
        json_dict = self.to_json_dict()
        log_file = self.log_dir / f"{self.uuid}.jsonl"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(json_dict, default=str) + "\n")
