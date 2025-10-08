from __future__ import annotations

import pathlib
import re
import tempfile

from pyvis.network import Network
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import NamespaceManager

# --- Presentation fragments moved from templates into service boundary where needed ---

THEME_CSS = """
<style>
/* ... keep your existing variables and base styles ... */

  .wrap{ max-width:1100px; margin:min(6vw,3rem) auto; padding:0 1.25rem 2rem; }

  header.appbar{ display:flex; align-items:center; gap:0.9rem; margin-bottom:1rem; }
  .logo{ width:44px; height:44px; border-radius:12px; display:grid; place-items:center;
         background:linear-gradient(135deg, var(--accent), var(--accent-2)); color:#fff;
         box-shadow:var(--glow); font-size:1.25rem; }
  header.appbar h1{ margin:0; font-size:clamp(1.25rem, 2.5vw, 1.6rem); letter-spacing:.2px; }
  .subtitle{ margin:.25rem 0 0; color:var(--muted); font-size:.95rem; }

  /* ↓↓↓ IMPORTANT CHANGES ↓↓↓ */
  .card{
    background: color-mix(in srgb, var(--card) 92%, transparent);
    border:1px solid var(--border);
    border-radius:16px;
    box-shadow:0 6px 30px rgba(0,0,0,.12);

    /* layout so header/toolbar don't eat graph height */
    display:flex;
    flex-direction:column;
    min-height: calc(100vh - 180px); /* header + margins */
    overflow:hidden;
  }
  .toolbar{
    display:flex; justify-content:space-between; align-items:center; gap:0.75rem;
    padding:0.6rem 0.9rem;
    border-bottom:1px solid color-mix(in srgb, var(--border) 70%, transparent);
  }

  /* Force the graph container to fill the remaining viewport space */
  #mynetwork,
  .mynetwork{
    flex:1 1 auto;
    height: calc(100vh - 240px) !important; /* viewport-based height */
    width: 100% !important;
    border-radius: 0 0 12px 12px;
  }

  /* Ensure vis.js internals expand with the container */
  .vis-network, .vis-network canvas{
    width:100% !important;
    height:100% !important;
    display:block;
  }
</style>
"""

HEADER_HTML = """
<header class="appbar">
  <div class="logo">🐢</div>
  <div>
    <h1>TurtlyScope</h1>
    <p class="subtitle"><i>Because even turtles deserve clarity</i></p>
  </div>
</header>
"""


def _qname_or_str(g: Graph, term: URIRef | BNode | Literal | str) -> str:
    if isinstance(term, Literal):
        if term.language:
            return f'"{term}"@{term.language}'
        if term.datatype:
            nm: NamespaceManager = g.namespace_manager
            try:
                dt = nm.normalizeUri(term.datatype)
            except Exception:  # noqa: BLE001
                dt = str(term.datatype)
            return f'"{term}"^^{dt}'
        return f'"{term}"'
    if isinstance(term, (URIRef, BNode)):
        try:
            return g.namespace_manager.normalizeUri(term)
        except Exception:  # noqa: BLE001
            return str(term)
    return str(term)


def _apply_theme_to_pyvis_html(pyvis_html: str) -> str:
    # 1) Insert CSS in <head>
    themed = re.sub(
        r"<head(.*?)>",
        lambda m: f"<head{m.group(1)}>{THEME_CSS}",
        pyvis_html,
        count=1,
        flags=re.I | re.S,
    )
    # 2) Inject header + frame at top of <body>
    inject_top = f"""
    <div class="wrap">
      {HEADER_HTML}
      <div class="card">
        <div class="toolbar">
          <a class="btn" href="/">← Back to Home</a>
          <span class="hint">Tip: pan with drag, zoom with wheel</span>
        </div>
    """
    themed = re.sub(
        r"<body(.*?)>",
        lambda m: f"<body{m.group(1)}>{inject_top}",
        themed,
        count=1,
        flags=re.I | re.S,
    )

    return re.sub(r"</body>", "</div></div></body>", themed, count=1, flags=re.I | re.S)


def visualize_rdflib_graph_to_html(
    graph: Graph,
    include_literals: bool,
    bgcolor: str = "#0b1020",
    fontcolor: str = "#e7ecf5",
) -> str:
    net = Network(
        height="100%",
        width="100%",
        bgcolor=bgcolor,
        font_color=fontcolor,
        cdn_resources="in_line",  # self-contained HTML
    )

    seen = set()

    def add_node(term):
        if term in seen:
            return str(id(term)) if isinstance(term, Literal) else str(term)
        if isinstance(term, Literal):
            node_id = str(id(term))
            net.add_node(
                node_id,
                label=_qname_or_str(graph, term),
                title=(
                    f"Literal\nvalue={term}\n"
                    "datatype={getattr(term, 'datatype', None)}\n"
                    "lang={getattr(term, 'language', None)}"
                ),
                shape="box",
                group="Literal",
            )
            seen.add(term)
            return node_id
        group = "BNode" if isinstance(term, BNode) else "IRI"
        node_id = str(term)
        net.add_node(
            node_id,
            label=_qname_or_str(graph, term),
            title=f"{group}\n{term}",
            group=group,
        )
        seen.add(term)
        return node_id

    for s, p, o in graph.triples((None, None, None)):
        sid = add_node(s)
        if isinstance(o, (URIRef, BNode)) or include_literals:
            oid = add_node(o)
            net.add_edge(sid, oid, label=_qname_or_str(graph, p), title=str(p))

    net.set_options(
        """
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -100,
          "centralGravity": 0.01,
          "springLength": 200,
          "springConstant": 0.08
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based"
      },
      "nodes": { "font": {"multi": "md"} }
    }"""
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        out = pathlib.Path(tmpdir) / "graph.html"
        net.write_html(str(out), open_browser=False, notebook=False)
        raw = out.read_text(encoding="utf-8")

    return _apply_theme_to_pyvis_html(raw)
