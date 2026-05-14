from pathlib import Path
import logging
import os
import tempfile
import shutil
import types

import git

IGNORE_DIRS = {
    "node_modules",
    ".git",
    ".vscode",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
}

IGNORE_FILES = {
    "uv.lock",
    ".gitignore",
}


class CloneRepo:
    def __init__(self, url: str):
        self.url = url
        self.repo_path = None
        self.base_temp_dir = Path(tempfile.gettempdir()) / "repochat"
        os.makedirs(self.base_temp_dir, exist_ok=True)

    def clone_repo(self) -> Path:
        """Clone repo from github url

        Args:
            url (str): url to repo

        Returns:
            pathlib.Path: path to repo

        Raises:
            ValueError: if url is invalid
        """

        self.repo_path = self.base_temp_dir / self.url.replace(
            "https://github.com/", ""
        ).replace(".git", "").replace("/", "_")

        if os.path.exists(self.repo_path):
            return self.repo_path

        try:
            git.Repo.clone_from(
                self.url, self.repo_path, env={"GIT_TERMINAL_PROMPT": "0"}
            )
            return self.repo_path
        except git.exc.GitCommandError as e:
            if os.path.exists(self.repo_path):
                shutil.rmtree(self.repo_path)
            logging.error(f"Error cloning repo: {self.url} with error: {e}")
            raise ValueError(f"Invalid url: {self.url}") from e

    def get_repo_files(self) -> types.GeneratorType:
        """yield files in repo

        Args:
            repo_path (str): path to repo

        Yields:
            str: path to file
        """
        walk = os.walk(self.repo_path)
        for root, dirs, files in walk:
            if set(dirs) & IGNORE_DIRS:
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                yield os.path.join(root, file)

    @staticmethod
    def is_text_file(file_path: str) -> bool:
        """Check if file is text file

        Args:
            file_path (str): path to file

        Returns:
            bool: True if file is text file
        """
        if not os.path.isfile(file_path):
            return False

        try:
            with open(file_path) as f:
                f.read()
            return True
        except UnicodeDecodeError:
            return False
