from pathlib import Path
import reflex as rx

from domain.models.latexmkrc_source import LatexmkrcSource

from application.dto.process_result import ProcessResult
from application.dto.pipeline_request import PipelineRequest

from application.usecases.generate_pdf_usecase import GeneratePdfUseCase
from application.usecases.trim_pdf_usecase import TrimPdfUseCase
from application.usecases.embed_tex_usecase import EmbedTexUseCase
from application.usecases.make_transparent_usecase import MakeTransparentUseCase
from application.usecases.process_pdf_pipeline_usecase import ProcessPdfPipelineUseCase

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
OUTPUT_PDF_NAME = "output.pdf"

CONFIG_DIR = Path(__file__).parents[2] / "config"
CONFIG_DIR.mkdir(exist_ok=True)
PREAMBLE_FILE = CONFIG_DIR / "preamble"
RC_FILE = CONFIG_DIR / "latexmkrc"

INITIAL_TEX_PREAMBLE = (
    PREAMBLE_FILE.read_text(encoding="utf-8")
    if PREAMBLE_FILE.exists()
    else DEFAULT_TEX_PREAMBLE
)
INITIAL_LATEXMKRC_CONTENT = (
    RC_FILE.read_text(encoding="utf-8")
    if RC_FILE.exists()
    else DEFAULT_LATEXMKRC_CONTENT
)


class AppState(rx.State):
    tex_body: str = DEFAULT_TEX_BODY
    tex_preamble: str = INITIAL_TEX_PREAMBLE
    rc_content: str = INITIAL_LATEXMKRC_CONTENT
    is_loading: bool = False
    output_pdf_path: str = ""
    is_result_available: bool = False
    logs: list[str] = []

    @rx.event
    def set_loading_true(self):
        self.is_loading = True

    @rx.event
    def set_loading_false(self):
        self.is_loading = False

    @rx.event
    async def initialize_page(self):
        """
        The event handler for the page load.
        """
        self.set_loading_false()
        if self.is_result_available:
            self.output_pdf_path = str(OUTPUT_PDF_NAME)
            self.logs.append("[Page loaded] Result PDF is available.")
        else:
            self.logs.append("[Page loaded] No result PDF available.")

    @rx.event
    async def load_config(self):
        """
        assets/preamble と latexmkrc をロード
        """
        self.set_loading_true()
        self.logs = []
        preamble_path = CONFIG_DIR / "preamble"
        rc_path = CONFIG_DIR / "latexmkrc"

        if preamble_path.exists():
            self.tex_preamble = preamble_path.read_text(encoding="utf-8")
            self.logs.append(f"Loaded preamble from {preamble_path}.")
        else:
            self.logs.append(f"[Warning] {preamble_path} does not exist.")

        if rc_path.exists():
            self.rc_content = rc_path.read_text(encoding="utf-8")
            self.logs.append(f"Loaded latexmkrc from {rc_path}.")
        else:
            self.logs.append(f"[Warning] {rc_path} does not exist.")

        self.set_loading_false()

    @rx.event
    async def save_config(self):
        """
        assets/preamble に現在の tex_preamble を書き込む
        """
        self.set_loading_true()
        self.logs = []
        preamble_path = CONFIG_DIR / "preamble"
        rc_path = CONFIG_DIR / "latexmkrc"

        try:
            LatexmkrcSource(content=self.rc_content)
            self.logs.append("Validated LatexmkrcSource.")
        except ValueError as e:
            self.logs.append(f"[Error] {e}")
            self.set_loading_false()
            return

        preamble_path.write_text(self.tex_preamble, encoding="utf-8")
        self.logs.append(f"Saved preamble to {preamble_path}.")

        rc_path.write_text(self.rc_content, encoding="utf-8")
        self.logs.append(f"Saved latexmkrc to {rc_path}.")

        self.set_loading_false()

    @rx.event
    async def reset_config(self):
        self.set_loading_true()
        self.logs = []
        self.tex_preamble = DEFAULT_TEX_PREAMBLE
        self.rc_content = DEFAULT_LATEXMKRC_CONTENT
        self.logs.append("Reset preamble and latexmkrc to default values.")
        self.set_loading_false()

    @rx.event
    async def execute(self):
        self.set_loading_true()
        self.output_pdf_path = ""
        self.logs = []
        yield

        tex_content = (
            self.tex_preamble
            + "\n\\begin{document}\n"
            + self.tex_body
            + "\n\\end{document}\n"
        )
        rc_content = self.rc_content

        compile_svc = LatexCompileService()
        crop_svc = PdfCropService()
        embed_svc = PdfEmbedService()
        transparency_svc = PdfTransparencyService()

        pipeline_uc = ProcessPdfPipelineUseCase(
            generate_uc=GeneratePdfUseCase(compile_svc),
            trim_uc=TrimPdfUseCase(crop_svc),
            embed_uc=EmbedTexUseCase(embed_svc),
            transparency_uc=MakeTransparentUseCase(transparency_svc),
        )

        try:
            result: ProcessResult = pipeline_uc.execute(
                PipelineRequest(
                    tex_content=tex_content,
                    latexmkrc_content=rc_content,
                    margins=DEFAULT_PDF_MARGINS,
                    embedded_files=[],
                )
            )
        except Exception as e:
            self.logs.append(f"[Error] {e}")
            self.set_loading_false()
            return
        self.logs.extend(result.logs)
        dest = Path(__file__).parent / OUTPUT_FOLDER / OUTPUT_PDF_NAME
        Path(result.pdf_path).rename(dest)
        self.is_result_available = True
        self.logs.append(f"Saved to {OUTPUT_FOLDER}/{OUTPUT_PDF_NAME}")
        self.logs.append(
            "Please wait. If the page does not update automatically, please reload."
        )


