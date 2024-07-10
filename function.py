from __future__ import annotations
from packages.output_api_stream.config import OutputAPIStreamConfig
from src.pipe.function import IO, Function

class OutputAPIInput(IO):
    data: bytes # = b""

class OutputAPIStreamFunction(Function):
    cls_input: type[OutputAPIInput] = OutputAPIInput
    cls_output: type[IO] = IO

    def __init__(self, config: OutputAPIStreamConfig) -> None:
        self.config: OutputAPIStreamConfig = config

    def __call__(self, input: OutputAPIInput) -> IO:
        if self.config._queue is not None:
            self.config._queue.put(input.data)
        return IO()
