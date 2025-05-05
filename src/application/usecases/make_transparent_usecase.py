from application.dto.transparency_request import TransparencyRequest
from application.dto.process_result import ProcessResult
from domain.models.pdf_document import PdfDocument
from domain.services.pdf_transparency_service import PdfTransparencyService

class MakeTransparentUseCase:
    """
    PDF透過処理のユースケース
    """

    def __init__(
        self,
        transparency_service: PdfTransparencyService
    ):
        self.transparency_service = transparency_service

    def execute(self, request: TransparencyRequest) -> ProcessResult:
        logs: list[str] = []

        # 入力モデル生成と検証
        pdf_doc = PdfDocument(path=request.pdf_path)
        pdf_doc.validate()
        logs.append(f"Validated PDF: {request.pdf_path}")

        # 透過処理実行
        transp_doc = self.transparency_service.make_transparent(
            pdf_doc,
            output_name=request.output_name,
            mask_color=request.mask_color,
            compatibility_level=request.compatibility_level
        )
        logs.append(f"Generated transparent PDF: {transp_doc.path}")

        return ProcessResult(pdf_path=transp_doc.path, logs=logs)
