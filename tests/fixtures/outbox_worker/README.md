# Synthetic offline outbox worker fixture

This is a tiny, disposable Python/SQLite reproduction environment. It has no
network access, no external services, and uses only the Python standard
library. All records and effects are synthetic.

Run the checks from this directory with:

```sh
python3 -m unittest -v
```

The command creates an in-memory database for each test. To experiment in a
disposable checkout, copy or clone the parent repository elsewhere, make a
separate branch or worktree there, and inspect only this directory. Do not
initialize a nested Git repository inside this versioned fixture.

`ticket.md` is the issue description supplied to an investigator. The
expected-results checklist is deliberately kept outside this source directory
in `tests/fixtures/outbox_worker_oracle.md`.
