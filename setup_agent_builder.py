import json
import sys
import argparse
import os
import time

try:
    import requests
except ImportError:
    print("❌  pip install requests")
    sys.exit(1)

# Constants 
AGENT_ID    = "hr-onboarding-agent"
AGENT_NAME  = "HR Onboarding Automation Agent"

# Tool definitions 
TOOLS = [

    # 1. Get onboarding status for one employee (ES|QL) 
    {
        "id":   "hr_onboarding_status",
        "type": "esql",
        "tags": ["hr", "onboarding", "status"],
        "description": (
            "Retrieve the onboarding task completion status for a specific employee. "
            "Returns total tasks, completed count, blocked count, overdue count, "
            "and completion percentage. "
            "Use this first when asked about a specific employee's onboarding progress."
        ),
        "configuration": {
            "query": """FROM task_completion_logs
| WHERE employee_id == ?employee_id
| STATS
    total     = COUNT(*),
    completed = COUNT_IF(status == "Completed"),
    blocked   = COUNT_IF(status == "Blocked"),
    overdue   = COUNT_IF(is_overdue == true),
    in_progress = COUNT_IF(status == "In Progress")
| EVAL completion_pct = ROUND(completed * 100.0 / total, 1)""",
            "params": {
                "employee_id": {
                    "type": "string",
                    "description": (
                        "Employee ID in the format EMP-XXXX (e.g. EMP-0001). "
                        "Always required."
                    )
                }
            }
        }
    },

    # 2. List all blocked / overdue tasks (ES|QL) 
    {
        "id":   "hr_blocked_tasks",
        "type": "esql",
        "tags": ["hr", "onboarding", "blocked", "escalation"],
        "description": (
            "List onboarding tasks that are currently Blocked or overdue across "
            "all employees. Optionally filter by department. "
            "Returns employee ID, name, department, task name, phase, owner team, "
            "status, and the reason for the block. "
            "Use this to identify bottlenecks and decide which tickets to create."
        ),
        "configuration": {
            "query": """FROM task_completion_logs
| WHERE (status == "Blocked" OR is_overdue == true)
    AND (department == ?department OR ?department == "ALL")
| KEEP employee_id, employee_name, department, activity_name,
       phase, owner_team, status, is_overdue, scheduled_date, blocked_reason, ticket_id
| SORT scheduled_date ASC
| LIMIT ?limit""",
            "params": {
                "department": {
                    "type": "string",
                    "description": (
                        "Department name to filter results (e.g. Engineering, Sales, HR). "
                        "Pass 'ALL' to return results for all departments. "
                        "Defaults to 'ALL'."
                    ),
                    "optional": True,
                    "defaultValue": "ALL"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return. Defaults to 25.",
                    "optional": True,
                    "defaultValue": 25
                }
            }
        }
    },

    # 3. Task detail for one employee – phase breakdown (ES|QL) 
    {
        "id":   "hr_task_detail",
        "type": "esql",
        "tags": ["hr", "onboarding", "tasks"],
        "description": (
            "Get the full task-level breakdown for a specific employee, showing "
            "every individual onboarding task, its phase (pre_arrival / first_day / first_week), "
            "owner team, status, and whether it is overdue. "
            "Use this after hr_onboarding_status to drill into exactly which tasks need attention."
        ),
        "configuration": {
            "query": """FROM task_completion_logs
| WHERE employee_id == ?employee_id
| KEEP activity_name, phase, owner_team, status,
       is_overdue, scheduled_date, completed_at, blocked_reason, ticket_id
| SORT phase ASC, scheduled_date ASC
| LIMIT 50""",
            "params": {
                "employee_id": {
                    "type": "string",
                    "description": "Employee ID (EMP-XXXX) to retrieve tasks for."
                }
            }
        }
    },

    # 4. Completion analytics by department (ES|QL)
    {
        "id":   "hr_onboarding_analytics",
        "type": "esql",
        "tags": ["hr", "onboarding", "analytics", "dashboard"],
        "description": (
            "Aggregate onboarding task completion metrics grouped by department. "
            "Returns total tasks, completed tasks, blocked tasks, and a completion "
            "percentage for each department — sorted from lowest to highest completion. "
            "Use this for dashboards, weekly HR reports, or identifying which department "
            "has the most onboarding problems."
        ),
        "configuration": {
            "query": """FROM task_completion_logs
| STATS
    total     = COUNT(*),
    completed = COUNT_IF(status == "Completed"),
    blocked   = COUNT_IF(status == "Blocked"),
    overdue   = COUNT_IF(is_overdue == true)
  BY department
| EVAL completion_pct = ROUND(completed * 100.0 / total, 1)
| SORT completion_pct ASC""",
            "params": {}
        }
    },

    # 5. Blocked task count by owner team (ES|QL)
    {
        "id":   "hr_blocked_by_team",
        "type": "esql",
        "tags": ["hr", "onboarding", "analytics", "teams"],
        "description": (
            "Count how many onboarding tasks are currently Blocked, grouped by "
            "the responsible owner team (IT, HR, Manager, Finance, Legal). "
            "Use this to identify which team is the biggest bottleneck and "
            "where escalation efforts should be focused."
        ),
        "configuration": {
            "query": """FROM task_completion_logs
| WHERE status == "Blocked"
| STATS blocked_count = COUNT(*) BY owner_team
| SORT blocked_count DESC
| LIMIT 10""",
            "params": {}
        }
    },

    # 6. Log an agent ticket action (ES|QL – write via INGEST pipeline)
    {
        "id":   "hr_ticket_recommendation",
        "type": "esql",
        "tags": ["hr", "onboarding", "tickets"],
        "description": (
            "Look up whether a specific onboarding task already has an open ticket "
            "so the agent can decide whether to recommend creating a new one. "
            "Returns the ticket_id, status, and agent_action for the task."
        ),
        "configuration": {
            "query": """FROM task_completion_logs
| WHERE employee_id == ?employee_id AND activity_name == ?task_name
| KEEP employee_id, employee_name, activity_name, status,
       ticket_id, agent_action, agent_explanation, blocked_reason
| LIMIT 5""",
            "params": {
                "employee_id": {
                    "type": "string",
                    "description": "Employee ID (EMP-XXXX)."
                },
                "task_name": {
                    "type": "string",
                    "description": "Exact name of the onboarding task to check."
                }
            }
        }
    },

    # 7. Search new-employee knowledge base (Index Search) 
    {
        "id":   "hr_search_guides",
        "type": "index_search",
        "tags": ["hr", "onboarding", "guides", "knowledge-base"],
        "description": (
            "Full-text search the new employee knowledge base. "
            "Use this to find relevant onboarding guide articles when an employee "
            "asks how to do something, is stuck on a task, or needs documentation. "
            "Examples: 'how to set up VPN', 'benefits enrollment steps', "
            "'development environment setup', 'security MFA requirements'. "
            "Always call this tool when a blocked task relates to a known guide topic."
        ),
        "configuration": {
            "pattern": "new_employee_guides"
        }
    },

    # 8. Look up an employee's full checklist (Index Search) 
    {
        "id":   "hr_employee_checklist",
        "type": "index_search",
        "tags": ["hr", "onboarding", "checklist"],
        "description": (
            "Search the onboarding checklists index to retrieve an employee's "
            "full onboarding record including personal info, manager, start date, "
            "equipment list, orientation schedule, and 30-60-90 day follow-up tasks. "
            "Use this when you need full profile details beyond task completion stats."
        ),
        "configuration": {
            "pattern": "onboarding_checklists"
        }
    },
]

