import subprocess
from domain.models.pdf_document import PdfDocument

class PdfTransparencyService:
    """
    PDF の白背景を透明化するサービス。
    Ghostscript の pdfwrite デバイスでマスクカラーを設定し、
    ベクターベースの透過 PDF を生成する。
    """

    def make_transparent(
        self,
        pdf_doc: PdfDocument,
        output_name: str | None = None,
        mask_color: tuple[float, float, float] = (1.0, 1.0, 1.0),
        compatibility_level: float = 1.4
    ) -> PdfDocument:
        """
        Args:
            pdf_doc: 入力の PdfDocument
            output_name: 出力ファイル名 (省略時は '<stem>-transp.pdf')
            mask_color: 透過させたい背景色の RGB 値 (0.0-1.0)
            compatibility_level: PDF 互換性レベル

        Returns:
            PdfDocument: 透過化後の PDF ドキュメント
        """
        # 入力検証
        pdf_doc.validate()

        # 出力パス決定
        stem = pdf_doc.path.stem
        parent = pdf_doc.path.parent
        name = output_name or f"{stem}-transp.pdf"
        output_path = parent / name

        # Ghostscript コマンド構築
        # 順序: -sDEVICE, -dCompatibilityLevel, -sOutputFile, -c, -f
        cmd = [
            "gs",
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=pdfwrite",
            f"-dCompatibilityLevel={compatibility_level}",
            f"-sOutputFile={output_path}",
            "-c",
            f"<< /MaskColor [{mask_color[0]} {mask_color[1]} {mask_color[2]}] /ProcessColorModel /DeviceRGB >> setpagedevice",
            "-f",
            str(pdf_doc.path)
        ]
        subprocess.run(cmd, check=True)

        return PdfDocument(path=output_path)
