from dataclasses import dataclass
from pathlib import Path
from typing import List

from domain.models.embedded_file import EmbeddedFile


@dataclass(frozen=True)
class EmbedRequest:
    """
    DTO that will be passed to EmbedTexUseCase.

    Attributes:
        pdf_path (Path): 添付対象の PDF ファイルへのパス
        embedded_files (List[EmbeddedFile]): 添付するファイルのリスト
    """

    pdf_path: Path
    embedded_files: List[EmbeddedFile]
