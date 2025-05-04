# application/dto/pipeline_request.py
from dataclasses import dataclass
from typing import Tuple, Sequence
from domain.models.embedded_file import EmbeddedFile


@dataclass(frozen=True)
class PipelineRequest:
    tex_content: str
    latexmkrc_content: str
    margins: Tuple[int, int, int, int]
    embedded_files: Sequence[EmbeddedFile]
