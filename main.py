"""Single FastAPI app for visualizing RDF contents from Turtle format

Thomas F. Hagelien
SINTEF, SemanticMatter - 2025
"""

import re
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import NamespaceManager
from pyvis.network import Network
import tempfile
import pathlib


app = FastAPI()

FORM_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>🐢 TurtlyScope</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      :root {
        --bg: #0b1020;
        --bg-soft: #0f1428;
        --card: #111936;
        --text: #e7ecf5;
        --muted: #a9b3c9;
        --accent: #6ea8fe;
        --accent-2: #9b8cff;
        --border: #223055;
        --glow: 0 10px 30px rgba(110,168,254,0.25);
      }
      @media (prefers-color-scheme: light) {
        :root {
          --bg: #f7f8fb;
          --bg-soft: #eef2fb;
          --card: #ffffff;
          --text: #0f172a;
          --muted: #51607a;
          --accent: #3b82f6;
          --accent-2: #7c3aed;
          --border: #dbe2f1;
          --glow: 0 10px 30px rgba(59,130,246,0.25);
        }
      }

      /* Base layout */
      * { box-sizing: border-box; }
      html, body { height: 100%; }
      body {
        margin: 0;
        font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: var(--text);
        background:
          radial-gradient(1000px 600px at 20% -10%, rgba(110,168,254,0.25), transparent 60%),
          radial-gradient(800px 500px at 120% 20%, rgba(155,140,255,0.20), transparent 60%),
          linear-gradient(180deg, var(--bg-soft), var(--bg));
      }

      .wrap {
        max-width: 900px;
        margin: min(8vw,5rem) auto;
        padding: 0 1.25rem 3rem;
      }

      /* Header */
      header {
        display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem;
      }
      .logo {
        width: 52px; height: 52px; display: grid; place-items: center;
        border-radius: 14px;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        color: #fff; font-size: 1.5rem; box-shadow: var(--glow);
      }
      h1 {
        margin: 0;
        font-size: clamp(1.5rem, 3.5vw, 2.25rem);
        letter-spacing: 0.2px;
      }
      .subtitle {
        margin: 0.25rem 0 0; color: var(--muted); font-size: 0.975rem;
      }

      /* Card */
      .card {
        background: color-mix(in srgb, var(--card) 92%, transparent);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: 0 6px 30px rgba(0,0,0,0.12);
      }

      /* Textarea */
      .input-label {
        display: flex; align-items: center; justify-content: space-between;
        gap: 0.75rem; margin-bottom: 0.5rem;
      }
      .input-label span { color: var(--muted); font-size: 0.9rem; }
      textarea[name="turtle"] {
        width: 100%;
        min-height: min(52vh, 520px);
        resize: vertical;
        font: 500 0.95rem/1.45 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        padding: 1rem 1.1rem;
        border-radius: 12px;
        background: linear-gradient(180deg, color-mix(in srgb, var(--card) 96%, transparent), color-mix(in srgb, var(--card) 92%, transparent));
        border: 1px solid var(--border);
        color: var(--text);
        outline: none;
        transition: border-color .2s ease, box-shadow .2s ease, background .2s ease;
        caret-color: var(--accent);
      }
      textarea[name="turtle"]:focus {
        border-color: color-mix(in srgb, var(--accent) 60%, var(--border));
        box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 20%, transparent);
      }
      textarea::placeholder { color: color-mix(in srgb, var(--muted) 70%, transparent); }

      /* Controls row */
      .controls {
        display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; margin-top: 0.9rem;
      }

      /* Fancy toggle for include_literals */
      .switch {
        --h: 22px;
        position: relative; display: inline-flex; align-items: center; gap: 0.5rem;
        font-size: 0.95rem; color: var(--muted);
      }
      .switch input { position: absolute; opacity: 0; inset: 0; cursor: pointer; }
      .track {
        width: 42px; height: var(--h); border-radius: 999px;
        background: color-mix(in srgb, var(--border) 60%, transparent);
        border: 1px solid var(--border);
        transition: background .2s ease, border-color .2s ease;
        position: relative;
      }
      .thumb {
        width: calc(var(--h) - 6px); height: calc(var(--h) - 6px);
        background: #fff; border-radius: 999px; position: absolute; top: 50%; left: 3px; translate: 0 -50%;
        box-shadow: 0 3px 10px rgba(0,0,0,0.25);
        transition: left .2s ease, background .2s ease;
      }
      .switch input:checked + .track { background: color-mix(in srgb, var(--accent) 45%, transparent); border-color: color-mix(in srgb, var(--accent) 60%, var(--border)); }
      .switch input:checked + .track .thumb { left: calc(100% - (var(--h) - 3px)); }

      /* Buttons */
      .btn-row { display: flex; flex-wrap: wrap; gap: 0.6rem; margin-top: 0.6rem; }
      .btn {
        padding: 0.6rem 0.95rem;
        border-radius: 12px;
        border: 1px solid var(--border);
        background: linear-gradient(180deg, color-mix(in srgb, var(--card) 96%, transparent), color-mix(in srgb, var(--card) 92%, transparent));
        color: var(--text);
        cursor: pointer;
        transition: transform .06s ease, box-shadow .2s ease, border-color .2s ease, background .2s ease;
      }
      .btn:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(0,0,0,0.14); }
      .btn:active { transform: translateY(0); }

      .btn-primary {
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        color: #fff; border: none; box-shadow: var(--glow);
      }
      .btn-outline { color: var(--muted); }

      /* Footnote */
      .hint {
        margin-top: 0.5rem; color: var(--muted); font-size: 0.85rem;
      }

      /* Keep your existing .graph height in case it’s used elsewhere */
      .graph { height: 80vh; }
      
      /* Footer */
    .footer-brand{
        position: fixed;
        right: 1rem;
        bottom: 1rem;
        color: var(--muted);
        font-size: .9rem;
        opacity: .9;
        z-index: 1000;
        user-select: none;
        pointer-events: none; /* don't block graph or clicks */
    }
    </style>
  </head>
  <body>
    <div class="wrap">
      <header>
        <div class="logo" aria-hidden="true">🐢</div>
        <div>
          <h1>TurtlyScope</h1>
          <p class="subtitle">Drop your Turtles here.</p>
        </div>
      </header>

      <main class="card" role="main">
        <form method="post" action="/visualize" id="turtle-form">
          <label class="input-label" for="turtle">
            <strong>RDF Turtle</strong>
            <span>Supports `@prefix`, IRIs, and simple triples</span>
          </label>

          <textarea id="turtle" name="turtle" placeholder='@prefix ex: &lt;http://example.org/&gt; .
