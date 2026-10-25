r"""参数变化分析：包头大小与缓存配额对两种交换方式的影响。

只读取 src/ 的教师框架与本人实现，结果写入 results/extra/，不覆盖基线的
comparison.json / comparison.csv / 3 张图。运行：

    .\.venv\Scripts\python.exe analysis\param_sweep.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.metrics import summarize  # noqa: E402
from src.models import Config  # noqa: E402
from src.utils import make_traffic, simulate  # noqa: E402

SCENARIOS = ("continuous", "staggered_burst", "synchronized_burst", "light_random")
MODES = ("circuit", "packet")
HEADER_VALUES = (0, 16, 32, 48, 64)
BUFFER_VALUES = (1024, 2048, 4096, 8192)
KEYS = (
    "payload_utilization",
    "wire_utilization",
    "mean_delay_ms",
    "max_delay_ms",
    "loss_ratio",
    "backlog_payload_bits",
)


def sweep(experiment: str, param: str, value: int, cfg: Config) -> list[dict]:
    """对给定配置跑四场景 × 两模型，返回长表行。"""
    rows: list[dict] = []
    for scenario in SCENARIOS:
        arrivals = make_traffic(scenario, cfg)
        for mode in MODES:
            raw = simulate(arrivals, cfg, mode)
            metrics = summarize(raw, cfg)
            rows.append(
                dict(
                    experiment=experiment,
                    param=param,
                    value=value,
                    scenario=scenario,
                    mode=mode,
                    **metrics,
                )
            )
    return rows


def plot(rows: list[dict], out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    header_rows = [r for r in rows if r["experiment"] == "header_bits"]
    buffer_rows = [r for r in rows if r["experiment"] == "buffer_payload_bits"]

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.4))
    colors = {"continuous": "#27638b", "staggered_burst": "#d27a35",
              "synchronized_burst": "#4d8f5a", "light_random": "#8a5fa8"}

    ax = axs[0]
    for scenario in ("continuous", "staggered_burst", "synchronized_burst"):
        for mode, style in (("packet", "-o"), ("circuit", "--")):
            subset = [r for r in header_rows if r["scenario"] == scenario and r["mode"] == mode]
            ax.plot([r["value"] for r in subset],
                    [r["loss_ratio"] * 100 for r in subset],
                    style, color=colors[scenario], markersize=3,
                    label=f"{scenario} ({mode})")
    ax.set(xlabel="Packet header bits per record", ylabel="Payload loss ratio (%)",
           title="Header overhead: packet vs fixed-slot circuit")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=6)

    ax = axs[1]
    for scenario in ("continuous", "staggered_burst", "synchronized_burst"):
        for mode, style in (("packet", "-o"), ("circuit", "--")):
            subset = [r for r in buffer_rows if r["scenario"] == scenario and r["mode"] == mode]
            ax.plot([r["value"] for r in subset],
                    [r["loss_ratio"] * 100 for r in subset],
                    style, color=colors[scenario], markersize=3,
                    label=f"{scenario} ({mode})")
    ax.set(xlabel="Payload buffer quota (bits)", ylabel="Payload loss ratio (%)",
           title="Buffer quota sensitivity (header = 32 bit)", xscale="log")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=6)

    fig.tight_layout()
    fig.savefig(out / "param_sweep.png", dpi=150)
    plt.close(fig)


def main() -> int:
    out = ROOT / "results" / "extra"
    out.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    runs: list[dict] = []
    for header in HEADER_VALUES:
        cfg = Config(header_bits=header)
        rows += sweep("header_bits", "header_bits", header, cfg)
        runs.append(dict(experiment="header_bits", **{k: v for k, v in cfg.__dict__.items()}))
    for buffer_bits in BUFFER_VALUES:
        cfg = Config(buffer_payload_bits=buffer_bits)
        rows += sweep("buffer_payload_bits", "buffer_payload_bits", buffer_bits, cfg)
        runs.append(dict(experiment="buffer_payload_bits", **{k: v for k, v in cfg.__dict__.items()}))

    fields = ["experiment", "param", "value", "scenario", "mode", *KEYS]
    with (out / "parameter_sweep.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (out / "parameter_sweep.json").write_text(
        json.dumps(dict(conditions="除所列参数外其余为基线", runs=runs, rows=rows),
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    plot(rows, out)

    print(f"wrote {len(rows)} rows -> {out}")
    for experiment in ("header_bits", "buffer_payload_bits"):
        print(f"\n== {experiment} ==")
        for r in rows:
            if r["experiment"] != experiment or r["mode"] != "packet":
                continue
            if r["scenario"] not in ("continuous", "staggered_burst"):
                continue
            print(f"{r['scenario']:18s} value={r['value']:5d} "
                  f"util={r['payload_utilization']:.3f} loss={r['loss_ratio']:.3f} "
                  f"mean_delay={r['mean_delay_ms']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
