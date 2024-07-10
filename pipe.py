from __future__ import annotations
import threading
from fastapi.responses import StreamingResponse
from ray.util.queue import Queue
import src.pipe as pipe
# import time
import asyncio
from packages.output_api_stream.config import OutputAPIStreamConfig, OutputAPIStreamConfigUI
from packages.output_api_stream.function import OutputAPIStreamFunction
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from fastapi import Request, Response
    from src.manager import Manager
    from src.ui.common import ConfigPage

class OutputAPIStreamHandler:
    def __init__(self, fps: int | None = None, headers: dict = {}, media_type: str = "text/plain", template: tuple[bytes, bytes] = (b"", b""), placeholder: bytes = b"") -> None:
        self.headers: dict = headers
        self.media_type: str = media_type
        self.template: tuple[bytes, bytes] = template
        self.current: bytes = self.template[0] + placeholder + self.template[1]
        self.spf: float = 1.0 / float(fps) if fps else None
        self.inputs: set[threading.Event] = set()
        if not self.spf:
            self._loops: list[asyncio.AbstractEventLoop] = []
            self._loops_lock: threading.Lock = threading.Lock()

    def output(self, queue: Queue, stopped: threading.Event) -> None:
        self.inputs.add(stopped)
        while not stopped.is_set():
            try:
                self.current = self.template[0] + queue.get() + self.template[1]
                if not self.spf:
                    with self._loops_lock:
                        self._remove_inactive_loops()
                        for loop in self._loops:
                            loop[0].call_soon_threadsafe(loop[1].set)
            except:
                break

    def _add_loop(self) -> asyncio.Event:
        with self._loops_lock:
            self._remove_inactive_loops()
            update = asyncio.Event()
            self._loops.append((asyncio.get_event_loop(), update))
        return update

    def _remove_inactive_loops(self):
        self._loops = list(filter(lambda loop: loop[0].is_running(), self._loops))

    async def get_stream(self): # -> Generator[bytes, Any, NoReturn]:
        yield self.current
        if self.spf:
            while True:
                await asyncio.sleep(self.spf)
                yield self.current
        else:
            update = self._add_loop()
            while True:
                await update.wait()
                yield self.current
                update.clear()

    def __call__(self, request: Request) -> Response:
        return StreamingResponse(self.get_stream(), headers=self.headers, media_type=self.media_type)

class OutputAPIStreamPipe(pipe.Pipe):
    cls_name: str = "Output API Stream"
    cls_config: type[OutputAPIStreamConfig] = OutputAPIStreamConfig
    cls_function: type[OutputAPIStreamFunction] = OutputAPIStreamFunction

    def __init__(self, name: str, manager: Manager, config: OutputAPIStreamConfig) -> None:
        super().__init__(name, manager, config)
        self.config: OutputAPIStreamConfig = config
        self.handler: OutputAPIStreamHandler | None = None

    def config_ui(self, manager: Manager, config_page: ConfigPage) -> OutputAPIStreamConfigUI:
        return OutputAPIStreamConfigUI(self, manager, config_page)

    def play(self, manager: Manager) -> pipe.IO:
        if self.playing:
            return
        self.playing = True
        self._stopped = threading.Event()
        self.config._queue = Queue(1)
        self.handler: OutputAPIStreamHandler = manager.api.add_rest_handler(self.config.url, OutputAPIStreamHandler(self.config.fps, self.config.headers, self.config.media_type, self.config.template, self.config.placeholder))
        self._output_thread = threading.Thread(target=self.handler.output, args=(self.config._queue, self._stopped))
        self._output_thread.start()

    def stop(self, manager: Manager, result) -> None:
        if not self.playing:
            return
        self.playing = False
        self._stopped.set()
        try:
            self.config._queue.put_nowait(self.config.placeholder)
        except:
            pass
        try:
            self._output_thread.join()
            del self._output_thread
        except:
            pass
        if self.config._queue:
            try:
                self.config._queue.shutdown(force=True)
            except:
                raise
            finally:
                try:
                    del self.config._queue
                except:
                    pass
        if self.handler is not None:
            if self._stopped in self.handler.inputs:
                self.handler.inputs.remove(self._stopped)
            if not self.handler.inputs:
                manager.api.remove_rest_handler(self.config.url)
                self.handler: OutputAPIStreamHandler | None = None
        del self._stopped
