from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class ExtractRequest:
    """
    PDF から埋め込み TeX を抽出するリクエスト DTO。
    - pdf_path か pdf_bytes のどちらかを指定する。
    """
    pdf_path: Optional[Path] = None
    pdf_bytes: Optional[bytes] = None

    def __post_init__(self):
        if not (self.pdf_path or self.pdf_bytes):
            raise ValueError("pdf_path または pdf_bytes のいずれかを指定してください。")
