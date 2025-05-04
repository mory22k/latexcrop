from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class LatexmkrcSource:
    """
    Domain model for a latexmkrc configuration source.
    Attributes:
        content (str): The full text of the latexmkrc.
    """

    content: str

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """
        Validate that the latexmkrc content is non-empty and contains at least
        one latexmk directive (e.g. setting $latex).
        Raises:
            ValueError: If content is empty or missing expected directives.
        """
        if not self.content or not self.content.strip():
            raise ValueError("latexmkrc content must not be empty.")
        # Simple heuristic: ensure there's at least one variable assignment
        if not re.search(r"^\s*\$\w+\s*=", self.content, re.MULTILINE):
            raise ValueError(
                "latexmkrc should define at least one variable assignment, "
                "e.g. \"$latex = 'xelatex ...';\""
            )

    def write_to(self, directory: Path) -> Path:
        """
        Write this latexmkrc content into a file named 'latexmkrc' under the given directory.
        Args:
            directory (Path): Target directory (will be created if necessary).
        Returns:
            Path: Path to the written latexmkrc file.
        """
        directory.mkdir(parents=True, exist_ok=True)
        rc_path = directory / "latexmkrc"
        rc_path.write_text(self.content, encoding="utf-8")
        return rc_path
