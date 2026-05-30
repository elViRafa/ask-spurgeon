# Helper Scripts

## download_sermons.py

Downloads individual `chs*.pdf` files from spurgeongems.org for testing the PDF ingestion path.

**Strongly prefer the Markdown source** for real use:

```bash
git clone https://github.com/lyteword/chspurgeon-sermons.git ../data/chspurgeon-sermons
```

The PDF path is mainly useful for:
- Comparing extraction quality
- Historical fidelity projects
- Testing the `utils/metadata.py` PDF parser
