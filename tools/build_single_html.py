#!/usr/bin/env python3
"""Build a self-contained single-file HTML version of 鹈鹕骑行_纯代码全片.

Visuals stay vector-only (no external images or fonts); the single Opus mix at
data/audio.opus is embedded into the virtual file system. The gzip payload is
stored as escaped ISO-8859-1 text instead of base64 to avoid the 4/3 expansion.
"""

import base64
import gzip
import json
import pathlib
import re


PAYLOAD_PREFIX = "~"
PAYLOAD_CODES = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-_"
# Printable ISO-8859-1 except tab/LF, plus the HTML-hostile "<" and the escape "~".
PAYLOAD_ESCAPED = (
    list(range(0, 9)) + list(range(11, 32)) + [127] + list(range(128, 160)) + [60, 126]
)
PAYLOAD_ESCAPE = {value: PAYLOAD_CODES[index] for index, value in enumerate(PAYLOAD_ESCAPED)}
assert len(PAYLOAD_CODES) == len(PAYLOAD_ESCAPED) == 65


def encode_payload(data: bytes) -> str:
    """Encode bytes as printable ISO-8859-1, escaping unprintable/HTML-hostile bytes."""
    chunks = []
    for value in data:
        code = PAYLOAD_ESCAPE.get(value)
        chunks.append(PAYLOAD_PREFIX + code if code is not None else chr(value))
    return "".join(chunks)


def trim_js_lines(code: str) -> str:
    """Safely drop whole-line // comments and leading/trailing whitespace."""
    out = []
    for line in code.splitlines():
        s = line.strip()
        if not s or s.startswith("//"):
            continue
        out.append(s)
    return "\n".join(out)


def collect_topological_modules(root: pathlib.Path, entry_rel: str):
    """Collect active ES modules from entry in topological order (dependencies first)."""
    order = []
    visited = set()
    dep_map = {}

    def visit(rel: str):
        if rel in visited:
            return
        visited.add(rel)
        p = root / rel
        txt = p.read_text(encoding="utf-8")
        deps = []
        for m in re.finditer(r"""(?:from|import)\s*\(?\s*['"](\.[^'"]+)['"]""", txt):
            spec = m.group(1)
            nxt = (p.parent / spec).resolve()
            if nxt.is_file():
                nxt_rel = str(nxt.relative_to(root))
                deps.append([spec, nxt_rel])
                visit(nxt_rel)
        dep_map[rel] = deps
        order.append(rel)

    visit(entry_rel)
    return order, dep_map


