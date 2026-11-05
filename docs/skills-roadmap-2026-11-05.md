# Навыки с рынка: что добавить (2026-11-05)

Источник: `~/dev/jobs/data/corpus_roadmap.md` (11.5k вакансий, 2026-11-05) против [system-design](system-design.md) и [logic-map](logic-map.md). Берём только то, что нужно самому проекту; чего проект не требует — в «Отвергнуто». Сводка по всем репо: `~/dev/docs/skills-roadmap-report-2026-11-05.md`.

## Предложения

- [ ] **[github actions, pytest]** CI ruff + pytest (взять `.github/workflows/ci.yml` из RepoHarvester); тесты есть, CI нет. Усилие S.
- [ ] **[playwright, pytest]** Тесты селекторов и регекса цены на сохранённых HTML выдачи eBay (офлайн) — system-design Risks: хрупкие селекторы, опечатка `.s-item__selller`. Усилие M.

## Порядок

Тесты селекторов — после HIGH (запрос не вводится, `apply_filter` без await, регекс цены), иначе зафиксируем сломанную логику.

## Отвергнуто

- Docker/headless на OCI: §8 ставит условия (exit code, retries, dedup), плюс антибот eBay на датацентровом IP.
- PostgreSQL: ~1000 строк в день; SQLite уже в «Идеях».
