import reflex as rx
from typing import List, Optional, Tuple
import base64
import pikepdf
import logging
from pathlib import Path
import asyncio
import tempfile
import shutil

# バックエンドのインポート
from application.usecases.generate_pdf_usecase import GeneratePdfUseCase
from application.usecases.trim_pdf_usecase import TrimPdfUseCase
from application.usecases.embed_tex_usecase import EmbedTexUseCase
from application.dto.compile_request import CompileRequest
from application.dto.crop_request import CropRequest
from application.dto.embed_request import EmbedRequest
from domain.models.embedded_file import EmbeddedFile

# Logger設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackendIntegration:
    """バックエンドとの統合クラス"""
    
    def __init__(self):
        # 実際のサービス実装をインポート
        from infrastructure.services.services_implementations import (
            LatexCompileServiceImpl,
            PdfCropServiceImpl,
            PdfEmbedServiceImpl
        )
        
        compile_service = LatexCompileServiceImpl()
        crop_service = PdfCropServiceImpl()
        embed_service = PdfEmbedServiceImpl()
        
        self.generate_pdf_usecase = GeneratePdfUseCase(compile_service=compile_service)
        self.trim_pdf_usecase = TrimPdfUseCase(crop_service=crop_service)
        self.embed_tex_usecase = EmbedTexUseCase(embed_service=embed_service)
    
    async def process_latex(
        self,
        tex_content: str,
        latexmkrc_content: str,
        margins: Tuple[float, float, float, float] = (0, 0, 0, 0)
    ):
        """LaTeXを処理して埋め込みPDFを生成"""
        
        try:
            # 1. PDFコンパイル
            compile_request = CompileRequest(
                tex_content=tex_content,
                latexmkrc_content=latexmkrc_content
            )
            compile_result = self.generate_pdf_usecase.execute(compile_request)
            
            if compile_result.pdf_path is None:
                raise Exception("PDF compilation failed")
            
            # 2. PDFクロッピング
            crop_request = CropRequest(
                pdf_path=compile_result.pdf_path,
                margins=margins
            )
            crop_result = self.trim_pdf_usecase.execute(crop_request)
            
            if crop_result.pdf_path is None:
                raise Exception("PDF cropping failed")
            
            # 3. LaTeXソースコードの埋め込み
            tex_file = EmbeddedFile(
                name="source.tex",
                data=tex_content.encode('utf-8')
            )
            
            embed_request = EmbedRequest(
                pdf_path=crop_result.pdf_path,
                embedded_files=[tex_file]
            )
            embed_result = self.embed_tex_usecase.execute(embed_request)
            
            return embed_result
            
        except Exception as e:
            raise Exception(f"Processing failed: {str(e)}")


# シングルトン的に使用するバックエンドインスタンス
_backend_integration = None

def get_backend_integration():
    """バックエンド統合インスタンスを取得"""
    global _backend_integration
    if _backend_integration is None:
        _backend_integration = BackendIntegration()
    return _backend_integration


