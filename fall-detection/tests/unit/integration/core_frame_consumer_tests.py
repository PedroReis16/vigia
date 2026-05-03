"""Testes unitários para consumo de frames e buffers (app.core.frame_consumer)."""

from __future__ import annotations

import pickle
import queue
from collections import defaultdict, deque
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.core.frame_consumer import (
    WINDOW_SIZE,
    _capture_frame,
    _feed_buffers,
    run_frame_consumer,
)


def test_capture_frame_given_low_confidence_should_zero_xyv() -> None:
    pose_model = MagicMock()
    kpts = np.array(
        [
            [0.1, 0.2, 0.9],
            [0.3, 0.4, 0.1],
        ],
        dtype=np.float32,
    )
    flat_expected = kpts.copy()
    flat_expected[1] = 0.0

    result = MagicMock()
    result.keypoints = MagicMock()
    result.keypoints.data = [MagicMock()]
    result.keypoints.data[0].numpy.return_value = kpts
    result.boxes = MagicMock()
    result.boxes.id = None

    pose_model.track.return_value = [result]
    frame = np.zeros((4, 4, 3), dtype=np.uint8)

    out = _capture_frame(pose_model, frame)

    assert out is not None
    person_id, flat = out[0]
    assert person_id == 0
    np.testing.assert_array_equal(flat, flat_expected.flatten())


def test_capture_frame_given_empty_keypoints_should_return_empty_list() -> None:
    pose_model = MagicMock()
    result = MagicMock()
    result.keypoints = MagicMock()
    result.keypoints.data = []
    pose_model.track.return_value = [result]

    assert _capture_frame(pose_model, np.zeros((2, 2, 3))) == []


def test_feed_buffers_given_full_window_and_interval_should_put_window() -> None:
    buffer_queue: queue.Queue = queue.Queue()
    buffers = defaultdict[int, deque](lambda: deque(maxlen=WINDOW_SIZE))
    last_inference: dict[int, float] = {}
    last_seen: dict[int, float] = {}

    kpt = np.zeros(51, dtype=np.float32)
    t0 = 1000.0
    for i in range(WINDOW_SIZE):
        _feed_buffers(
            [(1, kpt)],
            buffers,
            last_inference,
            last_seen,
            buffer_queue,
            t0 + i * 0.01,
        )

    assert not buffer_queue.empty()
    pid, window = buffer_queue.get_nowait()
    assert pid == 1
    assert window.shape == (WINDOW_SIZE, 51)
    assert last_inference[1] == pytest.approx(t0 + (WINDOW_SIZE - 1) * 0.01)


def test_feed_buffers_given_recent_inference_should_not_enqueue_again() -> None:
    buffer_queue: queue.Queue = queue.Queue()
    buffers = defaultdict[int, deque](lambda: deque(maxlen=WINDOW_SIZE))
    last_inference: dict[int, float] = {}
    last_seen: dict[int, float] = {}

    kpt = np.zeros(51, dtype=np.float32)
    base = 2000.0
    for i in range(WINDOW_SIZE):
        _feed_buffers([(1, kpt)], buffers, last_inference, last_seen, buffer_queue, base + i * 0.01)

    assert not buffer_queue.empty()
    buffer_queue.get_nowait()

    _feed_buffers([(1, kpt)], buffers, last_inference, last_seen, buffer_queue, base + WINDOW_SIZE * 0.01)

    assert buffer_queue.empty()


def test_feed_buffers_given_inactive_person_should_drop_buffer_after_grace() -> None:
    buffer_queue: queue.Queue = queue.Queue()
    buffers = defaultdict[int, deque](lambda: deque(maxlen=WINDOW_SIZE))
    last_inference: dict[int, float] = {7: 0.0}
    last_seen: dict[int, float] = {7: 0.0}

    buffers[7].extend([np.zeros(51, dtype=np.float32)] * 5)

    _feed_buffers([], buffers, last_inference, last_seen, buffer_queue, 4.0)

    assert 7 not in buffers
    assert 7 not in last_inference
    assert 7 not in last_seen


def test_run_frame_consumer_given_one_frame_should_track_and_feed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arr = np.zeros((8, 8, 3), dtype=np.uint8)
    payload = pickle.dumps(arr)

    mock_socket = MagicMock()
    mock_socket.recv_multipart.side_effect = [
        [b"frame", payload],
        KeyboardInterrupt(),
    ]

    mock_context = MagicMock()
    mock_context.socket.return_value = mock_socket

    monkeypatch.setattr(
        "app.core.frame_consumer.zmq.Context",
        lambda *args: mock_context,
    )

    pose_model = MagicMock()
    kpts = np.ones((2, 3), dtype=np.float32) * 0.5
    result = MagicMock()
    result.keypoints = MagicMock()
    result.keypoints.data = [MagicMock()]
    result.keypoints.data[0].numpy.return_value = kpts
    result.boxes = MagicMock()
    result.boxes.id = None
    pose_model.track.return_value = [result]

    buffer_queue: queue.Queue = queue.Queue()

    with patch("app.core.frame_consumer.time.monotonic", side_effect=[0.0, 1.0, 1.0]):
        run_frame_consumer(pose_model, captures_per_second=10, buffer_queue=buffer_queue)

    pose_model.track.assert_called()
    mock_socket.close.assert_called_once()
    mock_context.term.assert_called_once()
