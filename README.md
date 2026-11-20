# AI Context Efficiency Lab

### Reducing AI Agent Token Costs with Better Engineering Context — Powered by Port.io + OpenAI

AI agents need organizational context to investigate production incidents: service ownership, dependencies, deployments, runbooks, logs, and incident history. Sending *all* that information to an LLM can waste input tokens on irrelevant records.

**AI Context Efficiency Lab** is a hands-on Python and Streamlit project that compares different ways of selecting engineering context for the **same OpenAI model**. It uses a fictional e-commerce organization and measures real OpenAI token usage, model cost (when pricing is configured), and execution time.

The central question is:

> **Why is checkout failing in production? Who owns it, what does it depend on, and what changed?**

The experiment explores whether better context selection can reduce token usage while preserving useful answers. **Port is a structured source of organizational context, not a token-compression algorithm.**

## What you'll build

A Streamlit dashboard that:

- Compares **Raw Context**, **Port Structured**, **Smart Retrieval**, and **Local Structured**.
- Calls OpenAI with the same question and model across strategies.
- Displays actual input/output token counts, estimated model costs, answers, and timing.
- Lets you inspect fictional service inventory, dependencies, logs, and incident evidence.
- Demonstrates **Context Freshness** by updating a demo service owner in Port and comparing it with a static local snapshot.
- Supports repeatable CLI benchmarks with CSV and JSON results.

## How the four strategies work

| Strategy | Where the context comes from | How it is selected |
| --- | --- | --- |
| **Raw Context** | Local synthetic service records, logs, and incident document | Sends the entire available dataset without relevance filtering |
| **Port Structured** | Live Port catalog entities plus local synthetic incident/log evidence | Retrieves catalog service records and selects relevant services and dependencies in Python |
| **Smart Retrieval** | Original local synthetic records | Uses a lightweight lexical relevance search to rank records and return top matches |
| **Local Structured** | Local synthetic service records, logs, and incident document | Uses explicit service-name/dependency filtering as a technical control |

**Important:** Smart Retrieval is a simple keyword-based search baseline, **not** embedding-based vector RAG. The Port strategy currently fetches catalog entities and filters them in Python; it does not yet perform targeted server-side Port search. Incident and log evidence in Port mode still comes from local demo files.

### High-level architecture

```text
                    Investigation question
                             |
              +--------------+---------------+
              |              |               |
        Raw Context    Smart Retrieval   Port Structured
              |              |               |
        All local       Ranked local      Port catalog
        demo data       source records    service entities
              |              |               |
              |              |          + local incident
              |              |            and log evidence
              +--------------+---------------+
                             |
                     OpenAI GPT model
                             |
                Answer + token usage + timing
                             |
                    Streamlit dashboard
```

The **Local Structured** mode is also available as an additional control.

## Demo data

This project contains a **fictional** e-commerce engineering organization with **12 microservices**, including checkout, payments, inventory, orders, authentication, and others.

- `data/services.json` — synthetic service metadata, owners, dependencies, deployments, and runbooks.
- `data/logs.json` — synthetic application logs.
- `data/incident.md` — fictional checkout incident narrative.

The OpenAI calls and Port API requests are real; the services, incidents, and logs are demo fixtures, **not production telemetry**.

## Prerequisites

- Python **3.10+** (Python 3.12 recommended).
- An OpenAI API key with billing enabled.
- A Port organization and API client credentials to use the **Port Structured** and **Context Freshness** features.
- Git and a terminal (examples below use macOS/Linux).

## 1. Clone and install

```bash
git clone https://github.com/pavanbelagatti/Token-Cost-Optimization.git
cd Token-Cost-Optimization

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

cp .env.example .env
```

On Windows, activate the virtual environment using `.venv\Scripts\activate` in Command Prompt or `.venv\Scripts\Activate.ps1` in PowerShell.

## 2. Configure environment variables

Edit `.env` locally:

```dotenv
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

PORT_CLIENT_ID=your_port_client_id
PORT_CLIENT_SECRET=your_port_client_secret
PORT_API_BASE=https://api.port.io/v1

# Optional: USD per million tokens for your chosen model
INPUT_PRICE_PER_M=
OUTPUT_PRICE_PER_M=
```

Use the API base URL appropriate for your Port environment. The values above are placeholders: **never commit real keys or secrets**. If pricing is left blank, the model-cost field is unavailable; token counts are still measured. For monetary estimates, enter the current pricing for the exact model you use.

The project `.gitignore` should exclude `.env`, `.venv/`, Python caches, and generated benchmark results.

## 3. Seed the Port catalog (for Port experiments)

Create a Port API client with permissions to create/update the demo Blueprint and entities, then configure its credentials in `.env`.

```bash
python seed_port.py
```

This creates or updates the **`contextcost_service`** Blueprint and uploads 12 fictional service entities to your Port organization.

In the Port UI, find the **ContextCost Demo Service** data model under **Builder → Data model**. You can inspect the corresponding entities in the catalog/entity view for that Blueprint. A separate Software Catalog page may need to be configured to display them.

The demo stores dependencies as a **string-array property**, not native Port entity relations. Use a test/sandbox Port organization if possible. If you've already seeded the same demo entities, you generally do not need to seed them again to run the benchmark.