# Agent definition 
AGENT = {
    "id":   AGENT_ID,
    "name": AGENT_NAME,
    "labels": ["hr", "onboarding", "automation"],
    "description": (
        "I automate the employee onboarding process for Acme Corp. "
        "I can check any new hire's progress, surface blocked tasks, "
        "find the right knowledge-base guide, and recommend escalation actions — "
        "all explained clearly so HR always knows what happened and why."
    ),
    "avatar_color":  "#1E3A5F",
    "avatar_symbol": "HR",
    "configuration": {
        "tools": [
            {
                "tool_ids": [
                    # Custom tools defined above
                    "hr_onboarding_status",
                    "hr_blocked_tasks",
                    "hr_task_detail",
                    "hr_onboarding_analytics",
                    "hr_blocked_by_team",
                    "hr_ticket_recommendation",
                    "hr_search_guides",
                    "hr_employee_checklist",
                    # Built-in platform tools (always available, no creation needed)
                    "platform.core.search",
                    "platform.core.execute_esql",
                    "platform.core.generate_esql",
                    "platform.core.get_document_by_id",
                    "platform.core.list_indices",
                    "platform.core.get_index_mapping",
                ]
            }
        ],
        "instructions": """You are the Acme Corp HR Onboarding Automation Agent.

Your role is to automate and streamline the employee onboarding process by:
- Monitoring task completion across all new hires
- Identifying blocked or overdue tasks that need escalation
- Surfacing relevant knowledge-base guides when employees are stuck
- Recommending specific ticket creation actions with clear reasoning
- Generating onboarding health dashboards for HR leadership

## Decision workflow — follow this order for every request:

1. UNDERSTAND: Determine if the request is about (a) a specific employee,
   (b) a department/team view, or (c) an org-wide analytics request.

2. RETRIEVE: Call the appropriate tool(s):
   - Specific employee → hr_onboarding_status, then hr_task_detail if blocked tasks exist
   - Org-wide blockers → hr_blocked_tasks, then hr_blocked_by_team
   - Dashboard/report  → hr_onboarding_analytics + hr_blocked_by_team
   - Guide/help needed → hr_search_guides

3. CROSS-REFERENCE: If tasks are blocked, always call hr_search_guides with
   relevant keywords so you can surface the right guide for the employee.

4. RECOMMEND ACTIONS — use this exact format for every blocked task:
   ┌─────────────────────────────────────────────────────────────────┐
   │ ACTION REQUIRED                                                 │
   │ Employee  : <name> (<id>)                                       │
   │ Task      : <task name>                                         │
   │ Reason    : <why it is blocked>                                 │
   │ Assign to : <owner team>                                        │
   │ Priority  : High (Day-1) | Medium (Week-1) | Low (follow-up)   │
   │ Guide     : <guide title if relevant>                           │
   │ Why       : <plain-English explanation of agent reasoning>      │
   └─────────────────────────────────────────────────────────────────┘

5. SUMMARISE: End every response with:
   - Number of employees checked
   - Number of blockers found
   - Number of recommended actions
   - Top bottleneck team

## Rules
- NEVER invent data. Only report what the tools return.
- ALWAYS explain your reasoning in plain English.
- If a task has an existing ticket_id, note it — do not recommend a duplicate.
- Escalate Day-1 blockers (phase = first_day) as High priority.
- Be concise. HR teams are busy. Lead with findings, then details.
"""
    }
}

