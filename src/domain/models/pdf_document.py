from dataclasses import dataclass
from pathlib import Path
import tempfile

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

    @classmethod
    def from_bytes(cls, data: bytes, path: Path) -> "PdfDocument":
        """
        バイナリ PDF データを指定のパスに書き出し、
        PdfDocument インスタンスを生成して返す。

        Args:
            data: PDF のバイナリコンテンツ
            path: 書き出すファイルパス。存在しなければ親ディレクトリを作成する。

        Returns:
            PdfDocument: 書き出されたファイルを指すモデル
        Raises:
            ValueError: 書き込み中にエラーが発生した場合
        """
        # ディレクトリ作成
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        except OSError as e:
            raise ValueError(f"Cannot write PDF bytes to {path}: {e}")
        return cls(path=path)

    @classmethod
    def from_bytes_tempfile(cls, data: bytes, suffix: str = ".pdf") -> "PdfDocument":
        """
        バイナリ PDF データを一時ファイルに書き出し、
        PdfDocument インスタンスを返すユーティリティ。

        Args:
            data: PDF のバイナリコンテンツ
            suffix: 一時ファイルの拡張子（デフォルト '.pdf'）

        Returns:
            PdfDocument: 一時ファイルを指すモデル
        """
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            tf.write(data)
            tf.flush()
        finally:
            tf.close()
        return cls(path=Path(tf.name))
