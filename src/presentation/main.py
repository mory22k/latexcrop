# main.py
from pathlib import Path
import reflex as rx

# DTO & Models
from domain.models.embedded_file import EmbeddedFile
from application.dto.compile_request import CompileRequest
from application.dto.crop_request import CropRequest
from application.dto.embed_request import EmbedRequest
from application.dto.process_result import ProcessResult

# UseCases
from application.usecases.generate_pdf_usecase import GeneratePdfUseCase
from application.usecases.trim_pdf_usecase import TrimPdfUseCase
from application.usecases.embed_tex_usecase import EmbedTexUseCase

# Services
from domain.services.latex_compile_service import LatexCompileService
from domain.services.pdf_crop_service import PdfCropService
from domain.services.pdf_embed_service import PdfEmbedService

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

        compile_service = LatexCompileService()
        crop_service = PdfCropService()
        embed_service = PdfEmbedService()
        generate_uc = GeneratePdfUseCase(compile_service)
        trim_uc = TrimPdfUseCase(crop_service)
        embed_uc = EmbedTexUseCase(embed_service)

        tex_state = await self.get_state(TexState)
        config_state = await self.get_state(ConfigState)

        tex_content = str(
            str(config_state.tex_preamble)
            + "\n\\begin{document}\n"
            + tex_state.tex_body
            + "\n\\end{document}\n"
        )
        rc_content = str(config_state.rc_content)

        self.logs = []

        compile_req = CompileRequest(
            tex_content=tex_content, latexmkrc_content=rc_content
        )
        compile_res: ProcessResult = generate_uc.execute(compile_req)
        self.logs.extend(compile_res.logs)
        if not compile_res.is_success:
            print("Compilation failed.")
            self.is_compiling = False
            return

        crop_req = CropRequest(
            pdf_path=compile_res.pdf_path, margins=DEFAULT_PDF_MARGINS
        )
        crop_res: ProcessResult = trim_uc.execute(crop_req)
        self.logs.extend(crop_res.logs)

        embedded_file = EmbeddedFile(name="main.tex", data=tex_content.encode("utf-8"))
        embed_req = EmbedRequest(
            pdf_path=crop_res.pdf_path, embedded_files=[embedded_file]
        )
        embed_res: ProcessResult = embed_uc.execute(embed_req)
        self.logs.extend(embed_res.logs)

        # copy output pdf to static folder
        Path(embed_res.pdf_path).rename(
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
