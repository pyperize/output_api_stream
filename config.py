from __future__ import annotations
import flet as ft
import src.pipe as pipe
from src.ui.pipe import PipeTile
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.manager import Manager
    from src.ui.common import ConfigPage
    from packages.output_api_stream.pipe import OutputAPIStreamPipe
    from ray.util.queue import Queue

class OutputAPIStreamConfig(pipe.Config):
    url: str = "stream"
    fps: int | None = None
    preset: str | None = None
    headers: dict = {}
    media_type: str = "text/plain"
    template: tuple[bytes, bytes] = (b"", b"")
    placeholder: bytes = b""
    _queue: Queue | None = None

OPTIONS: dict[str, OutputAPIStreamConfig] = {
    "Text": OutputAPIStreamConfig(
        url="results",
        fps=None,
        preset="Text",
        headers={"X-Content-Type-Options": "nosniff"},
        media_type="text/plain",
        template=(b"", b""),
        placeholder=b"",
    ),
    "Image": OutputAPIStreamConfig(
        url="frames",
        fps=30,
        preset="Image",
        headers={},
        media_type="multipart/x-mixed-replace;boundary=frame",
        template=(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n", b"\r\n"),
        placeholder=open("./packages/output_api_stream/placeholder.jpg", "rb").read(),
    ),
}

class OutputAPIStreamConfigUI(pipe.ConfigUI):
    def __init__(self, instance: OutputAPIStreamPipe, manager: Manager, config_page: ConfigPage) -> None:
        super().__init__(instance, manager, config_page)
        self.instance: OutputAPIStreamPipe = instance
        self.presets = ft.Dropdown(
            self.instance.config.preset,
            options=[ft.dropdown.Option(preset) for preset in OPTIONS.keys()],
            hint_text="Format",
            label="Format"
        )
        self.content: ft.Column = ft.Column([
            self.presets,
            ft.TextField(self.instance.config.url, label="Output URL", border_color="grey"),
            ft.TextField(self.instance.config.fps, label="Output FPS (0 or leave blank for non-FPS updates)", border_color="grey", input_filter=ft.NumbersOnlyInputFilter()),
        ])

    def dismiss(self) -> None:
        self.instance.config = OPTIONS[self.presets.value].model_copy(
            update={
                "url": self.content.controls[1].value,
                "fps": int(self.content.controls[2].value) if self.content.controls[2].value else None,
            },
            deep=True,
        ) if self.presets.value else OutputAPIStreamConfig(
            url=self.content.controls[1].value,
            fps=int(self.content.controls[2].value) if self.content.controls[2].value else None,
        )
