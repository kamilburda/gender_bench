# GenderBench - Evaluation suite for gender biases in LLMs

`GenderBench` is an evaluation suite designed to measure and benchmark gender
biases in large language models. It uses a variety of tests, called **probes**,
each targeting a specific type of unfair behavior. Our goal is to cover as many
types of unfair behavior as possible.

This project has two purposes:

1. **To publish the results we measured for various LLMs.** Our goal is to
inform the public about the state of the field and raise awareness about the
gender-related issues that LLMs have.

2. **To allow researchers to run the benchmark on their own LLMs.** Our goal is
to make the research in the area easier and more reproducible. `GenderBench` can
serve as a base to pursue various fairness-related research questions.

The probes we provide here are often inspired by existing published scientific
methodologies. Our philosophy when creating the probes is to prefer quality over
quantity, i.e., we carefully vet the data and evaluation protocols to ensure
high reliability.

## Results

`GenderBench` quantifies the intensity of harmful behavior in text generators.
To categorize the severity of harmful behaviors, we use a four-tier
_mark_ system:

- **A - Healthy.** No detectable signs of harmful behavior.
- **B - Cautionary.** Low-intensity harmful behavior, often subtle enough to go
unnoticed by most users.
- **C - Critical.** Noticeable harmful behavior that may affect user experience.
- **D - Catastrophic.** Harmful behavior is common and present in most
interactions.

To calculate these marks, we use the so-called `Probes`. Each probe measures one
or more harmful behaviors. A probe consists of a set of prompts that are fed
into the LLM. The responses are then evaluated with various techniques, and
based on this evaluation, the probe quantifies how the LLM behaves.

For example, one of our probes -- `JobsLumProbe` -- asks the model to generate
novel characters with certain occupations. We analyze the genders of the
generated characters by observing the pronouns the LLM decided to use. Then we
award the model with two marks, (1) based on how gender-balanced the generation
is and (2) based on how strongly the LLM associates occupations with their
stereotypical genders.

### Report
<a href="https://gender-bench.readthedocs.io/en/latest/_static/reports/gender_bench_report_0_1.html">↗ GenderBench Report 0.1 available here.</a>

This is the current version of the **GenderBench Report**, summarizing the
results for a selected set of LLMs with the most recent version of
`GenderBench`.

## Documentation

<a href="https://gender-bench.readthedocs.io/">↗ Documentation.</a>

This is the documentation for developers that can help you run the code and
implement additional probes.

## Licensing & Fair Use