class State(rx.State):
    # LaTeXコンテンツ
    tex_content: str = r"\textsc{Hello,} \smething{WORLD!}" + "\n"
    latexmkrc_content: str = r"""$pdf_mode = 1;
$latex = 'xelatex -synctex=1 -interaction=nonstopmode %O %S';
$max_repeat = 5;
"""
    
    # PDFビューア関連
    pdf_src: str = ""
    pdf_filename: str = "output.pdf"
    current_page: int = 1
    total_pages: int = 1
    zoom_level: int = 100
    
    # ログ表示
    process_logs: List[str] = []
    is_processing: bool = False
    
    # エラー状態
    error_message: str = ""
    
    def update_tex_content(self, content: str):
        """LaTeXコンテンツを更新"""
        self.tex_content = content
    
    def update_latexmkrc_content(self, content: str):
        """latexmkrcコンテンツを更新"""
        self.latexmkrc_content = content
    
    async def compile_latex(self):
        """LaTeXをコンパイルし、PDFを生成、クロップ、埋め込みを実行"""
        self.is_processing = True
        self.error_message = ""
        self.process_logs = []
        self.pdf_src = ""
        
        yield
        
        try:
            # バックエンドを取得
            backend = get_backend_integration()
            
            # バックエンドでLaTeXを処理
            self.add_log("Starting compilation process...")
            result = await backend.process_latex(
                tex_content=self.tex_content,
                latexmkrc_content=self.latexmkrc_content,
                margins=(0, 0, 0, 0)
            )
            
            # ログを更新
            for log in result.logs:
                self.add_log(log)
            
            # PDFを読み込んでbase64エンコード
            if result.pdf_path and result.pdf_path.exists():
                with open(result.pdf_path, "rb") as f:
                    pdf_data = f.read()
                base64_data = base64.b64encode(pdf_data).decode()
                self.pdf_src = f"data:application/pdf;base64,{base64_data}"
                self.pdf_filename = "output.pdf"
                
                # PDFページ数取得
                try:
                    with pikepdf.open(result.pdf_path) as pdf:
                        self.total_pages = len(pdf.pages)
                        self.current_page = 1
                except Exception as e:
                    self.add_log(f"Warning: Could not determine PDF page count: {e}")
            else:
                raise Exception("Processed PDF not found")
            
            self.add_log("Process completed successfully!")
            
        except Exception as e:
            self.error_message = f"Error: {str(e)}"
            self.add_log(f"Error: {str(e)}")
            logger.error(f"Error in compile_latex: {e}")
        finally:
            self.is_processing = False
            yield
    
    def add_log(self, message: str):
        """ログを追加"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.process_logs.append(log_entry)
        logger.info(message)
    
    def handle_upload(self, files: List[rx.UploadFile]):
        """PDFファイルのアップロード処理"""
        if not files:
            return
        
        file = files[0]
        uploaded_filename = file.filename or "uploaded.pdf"
        
        # ファイルの内容を読み込んでbase64エンコード
        content = file.read()
        base64_data = base64.b64encode(content).decode()
        self.pdf_src = f"data:application/pdf;base64,{base64_data}"
        self.pdf_filename = uploaded_filename
        
        # PDFページ数取得
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
                tmp.write(content)
                tmp.flush()
                with pikepdf.open(tmp.name) as pdf:
                    self.total_pages = len(pdf.pages)
                    self.current_page = 1
                    self.zoom_level = 100
        except Exception as e:
            self.error_message = f"Error reading PDF: {str(e)}"
            self.pdf_src = ""
            self.add_log(f"Error reading PDF: {str(e)}")
    
    def download_pdf(self):
        """PDFをダウンロード"""
        if self.pdf_src:
            import webbrowser
            from urllib.parse import quote
            
            # data URLはブラウザに任せる
            webbrowser.open(self.pdf_src)
        
    def change_page(self, delta: int):
        """PDFページを変更"""
        new_page = self.current_page + delta
        if 1 <= new_page <= self.total_pages:
            self.current_page = new_page
    
    def change_zoom(self, delta: int):
        """ズームレベルを変更"""
        new_zoom = self.zoom_level + delta
        if 50 <= new_zoom <= 200:
            self.zoom_level = new_zoom
    
    def reset_view(self):
        """ビューをリセット"""
        self.current_page = 1
        self.zoom_level = 100


def pdf_viewer() -> rx.Component:
    """PDFビューアコンポーネント"""
    return rx.vstack(
        # PDFビューア
        rx.cond(
            State.pdf_src,
            rx.vstack(
                # ツールバー
                rx.hstack(
                    rx.hstack(
                        rx.button(
                            rx.icon("arrow-left", size=16),
                            on_click=lambda: State.change_page(-1),
                            disabled=State.current_page <= 1,
                            size="2",
                            variant="surface",
                        ),
                        rx.text(
                            State.current_page,
                            " / ",
                            State.total_pages,
                            align="center",
                        ),
                        rx.button(
                            rx.icon("arrow-right", size=16),
                            on_click=lambda: State.change_page(1),
                            disabled=State.current_page >= State.total_pages,
                            size="2",
                            variant="surface",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon("minus", size=16),
                            on_click=lambda: State.change_zoom(-25),
                            disabled=State.zoom_level <= 50,
                            size="2",
                            variant="surface",
                        ),
                        rx.text(f"{State.zoom_level}%", width="4em", text_align="center"),
                        rx.button(
                            rx.icon("plus", size=16),
                            on_click=lambda: State.change_zoom(25),
                            disabled=State.zoom_level >= 200,
                            size="2",
                            variant="surface",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon("refresh-cw", size=16),
                            on_click=State.reset_view,
                            size="2",
                            variant="surface",
                        ),
                        rx.button(
                            rx.icon("download", size=16),
                            on_click=State.download_pdf,
                            size="2",
                            variant="surface",
                        ),
                        spacing="2",
                    ),
                    justify="between",
                    width="100%",
                    padding="2",
                    border_bottom="1px solid #E2E8F0",
                ),
                # PDF表示エリア
                rx.box(
                    rx.html(
                        f"""
                        <iframe 
                            src="{State.pdf_src}#page={State.current_page}" 
                            style="width: {State.zoom_level}%; height: 100%; border: none;"
                        ></iframe>
                        """
                    ),
                    width="100%",
                    height="500px",
                    overflow="auto",
                    border="1px solid #E2E8F0",
                    border_radius="md",
                    bg="gray.100",
                ),
                width="100%",
                spacing="2",
            ),
            rx.box(
                rx.text("No PDF to display", color="gray", size="4"),
                width="100%",
                height="500px",
                display="flex",
                align_items="center",
                justify_content="center",
                border="1px solid #E2E8F0",
                border_radius="md",
            ),
        ),
        width="100%",
        spacing="2",
    )


def index() -> rx.Component:
    """メインページ"""
    return rx.container(
        rx.vstack(
            # ヘッダー
            rx.heading("LaTeX Crop Renderer", size="7", margin_bottom="4"),
            
            # PDFビューア
            pdf_viewer(),
            
            # LaTeXエディタ
            rx.hstack(
                rx.vstack(
                    rx.heading("LaTeX Source", size="4", margin_bottom="2"),
                    rx.text_area(
                        value=State.tex_content,
                        on_change=State.update_tex_content,
                        placeholder="Enter LaTeX code...",
                        width="100%",
                        height="250px",
                        font_family="monospace",
                        resize="none",
                    ),
                    rx.button(
                        "Compile",
                        on_click=State.compile_latex,
                        loading=State.is_processing,
                        size="3",
                        color_scheme="blue",
                        width="100%",
                    ),
                    width="50%",
                    spacing="2",
                ),
                rx.vstack(
                    rx.heading("latexmkrc", size="4", margin_bottom="2"),
                    rx.text_area(
                        value=State.latexmkrc_content,
                        on_change=State.update_latexmkrc_content,
                        placeholder="Enter latexmkrc content...",
                        width="100%",
                        height="250px",
                        font_family="monospace",
                        resize="none",
                    ),
                    rx.button(
                        "Reset",
                        on_click=lambda: State.update_latexmkrc_content(
                            r"""$pdf_mode = 1;
