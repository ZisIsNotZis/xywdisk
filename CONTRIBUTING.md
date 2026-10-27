# Contributing to xywdisk

This repository is an archive of a finished experiment, not a maintained
project. It is kept because the four capture files and the two script revisions
are the only surviving record of a bench that no longer exists. Contributions
are welcome, but they are corrections and additions of evidence, not feature
work.

## Scope

In scope:

- Experiment metadata: what each `real*.47f,34f` file is, row order, the
  physical unit of the 34 sensor channels, the meaning of the `120.1` baseline.
- Corrections to `docs/project-status.md` or `README.md` that are backed by the
  code, the notebook contents, or the bytes in a capture file.
- Sanitisation: anything that still leaks a private bench address, hostname or
  credential.
- Clearly labelled experimental branches, kept off `master`.

Out of scope:

- Reviving the bench controller as a working system, or claiming in prose that
  it works. It does not.
- Rewriting the captures, re-recording them, or regenerating them from a
  simulation.
- Packaging, publishing, adding a test suite, or adding CI. The repository has
  none of these on purpose.

## Checks

There is nothing to build and nothing to run automatically: no package, no test
suite, no linter, no CI. The only verification available is reading the files.

Before opening a pull request:

- Quote the evidence for the claim: a file and line, a notebook cell, or a byte
  offset and size. `docs/project-status.md` is where a new fact belongs, with
  the evidence beside it.
- Confirm the capture files are byte-identical to `master`
  (`git diff --stat master -- 'real*.47f,34f'` must be empty).
- If you touched a notebook, run it end to end yourself and say which capture
  file it read. The committed notebooks ask numpy for `shape=9999`, which is
  larger than every capture; map the real row count instead.
- Keep a change to one idea. Documentation, sanitisation and experimental code
  are separate pull requests.

## Issues

- One issue per correction, titled with the file it concerns.
- Say what you observed and how you observed it. "Row 48 of `real3.47f,34f` is
  all zeros" is actionable; "the data looks wrong" is not.
- Do not paste bench addresses, credentials, or private network details into an
  issue — that is the one thing this archive was cleaned of.

## Licence

By contributing you agree your contribution is released under
[AGPL-3.0-only](LICENSE), the licence of the repository.