ex:Alice ex:knows ex:Bob .
ex:Bob ex:age "42"^^&lt;http://www.w3.org/2001/XMLSchema#integer&gt; .'></textarea>

          <div class="controls">
            <label class="switch">
              <input type="checkbox" name="include_literals" id="include_literals" checked />
              <span class="track" aria-hidden="true"><span class="thumb"></span></span>
              <span>include literals</span>
            </label>
            <span class="hint">Tip: Press <kbd>Ctrl</kbd>/<kbd>⌘</kbd> + <kbd>Enter</kbd> to visualize</span>
          </div>

          <div class="btn-row">
            <button class="btn btn-primary" type="submit">Visualize</button>
            <button class="btn btn-outline" type="button" id="insert-example">Insert example</button>
            <button class="btn btn-outline" type="reset" id="clear">Clear</button>
          </div>

          <p class="hint">You can also paste or drag &amp; drop a `.ttl` file or snippet into the field.</p>
        </form>
      </main>
    </div>

    <script>
      // Submit on Ctrl/Cmd+Enter
      const form = document.getElementById('turtle-form');
      const textarea = document.getElementById('turtle');
      form.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') form.requestSubmit();
      });

      // Drag & drop support (text / .ttl files)
      ;(() => {
        const prevent = e => { e.preventDefault(); e.stopPropagation(); };
        ['dragenter','dragover','dragleave','drop'].forEach(evt => {
          textarea.addEventListener(evt, prevent, false);
        });
        ['dragenter','dragover'].forEach(evt => {
          textarea.addEventListener(evt, () => textarea.style.borderColor = 'var(--accent)', false);
        });
        ['dragleave','drop'].forEach(evt => {
          textarea.addEventListener(evt, () => textarea.style.borderColor = 'var(--border)', false);
        });
        textarea.addEventListener('drop', async (e) => {
          const dt = e.dataTransfer;
          if (!dt) return;
          // Prefer files if present
          if (dt.files && dt.files.length) {
            const file = dt.files[0];
            if (file.type.startsWith('text') || file.name.endsWith('.ttl')) {
              const text = await file.text();
              textarea.value = text;
            }
            return;
          }
          // Fallback to dropped text/HTML
          const text = dt.getData('text/plain') || dt.getData('text/html');
          if (text) textarea.value = text;
        });
      })();

      // Insert example
      document.getElementById('insert-example').addEventListener('click', () => {
        const example = `@prefix ex: <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:Alice a ex:Person ;
  ex:name "Alice" ;
  ex:knows ex:Bob .

ex:Bob a ex:Person ;
  ex:name "Bob" ;
  ex:age "42"^^xsd:integer ;
  ex:knows ex:Carol .

ex:Carol a ex:Person ;
  ex:name "Carol" ;
  ex:knows ex:Alice .`;
        textarea.value = example;
        textarea.focus();
      });

      // Clear button resets focus
      document.getElementById('clear').addEventListener('click', () => {
        setTimeout(() => textarea.focus(), 0);
      });
    </script>
    <footer class="footer-brand">By SemanticMatter</footer>
  </body>
