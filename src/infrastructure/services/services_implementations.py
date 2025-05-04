# src/infrastructure/services/latex_compile_service_impl.py
import subprocess
from pathlib import Path
from typing import Optional
import logging

from domain.services.latex_compile_service import LatexCompileService
from domain.models.pdf_document import PdfDocument
from domain.models.tex_document import TexDocument
from domain.models.latexmkrc_source import LatexmkrcSource

logger = logging.getLogger(__name__)


class LatexCompileServiceImpl(LatexCompileService):
    """LaTeXコンパイルサービスの実装"""
    
    def compile(self, tex_doc: TexDocument, latexmkrc: LatexmkrcSource) -> PdfDocument:
        # 一時ディレクトリでコンパイル
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # TeXファイルを書き込み
            tex_file = tmpdir_path / "main.tex"
            tex_file.write_text(tex_doc.content, encoding="utf-8")
            
            # latexmkrcを書き込み
            latexmkrc_file = tmpdir_path / ".latexmkrc"
            latexmkrc_file.write_text(latexmkrc.content, encoding="utf-8")
            
            # latexmkコマンドを実行
            try:
                subprocess.run(
                    ["latexmk", "-pdf", "-f", "main.tex"],
                    cwd=tmpdir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # PDFファイルの場所
                pdf_path = tmpdir_path / "main.pdf"
                if not pdf_path.exists():
                    raise FileNotFoundError("PDF was not generated")
                
                # 出力ディレクトリにコピー
                output_path = Path.cwd() / f"output_{tex_doc.hash()}.pdf"
                import shutil
                shutil.copy(pdf_path, output_path)
                
                return PdfDocument(path=output_path)
                
            except subprocess.CalledProcessError as e:
                logger.error(f"LaTeX compilation failed: {e.stderr}")
                raise RuntimeError(f"Compilation failed: {e.stderr}")


# src/infrastructure/services/pdf_crop_service_impl.py
import pikepdf
from typing import Tuple

from domain.services.pdf_crop_service import PdfCropService
from domain.models.pdf_document import PdfDocument


class PdfCropServiceImpl(PdfCropService):
    """PDFクロップサービスの実装"""
    
    def crop(self, pdf_doc: PdfDocument, margins: Tuple[float, float, float, float]) -> PdfDocument:
        top, right, bottom, left = margins
        
        # PDFを開いてクロップ
        with pikepdf.open(pdf_doc.path) as pdf:
            for page in pdf.pages:
                # MediaBoxを取得
                mediabox = page.MediaBox
                
                # 新しいMediaBoxを設定（マージンを適用）
                new_mediabox = [
                    float(mediabox[0]) + left,
                    float(mediabox[1]) + bottom,
                    float(mediabox[2]) - right,
                    float(mediabox[3]) - top
                ]
                
                page.MediaBox = new_mediabox
                # TrimBoxも同様に設定
                page.TrimBox = new_mediabox
            
            # 新しいファイルに保存
            output_path = pdf_doc.path.with_name(f"{pdf_doc.path.stem}-crop.pdf")
            pdf.save(output_path)
            
        return PdfDocument(path=output_path)


# src/infrastructure/services/pdf_embed_service_impl.py
from typing import List

from domain.services.pdf_embed_service import PdfEmbedService
from domain.models.pdf_document import PdfDocument
from domain.models.embedded_file import EmbeddedFile


class PdfEmbedServiceImpl(PdfEmbedService):
    """PDF埋め込みサービスの実装"""
    
    def embed(self, pdf_doc: PdfDocument, files: List[EmbeddedFile]) -> PdfDocument:
        import pikepdf
        
        with pikepdf.open(pdf_doc.path) as pdf:
            # Names辞書を取得または作成
            if "/Names" not in pdf.Root:
                pdf.Root.Names = pdf.make_indirect(pikepdf.Dictionary())
            
            if "/EmbeddedFiles" not in pdf.Root.Names:
                pdf.Root.Names.EmbeddedFiles = pdf.make_indirect(pikepdf.Dictionary())
                pdf.Root.Names.EmbeddedFiles.Names = pikepdf.Array()
            
            # ファイルを埋め込み
            for file in files:
                # File Specificationオブジェクトを作成
                file_spec = pdf.make_indirect(pikepdf.Dictionary(
                    Type=pikepdf.Name("/Filespec"),
                    F=file.name,
                    UF=file.name,
                    EF=pikepdf.Dictionary(
                        F=pdf.make_indirect(pikepdf.Dictionary(
                            Type=pikepdf.Name("/EmbeddedFile"),
                            Length=len(file.data),
                            Params=pikepdf.Dictionary(
                                Size=len(file.data)
                            )
                        ))
                    )
                ))
                
                # ストリームデータを設定
                file_spec.EF.F._data = file.data
                
                # Namesに追加
                names_array = pdf.Root.Names.EmbeddedFiles.Names
                names_array.append(file.name)
                names_array.append(file_spec)
            
            # 新しいファイルに保存
            output_path = pdf_doc.path.with_name(f"{pdf_doc.path.stem}-embed.pdf")
            pdf.save(output_path)
            
        return PdfDocument(path=output_path)