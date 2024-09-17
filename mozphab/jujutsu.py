import os
import re
from pathlib import Path

from .exceptions import Error
from .git import Git
from .logger import logger
from .repository import Repository
from .subprocess_wrapper import check_output


class Jujutsu(Repository):
    @classmethod
    def is_repo(cls, path: str) -> bool:
        """Quick check for repository at specified path."""
        return os.path.exists(os.path.join(path, ".jj"))

    # ----
    # Methods expected from callers of the `Repository` interface:
    # ----

    def __init__(self, path: str):
        self.vcs_version = Jujutsu.__check_and_get_version()

        self.git_path = Path(check_output(["jj", "git", "root"], split=False))
        logger.debug(f"git_path: {self.git_path}")
        self.__git_repo = Git(self.git_path.parent)

        # Populate common fields expected from a `Repository`

        dot_path = os.path.join(path, ".jj")
        if not os.path.exists(dot_path):
            raise ValueError("%s: not a Jujutsu repository" % path)
        logger.debug("found Jujutsu repo in %s", path)
        super().__init__(path, dot_path)

        self.vcs = "jj"

        self.revset = None
        self.branch = None

    @staticmethod
    def __check_and_get_version() -> str:
        version_re = re.compile(r"jj (\d+)\.(\d+)\.(\d+)(-[a-fA-F0-9]{40})?")
        m = version_re.fullmatch(check_output(["jj", "version"], split=False))
        if not m:
            raise Error("Failed to determine Jujutsu version.")
        version_number_strs = m.group(1, 2, 3)
        version = list(map(int, version_number_strs))
        min_version = [0, 28, 0]
        if version < min_version:
            raise Error(
                f"`moz-phab` requires Jujutsu {'.'.join(map(str, min_version))} or higher."
            )
        return m.group(0)

