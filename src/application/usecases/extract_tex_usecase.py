# application/usecases/extract_tex_usecase.py

import re
from application.dto.extract_request import ExtractRequest
from application.dto.extract_result import ExtractResult
from domain.models.pdf_document import PdfDocument
from domain.services.pdf_extract_service import PdfExtractService

class ExtractTexUseCase:
    """
    ユースケース：PDF に埋め込まれた最初の .tex ファイルから
    preamble と body を抽出して返却する。
    """

    def __init__(self, extract_service: PdfExtractService):
        self.extract_service = extract_service

    def execute(self, request: ExtractRequest) -> ExtractResult:
        # PdfDocument をバイナリ or パスから生成
        if request.pdf_bytes is not None:
            pdf_doc = PdfDocument.from_bytes_tempfile(request.pdf_bytes)
        else:
            pdf_doc = PdfDocument(path=request.pdf_path)  # type: ignore

        pdf_doc.validate()
        # 全ての埋め込み .tex ファイルを抽出
        files = self.extract_service.extract(pdf_doc)
        if not files:
            raise ValueError("PDF内に .tex ファイルが埋め込まれていません。")

        # 最初のファイルのみ対象
        tex_content = files[0].data.decode("utf-8")

        # preamble と body に分割
        # \begin{document} の前後で split
        parts = re.split(r"\\begin\{document\}", tex_content, maxsplit=1)
        if len(parts) < 2:
            raise ValueError("\\begin{document} が見つかりません。")
        preamble = parts[0]

        rest = parts[1]
        body_parts = re.split(r"\\end\{document\}", rest, maxsplit=1)
        if not body_parts:
            raise ValueError("\\end{document} が見つかりません。")
        body = body_parts[0]

        return ExtractResult(
            preamble=preamble.strip(),
            body=body.strip()
        )
