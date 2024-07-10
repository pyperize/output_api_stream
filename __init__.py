from __future__ import annotations
from packages.output_api_stream.config import OutputAPIStreamConfig, OutputAPIStreamConfigUI
from packages.output_api_stream.function import OutputAPIStreamFunction
from packages.output_api_stream.pipe import OutputAPIStreamPipe

from src.package.package import Package
from typing import TYPE_CHECKING, Iterable
if TYPE_CHECKING:
    from src.pipe import Pipe

class OutputAPIStreamPackage(Package):
    name: str = "Output API Stream"
    _pipes: Iterable[type[Pipe]] = [OutputAPIStreamPipe]
    dependencies: dict[str, Package] = {}