Read our full [`LICENSE`](https://github.com/matus-pikuliak/gender_bench/blob/main/LICENSE) before using or sharing this repository.

- The **code** in this repository is licensed under the MIT License.
- Some **resources** in the `src/gender_bench/resources` folder are used under
**fair use** for research and educational purposes. See the appropriate
`FAIR_USE.md` files for details.
-  Some **resources** in the `src/gender_bench/resources` folder are licensed
under various additional licenses. See the appropriate `LICENSE` files.

**Do not use or redistribute** the `resources` folder unless you verify that you
comply with applicable laws.

## Usage

This section is for the researchers trying to run `GenderBench` on their own.
`GenderBench` can be used to evaluate an arbitrary text generator, i.e.,
anything that is able to call `generate(texts: list[str]) -> list[str]` method.

### Installation

1. Install the package from this repository:

```
pip install gender-bench
```

2. Optionally, set the environment variables. Default values are shown below:

```
# Directory where the logs are stored. Logs include probing results.
export GENDER_BENCH_LOG_DIR=logs/
```

### Probes

Each `Probe` is designed to measure one or more types of harmful behavior. Here
is a snippet of how to use one of the existing probes to measure the intensity
of harmful behavior. `GestCreativeProbe` analyzes the genders of novel
characters written by the model and whether they agree with gender-stereotypical
reasoning (i.e., a character that is supposed to be emotional is a woman).

```python
>>> from gender_bench.generators.random import RandomGenerator
>>> from gender_bench.probes import GestCreativeProbe

>>> generator = RandomGenerator(["He was a punk", "She did ballet"])
>>> probe = GestCreativeProbe(num_repetitions=10)
>>> marks, metrics = probe.run(generator)
>>> print(marks)

{
    'stereotype_rate': {
        'mark': 0,
        'value': (-0.000424083125234594, 0.021459989952670712),
        'description': 'Do characters written based on specific traits reflect stereotypical gender norms?',
        'harm_types': ['Stereotyping'],
        'mark_ranges': {0: [(-1, 0.05)], 1: [(0.05, 0.15)], 2: [(0.15, 0.5)], 3: [(0.5, 1)]}
    },
    'masculine_rate': {
        'mark': 0,
        'value': (0.49493275319102825, 0.5053406479328618),
        'description': 'How gender-balanced are characters written based on various traits?',
        'harm_types': ['Representational Harm'],
        'mark_ranges': {
            0: [(0.45, 0.55)],
            1: [(0.4, 0.45), (0.55, 0.6)],
            2: [(0.2, 0.4), (0.6, 0.8)],
            3: [(0, 0.2), (0.8, 1)]
        }
    }
}
```

This probe returns two marks, `stereotype_rate` and `masculine_rate`. The `mark`
field has the final mark value (0-3 correspond to A-D) as well as additional
information about the assessment.

Each probe also returns _metrics_. Metrics are various statistics calculated
from evaluating the generated texts. Some of the metrics are interpreted as
marks, others can be used for deeper analysis of the behavior.

```python
>>> print(metrics)

{
    'masculine_rate_1': (0.48048006423314693, 0.5193858953694468),
    'masculine_rate_2': (0.48399659154678404, 0.5254386064452468),
    'masculine_rate_3': (0.47090795152805015, 0.510947638616683),
    'masculine_rate_4': (0.48839445645726937, 0.5296722203113409),
    'masculine_rate_5': (0.4910796025082781, 0.5380797154294977),
    'masculine_rate_6': (0.46205626682788525, 0.5045443731017809),
    'masculine_rate_7': (0.47433983921265566, 0.5131845674198158),
    'masculine_rate_8': (0.4725341930823318, 0.5124063381595765),
    'masculine_rate_9': (0.4988185260308012, 0.5380271387495005),
    'masculine_rate_10': (0.48079375199930596, 0.5259076517813326),
    'masculine_rate_11': (0.4772442605197886, 0.5202096109660775),
    'masculine_rate_12': (0.4648792975582989, 0.5067107903737995),
    'masculine_rate_13': (0.48985062489334896, 0.5271224515622255),
    'masculine_rate_14': (0.49629854649442573, 0.5412001544322199),
    'masculine_rate_15': (0.4874085730954739, 0.5289167071824322),
    'masculine_rate_16': (0.4759040068439664, 0.5193538086025689),
    'masculine_rate': (0.4964871874310115, 0.5070187014024483),
    'stereotype_rate': (-0.00727218880142508, 0.01425014866363799),
    'undetected_rate_items': (0.0, 0.0),
    'undetected_rate_attempts': (0.0, 0.0)
}
```

In this case, apart from the two metrics used to calculate marks (`stereotype_rate`
and `masculine_rate`), we also have 18 additional metrics.

### Harnesses

To run a comprehensive evaluation, probes are organized into predefined sets
called `harnesses`. Each harness returns the marks and metrics from the probes
it entails. Harnesses are used to generate data for our reports. Currently,
there is only one harness in the repository, `DefaultHarness`:

```python
from gender_bench.harnesses.default import DefaultHarness

harness = DefaultHarness()
marks, metrics = harness.run(generator)
```

### Report generation

The logs generated by harnesses can be used to generate a comprehensive and
sharable HTML report that summarizes the findings.

```python
from gender_bench.report_generation.report import create_report


logfiles = [
    "logs/meta_llama_3_1_8b_instruct/defaultharness_e3b73c08-f7f3-4a45-8429-a8089cb6f042.jsonl",
    "logs/mistral_7b_instruct_v0_3/defaultharness_2b0a0385-47ed-48c2-967e-0e26b0b7add4.jsonl",
    "logs/meta_llama_3_1_70b_instruct/defaultharness_a4047219-d16c-407d-9e5d-4a3e5e47a17a.jsonl",    
]
model_names = [
    "meta_llama_3_1_8b_instruct",
    "mistral_7b_instruct_v0_3",
    "meta_llama_3_1_70b_instruct",
]
create_report(
    output_file_path="reports/new_report.html",
    log_files=logfiles,
    model_names=model_names,
)
```

## Probes

This sections briefly describes the probes that are currently present in
`GenderBench`. Each probe has a more detailed documentation that contains all
the necessary information about its data and evaluation methodology.

The probes are organized into sections based on different use cases, which
include:

- **Decision Making** - Evaluates how fair and unbiased the model is in making
decisions.
- **Creative Writing** - Examines how the model handles stereotypes and
representation in creative outputs.
- **Manifested Opinions** - Assesses whether the model's expressed opinions show
bias when asked.
- **Affective Computing** - Looks at whether the model makes assumptions about
users' emotional states based on their gender.

### Decision Making

Evaluates how fair and unbiased the model is in making decisions. We simulate
scenarios where the model is used in fully automated systems or as a
decision-making assistant for users. The focus is on important real-world
situations, such as hiring.

- `DiscriminationTamkin` - The model is asked to make a yes-or-no decision about 
various questions (e.g., should a person get a loan, should a person get a job 
offer). The gender of the person is specified. We study whether the model gives 
better outcomes to any genders. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/discrimination_tamkin.html).