## 4. Start the dashboard

```bash
streamlit run app.py
```

Open the local URL displayed by Streamlit (typically `http://localhost:8501`).

In the sidebar:

1. Choose the investigation question, or enter your own.
2. The main comparison defaults to **Raw** and **Port Structured**.
3. Enable **Show advanced retrieval baselines** to add **Smart Retrieval** and/or **Local Structured**.
4. Click **Run selected comparison**.
5. Review the results and the context sources used.

**Without Port credentials:** run the **Raw** and **Smart Retrieval** modes (or Local Structured). Deselect Port Structured before running.

OpenAI requests incur real API charges.

## Dashboard tabs

| Tab | What it shows |
| --- | --- |
| **Executive overview** | Service statistics, token consumption, and illustrative cost scenarios |
| **Benchmark & answers** | Token counts, estimated model cost, timing, answers, and basic factual checks |
| **Service catalog** | Local synthetic service inventory, owners, dependencies, and deployment details |
| **Incident evidence** | Fictional incident narrative, logs, and context payload inspection |
| **Context freshness** | Live Port owner versus local snapshot, with controlled update and restore actions |

**Note:** The Service Catalog tab in Streamlit displays local fixture data. Port Structured independently reads the Port API when you run that strategy.

## 5. Run repeatable benchmarks from the terminal

Without Port:

```bash
python benchmark.py --repeat 2
```

Including Port:

```bash
python benchmark.py --repeat 2 --port
```

The CLI runs the built-in investigation questions across the available strategies. Results are saved under `results/` as **JSON** and **CSV**.

Recorded fields include:

- `input_tokens`, `output_tokens`, and `total_tokens` — usage returned by OpenAI.
- `model_cost_usd` — calculated using your configured model token prices, if provided.
- `retrieval_seconds` — time spent preparing/retrieving context.
- `latency_seconds` — model API call time.
- `end_to_end_seconds` — context preparation/retrieval plus model API time.
- `context_characters` — size of the context payload.

Timing reflects this application's measured operations; it is **not** a full production-system latency benchmark.

## 6. Experiment: Context Freshness

This experiment demonstrates why a live organizational catalog can be useful when local snapshots become stale.

1. Open the **Context freshness** tab.
2. Select `checkout` and click **Read live owner from Port**.
3. Compare the live Port owner with the owner in local `data/services.json`.
4. Enter a different **demo owner**, confirm the change, and click **Update owner in Port**.
5. Click **Read live owner from Port** again to verify the updated value.
6. Click **Restore Port owner from local snapshot** when finished, and read the live value once more to confirm restoration.

**Caution:** This action **writes to your real Port organization**, specifically to the demo entity. Use only test entities. The local JSON remains unchanged. This is a manual update and fresh API read, **not automatic synchronization** from external engineering tools, and it does not automatically rerun previous model answers.

## Project structure

```text
Token-Cost-Optimization/
├── app.py                 # Streamlit dashboard
├── engine.py              # OpenAI calls, token usage, costs, timing
├── context.py             # Raw, local structured, Port context selection
├── smart_retrieval.py     # Lightweight lexical search baseline
├── port_client.py         # Port API authentication and entity operations
├── seed_port.py           # Populate the demo Blueprint and services
├── benchmark.py           # Repeatable CLI benchmark and exports
├── data/
│   ├── services.json      # Fictional service inventory
│   ├── logs.json          # Synthetic logs
│   └── incident.md        # Fictional incident
├── tests/                 # Automated tests
├── requirements.txt
├── .env.example           # Safe environment variable template
├── .gitignore
└── README.md
```

## Methodology and limitations

This project is an **educational comparison**, not proof of a guaranteed percentage of savings in production.

- The same model and question are used across strategies, but the context payloads differ.
- Raw Context is intentionally inefficient; it is a useful baseline, **not** a strong production retrieval architecture.
- Smart Retrieval is a more meaningful non-Port competitor, but its lexical ranking may omit important evidence.
- Port Structured demonstrates a live, reusable service catalog. **Token reductions come from selecting smaller relevant context**, not from Port inherently compressing tokens.
- Local Structured and Port Structured may produce nearly identical token counts when their selected context is the same.
- Port catalog metadata is live; incident descriptions and logs in this demo are local synthetic fixtures.
- The built-in factual coverage checks are keyword heuristics, **not an independent accuracy evaluation**. Inspect answers manually before making quality claims.
- Model cost estimates depend on user-provided pricing and do not include Port licensing, ingestion, infrastructure, operational labor, or all caching effects.
- For production use, consider server-side Port entity search, native entity relations, authorization controls, source synchronization, observability integrations, and a stronger retrieval/evaluation pipeline.

## Security

- Never commit `.env`, real API keys, access tokens, or private service credentials.
- Use a sandbox Port organization when seeding or modifying entities.
- Do not replace the synthetic fixtures with confidential production data without appropriate authorization and privacy review.
- Review files and Git history for secrets before publishing.

## Why this matters

The goal is not just to make an AI agent cheaper. It is to understand how **better context engineering** helps agents receive the right organizational information without overwhelming the model with unrelated data.

**Better context selection → less unnecessary context → more efficient AI-assisted incident investigation.**
