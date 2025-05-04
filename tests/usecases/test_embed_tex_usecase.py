from unittest.mock import MagicMock, ANY

from application.usecases.embed_tex_usecase import EmbedTexUseCase
from application.dto.embed_request import EmbedRequest
from application.dto.process_result import ProcessResult
from domain.services.pdf_embed_service import PdfEmbedService
from domain.models.pdf_document import PdfDocument
from domain.models.embedded_file import EmbeddedFile


def test_embed_tex_usecase_success(tmp_path):
    # Arrange
    input_pdf_path = tmp_path / "in.pdf"
    input_pdf_path.write_bytes(b"%PDF-1.4")
    dummy_embed_path = tmp_path / "in-embed.pdf"
    dummy_embed_path.write_bytes(b"%PDF-1.4")
    dummy_embedded = PdfDocument(path=dummy_embed_path)

    embedded_file = EmbeddedFile(name="test.tex", data=b"content")
    mock_service = MagicMock(spec=PdfEmbedService)
    mock_service.embed.return_value = dummy_embedded

    usecase = EmbedTexUseCase(embed_service=mock_service)
    request = EmbedRequest(pdf_path=input_pdf_path, embedded_files=[embedded_file])

    # Act
    result = usecase.execute(request)

    # Assert
    assert isinstance(result, ProcessResult)
    assert result.pdf_path == dummy_embedded.path
    assert "Validated PdfDocument." in result.logs
    assert f"Embedded files into PDF at {dummy_embedded.path}" in result.logs
    mock_service.embed.assert_called_once_with(ANY, [embedded_file])

    print(result.logs)
