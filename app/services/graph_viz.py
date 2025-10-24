from __future__ import annotations

import pathlib
import re
import tempfile

from pyvis.network import Network
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import NamespaceManager
from rdflib.extras.external_graph_libs import rdflib_to_networkx_digraph
import networkx as nx
from networkx.algorithms.community import (
    louvain_communities,
    asyn_lpa_communities,
    greedy_modularity_communities,
    quality,
)

try:
    from networkx.algorithms.community import leiden_communities
    HAS_LEIDEN = True
except Exception:  # noqa: BLE001
    HAS_LEIDEN = False

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


def _apply_theme_to_pyvis_html(pyvis_html: str, toolbar_right_extra: str = "") -> str:
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
          <span style="margin-left:auto"></span>
          {toolbar_right_extra}
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
    community_algo: str = "leiden",   # ← NEW
) -> str:
    net = Network(
        height="100%",
        width="100%",
        bgcolor=bgcolor,
        font_color=fontcolor,
        cdn_resources="in_line",
    )

    # --- Build an NX view of the RDF graph for community detection ---
    nx_dg = rdflib_to_networkx_digraph(graph)  # nodes are rdflib terms
    G_u = nx_dg.to_undirected()

    # Compute communities (non-overlapping)
    comms: list[set] | None = None
    algo_used = "none"
    try:
        if community_algo == "leiden":
            if HAS_LEIDEN:
                comms = list(leiden_communities(G_u, weight=None, resolution=1.0, seed=42))
                algo_used = "leiden"
            else:
                # graceful fallback if Leiden not available
                comms = list(louvain_communities(G_u, weight=None, resolution=1.0, seed=42))
                algo_used = "louvain (fallback)"
        elif community_algo == "louvain":
            comms = list(louvain_communities(G_u, weight=None, resolution=1.0, seed=42))
            algo_used = "louvain"
        elif community_algo == "label_propagation":
            comms = list(asyn_lpa_communities(G_u, weight=None, seed=42))
            algo_used = "label_propagation"
        elif community_algo == "greedy_modularity":
            comms = list(greedy_modularity_communities(G_u, weight=None, resolution=1.0))
            algo_used = "greedy_modularity"
        else:
            comms = None
            algo_used = "none"
    except Exception:
        # If anything fails, render without community coloring
        comms = None
        algo_used = "none"

    # Map node -> community id (if we have communities)
    node_to_comm: dict[object, int] = {}
    if comms:
        for cid, cset in enumerate(comms):
            for n in cset:
                node_to_comm[n] = cid

    # Optional: modularity (only if we have a partition)
    modularity = None
    if comms:
        try:
            modularity = quality.modularity(G_u, comms, weight=None)
        except Exception:
            modularity = None

    # ---- PyVis node/edge construction (color by community via "group") ----

    node_ids: dict[object, str] = {}
    lit_counter = 0

    def _make_literal_id(lit: Literal) -> str:
        nonlocal lit_counter
        lit_counter += 1
        return f"lit:{lit_counter}"

    def add_node(term):
        if term in node_ids:
            return node_ids[term]

        # PyVis color handling: set 'group' == community id if known, otherwise type-based
        comm_group = node_to_comm.get(term, None)
        group = f"C{comm_group}" if comm_group is not None else ("BNode" if isinstance(term, BNode) else "IRI")

        if isinstance(term, Literal):
            node_id = _make_literal_id(term)
            net.add_node(
                node_id,
                label=_qname_or_str(graph, term),
                title=f"Literal\nvalue={term}\ndatatype={getattr(term, 'datatype', None)}\nlang={getattr(term, 'language', None)}"
                      + (f"\ncommunity=C{comm_group}" if comm_group is not None else ""),
                shape="box",
                group=f"C{comm_group}" if comm_group is not None else "Literal",
            )
        else:
            node_id = str(term)
            net.add_node(
                node_id,
                label=_qname_or_str(graph, term),
                title=f"{'BNode' if isinstance(term, BNode) else 'IRI'}\n{term}"
                      + (f"\ncommunity=C{comm_group}" if comm_group is not None else ""),
                group=group,
            )

        node_ids[term] = node_id
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

    # Render PyVis
    with tempfile.TemporaryDirectory() as tmpdir:
        out = pathlib.Path(tmpdir) / "graph.html"
        net.write_html(str(out), open_browser=False, notebook=False)
        raw = out.read_text(encoding="utf-8")

    # Toolbar status badge (algo, #comms, modularity)
    k = len(comms) if comms else 0
    mod_str = f"{modularity:.3f}" if isinstance(modularity, (int, float)) else "—"
    badge = f"""
      <span class="hint" style="opacity:.9">
        algo: <b>{algo_used}</b> • communities: <b>{k}</b> • modularity: <b>{mod_str}</b>
      </span>
    """

    return _apply_theme_to_pyvis_html(raw, toolbar_right_extra=badge)

