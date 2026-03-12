# ТЗ: RugSignal

## 1. Описание проекта

`RugSignal` — web-сервис для проверки `token`, `wallet` и `project` в сети `Solana` с выдачей `risk score`, explainable risk factors и итогового статуса риска.

Основная задача MVP:

- дать пользователю быстрый способ проверить объект перед действием;
- показать не только итоговый verdict, но и причины;
- поддержать будущую ручную модерацию и review queue.

## 2. Стек

### Frontend

- `React`
- `TypeScript`
- `Tailwind CSS`
- `Next.js`

### Backend

- `Python`
- `FastAPI`

### Solana / analysis layer

- `Rust`
- Solana RPC / adapters

## 3. Цели MVP

- проверка `SPL token`;
- проверка `wallet address`;
- проверка `project`;
- расчет `risk score` от `0` до `100`;
- статусы: `low`, `medium`, `high`, `critical`;
- explainable factors;
- история проверок;
- watchlist;
- admin review queue;
- публичное API для frontend.

## 4. Сущности

### Token

Проверка должна учитывать:

- mint authority;
- freeze authority;
- liquidity;
- holder concentration;
- age;
- metadata consistency.

### Wallet

Проверка должна учитывать:

- links to flagged addresses;
- launch-dump behavior;
- transaction patterns;
- deployer history.

### Project

Проверка должна учитывать:

- token signals;
- domain age;
- social presence;
- trust signals;
- moderation labels.

## 5. Risk scoring

Система должна:

- считать `risk score 0..100`;
- выдавать `status`;
- хранить `rule hits`;
- показывать `confidence`;
- поддерживать ручные override labels в будущем.

### Диапазоны

- `0-24` → `low`
- `25-49` → `medium`
- `50-74` → `high`
- `75-100` → `critical`

## 6. Основные экраны

### Public / landing

- hero;
- universal search input;
- coverage blocks;
- workflow;
- sample report;
- trust section.

### Dashboard

- universal check;
- recent checks;
- watchlist preview;
- navigation to reports.

### Result Page

- score;
- status;
- confidence;
- top findings;
- metrics;
- timeline;
- refresh state.

### History

- recent checks list;
- status overview;
- access to report pages.

### Watchlist

- watched entities;
- score delta;
- review state changes.

### Admin Queue

- moderation queue;
- severity;
- score;
- owner;
- update time.

## 7. Backend API MVP

### Implemented now

- `GET /health`
- `GET /api/v1/overview`
- `GET /api/v1/checks`
- `GET /api/v1/checks/{check_id}`
- `GET /api/v1/watchlist`
- `GET /api/v1/admin/review-queue`
- `POST /api/v1/check/token`

### Planned next

- `POST /api/v1/check/wallet`
- `POST /api/v1/check/project`
- `POST /api/v1/recheck/{entityType}/{entityId}`
- `POST /api/v1/admin/labels`
- `GET /api/v1/rules`

## 8. Архитектурные требования

### Frontend

- SSR/route-based app on Next.js;
- reusable typed API layer;
- pages separated by product scenario;
- support for future filters, actions and auth.

### Backend

- FastAPI as public/internal API;
- typed response models;
- modular extension for real Solana analyzers;
- CORS for frontend integration.

### Solana layer

- separate Rust module/service;
- fetch onchain signals from Solana RPC;
- prepare normalized analysis signals for API.

## 9. Нефункциональные требования

- быстрый первичный ответ;
- explainability обязательна;
- UI должен показывать freshness состояния;
- API versioning через `/api/v1`;
- кодовая база должна быть разделена по фронту и бэку.

## 10. Текущее состояние реализации

Сейчас в проекте уже есть:

- frontend на `Next.js + React + TypeScript + Tailwind`;
- backend на `FastAPI`;
- dashboard;
- result page;
- history;
- watchlist;
- admin queue;
- mock API contracts для дальнейшего перехода к реальным данным.

## 11. Следующие этапы

1. Реализовать реальные submit flows из frontend в backend.
2. Добавить формы и фильтры для admin queue.
3. Подключить реальные Solana RPC adapters.
4. Поднять Rust analysis layer.
5. Добавить БД и хранение истории.
6. Реализовать rule engine и moderation labels.