def save_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                "Save",
                loading=AppState.is_loading,
            )
        ),
        rx.dialog.content(
            rx.dialog.title("Saving the configuration"),
            rx.dialog.description(
                "Are you sure you save the configuration?",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        color_scheme="gray",
                        variant="soft",
                    ),
                ),
                rx.dialog.close(
                    rx.button(
                        "Save",
                        on_click=AppState.save_config,
                        color_scheme="blue",
                    ),
                ),
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
        ),
    )


def load_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                "Load",
                loading=AppState.is_loading,
            ),
        ),
        rx.dialog.content(
            rx.dialog.title("Loading the configuration"),
            rx.dialog.description(
                rx.text("Are you sure you load the configuration?"),
                rx.text("The current configuration will be overwritten."),
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        color_scheme="gray",
                        variant="soft",
                    ),
                ),
                rx.dialog.close(
                    rx.button(
                        "Load",
                        on_click=AppState.load_config,
                        color_scheme="blue",
                    ),
                ),
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
        ),
    )


def reset_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                "Reset",
                color_scheme="red",
                loading=AppState.is_loading,
            ),
        ),
        rx.dialog.content(
            rx.dialog.title("Resetting the configuration"),
            rx.dialog.description(
                rx.text("Are you sure you reset the configuration?"),
                rx.text("The current configuration will be overwritten."),
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        color_scheme="gray",
                        variant="soft",
                    ),
                ),
                rx.dialog.close(
                    rx.button(
                        "Reset",
                        on_click=AppState.reset_config,
                        color_scheme="red",
                    ),
                ),
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
        ),
    )


@rx.page(on_load=AppState.initialize_page)
def index() -> rx.Component:
    return rx.container(
        rx.heading(
            "LaTeX Crop Renderer",
            font_size="2em",
            margin_bottom="4px",
        ),
        # PDF プレビュー & ダウンロード
        rx.card(
            rx.el.iframe(
                src=AppState.output_pdf_path,
                width="100%",
                height="300px",
            ),
            rx.flex(
                rx.button(
                    "Download",
                    on_click=rx.download(AppState.output_pdf_path, "output.pdf"),
                    loading=AppState.is_loading,
                    disabled=rx.cond(AppState.output_pdf_path, False, True),
                    color_scheme="blue",
                ),
                spacing="3",
                margin_top="4px",
                justify="start",
            ),
        ),
        # TeX 本文入力
        rx.card(
            rx.text_area(
                placeholder="Type your LaTeX code here...",
                value=AppState.tex_body,
                on_change=AppState.set_tex_body,
                resize="vertical",
                min_height="200px",
                font_family=MONOSPACE_FONT_FAMILY,
            ),
            rx.flex(
                rx.button(
                    "Compile!",
                    on_click=AppState.execute,
                    color_scheme="blue",
                    loading=AppState.is_loading,
                ),
                spacing="3",
                margin_top="4px",
                justify="start",
            ),
        ),
        # Preamble & latexmkrc 入力
        rx.card(
            rx.heading(
                "Preamble and latexmkrc",
                font_size="1.2em",
                margin_bottom="4px",
            ),
            rx.hstack(
                rx.text_area(
                    placeholder="Type your LaTeX preamble here...",
                    value=AppState.tex_preamble,
                    on_change=AppState.set_tex_preamble,
                    resize="vertical",
                    font_family=MONOSPACE_FONT_FAMILY,
                    width="100%",
                    min_height="200px",
                ),
                rx.text_area(
                    placeholder="Type your latexmkrc code here...",
                    value=AppState.rc_content,
                    on_change=AppState.set_rc_content,
                    resize="vertical",
                    font_family=MONOSPACE_FONT_FAMILY,
                    width="100%",
                    min_height="200px",
                ),
            ),
            rx.flex(
                save_dialog(),
                load_dialog(),
                reset_dialog(),
                spacing="3",
                margin_top="4px",
                justify="end",
            ),
        ),
        # ログ表示
        rx.card(
            rx.list.ordered(
                rx.foreach(AppState.logs, lambda log: rx.list_item(log)),
                font_family="monospace",
                padding="1em",
                color="gray",
            )
        ),
    )


app = rx.App()
app.add_page(index)
