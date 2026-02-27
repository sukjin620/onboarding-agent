# DayOne AI - Onboarding Automation Agent

> **Elastic Agent Builder Hackathon 2026**

[![DevPost](https://img.shields.io/badge/DevPost-Submission-003E54?logo=devpost)](https://devpost.com/software/dayone-ai-onboarding-automation-agent)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-Serverless-005571?logo=elasticsearch)](https://my-elasticsearch-project-d0a46c.es.us-central1.gcp.elastic.cloud)
[![Docs](https://img.shields.io/badge/Tool%20Documentation-Google%20Docs-4285F4?logo=googledocs)](https://docs.google.com/document/d/1y5ryspHc8cIrScCJiDs7jIfpVW6CyCwrMDtu09j2fRs/edit?tab=t.0)

Automate messy internal HR onboarding work with a multi-step AI agent backed by Elasticsearch. The agent monitors checklist completion, surfaces knowledge-base guides, auto-creates Jira tickets for blockers, and logs every decision with a plain-English explanation — giving HR teams full auditability with a confidence score on every output.

---

## Links

| Resource | URL |
|---|---|
| DevPost submission | https://devpost.com/software/dayone-ai-onboarding-automation-agent |
| Elasticsearch endpoint | https://my-elasticsearch-project-d0a46c.es.us-central1.gcp.elastic.cloud |
| Tool documentation | https://docs.google.com/document/d/1y5ryspHc8cIrScCJiDs7jIfpVW6CyCwrMDtu09j2fRs/edit?tab=t.0 |

---

## How the Agent Works

DayOne is built entirely inside Elastic's Agent Builder. When an HR manager types a question, the agent follows a fixed reasoning workflow — it never guesses, only reports what its tools return, and attaches a confidence score (0–100) to every recommendation so HR knows exactly how much to trust each action.

### Decision workflow (every request, in order)

**1 — UNDERSTAND** The agent classifies the request as one of three scopes:
- *Single employee* — a specific EMP-XXXX is mentioned or implied
- *Department / team view* — a group is the subject
- *Org-wide analytics* — a report, dashboard, or summary is requested

**2 — RETRIEVE** Based on scope, the agent selects and calls the minimum set of tools needed.

**3 — CROSS-REFERENCE** If any blocked tasks are found the agent always calls `hr_search_guides` with keywords extracted from the blocked task's name and reason. This surfaces the most relevant knowledge-base article for the employee without requiring HR to search manually.

**4 — SCORE CONFIDENCE** After every tool call the agent scores the result on a 0–100 rubric.

Scores are calculated from factors like: whether all expected fields are populated (+30), whether completion percentages are arithmetically consistent (+30), whether blocked tasks have a populated `blocked_reason` (+30), and cross-reference bonuses (+10) when two separate tool results confirm the same count. Empty results, null reasons, and contradictory data all reduce the score with specific penalties.

**5 — RECOMMEND** For every blocked task the agent outputs a structured `ACTION REQUIRED` block.

**6 — SUMMARISE** Every response ends with a `RETRIEVAL CONFIDENCE REPORT` — a table of every tool called, its score, tier, and key factor, plus an overall weighted confidence and a plain-English trust guidance line.

---

## Tools

### ES|QL Tools — pre-defined parameterized queries

| Tool | Purpose | Scope |
|---|---|---|
| `hr_onboarding_status` | Completion stats: total, completed, blocked, overdue, pct | One employee |
| `hr_blocked_tasks` | List Blocked/overdue tasks, optional dept filter | Org or dept |
| `hr_task_detail` | Full task breakdown by phase and status | One employee |
| `hr_onboarding_analytics` | Completion rates aggregated by department | Org-wide |
| `hr_blocked_by_team` | Count blocked tasks grouped by owner team | Org-wide |
| `hr_ticket_recommendation` | Check if a ticket already exists for a specific task | Single task |

### Index Search Tools — LLM dynamically queries the index

| Tool | Index | Purpose |
|---|---|---|
| `hr_search_guides` | `new_employee_guides` | Semantic search the knowledge base |
| `hr_employee_checklist` | `onboarding_checklists` | Retrieve full employee profile |

### Built-in Platform Tools

`platform.core.search`, `platform.core.execute_esql`, `platform.core.generate_esql`, `platform.core.get_document_by_id`, `platform.core.list_indices`, `platform.core.get_index_mapping`

---


## Business Value

| Before | After |
|---|---|
| HR chases IT/Finance/Manager over Slack with no audit trail | Agent scans all 50 employees, surfaces every blocker in one prompt |
| Tasks fall through the cracks between teams | Confidence scoring flags uncertain data before HR acts |
| New hire calls HR on Day 1 — laptop not ready | Agent detects Day-1 blockers the night before start date |
| Weekly onboarding report takes an analyst 2 hours | One prompt, 3 seconds, overall confidence score included |
| No way to know if a ticket was already created | `hr_ticket_recommendation` prevents duplicate ticket creation |
