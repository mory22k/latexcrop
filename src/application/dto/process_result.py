from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class ProcessResult:
    """
    DTO that will be returned from Use Cases.

    Attributes:
        pdf_path (Path): 処理後の PDF ファイルへのパス
        logs (List[str]): 実行時に生成されたログメッセージのリスト
    """

    pdf_path: Path
    logs: List[str]
    is_success: bool = True
