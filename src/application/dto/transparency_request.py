from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Optional

@dataclass(frozen=True)
class TransparencyRequest:
    """
    Attributes:
        pdf_path (Path): 入力 PDF ファイルへのパス
        output_name (Optional[str]): 出力ファイル名（省略時は '<stem>-transp.pdf'）
        mask_color (Tuple[float, float, float]): 透過させたい背景色の RGB 値 (0.0-1.0)
        compatibility_level (float): PDF 互換性レベル
    """
    pdf_path: Path
    output_name: Optional[str] = None
    mask_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    compatibility_level: float = 1.4