</html>
"""

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


def apply_theme_to_pyvis_html(pyvis_html: str) -> str:
    """
    Injects our theme CSS, header, and a 'Back to Home' button into the PyVis HTML.
    Works with the standard HTML skeleton that pyvis.write_html generates.
    """
    # 1) Add our CSS into <head>
    themed = re.sub(
        r"<head(.*?)>",
        lambda m: f"<head{m.group(1)}>{THEME_CSS}",
        pyvis_html,
        count=1,
        flags=re.I | re.S,
    )

    # 2) Wrap the body content with our container + toolbar
    #    Insert header + card + toolbar right after <body>
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

    # 3) Close our wrappers before </body>
    themed = re.sub(
        r"</body>", "</div></div></body>", themed, count=1, flags=re.I | re.S
    )

    return themed


def _qname_or_str(g: Graph, term) -> str:
    if isinstance(term, Literal):
        if term.language:
            return f'"{term}"@{term.language}'
        if term.datatype:
            nm: NamespaceManager = g.namespace_manager
            try:
                dt = nm.normalizeUri(term.datatype)
            except Exception:
                dt = str(term.datatype)
            return f'"{term}"^^{dt}'
        return f'"{term}"'
    if isinstance(term, (URIRef, BNode)):
        try:
            return g.namespace_manager.normalizeUri(term)
        except Exception:
            return str(term)
    return str(term)


def visualize_rdflib_graph_to_html(graph: Graph, include_literals: bool) -> str:
    net = Network(
        height="100%",
        width="100%",
        bgcolor="#0b1020",
        font_color="#e7ecf5",
        cdn_resources="in_line",
    )

    added = set()

    def add_node(term):
        if term in added:
            return str(id(term)) if isinstance(term, Literal) else str(term)
        if isinstance(term, Literal):
            net.add_node(
                str(id(term)),
                label=_qname_or_str(graph, term),
                title=f"Literal\nvalue={term}\ndatatype={getattr(term, 'datatype', None)}\nlang={getattr(term, 'language', None)}",
                shape="box",
                group="Literal",
            )
            added.add(term)
            return str(id(term))
        else:
            group = "BNode" if isinstance(term, BNode) else "IRI"
            net.add_node(
                str(term),
                label=_qname_or_str(graph, term),
                title=f"{group}\n{term}",
                group=group,
            )
            added.add(term)
            return str(term)

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
        }
        """
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        out = pathlib.Path(tmpdir) / "graph.html"
        net.write_html(str(out), open_browser=False, notebook=False)
        raw = out.read_text(encoding="utf-8")

    return apply_theme_to_pyvis_html(raw)


@app.get("/", response_class=HTMLResponse)
def index():
    return FORM_HTML


@app.post("/visualize", response_class=HTMLResponse)
def visualize(turtle: str = Form(...), include_literals: str | None = Form(None)):
    try:
        g = Graph()
        g.parse(data=turtle, format="turtle")
        html = visualize_rdflib_graph_to_html(
            g, include_literals=include_literals is not None
        )
        return html
    except Exception as e:
        return HTMLResponse(f"<pre>Parse error:\n{e}</pre>", status_code=400)


@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"
