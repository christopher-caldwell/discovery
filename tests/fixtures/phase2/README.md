# Phase 2 webhook ordering fixture

This is a tiny, offline source repository used to exercise Discovery Phase 2
claims about webhook ordering and retries. The app intentionally has a
last-write-wins bug: a late retry can overwrite a newer event.

Everything in this directory is a fabricated test fixture. The file named
`vendor-webhook-doc.md` is a fabricated local transcription of primary vendor
guidance; it is not live research and contains no network citation. The ticket,
reproduction, and question are likewise fabricated evidence for the scenario.

To run it from this seed directory:

```sh
python -m pytest -q
```

The disposable runnable copy lives in `.discovery/phase2-fixture/` and may be
recreated from these seed files by copying this directory. It is deliberately
not a production implementation and must not be used as one.
