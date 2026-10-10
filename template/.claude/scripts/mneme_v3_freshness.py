"""Open-loop notice for the opening context: what has gone quiet. Read-only, no model.

A vault fills with tasks nobody touches and data that stops being refreshed while the
agent keeps working on something else. Nothing says so until the user notices weeks later.
This module names it in one bounded line at session start:

- open tasks (`tasks/*.md`, status inbox/active/waiting/blocked) whose file has not changed
  for `task_days` days;
- user-chosen files that should stay fresh (`watch`), e.g. a data export a script refreshes.

Settings live in the vault (`.mneme-freshness.json`), so they travel with the notes:
    {"task_days": 3, "watch": [{"path": "data/last_sync.json", "max_days": 3, "label": "Hevy"}]}
A missing or invalid file means defaults; a check never costs the session its context.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import time

CONFIG_NAME = '.mneme-freshness.json'
TASK_DAYS = 3
OPEN = ('inbox', 'active', 'waiting', 'blocked')
MAX_WATCH = 32
MAX_NAMES = 3
DAY = 86400


def settings(vault):
    result = {'task_days': TASK_DAYS, 'watch': []}
    path = Path(vault) / CONFIG_NAME
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
            return result
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return result
    if not isinstance(value, dict):
        return result
    days = value.get('task_days')
    if type(days) is int and 0 <= days <= 365:
        result['task_days'] = days
    watch = value.get('watch')
    if isinstance(watch, list):
        for item in watch[:MAX_WATCH]:
            if (isinstance(item, dict) and isinstance(item.get('path'), str) and item['path'].strip()
                    and type(item.get('max_days')) in (int, float) and 0 < item['max_days'] <= 365):
                label = item.get('label')
                result['watch'].append({'path': item['path'].replace('\\', '/'), 'max_days': item['max_days'],
                                        'label': label[:60] if isinstance(label, str) and label.strip() else item['path']})
    return result


def _inside(vault, relative):
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        return None
    target = (vault / relative)
    try:
        resolved = target.resolve()
    except OSError:
        return None
    return target if resolved.is_relative_to(vault) else None


STATUS = re.compile(r'"status"\s*:\s*"([a-z]+)"|^status:\s*"?([a-z]+)"?\s*$', re.M)


def stale_tasks(vault, days, now):
    folder = vault / 'tasks'
    if days == 0 or not folder.is_dir():
        return []
    found = []
    for path in sorted(folder.glob('*.md')):
        try:
            if path.is_symlink():
                continue
            age = (now - path.stat().st_mtime) / DAY
            if age < days:
                continue
            head = path.read_text(encoding='utf-8', errors='replace')[:4000]
        except OSError:
            continue
        match = STATUS.search(head)
        status = match and (match[1] or match[2])
        if status in OPEN:
            found.append((int(age), path.stem))
    found.sort(key=lambda item: (-item[0], item[1]))
    return found


def stale_watches(vault, watch, now):
    found = []
    for item in watch:
        target = _inside(vault, item['path'])
        if target is None:
            continue
        try:
            age = (now - target.stat().st_mtime) / DAY
        except OSError:
            found.append((None, item['label']))  # a watched file that is gone is the stalest of all
            continue
        if age >= item['max_days']:
            found.append((int(age), item['label']))
    return found


def notice(vault, now=None):
    """One line, or '' when nothing has gone quiet."""
    vault = Path(vault).resolve()
    now = time.time() if now is None else now
    config = settings(vault)
    parts = []
    tasks = stale_tasks(vault, config['task_days'], now)
    if tasks:
        names = ', '.join(name for _, name in tasks[:MAX_NAMES]) + (', …' if len(tasks) > MAX_NAMES else '')
        parts.append(f'{len(tasks)} open task(s) untouched for {config["task_days"]}+ days ({names})')
    for age, label in stale_watches(vault, config['watch'], now):
        parts.append(f'{label} missing' if age is None else f'{label} {age} days old')
    if not parts:
        return ''
    return 'Open loops: ' + '; '.join(parts) + '. Mention briefly to the user; close, update or drop them.\n'
