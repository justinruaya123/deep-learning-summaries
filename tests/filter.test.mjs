import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
const path = new URL('../web/site.mjs', import.meta.url);

async function matcher() {
  assert.ok(existsSync(path), 'Feed filtering is not implemented');
  return (await import(path)).matchesStory;
}

test('search matches all query words without case sensitivity', async () => {
  const match = await matcher();
  assert.equal(match('SinkState Hybrid LLM Serving', 'hybrid SINK', 'research', 'all'), true);
  assert.equal(match('SinkState Hybrid LLM Serving', 'hybrid vision', 'research', 'all'), false);
});

test('topic and query intersect rather than overwrite each other', async () => {
  const match = await matcher();
  assert.equal(match('Gemini Robotics vision action', 'gemini', 'robotics', 'robotics'), true);
  assert.equal(match('Gemini Robotics vision action', 'gemini', 'robotics', 'models'), false);
  assert.equal(match('Gemini Robotics vision action', 'unknown', 'robotics', 'robotics'), false);
});

test('clearing inputs restores all stories', async () => {
  const match = await matcher();
  assert.equal(match('Claude Fable', '  ', 'models', 'all'), true);
  assert.equal(match('SinkState', '', 'research', 'all'), true);
});
