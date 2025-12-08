from __future__ import annotations

import argparse
from pathlib import Path

from novaedit.model.tokenization_novaedit import NovaEditTokenizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a BPE tokenizer for NovaEdit.")
    parser.add_argument("--input-glob", required=True, help="Glob for training text files, e.g. 'data/python/raw/**/*.py'")
    parser.add_argument("--output", required=True, type=Path, help="Where to save the tokenizer json file.")
    parser.add_argument("--vocab-size", type=int, default=32000)
    parser.add_argument("--min-frequency", type=int, default=2)
    args = parser.parse_args()

    files = [str(p) for p in Path().glob(args.input_glob)]
    if not files:
        raise SystemExit(f"No files matched glob {args.input_glob}")

    tokenizer = NovaEditTokenizer()
    tokenizer.train_from_files(files, vocab_size=args.vocab_size, min_frequency=args.min_frequency)
    tokenizer.save(args.output)
    print(f"Saved tokenizer to {args.output}")


if __name__ == "__main__":
    main()
