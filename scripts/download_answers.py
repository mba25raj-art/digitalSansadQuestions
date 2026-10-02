"""Download untouched official PDFs and validate completeness before Pages publication."""
import concurrent.futures, hashlib, io, json, re, time, urllib.request, zipfile
from pathlib import Path
from pypdf import PdfReader

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'pdf-manifest.json').read_text())
out=root/'_site'
assert len(manifest)==86 and len({r['id'] for r in manifest})==86
(out/'answers').mkdir(parents=True, exist_ok=True)

def download(r):
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(r['url'],headers={'User-Agent':'Mozilla/5.0','Accept':'application/pdf'})
            with urllib.request.urlopen(req,timeout=45) as response: raw=response.read()
            assert raw.startswith(b'%PDF-'), 'Response is not a PDF'
            pdf=PdfReader(io.BytesIO(raw))
            assert len(pdf.pages)==r['pages'], f"Page count differs: {len(pdf.pages)} vs {r['pages']}"
            text=pdf.pages[0].extract_text() or ''
            if text.strip():
                assert re.search(r'(?<!\d)'+re.escape(r['number'])+r'(?!\d)',text), 'Question number missing'
            (out/r['file']).write_bytes(raw)
            print(f"Verified {r['id']}: {len(raw)} bytes, {len(pdf.pages)} pages",flush=True)
            return {**r,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
        except Exception as exc:
            last=exc
            if attempt<2: time.sleep(2)
    raise RuntimeError(f"Cannot archive {r['id']}: {last}")

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    verified=list(pool.map(download,manifest))
assert sum(r['pages'] for r in verified)==273
(out/'answers/manifest.json').write_text(json.dumps(verified,indent=2,ensure_ascii=False))
with zipfile.ZipFile(out/'answers/all-86-answer-pdfs.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for r in verified: archive.write(out/r['file'],Path(r['file']).name)
    archive.write(out/'answers/manifest.json','manifest.json')
print('SUCCESS: 86 original PDFs, 273 pages, individual downloads and complete ZIP verified.',flush=True)
