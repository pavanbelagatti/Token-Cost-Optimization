# ContextCost Lab — structured context vs raw data

A runnable, **synthetic** incident investigation benchmark comparing three strategies: raw source files, local structured filtering, and a Port.io software catalog. It measures **actual OpenAI API token usage**, not estimated token counts. The experiment is designed to test a hypothesis, not guarantee savings.

## Prerequisites
- Python 3.10+ (3.12 recommended)
- OpenAI API key and billing enabled
- Optional: Port organization with API client credentials and permission to manage a demo blueprint and entities

## 1. Install (macOS / VS Code terminal)
```bash
unzip contextcost-lab.zip
cd contextcost-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```
Edit `.env` and add your `OPENAI_API_KEY`. Do not commit `.env`.

## 2. Run without Port first
```bash
pytest -q
streamlit run app.py
```
Choose **Raw** and **Local structured**, then press **Run comparison**. OpenAI calls incur real usage charges.

## 3. Connect Port (optional)
Create a Port API client with appropriate permissions. Put `PORT_CLIENT_ID` and `PORT_CLIENT_SECRET` in `.env`.
```bash
python seed_port.py
streamlit run app.py
```
Enable **Port structured**. The seed creates/upserts the `contextcost_service` blueprint and 12 fictional entities. It does **not** touch your existing service blueprints. Check API permissions before seeding. The demo models dependencies as a string-array property rather than native Port relations to keep setup beginner-friendly; a production version should use relations and narrower server-side queries.

## 4. Repeatable experiment
```bash
python benchmark.py --repeat 2
python benchmark.py --repeat 2 --port
```
Results are written as JSON and CSV under `results/`. For price comparison set `INPUT_PRICE_PER_M` and `OUTPUT_PRICE_PER_M` in `.env` using **your model's current pricing**. Blank means cost is shown as unknown rather than guessed.

## What is fair, and what isn't?
- Same model, system prompt, question, temperature, and underlying seeded facts.
- **Raw** intentionally includes noisy irrelevant services/logs; **Local structured** and **Port** filter down to the queried service and its direct dependencies. This tests *retrieval/selection*, not a magical Port token compression feature.
- Port and local modes deliberately use the same JSON serialization and selection logic; their input token counts should be similar if the catalog is synced. Port's value is the operational context source, not the byte count of its API.
- Incident/log evidence is read locally in all modes because the Port catalog is not a log store. In production, source it from your observability system.
- Port mode currently downloads the catalog then filters in Python. For a large organization, replace it with a Port server-side entity search and field selection to reduce retrieval time and payload size.
- The heuristic coverage checks are *not* a reliable semantic accuracy metric. Manually inspect answers and add expert-labeled expected facts before making public accuracy claims.
- Input token counts include prompt + context. Output tokens and cost are also recorded. Model latency is recorded; retrieval/Port API latency is **not** included in the current timing, so don't claim end-to-end latency improvements.
- This prototype does not account for prompt caching, catalog synchronization, Port subscription, infrastructure costs, or setup labor.

## Project files
- `data/services.json`, `data/logs.json`, `data/incident.md` — synthetic organization
- `context.py` — three context strategies
- `port_client.py`, `seed_port.py` — Port adapter and seed
- `engine.py` — OpenAI call and usage collection
- `app.py` — Streamlit comparison UI
- `benchmark.py` — repeatable experiment with CSV/JSON export
- `tests/` — baseline unit tests

## Safety
The data is fictional. Use a sandbox Port organization if possible. Do not upload sensitive production logs or secrets to an LLM without your organization's approval.
