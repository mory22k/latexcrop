from unittest.mock import MagicMock, ANY

from application.usecases.trim_pdf_usecase import TrimPdfUseCase
from application.dto.crop_request import CropRequest
from application.dto.process_result import ProcessResult
from domain.services.pdf_crop_service import PdfCropService
from domain.models.pdf_document import PdfDocument


def test_trim_pdf_usecase_success(tmp_path):
    # Arrange
    input_pdf_path = tmp_path / "input.pdf"
    input_pdf_path.write_bytes(b"%PDF-1.4")
    dummy_cropped_path = tmp_path / "input-crop.pdf"
    dummy_cropped_path.write_bytes(b"%PDF-1.4")
    dummy_cropped = PdfDocument(path=dummy_cropped_path)

    mock_service = MagicMock(spec=PdfCropService)
    mock_service.crop.return_value = dummy_cropped

    usecase = TrimPdfUseCase(crop_service=mock_service)
    request = CropRequest(pdf_path=input_pdf_path, margins=(0, 0, 0, 0))

    # Act
    result = usecase.execute(request)

    # Assert
    assert isinstance(result, ProcessResult)
    assert result.pdf_path == dummy_cropped.path
    assert "Validated PdfDocument." in result.logs
    mock_service.crop.assert_called_once_with(ANY, request.margins)
    print(result.logs)
