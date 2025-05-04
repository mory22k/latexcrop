import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TexDocument:
    content: str

    def validate(self) -> None:
        r"""
        Validate that the TeX source contains the following elements:
        - \documentclass
        - \begin{document}
        - \end{document}
        """
        # patterns = [r"\begin{document}", r"\end{document}"]
        patterns = [r"\\documentclass", r"\\begin{document}", r"\\end{document}"]
        for pat in patterns:
            if re.search(pat, self.content) is None:
                raise ValueError(
                    f"TeX source missing required element: {pat}"
                    f"TeX source: {self.content}"
                )

    def write_to(self, path: Path) -> None:
        """
        Export the TeX source to a file.
        """
        path.write_text(self.content, encoding="utf-8")
