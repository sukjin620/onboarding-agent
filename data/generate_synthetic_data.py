"""
Synthetic Data Generator for Employee Onboarding Automation
Generates three datasets based on the Documentero HR template:
  1. onboarding_checklists    – per-employee checklist snapshots
  2. new_employee_guides      – reusable guide articles
  3. task_completion_logs     – event-level audit trail (process-mining ready)
"""

import json
import random
import uuid
from datetime import datetime, timedelta

# helpers
def rand_date(start: datetime, end: datetime) -> datetime:
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def date_only(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")

# reference data
DEPARTMENTS   = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Legal", "Product", "Design"]
POSITIONS     = {
    "Engineering": ["Software Engineer", "Senior SWE", "DevOps Engineer", "QA Engineer"],
    "Marketing":   ["Content Strategist", "Growth Manager", "SEO Specialist"],
    "Sales":       ["Account Executive", "SDR", "Sales Manager"],
    "HR":          ["HR Generalist", "Recruiter", "People Ops Manager"],
    "Finance":     ["Financial Analyst", "Accountant", "Controller"],
    "Legal":       ["Legal Counsel", "Compliance Analyst"],
    "Product":     ["Product Manager", "Senior PM"],
    "Design":      ["UX Designer", "Visual Designer"],
}
MANAGERS = {
    "Engineering": "Laura Kim",   "Marketing": "Chris Patel",
    "Sales":       "Danny Moore", "HR":        "Sarah Nguyen",
    "Finance":     "Tom Rivera",  "Legal":     "Ava Johnson",
    "Product":     "Marcus Lee",  "Design":    "Priya Singh",
}

FIRST_NAMES = ["Alice","Bob","Carlos","Diana","Ethan","Fatima","George","Hannah",
               "Ivan","Julia","Kevin","Linda","Michael","Nora","Oscar","Paula",
               "Quinn","Rachel","Sam","Tina","Uma","Victor","Wendy","Xander","Yara","Zoe"]
LAST_NAMES  = ["Smith","Jones","Williams","Brown","Davis","Miller","Wilson","Moore",
               "Taylor","Anderson","Thomas","Jackson","White","Harris","Martin"]

# task library
PRE_ARRIVAL_TASKS = [
    {"task": "Send Offer Letter",         "description": "Email signed offer letter and welcome package to new hire.", "phase": "pre_arrival", "owner": "HR"},
    {"task": "Background Check",          "description": "Initiate background screening via Checkr; await clearance.",  "phase": "pre_arrival", "owner": "HR"},
    {"task": "Provision Laptop",          "description": "Order and configure laptop with standard software image.",     "phase": "pre_arrival", "owner": "IT"},
    {"task": "Create AD Account",         "description": "Set up Active Directory / SSO account and email mailbox.",     "phase": "pre_arrival", "owner": "IT"},
    {"task": "Assign Desk / Badge",       "description": "Reserve workspace; issue physical access badge.",              "phase": "pre_arrival", "owner": "Facilities"},
    {"task": "Enroll Benefits",           "description": "Send benefits enrollment link (30-day window).",              "phase": "pre_arrival", "owner": "HR"},
    {"task": "Slack Workspace Invite",    "description": "Invite to company Slack and add to department channels.",      "phase": "pre_arrival", "owner": "IT"},
    {"task": "Payroll Setup",             "description": "Enter new hire in payroll system; confirm bank details.",      "phase": "pre_arrival", "owner": "Finance"},
]

FIRST_DAY_TASKS = [
    {"task": "Welcome Meeting with Manager", "description": "30-min intro call to discuss role, team, and first-week goals.", "phase": "first_day", "owner": "Manager"},
    {"task": "Office Tour / Virtual Intro",  "description": "Tour facilities or introduce to remote team via video call.",   "phase": "first_day", "owner": "HR"},
    {"task": "Hand Over Equipment",          "description": "Deliver laptop, peripherals, and access credentials.",           "phase": "first_day", "owner": "IT"},
    {"task": "Complete I-9 / Tax Forms",     "description": "Collect identity documents; file W-4 and state equivalents.",   "phase": "first_day", "owner": "HR"},
    {"task": "Security Awareness Training",  "description": "Complete mandatory security-awareness course in LMS.",           "phase": "first_day", "owner": "IT"},
    {"task": "Meet the Team Lunch",          "description": "Arrange team lunch (in-person) or virtual coffee chat.",         "phase": "first_day", "owner": "Manager"},
]

FIRST_WEEK_TASKS = [
    {"task": "Role-Specific Tool Setup",     "description": "Configure Jira, GitHub, Salesforce or relevant tools.",          "phase": "first_week", "owner": "IT"},
    {"task": "Read Company Handbook",        "description": "Review and acknowledge Employee Handbook in HR portal.",          "phase": "first_week", "owner": "HR"},
    {"task": "Compliance Training",          "description": "Complete GDPR / HIPAA / SOC2 compliance modules in LMS.",         "phase": "first_week", "owner": "Legal"},
    {"task": "Set 30-Day Goals",             "description": "Draft initial OKRs with manager; upload to performance system.",  "phase": "first_week", "owner": "Manager"},
    {"task": "Buddy / Mentor Assigned",      "description": "Pair new hire with an experienced colleague for peer mentoring.", "phase": "first_week", "owner": "HR"},
    {"task": "Department Deep-Dive",         "description": "Attend departmental overview session or watch recording.",        "phase": "first_week", "owner": "Manager"},
    {"task": "Intro to Key Stakeholders",    "description": "Schedule 15-min intros with cross-functional partners.",         "phase": "first_week", "owner": "Manager"},
]

FOLLOW_UP_MILESTONES = [
    {"milestone": "30 Day",  "task": "Check-in with Manager",         "statuses": ["Not Started","In Progress","Completed"]},
    {"milestone": "30 Day",  "task": "Complete Role Training Path",    "statuses": ["Not Started","In Progress","Completed"]},
    {"milestone": "60 Day",  "task": "First Performance Conversation", "statuses": ["Not Started","In Progress","Completed"]},
    {"milestone": "60 Day",  "task": "Finalize Benefits Enrollment",   "statuses": ["Not Started","Completed"]},
    {"milestone": "90 Day",  "task": "90-Day Review Meeting",          "statuses": ["Not Started","Scheduled","Completed"]},
    {"milestone": "90 Day",  "task": "Confirm Probation Passed",       "statuses": ["Not Started","Completed"]},
]

EQUIPMENT_POOL = [
    "MacBook Pro 14-inch M3", "Dell XPS 15", "ThinkPad X1 Carbon",
    "27-inch External Monitor", "USB-C Hub", "Mechanical Keyboard",
    "Logitech MX Master Mouse", "Bose QuietComfort Headset",
    "iPhone 14 (work SIM)", "Desk Phone (VOIP)", "YubiKey Security Token",
    "Webcam Logitech C920", "Ergonomic Chair Upgrade",
]

ORIENTATION_TOPICS = [
    ("Company Mission & Values",   "CEO / HR"),
    ("Org Structure & Teams",      "HR"),
    ("Engineering Bootcamp",       "Engineering Lead"),
    ("Security & Compliance 101",  "InfoSec"),
    ("Product Demo & Roadmap",     "Product Manager"),
    ("Benefits & Perks Overview",  "HR"),
    ("Communication Norms",        "HR"),
    ("Data Privacy & GDPR",        "Legal"),
    ("Tools & Systems Walkthrough","IT"),
]

TASK_STATUSES = ["Not Started", "In Progress", "Completed", "Blocked", "Skipped"]

# generators 

def make_employee(emp_id: int, base_date: datetime) -> dict:
    dept   = random.choice(DEPARTMENTS)
    fname  = random.choice(FIRST_NAMES)
    lname  = random.choice(LAST_NAMES)
    start  = base_date + timedelta(days=random.randint(0, 180))
    return {
        "employee_id":   f"EMP-{emp_id:04d}",
        "full_name":     f"{fname} {lname}",
        "email":         f"{fname.lower()}.{lname.lower()}@acmecorp.com",
        "department":    dept,
        "position":      random.choice(POSITIONS[dept]),
        "manager":       MANAGERS[dept],
        "start_date":    date_only(start),
        "hire_date":     date_only(start - timedelta(days=random.randint(7, 21))),
        "_start_dt":     start,   # internal use
    }


def make_checklist(emp: dict) -> dict:
    """One checklist document per employee (matches Documentero template)."""
    start_dt = emp["_start_dt"]

    def task_status(phase_offset_days: int) -> dict:
        # simulate realistic completion lag
        due     = start_dt + timedelta(days=phase_offset_days)
        done    = random.random() < 0.82  # 82% completion rate
        blocked = (not done) and random.random() < 0.2
        completed_at = iso(due + timedelta(hours=random.randint(-4, 48))) if done else None
        return {
            "status":       "Completed" if done else ("Blocked" if blocked else "In Progress"),
            "completed_at": completed_at,
            "assignee":     None,   # filled per-task
        }

    pre_tasks = []
    for t in PRE_ARRIVAL_TASKS:
        s = task_status(-7)
        pre_tasks.append({**t, **s, "assignee": t["owner"]})

    first_day_tasks = []
    for t in FIRST_DAY_TASKS:
        s = task_status(0)
        first_day_tasks.append({**t, **s, "assignee": t["owner"]})

    first_week_tasks = []
    for t in FIRST_WEEK_TASKS:
        s = task_status(5)
        first_week_tasks.append({**t, **s, "assignee": t["owner"]})

    follow_ups = []
    for f in FOLLOW_UP_MILESTONES:
        status = random.choice(f["statuses"])
        follow_ups.append({"milestone": f["milestone"], "task": f["task"], "status": status})

    equipment = random.sample(EQUIPMENT_POOL, k=random.randint(3, 6))

    orient_days = sorted(random.sample(range(0, 5), k=min(5, len(ORIENTATION_TOPICS))))
    orientation = []
    for i, (topic, facilitator) in enumerate(random.sample(ORIENTATION_TOPICS, k=min(5, len(orient_days)))):
        session_date = start_dt + timedelta(days=orient_days[i] if i < len(orient_days) else i)
        orientation.append({"date": date_only(session_date), "topic": topic, "facilitator": facilitator})

    completed_count = sum(1 for t in pre_tasks + first_day_tasks + first_week_tasks if t["status"] == "Completed")
    total_count     = len(pre_tasks) + len(first_day_tasks) + len(first_week_tasks)

    return {
        "checklist_id":    str(uuid.uuid4()),
        "employee_id":     emp["employee_id"],
        "full_name":       emp["full_name"],
        "email":           emp["email"],
        "start_date":      emp["start_date"],
        "hire_date":       emp["hire_date"],
        "position":        emp["position"],
        "department":      emp["department"],
        "manager":         emp["manager"],
        "pre_arrival_tasks":  pre_tasks,
        "first_day_tasks":    first_day_tasks,
        "first_week_tasks":   first_week_tasks,
        "follow_up_tasks":    follow_ups,
        "equipment":          equipment,
        "orientation_schedule": orientation,
        "additional_notes":   random.choice([
            "Remote employee — ship equipment to home address.",
            "On-site role; badge activation required day 1.",
            "Hybrid schedule: M/W/F in office.",
            "Requires VPN access for contractor systems.",
            "",
        ]),
        "completion_rate":  round(completed_count / total_count * 100, 1),
        "overall_status":   (
            "Completed"   if completed_count == total_count else
            "In Progress" if completed_count > 0            else
            "Not Started"
        ),
        "created_at":  iso(emp["_start_dt"] - timedelta(days=14)),
        "updated_at":  iso(datetime.utcnow()),
    }


def make_guide(guide_id: int) -> dict:
    """Reusable knowledge-base articles for new employees."""
    guides = [
        {
            "title": "How to Set Up Your Development Environment",
            "category": "Engineering",
            "audience": ["Engineering"],
            "content": (
                "Welcome to the Engineering team! Follow these steps:\n\n"
                "1. Clone the bootstrap repo: `git clone git@github.com:acmecorp/dev-setup.git`\n"
                "2. Run `./setup.sh` — installs Homebrew, Docker, nvm, and project dependencies.\n"
                "3. Configure your SSH key pair and add the public key to GitHub and the bastion host.\n"
                "4. Request AWS IAM access via the #it-requests Slack channel.\n"
                "5. Join the #engineering and #dev-general Slack channels.\n"
                "6. Attend the weekly Engineering All-Hands every Tuesday at 10 AM PT.\n"
                "7. Your buddy will walk you through the codebase in your first pair-programming session."
            ),
            "tags": ["setup", "engineering", "git", "docker", "aws"],
        },
        {
            "title": "Navigating Your Benefits: Health, Dental & 401k",
            "category": "HR",
            "audience": ["All"],
            "content": (
                "You have 30 days from your start date to enroll in benefits.\n\n"
                "**Health Insurance**: Log in to Gusto > Benefits > Medical. We offer three tiers (HMO, PPO, HDHP).\n"
                "**Dental & Vision**: Bundled with medical; same enrollment window.\n"
                "**401(k)**: We match up to 4% of salary. Enroll via Guideline — link in your welcome email.\n"
                "**PTO**: Unlimited PTO policy. Log time off in Lattice and notify your manager in Slack.\n"
                "**Parental Leave**: 16 weeks fully paid for primary caregiver; 8 weeks for secondary.\n\n"
                "Questions? Ping #people-ops or email benefits@acmecorp.com."
            ),
            "tags": ["benefits", "health", "401k", "pto", "hr"],
        },
        {
            "title": "Company Communication Tools Guide",
            "category": "Operations",
            "audience": ["All"],
            "content": (
                "We use the following tools — get familiar with each:\n\n"
                "- **Slack**: Primary async chat. Join your department channel and #general, #announcements.\n"
                "- **Notion**: Company wiki and project docs. Your manager will share the team Notion.\n"
                "- **Google Workspace**: Email, Calendar, Drive, Meet. SSO via Okta.\n"
                "- **Jira**: Engineering tickets and sprints. PM creates your first sprint tickets.\n"
                "- **Lattice**: Performance reviews, 1:1 agendas, and goal tracking.\n"
                "- **Zoom**: Video calls with external partners. License provisioned in your first week.\n\n"
                "Slack etiquette: use threads for replies; set a status when in Do Not Disturb mode."
            ),
            "tags": ["slack", "notion", "jira", "communication", "tools"],
        },
        {
            "title": "Security & Compliance Essentials",
            "category": "Security",
            "audience": ["All"],
            "content": (
                "Security is everyone's responsibility. Required actions in Week 1:\n\n"
                "1. Enable MFA on all company accounts (Google, Slack, GitHub, AWS).\n"
                "2. Install CrowdStrike Falcon on your laptop — IT will push the agent automatically.\n"
                "3. Complete the **Security Awareness** course in Workday LMS (≈ 45 min).\n"
                "4. Never share credentials. Use 1Password (team vault) for all passwords.\n"
                "5. Report phishing attempts to security@acmecorp.com immediately.\n"
                "6. Do not use personal cloud storage (Dropbox, personal Drive) for work files.\n\n"
                "Policy docs are in Notion > Security > Policies."
            ),
            "tags": ["security", "mfa", "compliance", "1password", "mandatory"],
        },
        {
            "title": "Your First 30-60-90 Day Plan",
            "category": "HR",
            "audience": ["All"],
            "content": (
                "This plan helps you ramp up effectively.\n\n"
                "**Days 1–30 (Learn)**:\n"
                "- Complete all onboarding tasks and compliance training.\n"
                "- Schedule 1:1s with every teammate and key cross-functional partner.\n"
                "- Shadow existing processes; ask lots of questions.\n\n"
                "**Days 31–60 (Contribute)**:\n"
                "- Take ownership of a small project or ticket.\n"
                "- Draft your OKRs with your manager in Lattice.\n"
                "- Identify one process improvement opportunity.\n\n"
                "**Days 61–90 (Lead)**:\n"
                "- Deliver on your first project.\n"
                "- Complete your 90-day review with your manager.\n"
                "- Propose one new idea in your team's retrospective.\n"
            ),
            "tags": ["30-60-90", "goals", "ramp-up", "performance"],
        },
        {
            "title": "IT Troubleshooting: Common First-Week Issues",
            "category": "IT",
            "audience": ["All"],
            "content": (
                "Common issues and how to fix them:\n\n"
                "**Can't log in to Okta?** → Reset password at okta.acmecorp.com/forgot or ping #it-helpdesk.\n"
                "**Laptop not imaging?** → Boot to recovery mode and re-run MDM enrollment.\n"
                "**Slack invite expired?** → Ask your manager to resend from admin.slack.com.\n"
                "**VPN not connecting?** → Ensure Cisco AnyConnect is installed; use `vpn.acmecorp.com`.\n"
                "**Missing software?** → Submit a request in Jira Service Desk > IT Requests.\n\n"
                "IT Help Desk: #it-helpdesk (Slack) | it@acmecorp.com | ext. 1000 | SLA: 4 business hours."
            ),
            "tags": ["it", "troubleshooting", "okta", "vpn", "helpdesk"],
        },
        {
            "title": "Sales Playbook for New Account Executives",
            "category": "Sales",
            "audience": ["Sales"],
            "content": (
                "Welcome to the Sales team! Here is what you need in Week 1:\n\n"
                "1. **CRM Access**: Log in to Salesforce (SFDC) using your Okta credentials.\n"
                "2. **Territory Assignment**: Your manager will assign your named accounts in SFDC.\n"
                "3. **Product Certification**: Complete the 4-hour Sales Certification in Highspot.\n"
                "4. **Shadow Calls**: Join 3 discovery calls with a senior AE in your first two weeks.\n"
                "5. **Quota**: Your ramping quota for Month 1 is 25% of OTE target.\n"
                "6. **Commission Plan**: Reviewed in Finance's onboarding session (Day 3).\n\n"
                "Key contacts: Sales Ops (#sales-ops), RevOps (#revenue-ops), SE pool (#solutions-engineering)."
            ),
            "tags": ["sales", "salesforce", "quota", "crm", "playbook"],
        },
        {
            "title": "Design System & Brand Guidelines",
            "category": "Design",
            "audience": ["Design", "Marketing"],
            "content": (
                "The Acme Design System lives in Figma (team: Acme Design).\n\n"
                "**Brand Colors**: Primary #1E3A5F (Navy), Accent #F4A916 (Gold), Neutral #F5F5F5.\n"
                "**Typography**: Inter for UI; Playfair Display for marketing headlines.\n"
                "**Logo Usage**: Never stretch or recolor the logo. Assets in Figma > Brand Assets.\n"
                "**Component Library**: Use existing components before creating new ones. PR to the Figma library requires design lead approval.\n"
                "**Review Process**: All external-facing designs must be reviewed by the Brand team before handoff.\n\n"
                "Design Slack channels: #design-critique, #brand-assets, #design-system."
            ),
            "tags": ["design", "figma", "brand", "guidelines", "ui"],
        },
    ]
    g = guides[guide_id % len(guides)]
    return {
        "guide_id":    f"GUIDE-{guide_id:04d}",
        "title":       g["title"],
        "category":    g["category"],
        "audience":    g["audience"],
        "content":     g["content"],
        "tags":        g["tags"],
        "version":     f"1.{random.randint(0, 5)}",
        "created_at":  iso(datetime(2024, 1, 1) + timedelta(days=random.randint(0, 180))),
        "updated_at":  iso(datetime(2025, 1, 1) + timedelta(days=random.randint(0, 300))),
        "author":      random.choice(["HR Team", "IT Team", "Security Team", "Sales Ops", "People Ops"]),
        "view_count":  random.randint(10, 500),
        "helpful_votes": random.randint(5, 200),
    }


def make_task_log_events(emp: dict, checklist: dict) -> list[dict]:
    """
    Expand each task in a checklist into an event-log record.
    Schema is process-mining-ready (Case ID, Activity, Timestamp, Actor).
    """
    events = []
    start_dt = emp["_start_dt"]

    def phase_offset(phase: str) -> int:
        return {"pre_arrival": -7, "first_day": 0, "first_week": 5}[phase]

    all_tasks = (
        checklist["pre_arrival_tasks"] +
        checklist["first_day_tasks"]   +
        checklist["first_week_tasks"]
    )

    for t in all_tasks:
        offset      = phase_offset(t["phase"])
        scheduled   = start_dt + timedelta(days=offset, hours=random.randint(8, 17))
        completed_at = t.get("completed_at")

        events.append({
            "log_id":          str(uuid.uuid4()),
            "case_id":         emp["employee_id"],           # process-mining Case ID
            "checklist_id":    checklist["checklist_id"],
            "employee_id":     emp["employee_id"],
            "employee_name":   emp["full_name"],
            "department":      emp["department"],
            "position":        emp["position"],
            "manager":         emp["manager"],
            "start_date":      emp["start_date"],
            # activity fields
            "activity_name":   t["task"],
            "phase":           t["phase"],
            "owner_team":      t["owner"],
            "assignee":        t.get("assignee", t["owner"]),
            "status":          t["status"],
            "scheduled_date":  iso(scheduled),
            "completed_at":    completed_at,
            "duration_hours":  (
                round((datetime.strptime(completed_at, "%Y-%m-%dT%H:%M:%SZ") - scheduled).total_seconds() / 3600, 2)
                if completed_at else None
            ),
            "is_overdue":      (
                completed_at is not None and
                datetime.strptime(completed_at, "%Y-%m-%dT%H:%M:%SZ") > scheduled + timedelta(hours=24)
            ),
            "blocked_reason":  (
                random.choice([
                    "Waiting on background check clearance",
                    "IT equipment backordered",
                    "Manager not available",
                    "System provisioning error",
                    "Form not submitted by employee",
                ]) if t["status"] == "Blocked" else None
            ),
            "ticket_id":       f"JIRA-{random.randint(1000, 9999)}" if random.random() > 0.5 else None,
            "auto_created":    random.random() > 0.4,   # was this ticket auto-created by the agent?
            "agent_action":    random.choice([
                "ticket_created", "record_updated", "reminder_sent",
                "escalation_triggered", "guide_linked", "none"
            ]),
            "agent_explanation": None,   # filled at inference time
            "timestamp":       iso(datetime.utcnow()),
        })

    return events


# main 
def generate_all(n_employees: int = 50) -> dict:
    base_date   = datetime(2024, 6, 1)
    employees   = [make_employee(i + 1, base_date) for i in range(n_employees)]
    checklists  = [make_checklist(e) for e in employees]
    guides      = [make_guide(i) for i in range(8)]
    task_logs   = []
    for emp, cl in zip(employees, checklists):
        task_logs.extend(make_task_log_events(emp, cl))

    return {"checklists": checklists, "guides": guides, "task_logs": task_logs}


if __name__ == "__main__":
    data = generate_all(50)

    with open("onboarding_checklists.json", "w") as f:
        json.dump(data["checklists"], f, indent=2)

    with open("new_employee_guides.json", "w") as f:
        json.dump(data["guides"], f, indent=2)

    with open("task_completion_logs.json", "w") as f:
        json.dump(data["task_logs"], f, indent=2)

    print(f"Generated:")
    print(f"   {len(data['checklists'])} onboarding checklists")
    print(f"   {len(data['guides'])} new-employee guides")
    print(f"   {len(data['task_logs'])} task completion log events")
