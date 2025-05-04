import subprocess

from domain.models.pdf_document import PdfDocument


class PdfCropService:
    """
    PdfDocument を受け取り、pdfcrop コマンドで余白を削除し新しい PdfDocument を返すサービス
    """

    def crop(
        self,
        pdf_doc: PdfDocument,
        margins: tuple[int, int, int, int] = (0, 0, 0, 0),
        output_name: str | None = None,
    ) -> PdfDocument:
        """
        Args:
            pdf_doc: トリミング対象の PdfDocument
            margins: (left, top, right, bottom) の余白設定（pt単位）
            output_name: 出力ファイル名を指定（デフォルトは '<stem>-crop.pdf'）

        Returns:
            PdfDocument: トリミング後の PDF ドキュメントモデル
        """
        # 入力の検証
        pdf_doc.validate()

        # マージン文字列生成
        margin_str = " ".join(str(m) for m in margins)

        # 出力パス決定
        if output_name:
            output_path = pdf_doc.path.parent / output_name
        else:
            output_path = pdf_doc.path.with_name(f"{pdf_doc.path.stem}-crop.pdf")

        # pdfcrop コマンド実行
        subprocess.run(
            ["pdfcrop", "--margins", margin_str, str(pdf_doc.path), str(output_path)],
            cwd=pdf_doc.path.parent,
            check=True,
        )

        # 結果を PdfDocument として返却
        return PdfDocument(path=output_path)
