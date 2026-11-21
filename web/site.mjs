export function matchesStory(text, query, topic, selectedTopic) {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return (selectedTopic === 'all' || topic === selectedTopic)
    && words.every(word => text.toLocaleLowerCase().includes(word));
}

if (typeof document !== 'undefined') {
  const search = document.querySelector('#search');
  if (search) {
    const stories = [...document.querySelectorAll('[data-story]')];
    const filters = [...document.querySelectorAll('[data-filter]')];
    const count = document.querySelector('#result-count');
    const empty = document.querySelector('#empty-state');
    let selected = 'all';
    const update = () => {
      let visible = 0;
      for (const story of stories) {
        story.hidden = !matchesStory(story.dataset.search, search.value, story.dataset.topic, selected);
        if (!story.hidden) visible += 1;
      }
      count.textContent = `${visible} of ${stories.length} development${stories.length === 1 ? '' : 's'}`;
      empty.hidden = visible !== 0;
      for (const button of filters) {
        const active = button.dataset.filter === selected;
        button.setAttribute('aria-pressed', String(active));
        button.classList.toggle('is-active', active);
      }
    };
    const reset = () => {
      search.value = '';
      selected = 'all';
      update();
      search.focus();
    };
    search.addEventListener('input', update);
    search.addEventListener('keydown', event => {
      if (event.key === 'Escape') reset();
    });
    for (const button of filters) {
      button.addEventListener('click', () => {
        selected = button.dataset.filter;
        update();
      });
    }
    document.querySelector('#reset-filters').addEventListener('click', reset);
    document.addEventListener('keydown', event => {
      if (event.key === '/' && !event.ctrlKey && !event.metaKey
          && !event.altKey && !event.target.closest('input, textarea, [contenteditable]')) {
        event.preventDefault();
        search.focus();
      }
    });
    document.querySelectorAll('[data-enhanced]').forEach(element => { element.hidden = false; });
    update();
  }
}
