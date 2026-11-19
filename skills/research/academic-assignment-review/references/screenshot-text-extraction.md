# Reading a document that arrives as phone screenshots

Often the only copy of a submitted assignment is a run of tall phone screenshots (1179×2556 per image), sometimes eight or more. `vision_analyze` downscales those to roughly half width — body text becomes unreadable — and the image is dropped from context after the turn, so an unrecorded read is a lost read.

## Split before you read

Slice each screenshot at native width and read the slices:

```python
from PIL import Image
import glob, os

os.makedirs("/tmp/doc", exist_ok=True)
for p in sorted(glob.glob("/path/to/img_*.png")):
    im = Image.open(p).convert("RGB")
    w, h = im.size
    n = 3 if h > 3000 else 2
    step = h // n
    for i in range(n):
        box = (0, i * step, w, min(h, (i + 1) * step + 40))
        im.crop(box).save(f"/tmp/doc/{os.path.basename(p)[:-4]}_p{i}.png")
```

The `+40` overlap prevents a line of text from being cut in half at the slice boundary.

## Read, and record

- **Transcribe as you go.** Write each page's text into your reasoning or a scratch file the moment you read it. The image will not be in context on the next turn; re-reading the same slice because you did not record it is the main time sink in this workflow.
- **Read in document order.** Screenshot filenames are hashes, so establish order from content (page numbers, heading overlap between the bottom of one slice and the top of the next).
- **Expect overlap.** Consecutive screenshots usually repeat a paragraph; de-duplicate when assembling.
- **Ask for the original file.** If the user still has the `.docx` or `.pdf`, request it — a text layer is faster, exact, and preserves headings and the reference list. Screenshots are the fallback, not the source.
- **Note what is not there.** A run of screenshots rarely covers the whole document; say plainly which sections you could not see rather than inferring them.

## When OCR is worth it

For a handful of pages, vision reads Norwegian, tables and headings well and needs no install. Reaching for tesseract or a PyTorch OCR stack pays off only at dozens of pages; check `which tesseract` before planning around it rather than assuming it exists.

## Cross-check the numbers after transcription

Transcription introduces digit errors that look like author errors. Before reporting a wrong sample size, age range or percentage, re-crop that region at full resolution and confirm the glyphs — a misread "20–30" reported as an internal inconsistency is worse than missing it.
