"""Protect content preservation, citation navigation and subpath delivery."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.urls = []
        self.stories = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if 'data-story' in attrs:
            self.stories += 1
        for attr in ('href', 'src'):
            if attr in attrs:
                self.urls.append(attrs[attr])


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='dl-site-')
        cls.output = Path(cls.temp.name).resolve()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def build(self, root=ROOT):
        builder = ROOT / 'build_site.py'
        self.assertTrue(builder.exists(), 'Site builder is not implemented')
        result = subprocess.run([sys.executable, str(builder), '--root', str(root), '--output', str(self.output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_feed_preserves_all_twenty_two_developments(self):
        self.build()
        page = (self.output / 'index.html').read_text()
        self.assertEqual(Links(page).stories, 22)
        self.assertIn('Claude Fable', page)
        self.assertIn('Unbundling Multimodal Vision Encoding', page)

    def test_full_article_preserves_thirty_one_citation_targets(self):
        self.build()
        page = (self.output / 'issues/2026-11-09_to_2026-11-15.html').read_text()
        ids = Links(page).ids
        self.assertEqual(len([i for i in ids if re.fullmatch('source-[0-9]+', i)]), 31)
        self.assertIn('not preserved frontier-model quality', re.sub('<[^>]+>', '', page))
        self.assertIn('https://arxiv.org/html/2611.13378v1', page)

    def test_all_internal_links_and_fragments_resolve(self):
        self.build()
        pages = {p: Links(p.read_text()) for p in self.output.rglob('*.html')}
        for path, parsed in pages.items():
            for url in parsed.urls:
                parsed_url = urlsplit(url)
                if parsed_url.scheme or parsed_url.netloc:
                    continue
                self.assertFalse(parsed_url.path.startswith('/'), (path, url))
                target = (path.parent / unquote(parsed_url.path)).resolve() if parsed_url.path else path
                if target.is_dir():
                    target /= 'index.html'
                self.assertTrue(target.exists(), (path, url))
                if parsed_url.fragment:
                    self.assertIn(unquote(parsed_url.fragment), pages[target].ids, (path, url))

    def test_reading_does_not_require_javascript(self):
        self.build()
        home = (self.output / 'index.html').read_text()
        self.assertIn('SinkState', home)
        self.assertIn('issues/2026-11-09_to_2026-11-15.html#', home)
        article = (self.output / 'issues/2026-11-09_to_2026-11-15.html').read_text()
        self.assertIn('hardware', article.lower())
        self.assertIn('not an exhaustive', article)

    def test_unknown_source_is_rejected(self):
        self.assertTrue((ROOT / 'build_site.py').exists(), 'Site builder is not implemented')
        with tempfile.TemporaryDirectory(prefix='dl-bad-source-') as directory:
            root = Path(directory)
            for folder in ('sources', 'summaries'):
                (root / folder).mkdir()
                for original in (ROOT / folder).glob('*'):
                    (root / folder / original.name).write_bytes(original.read_bytes())
            (root / 'EDITORIAL_POLICY.md').write_bytes((ROOT / 'EDITORIAL_POLICY.md').read_bytes())
            source = next((root / 'summaries').glob('*.md'))
            source.write_text(source.read_text().replace('[19]', '[999]'))
            result = subprocess.run([sys.executable, str(ROOT / 'build_site.py'), '--root', str(root), '--output', str(self.output / 'bad')], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Unknown citation', result.stderr)


if __name__ == '__main__':
    unittest.main()
