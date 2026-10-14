"""Convert a '# %%' / '# %% [markdown]' percent-format .py file into an .ipynb (no outputs)."""
import re
import sys

import nbformat

src, dst = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()
parts = re.split(r"^# %%(.*)$", text, flags=re.M)
cells = []
for header, body in zip(parts[1::2], parts[2::2]):
    body = body.strip("\n")
    if "[markdown]" in header:
        lines = [re.sub(r"^# ?", "", l) for l in body.splitlines()]
        cells.append(nbformat.v4.new_markdown_cell("\n".join(lines)))
    else:
        cells.append(nbformat.v4.new_code_cell(body))
nb = nbformat.v4.new_notebook(cells=cells)
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nb.metadata["language_info"] = {"name": "python"}
nbformat.write(nb, dst)
print(f"{dst}: {len(cells)} cells")
