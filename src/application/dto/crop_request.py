from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass(frozen=True)
class CropRequest:
    """
    DTO that will be passed to TrimPdfUseCase.

    Attributes:
        pdf_path (Path): トリミング対象の PDF ファイルへのパス
        margins (Tuple[int, int, int, int]): (left, top, right, bottom) の余白設定（pt単位）
    """

    pdf_path: Path
    margins: Tuple[int, int, int, int]
