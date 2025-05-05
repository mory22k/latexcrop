from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class PipelineRequest:
    tex_content: str
    latexmkrc_content: str
    margins: Tuple[int, int, int, int]
