from application.dto.embed_request import EmbedRequest
from application.dto.process_result import ProcessResult
from domain.models.pdf_document import PdfDocument
from domain.services.pdf_embed_service import PdfEmbedService


class EmbedTexUseCase:
    """
    Use Case that executes EmbedRequest.
    """

    def __init__(self, embed_service: PdfEmbedService):
        self.embed_service = embed_service

    def execute(self, request: EmbedRequest) -> ProcessResult:
        logs: list[str] = []
        # 入力モデル生成と検証
        pdf_doc = PdfDocument(path=request.pdf_path)
        pdf_doc.validate()
        logs.append("Validated PdfDocument.")

        # 添付実行
        embedded = self.embed_service.embed(pdf_doc, request.embedded_files)
        logs.append(f"Embedded files into PDF at {embedded.path}")

        return ProcessResult(pdf_path=embedded.path, logs=logs)
