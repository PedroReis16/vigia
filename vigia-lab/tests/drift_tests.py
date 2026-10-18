"""Garantem que o lab usa os MESMOS parâmetros de pose do vigia-onboard."""

from pathlib import Path

from vigia_lab import models_gru, pose_source


def test_kwargs_come_from_onboard_and_match_known_deploy_values() -> None:
    kw = pose_source.read_stream_kwargs()
    assert kw["imgsz"] == 320 and kw["conf"] == 0.25 and kw["device"] == "cpu"
    assert kw["tracker"] == "botsort.yaml" and kw["classes"] == [0] and kw["stream"] is True
    assert "iou" not in kw          # iou fica no padrão do Ultralytics (0,7), como no deploy


def test_stream_function_still_forwards_the_kwargs() -> None:
    assert pose_source.stream_calls_model_track_with_kwargs()


def test_missing_constant_fails_loudly(tmp_path: Path) -> None:
    fake = tmp_path / "capture_runner.py"
    fake.write_text("X = 1\n", encoding="utf-8")
    try:
        pose_source.read_stream_kwargs(fake)
    except RuntimeError:
        return
    raise AssertionError("deveria falhar quando a constante some")


def test_lock_matches_files_on_disk() -> None:
    """Falha se um ONNX ou o pose_features.py mudou sem atualizar models.lock.json."""
    assert models_gru.verify_lock()


def test_close_stream_closes_ultralytics_dataset() -> None:
    from types import SimpleNamespace

    closed = []
    model = SimpleNamespace(predictor=SimpleNamespace(dataset=SimpleNamespace(close=lambda: closed.append(1))))
    pose_source.reset_tracker(model)
    assert closed == [1] and model.predictor is None
    pose_source.close_stream(SimpleNamespace(predictor=None))      # sem predictor: não quebra
