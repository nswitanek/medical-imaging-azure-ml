#!/usr/bin/env python
"""Render conceptual + Azure architecture diagrams from a single YAML spec.

One YAML spec describes zones, nodes and edges **once**. This utility renders
topologically-aligned artifacts from it:

- ``<stem>.conceptual.graphviz.png`` — vendor-neutral building blocks (plain labelled boxes,
  no logos).
- ``<stem>.azure.graphviz.png``      — the same graph mapped to Azure / Microsoft services, drawn
  with the **official Azure icon set** bundled by the ``diagrams`` library.
- ``<stem>.conceptual.drawio`` / ``<stem>.azure.drawio`` — editable draw.io starters (same
  nodes/edges/zones) so you can hand-tune a diagram in the **draw.io / Diagrams.net** editor.

Because every artifact is generated from the same nodes/edges with the same left-to-right layout,
they stay aligned by construction.

This is a repo-agnostic tool: it renders whatever spec file(s) you point it at. There is no
assumption about a ``scenarios/`` folder or a particular repository layout.

Usage
-----
    # Render one spec; outputs land next to the spec file.
    python render_diagrams.py path/to/architecture.yaml

    # Redirect outputs to another folder.
    python render_diagrams.py path/to/architecture.yaml --out-dir build/diagrams

    # Only (re)render the PNGs, leave the editable .drawio starters alone.
    python render_diagrams.py path/to/architecture.yaml --no-drawio

    # Batch: render every spec matching a glob (recursive ** supported).
    python render_diagrams.py --glob "diagrams/**/*.yaml"

Output naming
-------------
By default each artifact is prefixed with the spec's filename stem, e.g. ``payments.yaml`` ->
``payments.conceptual.graphviz.png``, ``payments.azure.graphviz.png``. As a special case, a spec
named exactly ``architecture.yaml`` uses the bare ``conceptual`` / ``azure`` names for
backwards-compatibility. Pass ``--stem NAME`` to force a specific prefix (``--stem ""`` for the
bare names).

Requirements
------------
Graphviz ``dot`` on PATH:
  - Windows: ``winget install Graphviz.Graphviz`` then add ``C:\\Program Files\\Graphviz\\bin`` to PATH
  - macOS:   ``brew install graphviz``
  - Linux:   ``sudo apt-get install graphviz`` (or your distro's package manager)
Python packages: ``pip install -r requirements.txt`` (``diagrams``, ``graphviz``, ``PyYAML``).

Spec format (YAML)
------------------
    title: Payments Fraud Scoring
    zones:                       # left-to-right order; ids referenced by nodes
      - {id: source,  label: "Sources"}
      - {id: prep,    label: "Ingest & Prep"}
      - {id: consume, label: "Consume"}
    nodes:
      - id: events
        zone: source
        conceptual: "Transaction events"
        azure: "Azure Event Hubs"
        icon: azure.analytics.EventHubs      # dotted path under the `diagrams` package (optional)
    edges:
      - [events, features]                                 # source -> target
      - [outcomes, features, "outcomes loop back", dashed] # + optional label + 'dashed'
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import diagrams  # noqa: F401  (used to locate the bundled icon resources)
import yaml
from graphviz import Digraph

# Resources ship at <site-packages>/resources/... (one level above the diagrams package).
_RESOURCES_BASE = Path(os.path.dirname(diagrams.__file__)).parent

# Vendor-neutral fill colours applied to conceptual boxes, cycled by zone order.
_ZONE_FILLS = ["#dae8fc", "#d5e8d4", "#ffe6cc", "#e1d5e7", "#f8cecc"]
_ZONE_STROKES = ["#6c8ebf", "#82b366", "#d79b00", "#9673a6", "#b85450"]

# Sans-serif font used everywhere. "Helvetica" can silently fall back to a serif face on some
# systems; Arial is reliably available on Windows. No italics anywhere by design.
_FONT = "Arial"


def _icon_path(dotted: str) -> str:
    """Resolve a `diagrams` node class (e.g. 'azure.ml.AzureOpenAI') to its icon PNG."""
    module_path, class_name = dotted.rsplit(".", 1)
    module = importlib.import_module(f"diagrams.{module_path}")
    node_cls = getattr(module, class_name)
    path = _RESOURCES_BASE / node_cls._icon_dir / node_cls._icon
    if not path.exists():
        raise FileNotFoundError(f"Icon not found for '{dotted}': {path}")
    return str(path)


def _load_spec(spec_path: Path) -> dict:
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec not found: {spec_path}")
    with open(spec_path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _resolve_stem(spec_path: Path, override: str | None) -> str:
    """Determine the filename prefix for a spec's rendered artifacts.

    ``override`` (including an explicit empty string) wins. Otherwise a spec literally named
    ``architecture.yaml`` uses bare ``conceptual``/``azure`` names; any other spec is prefixed
    with its filename stem so multiple diagrams can coexist in one folder.
    """
    if override is not None:
        return override
    stem = spec_path.stem
    return "" if stem == "architecture" else stem


def _output_stem(stem: str, kind: str) -> str:
    """Base filename (no extension) for a rendered artifact: ``kind`` or ``<stem>.<kind>``."""
    return kind if not stem else f"{stem}.{kind}"


def _zone_index(spec: dict) -> dict:
    return {z["id"]: i for i, z in enumerate(spec["zones"])}


def _base_graph(title: str) -> Digraph:
    g = Digraph("arch")
    g.attr(rankdir="LR", splines="ortho", nodesep="0.5", ranksep="1.0",
           bgcolor="white", fontname=_FONT, labelloc="t", fontsize="20", label=title)
    g.attr("edge", color="#555555")
    return g


def _add_edges(g: Digraph, spec: dict) -> None:
    for edge in spec.get("edges", []):
        src, dst = edge[0], edge[1]
        label = edge[2] if len(edge) > 2 else ""
        dashed = len(edge) > 3 and edge[3] == "dashed"
        attrs = {"label": label, "fontsize": "10", "fontname": _FONT}
        if dashed:
            # Dashed edges are feedback/loops by convention; drop their rank constraint so they
            # don't distort the primary left-to-right flow.
            attrs.update(style="dashed", color="#b85450", fontcolor="#b85450", constraint="false")
        g.edge(src, dst, **attrs)


def render_conceptual(spec: dict, out_no_ext: str) -> str:
    zi = _zone_index(spec)
    g = _base_graph(f"{spec['title']} — Conceptual")
    for zone in spec["zones"]:
        idx = zi[zone["id"]]
        with g.subgraph(name=f"cluster_{zone['id']}") as c:
            c.attr(label=zone["label"], style="dashed", color="#aaaaaa",
                   fontname=_FONT, fontsize="12", fontcolor="#666666")
            for node in spec["nodes"]:
                if node["zone"] != zone["id"]:
                    continue
                c.node(node["id"], label=node["conceptual"], shape="box", style="rounded,filled",
                       fillcolor=_ZONE_FILLS[idx % len(_ZONE_FILLS)],
                       color=_ZONE_STROKES[idx % len(_ZONE_STROKES)],
                       fontname=_FONT, fontsize="11", margin="0.18,0.12")
    _add_edges(g, spec)
    return g.render(filename=out_no_ext, format="png", cleanup=True)


def _html_label(text: str, image: str) -> str:
    """HTML-like label: fixed-size icon on top, wrapped text below (keeps text off the icon)."""
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe = safe.replace("\n", "<BR/>")
    img = image.replace("\\", "/")
    return (
        f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">'
        f'<TR><TD FIXEDSIZE="TRUE" WIDTH="62" HEIGHT="62"><IMG SCALE="TRUE" SRC="{img}"/></TD></TR>'
        f'<TR><TD><FONT FACE="{_FONT}" POINT-SIZE="10">{safe}</FONT></TD></TR>'
        f"</TABLE>>"
    )


def render_azure(spec: dict, out_no_ext: str) -> str:
    g = _base_graph(f"{spec['title']} — Azure / Microsoft")
    for zone in spec["zones"]:
        with g.subgraph(name=f"cluster_{zone['id']}") as c:
            c.attr(label=zone["label"], style="dashed", color="#aaaaaa",
                   fontname=_FONT, fontsize="12", fontcolor="#666666")
            for node in spec["nodes"]:
                if node["zone"] != zone["id"]:
                    continue
                if node.get("icon"):
                    c.node(node["id"], label=_html_label(node["azure"], _icon_path(node["icon"])),
                           shape="none", margin="0", fontname=_FONT)
                else:  # non-Azure source/sink without an icon — plain box
                    c.node(node["id"], label=node["azure"], shape="box", style="rounded",
                           fontname=_FONT, fontsize="10", margin="0.18,0.12")
    _add_edges(g, spec)
    return g.render(filename=out_no_ext, format="png", cleanup=True)


# --- editable draw.io starters ------------------------------------------------------------------
# Emitted from the same spec so a user can hand-tune in the draw.io editor. These are plain
# labelled boxes grouped by zone; swap in Azure shape stencils by hand if desired.

def _drawio(spec: dict, kind: str) -> str:
    zi = _zone_index(spec)
    # layout grid
    col_w, gap_x, x0 = 200, 20, 20
    row_h, gap_y, y0 = 70, 30, 70
    zone_h = 460
    # rows per zone
    rows: dict[str, int] = {z["id"]: 0 for z in spec["zones"]}
    pos: dict[str, tuple[int, int]] = {}
    cells: list[str] = []

    # zone containers
    for z in spec["zones"]:
        idx = zi[z["id"]]
        zx = x0 + idx * (col_w + gap_x)
        cells.append(
            f'<mxCell id="z_{z["id"]}" value="{escape(z["label"].upper())}" '
            f'style="rounded=0;whiteSpace=wrap;html=1;dashed=1;fillColor=none;strokeColor=#999999;'
            f'verticalAlign=top;fontStyle=2;fontSize=10;" vertex="1" parent="1">'
            f'<mxGeometry x="{zx}" y="40" width="{col_w}" height="{zone_h}" as="geometry" /></mxCell>'
        )

    # nodes
    for node in spec["nodes"]:
        idx = zi[node["zone"]]
        r = rows[node["zone"]]
        rows[node["zone"]] += 1
        nx = x0 + idx * (col_w + gap_x) + 20
        ny = y0 + r * (row_h + gap_y)
        pos[node["id"]] = (nx, ny)
        fill = _ZONE_FILLS[idx % len(_ZONE_FILLS)]
        stroke = _ZONE_STROKES[idx % len(_ZONE_STROKES)]
        raw = node["conceptual"] if kind == "conceptual" else node["azure"]
        label = escape(raw).replace("\n", "&#10;")
        cells.append(
            f'<mxCell id="{node["id"]}" value="{label}" '
            f'style="rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};" '
            f'vertex="1" parent="1">'
            f'<mxGeometry x="{nx}" y="{ny}" width="{col_w - 40}" height="60" as="geometry" /></mxCell>'
        )

    # edges
    for i, edge in enumerate(spec.get("edges", [])):
        src, dst = edge[0], edge[1]
        elabel = edge[2] if len(edge) > 2 else ""
        dashed = len(edge) > 3 and edge[3] == "dashed"
        style = "edgeStyle=orthogonalEdgeStyle;html=1;"
        if dashed:
            style += "dashed=1;strokeColor=#b85450;fontSize=9;"
        cells.append(
            f'<mxCell id="e{i}" value="{escape(elabel)}" style="{style}" edge="1" parent="1" '
            f'source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry" /></mxCell>'
        )

    body = "\n        ".join(cells)
    name = "Conceptual" if kind == "conceptual" else "Azure"
    return (
        f'<mxfile host="app.diagrams.net">\n'
        f'  <diagram name="{name}" id="{kind}">\n'
        f'    <mxGraphModel dx="900" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" '
        f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1100" pageHeight="540" '
        f'math="0" shadow="0">\n'
        f'      <root>\n'
        f'        <mxCell id="0" />\n'
        f'        <mxCell id="1" parent="0" />\n'
        f'        {body}\n'
        f'      </root>\n'
        f'    </mxGraphModel>\n'
        f'  </diagram>\n'
        f'</mxfile>\n'
    )


def render_drawio(spec: dict, out_dir: Path, stem: str) -> list:
    outputs = []
    for kind in ("conceptual", "azure"):
        out = out_dir / f"{_output_stem(stem, kind)}.drawio"
        out.write_text(_drawio(spec, kind), encoding="utf-8")
        outputs.append(str(out))
    return outputs


def render_spec(spec_path: Path, out_dir: Path | None = None, drawio: bool = True,
                stem: str | None = None) -> list:
    """Render a single spec file. Outputs go to ``out_dir`` (default: the spec's own folder)."""
    spec_path = spec_path.resolve()
    spec = _load_spec(spec_path)
    out_dir = (out_dir or spec_path.parent).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    resolved_stem = _resolve_stem(spec_path, stem)
    outputs = [
        render_conceptual(spec, str(out_dir / f"{_output_stem(resolved_stem, 'conceptual')}.graphviz")),
        render_azure(spec, str(out_dir / f"{_output_stem(resolved_stem, 'azure')}.graphviz")),
    ]
    if drawio:
        outputs += render_drawio(spec, out_dir, resolved_stem)
    for o in outputs:
        print(f"wrote {o}")
    return outputs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Render conceptual + Azure architecture diagrams from a YAML spec.")
    parser.add_argument("spec", nargs="?", help="Path to a YAML spec file.")
    parser.add_argument("--glob",
                        help="Render every spec matching this glob (recursive ** supported), "
                             "relative to the current directory. Mutually exclusive with a spec path.")
    parser.add_argument("--out-dir",
                        help="Write outputs here instead of next to each spec file.")
    parser.add_argument("--stem",
                        help="Force the output filename prefix (use '' for bare "
                             "conceptual/azure names). Default: derived from the spec filename.")
    parser.add_argument("--no-drawio", action="store_true",
                        help="Skip (re)writing the editable .drawio starters.")
    args = parser.parse_args(argv)

    if bool(args.spec) == bool(args.glob):
        parser.error("provide exactly one of: a spec path, or --glob PATTERN")

    if args.glob:
        targets = sorted(Path(".").glob(args.glob))
        targets = [t for t in targets if t.is_file()]
        if not targets:
            print(f"No spec files matched --glob {args.glob!r}", file=sys.stderr)
            return 1
    else:
        targets = [Path(args.spec)]

    out_dir = Path(args.out_dir) if args.out_dir else None
    for spec_path in targets:
        render_spec(spec_path, out_dir=out_dir, drawio=not args.no_drawio, stem=args.stem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
