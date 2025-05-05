# main.py
from pathlib import Path
import reflex as rx

# DTO & Models
from application.dto.process_result import ProcessResult
from application.dto.pipeline_request import PipelineRequest

# UseCases
from application.usecases.generate_pdf_usecase import GeneratePdfUseCase
from application.usecases.trim_pdf_usecase import TrimPdfUseCase
from application.usecases.embed_tex_usecase import EmbedTexUseCase
from application.usecases.make_transparent_usecase import MakeTransparentUseCase
from application.usecases.process_pdf_pipeline_usecase import ProcessPdfPipelineUseCase

# Services
from domain.services.latex_compile_service import LatexCompileService
from domain.services.pdf_crop_service import PdfCropService
from domain.services.pdf_embed_service import PdfEmbedService
from domain.services.pdf_transparency_service import PdfTransparencyService

# Default settings
DEFAULT_TEX_BODY = r"""Hello, world!
"""
DEFAULT_TEX_PREAMBLE = r"""\documentclass[a4paper,12pt]{article}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{xeCJK}
\setCJKmainfont{IPAexMincho}
\pagestyle{empty}
"""
DEFAULT_LATEXMKRC_CONTENT = r"""$pdf_mode = 3;
$latex = 'xelatex -synctex=1 -interaction=nonstopmode %O %S';
"""
DEFAULT_PDF_MARGINS = (0, 0, 0, 0)
MONOSPACE_FONT_FAMILY = (
    "'Source Han Code JP', Consolas, 'Courier New', Courier, Monaco, monospace"
)
OUTPUT_FOLDER = Path("assets")


class TexState(rx.State):
    tex_body: str = DEFAULT_TEX_BODY

    @rx.event
    def reset_tex_body(self):
        self.tex_body = DEFAULT_TEX_BODY


class ConfigState(rx.State):
    tex_preamble: str = DEFAULT_TEX_PREAMBLE
    rc_content: str = DEFAULT_LATEXMKRC_CONTENT

    @rx.event
    def reset_tex_preamble(self):
        self.tex_preamble = DEFAULT_TEX_PREAMBLE

    @rx.event
    def reset_rc_content(self):
        self.rc_content = DEFAULT_LATEXMKRC_CONTENT


class CompileState(rx.State):
    output_pdf_path: str = ""
    logs: list[str] = []
    is_compiling: bool = False

    @rx.event
    async def execute(self):
        self.is_compiling = True
        self.output_pdf_path = ""
        self.logs = []
        yield

        tex_state = await self.get_state(TexState)
        config_state = await self.get_state(ConfigState)
        tex_content = str(
            str(config_state.tex_preamble)
            + "\n\\begin{document}\n"
            + tex_state.tex_body
            + "\n\\end{document}\n"
        )
        rc_content = str(config_state.rc_content)

        compile_service = LatexCompileService()
        crop_service = PdfCropService()
        embed_service = PdfEmbedService()
        transparency_service = PdfTransparencyService()

        pipeline_uc = ProcessPdfPipelineUseCase(
            generate_uc=GeneratePdfUseCase(compile_service),
            trim_uc=TrimPdfUseCase(crop_service),
            embed_uc=EmbedTexUseCase(embed_service),
            transparency_uc=MakeTransparentUseCase(transparency_service)
        )

        result: ProcessResult = pipeline_uc.execute(
            PipelineRequest(
                tex_content=tex_content,
                latexmkrc_content=rc_content,
                margins=DEFAULT_PDF_MARGINS,
                embedded_files=[],
            )
        )
        self.logs.extend(result.logs)

        if not result.is_success:
            self.is_compiling = False
            return

        self.logs.append("Compilation succeeded.")
        Path(result.pdf_path).rename(
            Path(__file__).parent / OUTPUT_FOLDER / "output.pdf"
        )
        self.output_pdf_path = str("output.pdf")
        self.is_compiling = False


def index() -> rx.Component:
    return rx.container(
        rx.heading("LaTeX Crop Renderer", font_size="2em"),
        rx.card(
            rx.el.iframe(
                src=CompileState.output_pdf_path,
                width="100%",
                height="300px",
            ),
            rx.button(
                "Download",
                on_click=rx.download(
                    CompileState.output_pdf_path,
                    "output.pdf",
                ),
                loading=CompileState.is_compiling,
                disabled=rx.cond(CompileState.output_pdf_path, False, True),
                color_scheme="blue",
            ),
        ),
        # TeX 入力
        rx.card(
            rx.text_area(
                placeholder="Type your LaTeX code here...",
                value=TexState.tex_body,
                on_change=TexState.set_tex_body,
                resize="vertical",
                min_height="200px",
                font_family=MONOSPACE_FONT_FAMILY,
            ),
            rx.hstack(
                rx.button(
                    "Compile",
                    on_click=CompileState.execute,
                    color_scheme="blue",
                    loading=CompileState.is_compiling,
                ),
            ),
        ),
        # Preamble & latexmkrc 入力
        rx.card(
            rx.hstack(
                rx.vstack(
                    rx.text_area(
                        placeholder="Type your LaTeX preamble here...",
                        value=ConfigState.tex_preamble,
                        on_change=ConfigState.set_tex_preamble,
                        resize="vertical",
                        font_family=MONOSPACE_FONT_FAMILY,
                        width="100%",
                        min_height="200px",
                    ),
                    rx.button(
                        "Reset",
                        on_click=ConfigState.reset_tex_preamble,
                        color_scheme="blue",
                        loading=CompileState.is_compiling,
                    ),
                    width="50%",
                ),
                rx.vstack(
                    rx.text_area(
                        placeholder="Type your latexmkrc code here...",
                        value=ConfigState.rc_content,
                        on_change=ConfigState.set_rc_content,
                        resize="vertical",
                        font_family=MONOSPACE_FONT_FAMILY,
                        width="100%",
                        min_height="200px",
                    ),
                    rx.button(
                        "Reset",
                        on_click=ConfigState.reset_rc_content,
                        color_scheme="blue",
                        loading=CompileState.is_compiling,
                    ),
                    width="50%",
                ),
            )
        ),
        # ログ表示
        rx.card(
            rx.list.ordered(
                rx.foreach(CompileState.logs, lambda log: rx.list_item(log)),
                font_family=MONOSPACE_FONT_FAMILY,
            ),
            padding="1em",
            color="gray",
        ),
    )


app = rx.App()
app.add_page(index)
