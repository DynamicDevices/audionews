"""Exercise synthesis failures without contacting either speech service."""

import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
from aiohttp import web

from digest import tts


class TestTTSFallback(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "digest.mp3"
        self.config = {"tts_settings": {"edge_tts": {
            "max_retries": 1,
            "initial_retry_delay": 0,
            "retry_backoff_multiplier": 1,
            "force_ipv4": False,
        }}}
        self.dd = AsyncMock()
        self.edge = MagicMock()
        self.edge.return_value.stream.side_effect = self.audio_stream
        audio = MagicMock()
        audio.__len__.return_value = 1000
        for target, replacement in (
            ("digest.tts._generate_audio_dd", self.dd),
            ("digest.tts.edge_tts.Communicate", self.edge),
        ):
            mock_patch = patch(target, replacement)
            mock_patch.start()
            self.addCleanup(mock_patch.stop)
            if target == "digest.tts._generate_audio_dd":
                self.dd_patch = mock_patch
        mock_patch = patch.dict("sys.modules", {"pydub": SimpleNamespace(
            AudioSegment=SimpleNamespace(from_mp3=MagicMock(return_value=audio))
        )})
        mock_patch.start()
        self.addCleanup(mock_patch.stop)

    @staticmethod
    async def audio_stream():
        yield {"type": "WordBoundary", "text": "ignored"}
        yield {"type": "audio", "data": b"edge audio"}

    @staticmethod
    def http_error(status):
        return aiohttp.ClientResponseError(
            SimpleNamespace(real_url="http://unused/tts"), (),
            status=status, message="test failure",
        )

    async def generate(self, language="bella"):
        return await tts.generate_audio_digest(
            "Test transcript", str(self.output), tts_provider="dd_tts",
            voice_name="en-GB-SoniaNeural", language=language,
            voice_config=self.config,
        )

    async def test_server_errors_fall_back_to_edge(self):
        for status in (500, 502, 503, 504):
            with self.subTest(status=status):
                self.dd.side_effect = self.http_error(status)
                self.edge.reset_mock()
                result = await self.generate()
                self.edge.assert_called_once_with(
                    "Test transcript", "en-GB-SoniaNeural", rate="+0%"
                )
                self.assertEqual(self.output.read_bytes(), b"edge audio")
                self.assertEqual(result["filename"], str(self.output))

    async def test_healthy_endpoint_with_real_synthesis_500_falls_back(self):
        # Exercise real aiohttp error handling, not just an injected exception.
        self.dd_patch.stop()
        requests = []

        async def health(request):
            return web.json_response({"status": "ok"})

        async def synthesis(request):
            requests.append(await request.json())
            return web.Response(status=500, text="Internal Server Error")

        app = web.Application()
        app.router.add_get("/health", health)
        app.router.add_post("/tts", synthesis)
        runner = web.AppRunner(app)
        await runner.setup()
        self.addAsyncCleanup(runner.cleanup)
        await web.TCPSite(runner, "127.0.0.1", 0).start()
        url = f"http://127.0.0.1:{runner.addresses[0][1]}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url + "/health") as response:
                self.assertEqual(response.status, 200)
        with patch.dict("os.environ", {"DD_TTS_URL": url, "DD_TTS_TOKEN": ""}):
            await self.generate()
        self.assertEqual(requests[0]["text"], "Test transcript")
        self.edge.assert_called_once()
        self.assertEqual(self.output.read_bytes(), b"edge audio")

    async def test_connection_failure_and_timeout_fall_back(self):
        for error in (aiohttp.ClientConnectionError("disconnected"), asyncio.TimeoutError()):
            with self.subTest(error=type(error).__name__):
                self.dd.side_effect = error
                self.edge.reset_mock()
                await self.generate("en_GB")
                self.edge.assert_called_once()

    async def test_client_and_auth_errors_are_not_hidden(self):
        for status in (400, 401, 403, 404, 429):
            with self.subTest(status=status):
                error = self.http_error(status)
                self.dd.side_effect = error
                with self.assertRaises(aiohttp.ClientResponseError) as caught:
                    await self.generate()
                self.assertIs(caught.exception, error)
                self.edge.assert_not_called()

    async def test_configuration_and_invalid_response_errors_are_not_hidden(self):
        for error in (ValueError("missing URL"), RuntimeError("missing audio reference"),
                      RuntimeError("DD TTS auth failed (401)")):
            with self.subTest(error=str(error)):
                self.dd.side_effect = error
                with self.assertRaises(type(error)):
                    await self.generate()
                self.edge.assert_not_called()

    async def test_cancellation_is_not_hidden(self):
        self.dd.side_effect = asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            await self.generate()
        self.edge.assert_not_called()

    async def test_fallback_failure_still_fails_generation(self):
        self.dd.side_effect = self.http_error(500)
        self.edge.side_effect = RuntimeError("Edge unavailable")
        with self.assertRaisesRegex(RuntimeError, "Edge TTS failed"):
            await self.generate()
        self.dd.assert_awaited_once()
        self.edge.assert_called_once()

    async def test_partial_primary_audio_is_replaced(self):
        async def fail_after_writing(*args):
            self.output.write_bytes(b"partial primary audio")
            raise self.http_error(500)
        self.dd.side_effect = fail_after_writing
        await self.generate()
        self.assertEqual(self.output.read_bytes(), b"edge audio")

    async def test_successful_primary_does_not_use_edge(self):
        async def succeed(*args):
            self.output.write_bytes(b"primary audio")
        self.dd.side_effect = succeed
        await self.generate()
        self.edge.assert_not_called()
        self.assertEqual(self.output.read_bytes(), b"primary audio")


if __name__ == "__main__":
    unittest.main()
