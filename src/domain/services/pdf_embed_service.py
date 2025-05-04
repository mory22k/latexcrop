from typing import List, Optional
import pikepdf

from domain.models.pdf_document import PdfDocument
from domain.models.embedded_file import EmbeddedFile


class PdfEmbedService:
    """
    PdfDocument に .tex ファイルなどの添付を行い、新たな PdfDocument を返すサービス
    """

    def embed(
        self,
        pdf_doc: PdfDocument,
        embedded_files: List[EmbeddedFile],
        output_name: Optional[str] = None,
    ) -> PdfDocument:
        """
        Args:
            pdf_doc: 添付対象の PdfDocument
            embedded_files: EmbeddedFile オブジェクトのリスト
            output_name: 出力ファイル名（省略時は '<stem>-embed.pdf'）

        Returns:
            PdfDocument: 添付後の PDF ドキュメントモデル
        """
        # 入力 PDF の検証
        pdf_doc.validate()

        # 出力パスの決定
        stem = pdf_doc.path.stem
        parent = pdf_doc.path.parent
        output_filename = output_name or f"{stem}-embed.pdf"
        output_path = parent / output_filename

        # PDF を開いて添付を追加
        with pikepdf.Pdf.open(str(pdf_doc.path)) as pdf:
            for file in embedded_files:
                # EmbeddedFile の検証
                file.validate()
                # 添付処理
                pdf.attachments[file.name] = file.data
            # ファイルとして保存
            pdf.save(str(output_path))

        return PdfDocument(path=output_path)
