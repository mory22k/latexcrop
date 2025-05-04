from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PdfDocument:
    path: Path

    def validate(self) -> None:
        """
        Validate that:
        - The file exists
        - The file starts with '%PDF-'
        """
        # 存在確認
        if not self.path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.path}")

        # ヘッダー検証
        try:
            with self.path.open("rb") as f:
                header = f.read(5)
            if header != b"%PDF-":
                raise ValueError(f"File does not start with '%PDF-': {self.path}")
        except OSError as e:
            raise ValueError(f"Cannot read file: {e}")
