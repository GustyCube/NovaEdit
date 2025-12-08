from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import HfApi, HfFolder, upload_folder


def push_to_hub(repo: str, path: Path, private: bool = False) -> None:
    token = HfFolder.get_token()
    if token is None:
        raise SystemExit("Login with `huggingface-cli login` first.")
    api = HfApi()
    api.create_repo(repo_id=repo, exist_ok=True, private=private)
    upload_folder(repo_id=repo, folder_path=str(path))
    print(f"Uploaded {path} to {repo}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Hub repo name, e.g. org/novaedit-small")
    parser.add_argument("--path", type=Path, required=True, help="Folder containing weights/config")
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args()
    push_to_hub(args.repo, args.path, private=args.private)


if __name__ == "__main__":
    main()