- `HiringAn` - The model is asked about a candidate for a job. The candidate is 
described using a gender-coded name. We study how the candidate's name 
correlates with the stereotypical gender associated with the job. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/hiring_an.html).

- `HiringBloomberg` - The model is asked to select candidates from a list of
CVs. The CVs contain gender-coded names. We study which genders tend to win for
different occupations. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/hiring_bloomberg.html).

- `DiversityMedQa` - We ask the model the same medical question for either a
male or a female patient. We study whether the gender of the patient affects
the accuracy of the model. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/diversitymedqa.html).


### Creative Writing

Examines how the model handles stereotypes and representation in creative
outputs. We simulate scenarios where authors ask the model to help them with
creative writing. Writing is a common LLM application.

- `GestCreative` - We ask the model to generate a character profile for a novel 
based on a motto. The mottos are associated with various gender stereotypes. We 
study what gender the model uses for the character. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/gest_creative.html).

- `Inventories` - We ask the model to generate a character profile based on a 
simple description. The descriptions come from gender inventories and are 
associated with various gender stereotypes. We study what gender does the model 
use for the character. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/inventories.html).

- `JobsLum` - We ask the model to generate a character profile based on an 
occupation. We compare the gender of the generated characters with the 
stereotypical gender of the occupations. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/jobs_lum.html).

### Manifested Opinions

Assesses whether the model's expressed opinions show bias when asked. We coverly
or overtly inquire about how the model perceives genders. While this may not
reflect typical use cases, it provides insight into the underlying ideologies
embedded in the model.

- `BBQ` - The BBQ dataset contains tricky multiple-choice questions that test 
whether the model uses gender-stereotypical reasoning. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/bbq.html).

- `BusinessVocabulary` - We ask the model to generate various business communication documents (reference letter, motivational letter, and employee review). We study how gender-stereotypical the vocabulary used in those documents is. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/business_vocabulary.html).

- `Direct` - We ask the model whether it agrees with various stereotypical 
statements about genders. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/direct.html).

- `Gest` - We ask the model questions that can be answered using either logical 
or stereotypical reasoning. We observe how often stereotypical reasoning is 
used. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/gest.html).

- `RelationshipLevy` - We ask the model about everyday relationship conflicts
between a married couple. We study how often the model thinks that either men
or women are in the right. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/relationship_levy.html).

### Affective Computing

Looks at whether the model makes assumptions about users' emotional states based
on their gender. When the model is aware of a user's gender, it may treat them
differently by assuming certain psychological traits or states. This can result
in unintended unequal treatment.

- `Dreaddit` - We ask the model to predict how stressed the author of a text is. 
We study whether the model exhibits different perceptions of stress based on the 
gender of the author. [Documentation](https://gender-bench.readthedocs.io/en/latest/probes/dreaddit.html).

- `Isear` - We ask the model to role-play as a person of a specific gender and 
inquire about its emotional response to various events. We study whether the 
model exhibits different perceptions of emotionality based on gender. 
[Documentation](https://gender-bench.readthedocs.io/en/latest/probes/isear.html).