# HTTP helpers 
def kibana_request(
    method: str,
    kibana_url: str,
    path: str,
    api_key: str,
    payload: dict | None = None,
) -> dict:
    """Make a Kibana API request. Raises on HTTP error."""
    url = f"{kibana_url.rstrip('/')}{path}"
    headers = {
        "Authorization": f"ApiKey {api_key}",
        "kbn-xsrf":      "true",
        "Content-Type":  "application/json",
    }
    resp = requests.request(
        method,
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )
    if not resp.ok:
        print(f"   ⚠️   HTTP {resp.status_code} → {url}")
        print(f"        {resp.text[:400]}")
        resp.raise_for_status()
    return resp.json() if resp.text else {}


# Setup steps 
def delete_if_exists(kibana_url: str, api_key: str, path: str, name: str):
    try:
        kibana_request("DELETE", kibana_url, path, api_key)
        print(f"   🗑️   Deleted existing {name}")
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            pass   # doesn't exist yet — fine
        else:
            raise


def create_tools(kibana_url: str, api_key: str, recreate: bool = False) -> list[str]:
    print("\n── Creating tools ────────────────────────────────────────────────────")
    created = []
    for tool in TOOLS:
        tool_id = tool["id"]
        if recreate:
            delete_if_exists(kibana_url, api_key, f"/api/agent_builder/tools/{tool_id}", f"tool '{tool_id}'")

        try:
            kibana_request("POST", kibana_url, "/api/agent_builder/tools", api_key, tool)
            print(f"   ✅  Created tool: {tool_id:40s} [{tool['type']}]")
            created.append(tool_id)
        except requests.HTTPError as e:
            body = e.response.text or ""
            
            if "already exists" in body.lower():
                print(f"   ⏭️   Already exists (skipping): {tool_id}")
                created.append(tool_id)
            else:
                print(f"\n   ❌  Failed on tool: {tool_id}")
                print(f"       HTTP {e.response.status_code}: {body[:300]}")
                raise
        time.sleep(0.2)   # avoid rate-limiting

    return created


def create_agent(kibana_url: str, api_key: str, recreate: bool = False):
    print("\n── Creating agent ────────────────────────────────────────────────────")
    if recreate:
        delete_if_exists(kibana_url, api_key, f"/api/agent_builder/agents/{AGENT_ID}", f"agent '{AGENT_ID}'")

    try:
        result = kibana_request("POST", kibana_url, "/api/agent_builder/agents", api_key, AGENT)
        print(f"   ✅  Created agent: {result.get('name', AGENT_ID)!r} (id={result.get('id', '?')})")
        return result
    except requests.HTTPError as e:
        body = e.response.text or ""
        if "already exists" in body.lower():
            print(f"   ⏭️   Agent already exists (skipping — use --recreate to overwrite): {AGENT_ID}")
        else:
            raise