def build_single_html(root: pathlib.Path, out_path: pathlib.Path):
    css_parts = [
        (root / "styles/tokens.css").read_text(encoding="utf-8"),
        (root / "styles/layout.css").read_text(encoding="utf-8"),
        (root / "styles/components/player.css").read_text(encoding="utf-8"),
    ]
    bundled_css = "\n".join(css_parts)

    json_files = {}
    for p in sorted((root / "data").glob("*.json")):
        json_files[f"data/{p.name}"] = p.read_text(encoding="utf-8")
    json_files["data/audio/manifest.json"] = (root / "data/audio/manifest.json").read_text(encoding="utf-8")

    vendor_p5 = (root / "assets/vendor/p5.min.js").read_text(encoding="utf-8")
    vendor_brush = (root / "assets/vendor/p5.brush.js").read_text(encoding="utf-8")
    opus_b64 = base64.b64encode((root / "data/audio.opus").read_bytes()).decode("ascii")

    mod_order, dep_map = collect_topological_modules(root, "src/app.js")
    modules_payload = []
    for rel in mod_order:
        code = trim_js_lines((root / rel).read_text(encoding="utf-8"))
        modules_payload.append([rel, code, dep_map[rel]])

    vfs_obj = {
        "json": json_files,
        "audioOpus": opus_b64,
        "p5": vendor_p5,
        "brush": vendor_brush,
        "modules": modules_payload,
    }
    vfs_bytes = json.dumps(vfs_obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    vfs_gz = gzip.compress(vfs_bytes, compresslevel=9)
    vfs_payload = encode_payload(vfs_gz)

    html_out = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="iso-8859-1">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title></title>
  <link rel="icon" href="data:,">
  <style>
{bundled_css}
  </style>
</head>
<body>
  <main class="cinema-viewport">
    <div id="cinema-shell" class="cinema-shell">
      <div class="screen-wrap">
        <canvas id="film" width="1920" height="1440"></canvas>
      </div>
    </div>
  </main>
  <script id="vfs-payload" type="text/plain">{vfs_payload}</script>
  <script>
(async function bootSingleHtml() {{
  const filmTitle = String.fromCodePoint(0x9e49, 0x9e55, 0x516d, 0x5343, 0x5e74, 0x7684, 0x8f66);
  document.title = filmTitle;
  const filmCanvas = document.getElementById('film');
  if (filmCanvas) filmCanvas.setAttribute('aria-label', filmTitle);

  const codes = '{PAYLOAD_CODES}';
  const escaped = [];
  for (let i = 0; i < 9; i++) escaped.push(i);
  for (let i = 11; i < 32; i++) escaped.push(i);
  escaped.push(127);
  for (let i = 128; i < 160; i++) escaped.push(i);
  escaped.push(60, 126);

  const text = document.getElementById('vfs-payload').textContent;
  const bytes = new Uint8Array(text.length);
  let size = 0;
  for (let i = 0; i < text.length; i++) {{
    const code = text.charCodeAt(i);
    if (code === 126) {{
      if (++i >= text.length) throw new Error('Truncated VFS payload escape');
      const index = codes.indexOf(text[i]);
      if (index < 0 || index >= escaped.length) throw new Error('Invalid VFS payload escape');
      bytes[size++] = escaped[index];
    }} else if (code <= 0xFF) {{
      bytes[size++] = code;
    }} else {{
      throw new Error('VFS payload requires ISO-8859-1 decoding (got U+' + code.toString(16) + ')');
    }}
  }}
  const packed = bytes.subarray(0, size);
  const ds = new DecompressionStream('gzip');
  const stream = new Blob([packed]).stream().pipeThrough(ds);
  const vfs = JSON.parse(await new Response(stream).text());

  const origFetch = window.fetch.bind(window);
  window.fetch = async (input, init) => {{
    const urlStr = typeof input === 'string' ? input : (input && input.url) || '';
    const norm = urlStr.replace(/^\\.\\//, '').split('?')[0];
    if (Object.prototype.hasOwnProperty.call(vfs.json, norm)) {{
      return new Response(vfs.json[norm], {{
        status: 200,
        headers: {{ 'Content-Type': 'application/json; charset=utf-8' }}
      }});
    }}
    return origFetch(input, init);
  }};

  for (const srcCode of [vfs.p5, vfs.brush]) {{
    const s = document.createElement('script');
    s.textContent = srcCode;
    document.head.appendChild(s);
  }}

  const opusBin = atob(vfs.audioOpus);
  const opusBytes = new Uint8Array(opusBin.length);
  for (let i = 0; i < opusBin.length; i++) opusBytes[i] = opusBin.charCodeAt(i);
  window.__VFS_AUDIO_URL = URL.createObjectURL(new Blob([opusBytes], {{ type: 'audio/ogg' }}));

  const blobUrls = {{}};
  for (const [rel, rawCode, deps] of vfs.modules) {{
    let code = rawCode;
    for (const [spec, targetRel] of deps) {{
      const targetUrl = blobUrls[targetRel];
      if (!targetUrl) throw new Error('Missing topological module: ' + targetRel);
      code = code.split("'" + spec + "'").join(JSON.stringify(targetUrl));
      code = code.split('"' + spec + '"').join(JSON.stringify(targetUrl));
    }}
    blobUrls[rel] = URL.createObjectURL(new Blob([code], {{ type: 'application/javascript' }}));
  }}

  await import(blobUrls['src/app.js']);
}})().catch((err) => {{
  console.error(err);
  window.__loadError = String(err);
}});
  </script>
</body>
</html>
"""
    try:
        html_bytes = html_out.encode("iso-8859-1")
    except UnicodeEncodeError as exc:
        raise SystemExit(f"Single-file shell contains non-Latin-1 text: {exc}") from exc
    out_path.write_bytes(html_bytes)
    print(f"Built {out_path}")
    print(f"  Raw VFS JSON: {len(vfs_bytes):,} B ({len(vfs_bytes)/1024/1024:.2f} MiB)")
    print(f"  Gzip-9 VFS:   {len(vfs_gz):,} B ({len(vfs_gz)/1024/1024:.2f} MiB)")
    print(f"  Latin-1 payload: {len(vfs_payload):,} chars")
    sz = len(html_bytes)
    print(f"  Final HTML:   {sz:,} B ({sz/1024/1024:.2f} MiB | {sz/1000/1000:.2f} MB)")


if __name__ == "__main__":
    project_root = pathlib.Path(__file__).resolve().parent.parent
    out_file = project_root / "鹈鹕骑行_纯代码全片_单文件版.html"
    build_single_html(project_root, out_file)
