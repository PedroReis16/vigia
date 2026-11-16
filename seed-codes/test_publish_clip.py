"""Testes do seed de clipes (sem ffmpeg real nem rede)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SEED_CODES = Path(__file__).resolve().parent
if str(SEED_CODES) not in sys.path:
    sys.path.insert(0, str(SEED_CODES))

import publish_clip  # noqa: E402


class ParseFrameRateTests(unittest.TestCase):
    def test_fraction_and_decimal(self) -> None:
        self.assertEqual(publish_clip.parse_frame_rate("30/1"), 30)
        self.assertEqual(publish_clip.parse_frame_rate("30000/1001"), 30)
        self.assertEqual(publish_clip.parse_frame_rate("12.2"), 12)

    def test_invalid_rates(self) -> None:
        self.assertIsNone(publish_clip.parse_frame_rate(""))
        self.assertIsNone(publish_clip.parse_frame_rate("0/0"))
        self.assertIsNone(publish_clip.parse_frame_rate("N/A"))
        self.assertIsNone(publish_clip.parse_frame_rate("0.4"))


class ExtractCommandTests(unittest.TestCase):
    def test_command_samples_at_fps_and_optional_duration(self) -> None:
        command = publish_clip.build_extract_command(
            "ffmpeg",
            Path("clip.mp4"),
            Path("out/%06d.png"),
            12,
            30,
        )
        self.assertEqual(command[0], "ffmpeg")
        self.assertEqual(command[command.index("-t") + 1], "30")
        self.assertIn("fps=12", command)
        self.assertEqual(command[command.index("-start_number") + 1], "0")
        self.assertTrue(command[-1].endswith("%06d.png"))

    def test_extract_frames_lists_numbered_pngs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            video = dest / "clip.mp4"
            video.write_bytes(b"video")

            def runner(command, **kwargs):  # noqa: ANN001
                (dest / "000001.png").write_bytes(b"\x89PNG")
                (dest / "000000.png").write_bytes(b"\x89PNG")
                (dest / "notes.txt").write_bytes(b"ignore")
                return subprocess.CompletedProcess(command, 0, stderr=b"")

            frames = publish_clip.extract_frames(video, dest, fps=12, max_seconds=None, runner=runner)
            self.assertEqual([path.name for path in frames], ["000000.png", "000001.png"])


class UploadClipTests(unittest.TestCase):
    def test_posts_session_then_png_frames(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "000000.png"
            second = Path(tmp) / "000001.png"
            first_bytes = b"\x89PNG\r\n\x1a\nA"
            second_bytes = b"\x89PNG\r\n\x1a\nB"
            first.write_bytes(first_bytes)
            second.write_bytes(second_bytes)
            calls: list[tuple[str, dict]] = []

            class Response:
                status_code = 202
                reason = "Accepted"
                text = ""

                def raise_for_status(self) -> None:
                    return None

            class Session:
                def post(self, url, **kwargs):  # noqa: ANN001
                    calls.append((url, kwargs))
                    return Response()

            publish_clip.upload_clip(
                Session(),  # type: ignore[arg-type]
                "http://localhost:8090/vigia/",
                publish_clip.DEFAULT_DEVICE_ID,
                "11111111-1111-1111-1111-111111111111",
                12,
                [first, second],
            )

        self.assertEqual(len(calls), 3)
        session_url, session_kwargs = calls[0]
        self.assertTrue(session_url.endswith(f"/devices/{publish_clip.DEFAULT_DEVICE_ID}/clips"))
        self.assertEqual(
            session_kwargs["json"],
            {
                "clipId": "11111111-1111-1111-1111-111111111111",
                "frameCount": 2,
                "fps": 12,
            },
        )
        self.assertNotIn("headers", session_kwargs)
        frame_url, frame_kwargs = calls[1]
        self.assertTrue(frame_url.endswith("/frames/0"))
        self.assertEqual(frame_kwargs["headers"]["Content-Type"], "image/png")
        self.assertEqual(frame_kwargs["data"], first_bytes)
        self.assertEqual(calls[2][1]["data"], second_bytes)
        self.assertTrue(calls[2][0].endswith("/frames/1"))

    def test_rejects_more_frames_than_the_api(self) -> None:
        frames = [Path(f"{index:06d}.png") for index in range(publish_clip.MAX_FRAME_COUNT + 1)]
        with self.assertRaises(ValueError):
            publish_clip.upload_clip(
                object(),  # type: ignore[arg-type]
                "http://localhost:8090/vigia",
                publish_clip.DEFAULT_DEVICE_ID,
                "11111111-1111-1111-1111-111111111111",
                12,
                frames,
            )


if __name__ == "__main__":
    unittest.main()