def verify_tools(kibana_url: str, api_key: str):
    """List all tools and confirm ours are present."""
    print("\n── Verifying tools ───────────────────────────────────────────────────")
    result = kibana_request("GET", kibana_url, "/api/agent_builder/tools", api_key)
    all_tool_ids = {t["id"] for t in result.get("results", [])}
    our_ids      = {t["id"] for t in TOOLS}
    for tid in sorted(our_ids):
        status = "✅ " if tid in all_tool_ids else "❌  MISSING"
        print(f"   {status}  {tid}")
    builtin_count = sum(1 for t in result.get("results", []) if t.get("type") == "builtin")
    print(f"\n   Total tools in workspace: {len(all_tool_ids)} ({builtin_count} built-in)")


def print_next_steps(kibana_url: str):
    print(f"""
{'═'*65}
AGENT BUILDER SETUP COMPLETE
{'═'*65}

Your HR Onboarding Automation Agent is live in Elastic Agent Builder.

── CHAT WITH YOUR AGENT ──────────────────────────────────────────

Option A — Kibana UI (recommended for demo):
  1. Open {kibana_url}
  2. Go to the left nav → Agents
  3. Select "{AGENT_NAME}" from the dropdown
  4. Start chatting!

  Sample prompts:
  ▸ "What is the onboarding status of EMP-0001?"
  ▸ "Show me all blocked tasks in the Engineering department"
  ▸ "Give me the full onboarding analytics dashboard"
  ▸ "Which team is causing the most onboarding delays?"
  ▸ "Find guides for setting up a development environment"
  ▸ "EMP-0007 can't access Slack. What should we do?"

Option B — Kibana API (programmatic / CI-CD):
  See converse_with_agent.py for a ready-to-run example.

  curl -X POST "{kibana_url}/api/agent_builder/converse" \\
       -H "Authorization: ApiKey $KIBANA_API_KEY" \\
       -H "kbn-xsrf: true" \\
       -H "Content-Type: application/json" \\
       -d '{{
         "agent_id": "{AGENT_ID}",
         "messages": [
           {{"role": "user", "content": "Show blocked tasks across all departments"}}
         ]
       }}'

Option C — MCP (integrate with Claude Desktop, Cursor, etc.):
  In Kibana > Agents > Tools, click "Copy MCP server URL"
  Use the URL to connect any MCP-compatible client.

── TOOLS CREATED ─────────────────────────────────────────────────

  Type         ID
  ──────────── ──────────────────────────────────────────────────
  esql         hr_onboarding_status
  esql         hr_blocked_tasks
  esql         hr_task_detail
  esql         hr_onboarding_analytics
  esql         hr_blocked_by_team
  esql         hr_ticket_recommendation
  index_search hr_search_guides           (index: new_employee_guides)
  index_search hr_employee_checklist      (index: onboarding_checklists)
  + 6 built-in platform.core.* tools

{'═'*65}
""")


#Entry point

def main():
    parser = argparse.ArgumentParser(
        description="Set up the HR Onboarding Agent in Elastic Agent Builder via the Kibana API"
    )
    parser.add_argument(
        "--kibana-url",
        default=os.getenv("KIBANA_URL", ""),
        help="Kibana URL, e.g. https://<project>.kb.<region>.aws.elastic.cloud"
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("KIBANA_API_KEY", ""),
        help="Elastic API key with Kibana access"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate existing tools and agent"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing tools — do not create anything"
    )
    args = parser.parse_args()

    if not args.kibana_url or not args.api_key:
        print(" Required: --kibana-url and --api-key  (or env vars KIBANA_URL / KIBANA_API_KEY)")
        print("   Example:")
        print("     python setup_agent_builder.py \\")
        print("       --kibana-url https://my-project.kb.us-east-1.aws.elastic.cloud \\")
        print("       --api-key    <YOUR_SERVERLESS_API_KEY>")
        sys.exit(1)

    print(f"\n HR Onboarding Agent Builder Setup")
    print(f"    Kibana URL : {args.kibana_url}")
    print(f"    API Key    : {'*' * 8}{args.api_key[-6:]}")

    if args.verify_only:
        verify_tools(args.kibana_url, args.api_key)
        return

    create_tools(args.kibana_url, args.api_key, recreate=args.recreate)
    create_agent(args.kibana_url, args.api_key, recreate=args.recreate)
    verify_tools(args.kibana_url, args.api_key)
    print_next_steps(args.kibana_url)


if __name__ == "__main__":
    main()