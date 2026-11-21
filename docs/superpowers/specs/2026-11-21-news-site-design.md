# Deep Learning Summaries website

Approved in chat: dark news feed with compact headlines, topic filters and search; full weekly articles with clickable citations. User directed: build and publish now.

## Intent and scope
Turn the existing public content repository into a reading site without changing its research claims. Keep Markdown and source JSON canonical. Include all 22 current developments and all 31 cited sources. No tracking, backend, account system, or automated news generation.

## Approaches
Considered a minimal documentation archive and a light editorial reader. User selected a dark compact feed because it supports scanning the week's stories. Builder selects static HTML on GitHub Pages to avoid hosting costs and runtime dependencies.

## Site
Homepage: restrained dark charcoal, warm white type, lime accent, editorial serif masthead, sans-serif reading text, issue date, searchable/filterable story rows, archive link. Each row links to its section in the full issue. Article: readable measure, section navigation, anchored citations and source list. Policy page preserves editorial caveats. Mobile stacks navigation and wraps long source URLs; content remains readable without JavaScript. No external fonts or CDN scripts.

## Implementation and acceptance
Python builds static HTML from the original Markdown and sanitized source JSON; CSS and a small JavaScript module provide presentation/filtering. Commit generated docs/ output and enable GitHub Pages from main:/docs. Relative links must work under /deep-learning-summaries/. Validate source-ID integrity, story totals, links and fragments, filtering, narrow/enlarged text layouts, and live HTTP delivery. No automatic content updates; rebuild only when publishing changed content.
