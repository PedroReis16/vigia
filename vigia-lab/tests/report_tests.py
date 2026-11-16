from vigia_lab.report import evaluate_take, summarize, to_markdown


def _meta(label="FALL", **kw):
    m = {
        "take": "queda_take01", "scenario_label": label, "tag": "fps10_baseline",
        "event_t_auto": 2.0, "event_start_t": 2.4, "event_end_t": 3.0,
        "quality": {"delivered_fps": 10.0, "untracked_frames": 0, "id_set_changes_delivered": 0},
        "resets": [],
    }
    m.update(kw)
    return m


def _dec(model, t, alert):
    return {"model": model, "t_rel": str(t), "alert": str(int(alert))}


def _row(rows, model):
    return next(r for r in rows if r["model"] == model)


def test_fall_detected_within_window_and_latency_from_auto_onset() -> None:
    dec = [_dec("gru34", 1.0, 0), _dec("gru34", 3.5, 1), _dec("gru34", 4.0, 1), _dec("gru37", 1.0, 0)]
    rows = evaluate_take(_meta(), dec)
    g34, g37 = _row(rows, "gru34"), _row(rows, "gru37")
    assert g34["detected"] == 1 and g34["latency_s"] == 1.5 and g34["alert_before_start"] == 0
    assert g37["detected"] == 0 and g37["latency_s"] == ""


def test_alert_after_window_does_not_count_and_early_alert_is_flagged() -> None:
    dec = [_dec("gru34", 1.0, 1), _dec("gru37", 6.0, 1)]      # janela = [2.0, 3.0 + 2.0]
    rows = evaluate_take(_meta(), dec)
    assert _row(rows, "gru34")["detected"] == 0 and _row(rows, "gru34")["alert_before_start"] == 1
    assert _row(rows, "gru37")["detected"] == 0


def test_reference_falls_back_to_mark_minus_reaction_time() -> None:
    meta = _meta(event_t_auto=None, event_start_t=2.4, event_end_t=None)
    rows = evaluate_take(meta, [_dec("math", 2.2, 1)])         # início de referência = 2.0
    assert _row(rows, "math")["detected"] == 1 and _row(rows, "math")["latency_s"] == 0.2


def test_adl_false_alarm_and_max_gap() -> None:
    dec = [_dec("math", 1.0, 0), _dec("math", 1.1, 0), _dec("math", 3.1, 1)]
    row = _row(evaluate_take(_meta("ADL"), dec), "math")
    assert row["false_alarm"] == 1 and row["max_gap_s"] == 2.0 and row["detected"] == ""


def test_summary_and_markdown() -> None:
    rows = evaluate_take(_meta(), [_dec("gru34", 3.0, 1)]) + evaluate_take(_meta("ADL", take="adl_take01"), [])
    s = [x for x in summarize(rows) if x["model"] == "gru34"][0]
    assert (s["falls"], s["detected"], s["adl"], s["false_alarms"]) == (1, 1, 1, 0)
    assert "| fps10_baseline | gru34 | 1/1 |" in to_markdown([s])
