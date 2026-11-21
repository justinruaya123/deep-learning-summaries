# Deep Learning Summaries

Source-linked weekly digests of deep-learning research, models, and the infrastructure used to train and serve them.

**[Read the website →](https://justinruaya123.github.io/deep-learning-summaries/)**

The dark news feed includes search, topic filters, full weekly articles, and clickable citations. Reading works without JavaScript; only search and filtering require it.

## Latest issue

**[November 9–15, 2026](summaries/2026-11-09_to_2026-11-15.md)** — the last completed Monday–Sunday week before this repository was prepared on November 21, 2026.

The issue covers **22 developments backed by 31 primary sources** across model releases and access changes, selected research papers, safety and evaluation, and serving infrastructure. Each entry states what changed, why it matters, and what the evidence does **not** establish.

[Browse the source metadata and supporting excerpts](sources/2026-11-09_to_2026-11-15.json).

## Archive

| Week, inclusive | Digest |
| --- | --- |
| November 9–15, 2026 | [Read the summary](summaries/2026-11-09_to_2026-11-15.md) |

## How to read this repository

- **Curated, not exhaustive.** No claim is made to list every paper, launch, or announcement.
- **Primary sources first.** Dated official announcements, original papers, and release notes support the published entries.
- **Claims stay attributed.** Vendor benchmarks and authors' experiments are not independent reproductions.
- **Dates are explicit.** Research uses first-submission dates; updated products use the date of the particular change, not necessarily their original launch.
- **Manual content updates.** No recurring research or automatic news-generation job is configured. GitHub Pages publishes the committed `docs/` website when its content changes.

See [editorial policy](EDITORIAL_POLICY.md) for inclusion rules, limitations, and corrections.

## Build and publish the site

Requirements: Python 3.12+ and [uv](https://docs.astral.sh/uv/). Node.js 20+ is only needed for the small filter test suite.

```sh
uv run --with Markdown==3.11.3 python build_site.py
uv run --with Markdown==3.11.3 python -m unittest discover -s tests -v
node --test tests/filter.test.mjs
uv run python -m http.server 8000 --directory docs
```

Open `http://localhost:8000/` for a local preview. The committed `docs/` directory is the deployable artifact; GitHub Pages serves `main:/docs` with no runtime dependencies or third-party assets.

To add an edition, create matching `summaries/YYYY-MM-DD_to_YYYY-MM-DD.md` and `sources/YYYY-MM-DD_to_YYYY-MM-DD.json` files using the existing format, then run the builder, tests, and commit both the source content and regenerated `docs/` files. The latest issue and archive are selected from the dated filenames. Source metadata must provide the period, preparation date, development count, and complete numbered sources. The current five numbered topic sections define the homepage filters.
