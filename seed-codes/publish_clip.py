"""Extrai frames de um vídeo e publica um clipe na API local.

Espelha o contrato da placa: abre a sessão e envia cada PNG pelo índice,
sem autenticação. A API monta o MP4 quando a sequência fecha.

Requer ffmpeg (e ffprobe, para o fps da fonte) no PATH.

Uso (a partir de seed-codes/):
  python publish_clip.py caminho/video.mp4
  python publish_clip.py caminho/video.mp4 --fps 12 --max-seconds 30
  python publish_clip.py caminho/video.mp4 --dry-run --frames-dir ./frames
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Callable
from pathlib import Path

import requests

# Espelha ClipIngestService.MaxFrameCount e Vigia.Models.Seed.TestDeviceSeed.
MAX_FRAME_COUNT = 4096
DEFAULT_BASE_URL = "http://localhost:8090/vigia"
DEFAULT_DEVICE_ID = "b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"
DEFAULT_FPS = 12
_HTTP_TIMEOUT_S = 60


def _ffmpeg_executable() -> str:
    unix_candidates = (
        "/usr/bin/ffmpeg",
        "/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/opt/homebrew/bin/ffmpeg",
    )
    if sys.platform != "win32":
        for candidate in unix_candidates:
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate

    for name in ("ffmpeg.exe", "ffmpeg"):
        found = shutil.which(name)
        if found:
            return found
    return "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"


def _ffprobe_executable() -> str:
    ffmpeg = Path(_ffmpeg_executable())
    sibling_name = "ffprobe.exe" if ffmpeg.suffix.lower() == ".exe" else "ffprobe"
    sibling = ffmpeg.with_name(sibling_name)
    if sibling.is_file():
        return str(sibling)
    for name in ("ffprobe.exe", "ffprobe"):
        found = shutil.which(name)
        if found:
            return found
    return sibling_name


def parse_frame_rate(raw: str) -> int | None:
    """Converte ``30/1`` ou ``29.97`` no fps inteiro exigido pela API."""
    text = raw.strip().splitlines()[0].strip() if raw.strip() else ""
    if not text or text in {"0/0", "N/A"}:
        return None
    try:
        if "/" in text:
            numerator, denominator = text.split("/", 1)
            denominator_value = float(denominator)
            if denominator_value == 0:
                return None
            rate = float(numerator) / denominator_value
        else:
            rate = float(text)
    except ValueError:
        return None
    if rate < 1:
        return None
    return max(1, round(rate))


def probe_fps(video: Path, runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run) -> int | None:
    command = [
        _ffprobe_executable(),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate",
        "-of",
        "csv=p=0",
        str(video),
    ]
    try:
        completed = runner(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None
    return parse_frame_rate(completed.stdout.decode("utf-8", errors="replace"))


def build_extract_command(
    ffmpeg: str,
    video: Path,
    pattern: Path,
    fps: int,
    max_seconds: float | None,
) -> list[str]:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
    ]
    if max_seconds is not None:
        command.extend(["-t", _format_seconds(max_seconds)])
    command.extend(
        [
            "-i",
            str(video),
            "-vf",
            f"fps={fps}",
            "-start_number",
            "0",
            str(pattern),
        ]
    )
    return command


def extract_frames(
    video: Path,
    dest: Path,
    fps: int,
    max_seconds: float | None,
    runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> list[Path]:
    """Quebra o vídeo em PNG numerados ``000000.png`` no ritmo de ``fps``."""
    if not video.is_file():
        raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {video}")
    if fps < 1:
        raise ValueError("O fps precisa ser pelo menos 1")

    dest.mkdir(parents=True, exist_ok=True)
    for stale in dest.glob("*.png"):
        if stale.stem.isdigit():
            stale.unlink()

    command = build_extract_command(
        _ffmpeg_executable(),
        video,
        dest / "%06d.png",
        fps,
        max_seconds,
    )
    try:
        completed = runner(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg não encontrado. Instale e garanta que está no PATH.") from exc

    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"ffmpeg saiu com {completed.returncode}: {detail}")

    return sorted(path for path in dest.glob("*.png") if path.stem.isdigit())


def upload_clip(
    session: requests.Session,
    base_url: str,
    device_id: str,
    clip_id: str,
    fps: int,
    frames: list[Path],
) -> None:
    """Abre ``POST /devices/{id}/clips`` e envia cada PNG em ``.../frames/{index}``."""
    if not frames:
        raise ValueError("Não há frames para enviar")
    if len(frames) > MAX_FRAME_COUNT:
        raise ValueError(
            f"O clipe tem {len(frames)} frames; a API aceita no máximo {MAX_FRAME_COUNT}. "
            "Reduza com --fps ou --max-seconds."
        )

    base = base_url.rstrip("/")
    session_url = f"{base}/devices/{device_id}/clips"
    response = session.post(
        session_url,
        json={"clipId": clip_id, "frameCount": len(frames), "fps": fps},
        timeout=_HTTP_TIMEOUT_S,
    )
    _raise_for_status(response)

    total = len(frames)
    for index, path in enumerate(frames):
        frame_url = f"{base}/devices/{device_id}/clips/{clip_id}/frames/{index}"
        response = session.post(
            frame_url,
            data=path.read_bytes(),
            headers={"Content-Type": "image/png"},
            timeout=_HTTP_TIMEOUT_S,
        )
        _raise_for_status(response)
        if index == 0 or index + 1 == total or (index + 1) % 25 == 0:
            print(f"frame {index + 1}/{total}", flush=True)


def wait_for_clip(
    session: requests.Session,
    base_url: str,
    device_id: str,
    clip_id: str,
    timeout_s: float,
) -> str:
    """Consulta a listagem até o clipe sair de Receiving/Assembling."""
    url = f"{base_url.rstrip('/')}/devices/{device_id}/clips"
    deadline = time.monotonic() + timeout_s
    last_status = "desconhecido"
    while time.monotonic() < deadline:
        response = session.get(url, timeout=_HTTP_TIMEOUT_S)
        _raise_for_status(response)
        clips = response.json()
        match = next((clip for clip in clips if str(clip.get("id")) == clip_id), None)
        if match is not None:
            last_status = str(match.get("status", last_status))
            if last_status in {"Ready", "Failed"}:
                return last_status
        time.sleep(1)
    raise TimeoutError(f"Clipe {clip_id} não terminou a montagem em {timeout_s:.0f}s (último status: {last_status})")


def _format_seconds(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value)


def _raise_for_status(response: requests.Response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        body = response.text.strip()
        detail = f": {body}" if body else ""
        raise requests.HTTPError(f"{response.status_code} {response.reason}{detail}", response=response) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Quebra um vídeo em PNG e envia o clipe para a API (sem captura)."
    )
    parser.add_argument("input", type=Path, help="Caminho do vídeo")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("VIGIA_API_BASE_URL", DEFAULT_BASE_URL),
        help=f"Base da API (padrão: {DEFAULT_BASE_URL} ou VIGIA_API_BASE_URL)",
    )
    parser.add_argument(
        "--device-id",
        default=DEFAULT_DEVICE_ID,
        help="Device que recebe o clipe (padrão: device DEBUG da API)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=None,
        help=f"FPS da extração e da sessão. Sem valor, usa o da fonte ou {DEFAULT_FPS}",
    )
    parser.add_argument(
        "--max-seconds",
        type=float,
        default=None,
        help="Corta o vídeo neste ponto antes de extrair os frames",
    )
    parser.add_argument(
        "--clip-id",
        default=None,
        help="Id da sessão. Sem valor, gera um UUID. Reenviar o mesmo id sobrescreve frames enquanto a sessão está aberta",
    )
    parser.add_argument(
        "--frames-dir",
        type=Path,
        default=None,
        help="Pasta dos PNG. Sem valor, usa um diretório temporário apagado no fim",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Só extrai os frames e informa a contagem, sem chamar a API",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Depois do envio, espera o clipe ficar Ready ou Failed",
    )
    parser.add_argument(
        "--wait-timeout",
        type=float,
        default=180,
        help="Segundos máximos de --wait (padrão: 180)",
    )
    args = parser.parse_args(argv)

    video = args.input.expanduser().resolve()
    try:
        uuid.UUID(args.device_id)
    except ValueError:
        print(f"Erro: device id inválido: {args.device_id}", file=sys.stderr)
        return 1

    if args.max_seconds is not None and args.max_seconds <= 0:
        print("Erro: --max-seconds precisa ser maior que zero", file=sys.stderr)
        return 1

    clip_id = args.clip_id or str(uuid.uuid4())
    if args.clip_id is not None:
        try:
            clip_id = str(uuid.UUID(args.clip_id))
        except ValueError:
            print(f"Erro: clip id inválido: {args.clip_id}", file=sys.stderr)
            return 1

    fps = args.fps
    if fps is None:
        fps = probe_fps(video) or DEFAULT_FPS
    if fps < 1:
        print("Erro: --fps precisa ser pelo menos 1", file=sys.stderr)
        return 1

    frames_dir = args.frames_dir.expanduser().resolve() if args.frames_dir is not None else None
    temporary = None if frames_dir is not None else tempfile.TemporaryDirectory(prefix="vigia-seed-clip-")
    dest = frames_dir if frames_dir is not None else Path(temporary.name)

    try:
        frames = extract_frames(video, dest, fps, args.max_seconds)
        if not frames:
            print("Erro: o ffmpeg não gerou frames", file=sys.stderr)
            return 1
        if len(frames) > MAX_FRAME_COUNT:
            print(
                f"Erro: {len(frames)} frames excedem o limite de {MAX_FRAME_COUNT}. "
                "Use --fps menor ou --max-seconds.",
                file=sys.stderr,
            )
            return 1

        print(f"{len(frames)} frames @ {fps} fps em {dest}")
        if args.dry_run:
            print("dry-run: nenhum frame foi enviado")
            return 0

        base_url = args.base_url.rstrip("/")
        with requests.Session() as session:
            upload_clip(session, base_url, args.device_id, clip_id, fps, frames)
            video_url = f"{base_url}/devices/{args.device_id}/clips/{clip_id}"
            print(f"Clipe {clip_id} enviado")
            print(f"Vídeo: {video_url}")
            if args.wait:
                status = wait_for_clip(session, base_url, args.device_id, clip_id, args.wait_timeout)
                print(f"Status: {status}")
                if status != "Ready":
                    return 1
        return 0
    except (FileNotFoundError, ValueError, RuntimeError, TimeoutError, requests.RequestException) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
