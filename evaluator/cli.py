"""Command-line interface: evaluate, qa, agreement."""
import argparse
import sys

from . import metrics, storage


def ask_score(label, dim):
    while True:
        raw = input(f"  {label} - {dim} (1-5): ").strip()
        if raw.isdigit() and metrics.MIN_SCORE <= int(raw) <= metrics.MAX_SCORE:
            return int(raw)
        print("  Please enter a whole number from 1 to 5.")


def ask_choice():
    while True:
        raw = input("Better response? (A / B / tie): ").strip()
        if raw.upper() in ("A", "B"):
            return raw.upper()
        if raw.lower() == "tie":
            return "tie"
        print("Please type A, B or tie.")


def ask_justification():
    while True:
        text = input("Written justification: ").strip()
        if len(text.split()) >= metrics.MIN_JUSTIFICATION_WORDS:
            return text
        print(f"Please write at least {metrics.MIN_JUSTIFICATION_WORDS} words explaining your choice.")


def cmd_evaluate(args):
    tasks = storage.load_tasks(args.tasks)
    done = storage.done_task_ids(args.out)
    pending = [t for t in tasks if t["id"] not in done]
    if not pending:
        print("All tasks already evaluated.")
        return 0
    for number, task in enumerate(pending, 1):
        print(f"\n=== Task {task['id']} ({number}/{len(pending)}) | language: {task['language']} ===")
        print(f"PROMPT:\n{task['prompt']}\n")
        print(f"RESPONSE A:\n{task['response_a']}\n")
        print(f"RESPONSE B:\n{task['response_b']}\n")
        scores = {"A": {}, "B": {}}
        for label in ("A", "B"):
            for dim in metrics.DIMENSIONS:
                scores[label][dim] = ask_score(label, dim)
        implied = metrics.implied_preference(scores["A"], scores["B"])
        print(f"Rubric totals -> A: {metrics.total_score(scores['A'])}, "
              f"B: {metrics.total_score(scores['B'])} (favours: {implied})")
        preferred = ask_choice()
        justification = ask_justification()
        record = {
            "task_id": task["id"],
            "language": task["language"],
            "rater": args.rater,
            "scores_a": scores["A"],
            "scores_b": scores["B"],
            "preferred": preferred,
            "justification": justification,
        }
        for finding in metrics.qa_findings(record):
            print(f"  [QA warning] {finding}")
        storage.append_record(args.out, record)
    print(f"\nSaved to {args.out}")
    return 0


def cmd_qa(args):
    records = storage.load_records(args.file)
    flagged = 0
    for record in records:
        findings = metrics.qa_findings(record)
        if findings:
            flagged += 1
            print(f"Task {record['task_id']}:")
            for finding in findings:
                print(f"  - {finding}")
    print(f"\n{flagged} of {len(records)} evaluations flagged.")
    return 1 if flagged else 0


def cmd_agreement(args):
    by_id_a = {r["task_id"]: r["preferred"] for r in storage.load_records(args.a)}
    by_id_b = {r["task_id"]: r["preferred"] for r in storage.load_records(args.b)}
    shared = sorted(set(by_id_a) & set(by_id_b))
    if not shared:
        print("No tasks in common between the two files.")
        return 1
    labels_a = [by_id_a[t] for t in shared]
    labels_b = [by_id_b[t] for t in shared]
    kappa = metrics.cohens_kappa(labels_a, labels_b)
    agree = sum(x == y for x, y in zip(labels_a, labels_b))
    print(f"Tasks compared: {len(shared)}")
    print(f"Raw agreement: {agree}/{len(shared)}")
    print(f"Cohen's kappa: {kappa:.2f} ({metrics.interpret_kappa(kappa)})")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="evaluator", description="LLM Response Evaluator")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("evaluate", help="score response pairs interactively")
    p.add_argument("--tasks", default="data/sample_tasks.json")
    p.add_argument("--rater", required=True, help="your name or id")
    p.add_argument("--out", required=True, help="output .jsonl file")
    p.set_defaults(func=cmd_evaluate)

    p = sub.add_parser("qa", help="flag inconsistent or weak evaluations")
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_qa)

    p = sub.add_parser("agreement", help="Cohen's kappa between two raters")
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.set_defaults(func=cmd_agreement)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (EOFError, KeyboardInterrupt):
        print("\nStopped. Finished evaluations were saved; run the same command to resume.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
