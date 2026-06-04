# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

This repository is a Day 05 / Day 06 AI Product lab workspace for the Yumi food-ordering concept. The repo is mostly planning/spec material, but it also contains a small FastAPI backend prototype under `Backend/`.

The core flow is:
- Day 05: find a real problem, collect evidence, narrow scope, and write a thin spec
- Day 06: build a small prototype from that spec

Yumi is the main product theme: a conversational ordering assistant for food delivery.

## High-level structure

- `README.md` — explains the lab flow and the Day 06 submission layout.
- `Spec.md` — product spec for Yumi: problem statement, solution, AI architecture, roadmap, and metrics.
- `Core.md` — deeper technical design for the AI layer: system prompt, intent classification, tool calling, recommendation, memory, and conversation flow.
- `Plan.md` — condensed lab plan with the intended MVP scope, team split, API contract, and timeline.
- `Idea.md` — higher-level product framing and rationale for Yumi.
- `01-invidual-workshop/` — individual teardown/reflection artifact.
- `02-group-spec/` — templates for the evidence pack, synthesis, and thin spec.
- `Ca-nhan/` — personal writeups in Vietnamese.
- `Backend/` — FastAPI prototype for menu, cart, and chat flows.

## Backend architecture

The backend is a small in-memory FastAPI app:
- `Backend/main.py` wires the app, CORS, and routers.
- `Backend/api/` contains the HTTP layer for `/menu`, `/cart`, and `/chat`.
- `Backend/services/` holds the stateful business logic:
  - `menu_service.py` loads and filters menu data from `Backend/data/menu.json`
  - `cart_service.py` keeps carts in memory per `session_id`
  - `intent_service.py` does keyword-based intent detection
  - `recommender.py` filters and ranks menu items for suggestions
  - `state.py` creates single shared service instances used by the routers
- `Backend/models/schemas.py` defines the Pydantic request/response models shared across the API.

Important behavior:
- The chat endpoint depends on a required `session_id` and returns either cart state, add-to-cart behavior, or recommendations.
- There is no database; cart state lives only for the current process.
- The backend expects menu data to stay in sync with the schema in `models/schemas.py`.

## Common commands

Run these from `Backend/` unless noted otherwise.

- Install backend deps
  - `python -m pip install -r requirements.txt`
- Start the API locally
  - `uvicorn main:app --reload`
- Health check
  - `curl http://127.0.0.1:8000/health`
- Inspect menu
  - `curl http://127.0.0.1:8000/menu`
- Search menu
  - `curl 'http://127.0.0.1:8000/menu/search?q=pho'`
- Chat endpoint
  - `curl -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' -d '{"message":"cho mình món healthy","session_id":"demo"}'`
- Cart endpoint
  - `curl http://127.0.0.1:8000/cart/demo`

There is no dedicated automated test suite in the repo yet. If tests are added later, prefer running the narrowest test file or `pytest -k <name>` for a single test case.

## Editing guidance

- Keep `Spec.md`, `Core.md`, and `Plan.md` aligned when changing product scope or AI behavior.
- Preserve the Day 05 / Day 06 structure described in `README.md`.
- Keep backend changes minimal and consistent with the current in-memory prototype unless the task explicitly expands the architecture.