$latex = 'xelatex -synctex=1 -interaction=nonstopmode %O %S';
$max_repeat = 5;
"""
                        ),
                        size="3",
                        width="100%",
                        variant="surface",
                    ),
                    width="50%",
                    spacing="2",
                ),
                width="100%",
                spacing="4",
            ),
            
            # アップロードエリア
            rx.divider(margin="4"),
            rx.heading("Upload PDF", size="4", margin_bottom="2"),
            rx.upload(
                rx.vstack(
                    rx.button(
                        "Upload PDF",
                        rx.icon("upload", size=16),
                        size="3",
                        variant="surface",
                    ),
                    rx.text("or drag and drop here", color="gray"),
                    align="center",
                    spacing="2",
                ),
                id="pdf_upload",
                accept={"application/pdf": [".pdf"]},
                max_files=1,
                disabled=State.is_processing,
                multiple=False,
                padding="4",
                border="2px dashed #E2E8F0",
                border_radius="md",
                width="100%",
            ),
            rx.button(
                "Process Uploaded File",
                on_click=lambda: State.handle_upload(rx.upload_files()),
                loading=State.is_processing,
                size="3",
                variant="surface",
                width="100%",
                margin_top="2",
            ),
            
            # ログ表示
            rx.divider(margin="4"),
            rx.heading("Process Logs", size="4", margin_bottom="2"),
            rx.box(
                rx.foreach(
                    State.process_logs,
                    lambda log: rx.text(log, font_family="monospace", size="2"),
                ),
                width="100%",
                height="150px",
                overflow_y="auto",
                padding="2",
                bg="#F7FAFC",
                border="1px solid #E2E8F0",
                border_radius="md",
            ),
            
            # エラー表示
            rx.cond(
                State.error_message,
                rx.callout(
                    State.error_message,
                    icon="alert_circle",
                    color_scheme="red",
                    margin_top="4",
                ),
            ),
            
            width="100%",
            max_width="1200px",
            margin="auto",
            padding="4",
        ),
        sizing="content",
    )


app = rx.App(theme=rx.theme(accent_color="indigo"))
app.add_page(index)