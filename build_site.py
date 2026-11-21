"""Build the reading site from canonical Markdown and source metadata."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

import markdown
from markdown.extensions.toc import slugify

REPO = 'https://github.com/justinruaya123/deep-learning-summaries'
WEB = Path(__file__).resolve().parent / 'web'
TOPICS = {
    '1': ('models', 'Models & APIs'),
    '2': ('robotics', 'Vision & robotics'),
    '3': ('research', 'Research'),
    '4': ('safety', 'Safety & evaluation'),
    '5': ('infrastructure', 'Infrastructure'),
}


@dataclass(frozen=True)
class Story:
    title: str
    anchor: str
    topic: str
    label: str
    excerpt: str
    search: str
    source_ids: tuple[int, ...]
    event_date: str


@dataclass(frozen=True)
class Issue:
    key: str
    title: str
    date_range: str
    prepared: str
    body: str
    sources: tuple[dict, ...]
    stories: tuple[Story, ...]


def plain(text: str) -> str:
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'<[^>]*>', '', text)
    return ' '.join(re.sub(r'[*`#_]', '', text).split())


def load_issues(root: Path) -> list[Issue]:
    issues = []
    for path in sorted((root / 'summaries').glob('*.md'), reverse=True):
        text = path.read_text()
        metadata = json.loads((root / 'sources' / f'{path.stem}.json').read_text())
        sources = tuple(metadata['sources'])
        known = {int(source['id']) for source in sources}
        cited = {int(number) for number in re.findall(r'\[(\d+)\]', text)}
        if cited - known:
            raise ValueError(f'Unknown citation in {path.name}: {sorted(cited - known)}')
        body = text.split('## Sources', 1)[0]
        stories = []
        topic = None
        for block in re.split(r'(?m)(?=^## |^### )', body):
            section = re.match(r'## ([1-5])\. ', block)
            if block.startswith('## '):
                topic = TOPICS[section[1]] if section else None
            elif block.startswith('### ') and topic:
                title, content = block[4:].split('\n', 1)
                paragraphs = [p for p in content.strip().split('\n\n') if p.strip()]
                lead = re.sub(r'^\*\*(?:Date:|First arXiv submission:).*?\*\*\s*', '', paragraphs[0])
                excerpt = plain(lead)
                if len(excerpt) > 235:
                    excerpt = excerpt[:235].rsplit(' ', 1)[0] + '…'
                event = re.search(r'November (\d+)', paragraphs[0])
                stories.append(Story(title, slugify(title, '-'), *topic, excerpt,
                                     plain(content), tuple(sorted({int(n) for n in re.findall(r'\[(\d+)\]', content)})),
                                     f'NOV {event[1]}' if event else 'RESEARCH'))
        if len(stories) != metadata['development_count']:
            raise ValueError(f'Story count mismatch in {path.name}')
        start = date.fromisoformat(metadata['period_start'])
        end = date.fromisoformat(metadata['period_end'])
        date_range = f'{start:%B} {start.day}–{end.day}, {end.year}' if start.month == end.month else f'{start:%b} {start.day} – {end:%b} {end.day}, {end.year}'
        issues.append(Issue(path.stem, f'Deep Learning Weekly — {date_range}', date_range,
                            metadata['prepared'], body, sources, tuple(stories)))
    if not issues:
        raise ValueError('No weekly summaries found')
    return issues


def shell(title: str, body: str, prefix: str = '', active: str = '') -> str:
    def nav(label, href, key):
        current = ' aria-current="page"' if active == key else ''
        return f'<a href="{prefix}{href}"{current}>{label}</a>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="description" content="A source-linked weekly digest of deep-learning research, models, safety, and infrastructure. Curated, not exhaustive.">
<title>{escape(title)} · Deep Learning Summaries</title>
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/site.css"><script type="module" src="{prefix}assets/site.mjs"></script></head>
<body><a class="skip" href="#main">Skip to content</a><div class="site-wrap">
<header class="topbar"><a class="wordmark" href="{prefix}index.html" aria-label="Deep Learning Summaries home"><span class="brand-mark" aria-hidden="true">dl<span> /</span></span><span>DEEP LEARNING<br>SUMMARIES</span></a>
<nav aria-label="Main navigation">{nav('The feed', 'index.html', 'feed')}{nav('Archive', 'archive.html', 'archive')}{nav('About', 'about.html', 'about')}<a href="{REPO}">GitHub <span aria-hidden="true">↗</span></a></nav></header>
{body}
<footer class="site-footer"><span>Deep Learning Summaries<br><span class="muted">Signal, with the sources attached.</span></span><span>Curated, not exhaustive. No tracking.<br><a href="{prefix}about.html">Editorial policy</a> <span aria-hidden="true">·</span> <a href="{REPO}">View the source ↗</a></span></footer>
</div></body></html>'''


def feed(issue: Issue) -> str:
    href = f'issues/{issue.key}.html'
    rows = []
    for number, story in enumerate(issue.stories, 1):
        rows.append(f'''<article class="story" data-story data-topic="{story.topic}" data-search="{escape(story.title + ' ' + story.search, quote=True)}">
<div class="story-index">{number:02d}</div><div class="story-main"><div class="story-meta"><span class="topic-label">{escape(story.label)}</span><span>{story.event_date}</span></div>
<h3><a href="{href}#{story.anchor}">{escape(story.title)}<span class="story-arrow" aria-hidden="true">↗</span></a></h3><p>{escape(story.excerpt)}</p></div>
<a class="source-count" href="{href}#source-{story.source_ids[0]}">{len(story.source_ids)} source{'s' if len(story.source_ids) != 1 else ''} <span aria-hidden="true">↗</span></a></article>''')
    filters = '<button type="button" class="filter is-active" data-filter="all" aria-pressed="true">All topics</button>'
    filters += ''.join(f'<button type="button" class="filter" data-filter="{key}" aria-pressed="false">{label}</button>' for key, label in TOPICS.values())
    return shell('The feed', f'''<main id="main">
<section class="issue-intro"><div><p class="eyebrow"><span class="status-dot" aria-hidden="true"></span> THE WEEK IN DEEP LEARNING</p><h1>Less noise.<br><em>More understanding.</em></h1><p class="intro-copy">The models, papers, and systems worth a closer look.<br>What changed, why it matters, and where the evidence stops.</p></div>
<aside class="issue-stamp"><span class="eyebrow">LATEST EDITION</span><strong>{escape(issue.date_range)}</strong><p>{len(issue.stories)} developments <span aria-hidden="true">/</span> {len(issue.sources)} primary sources</p><a class="read-issue" href="{href}">Read the full issue <span aria-hidden="true">↗</span></a></aside></section>
<section class="feed-section" aria-labelledby="feed-heading"><div class="feed-heading"><h2 id="feed-heading">On the record<span class="accent">.</span></h2><div class="search-wrap" data-enhanced hidden><label class="sr-only" for="search">Search developments</label><span aria-hidden="true">⌕</span><input type="search" id="search" placeholder="Search this edition…" autocomplete="off"><kbd aria-hidden="true">/</kbd></div></div>
<div class="filter-bar" data-enhanced hidden role="group" aria-label="Filter by topic">{filters}</div>
<div class="feed-context"><span id="result-count" role="status" aria-live="polite">{len(issue.stories)} developments</span><span>{escape(issue.date_range.upper())}</span></div>
<div class="stories">{''.join(rows)}</div><div class="empty-state" id="empty-state" hidden><h3>No matches in this edition.</h3><p>Try another term or remove the topic filter.</p><button type="button" class="reset-button" id="reset-filters">Clear search & filters</button></div>
<noscript><p class="notice">All stories are shown. Search and topic filters require JavaScript.</p></noscript>
</section><section class="reading-note"><p class="eyebrow">A NOTE ON THE EVIDENCE</p><p>Announcements are not independent benchmarks. Every story links back to its sources, with the limitations kept in view.</p><a href="about.html">How this is put together ↗</a></section></main>''', active='feed')


def article(issue: Issue) -> str:
    body = re.sub(r'^# .*\n', '', issue.body, count=1)
    body = re.sub(r'\[(\d+)\]', lambda m: f'<a class="citation" href="#source-{m[1]}" aria-label="Source {m[1]}">[{m[1]}]</a>', body)
    md = markdown.Markdown(extensions=['extra', 'toc'])
    rendered = md.convert(body)
    toc = ''.join(f'<a href="#{escape(item["id"])}">{escape(re.sub(r"^\d+\. ", "", item["name"]))}</a>' for item in getattr(md, 'toc_tokens') if item['level'] == 2)
    sources = []
    for source in issue.sources:
        name = source.get('title') or urlsplit(source['url']).netloc + urlsplit(source['url']).path
        quotes = ''.join(f'<blockquote>{escape(q["text"])}</blockquote>' for q in source.get('quotes', []))
        sources.append(f'<li id="source-{source["id"]}"><div class="source-title"><span class="source-number">[{source["id"]}]</span><a href="{escape(source["url"], quote=True)}">{escape(name)} ↗</a></div><details><summary>Supporting excerpt</summary>{quotes}</details></li>')
    return shell(issue.date_range, f'''<main id="main"><div class="article-heading"><a class="back-link" href="../index.html">← Back to the feed</a><p class="eyebrow">THE WEEKLY EDITION</p><h1>{escape(issue.date_range)}</h1><p>{len(issue.stories)} developments. {len(issue.sources)} primary sources. The caveats stay in.</p></div><div class="article-layout"><aside class="article-toc"><nav aria-label="In this issue"><span class="eyebrow">IN THIS ISSUE</span>{toc}<a href="#sources">Sources & excerpts</a></nav></aside><article class="prose">{rendered}<h2 id="sources">Sources & excerpts</h2><p>Original sources, read during preparation. Expand an excerpt to see a short supporting passage; these are not substitutes for reading the full source.</p><ul class="sources-list">{''.join(sources)}</ul></article></div></main>''', prefix='../')


def build(root: Path, output: Path) -> None:
    issues = load_issues(root)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'assets').mkdir(exist_ok=True)
    (output / 'issues').mkdir(exist_ok=True)
    for file in WEB.iterdir():
        if file.is_file():
            shutil.copyfile(file, output / 'assets' / file.name)
    (output / '.nojekyll').write_text('')
    (output / 'index.html').write_text(feed(issues[0]))
    for issue in issues:
        (output / 'issues' / f'{issue.key}.html').write_text(article(issue))
    archive = ''.join(f'<a class="archive-row" href="issues/{issue.key}.html"><span>{escape(issue.date_range)}</span><span>{len(issue.stories)} developments / {len(issue.sources)} sources ↗</span></a>' for issue in issues)
    (output / 'archive.html').write_text(shell('Archive', f'<main id="main" class="simple-page"><p class="eyebrow">THE READING ROOM</p><h1>The archive<span class="accent">.</span></h1><p>Every edition, with its sources and limitations intact.</p><div class="archive-list">{archive}</div></main>', active='archive'))
    policy = markdown.markdown((root / 'EDITORIAL_POLICY.md').read_text(), extensions=['extra', 'toc'])
    (output / 'about.html').write_text(shell('Editorial policy', f'<main id="main" class="simple-page"><p class="eyebrow">HOW WE READ THE WEEK</p><article class="prose">{policy}</article></main>', active='about'))
    print(f'Built {len(issues)} issue(s), {len(issues[0].stories)} latest stories, {len(issues[0].sources)} sources → {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    build(args.root, args.output or args.root / 'docs')
