# LLM Response Evaluator

A small Python command-line tool for practising the core workflow of AI-response evaluation:
compare two answers to the same prompt, score them with a rubric, pick the better one,
justify the choice in writing, and check the quality and consistency of the judgments.

Built with the Python standard library only (no installs needed). Sample tasks are in
English and Portuguese.

## What it does

| Command | Purpose |
|---|---|
| `evaluate` | Shows a prompt with Response A and Response B, asks for 1-5 scores on **accuracy**, **instruction following** and **clarity**, then the preferred answer and a written justification. |
| `qa` | Flags evaluations where the preferred response **contradicts the rubric scores**, or where the justification is too short. |
| `agreement` | Computes **Cohen's kappa** between two raters who evaluated the same tasks. |

## Quick start

Requires Python 3.9+.

```bash
git clone https://github.com/gabzsamp/llm-response-evaluator.git
cd llm-response-evaluator

# 1. Evaluate the sample tasks (progress is saved after every task)
python -m evaluator evaluate --rater yourname --out data/evaluations_yourname.jsonl

# 2. Check your own judgments
python -m evaluator qa --file data/evaluations_yourname.jsonl

# 3. Compare two raters
python -m evaluator agreement --a data/evaluations_yourname.jsonl --b data/evaluations_friend.jsonl
```

Use your own tasks with `--tasks path/to/tasks.json`. Each task needs
`id`, `language`, `prompt`, `response_a`, `response_b` (see `data/sample_tasks.json`).

## The rubric

| Dimension | 1 | 5 |
|---|---|---|
| Accuracy | Mostly wrong or invented | Fully correct |
| Instruction following | Ignores the instructions (format, length, count) | Follows every instruction |
| Clarity | Confusing or padded | Clear, well organised, natural |

## How the checks work

- **Contradiction check:** the totals of the three scores imply a winner. If you chose the other
  response, the tool warns you. A tie never counts as a contradiction.
- **Cohen's kappa:** `(observed agreement - chance agreement) / (1 - chance agreement)`.
  0 means agreement no better than chance, 1 means perfect agreement.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```
evaluator/metrics.py   scoring, QA checks, Cohen's kappa (pure functions)
evaluator/storage.py   reading tasks, saving evaluations as JSON Lines
evaluator/cli.py       command-line interface
tests/                 unit tests for the metrics
data/sample_tasks.json sample tasks (English and Portuguese)
```

## Author

Gabriel Sampaio de Souza, Brazil. Licensed under the MIT License (see `LICENSE`).
