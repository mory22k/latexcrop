from application.dto.crop_request import CropRequest
from application.dto.process_result import ProcessResult
from domain.models.pdf_document import PdfDocument
from domain.services.pdf_crop_service import PdfCropService


class TrimPdfUseCase:
    """
    Use Case that executes CropRequest.
    """

    def __init__(self, crop_service: PdfCropService):
        self.crop_service = crop_service

    def execute(self, request: CropRequest) -> ProcessResult:
        logs: list[str] = []
        # 入力モデル生成と検証
        pdf_doc = PdfDocument(path=request.pdf_path)
        pdf_doc.validate()
        logs.append("Validated PdfDocument.")

        # トリミング実行
        cropped = self.crop_service.crop(pdf_doc, request.margins)
        logs.append(f"Cropped PDF at {cropped.path}")

        return ProcessResult(pdf_path=cropped.path, logs=logs)
