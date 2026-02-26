import json
import argparse
import sys
from pathlib import Path

try:
    from elasticsearch import Elasticsearch, helpers
except ImportError:
    print("elasticsearch-py not installed. Run: pip install elasticsearch")
    sys.exit(1)


CHECKLIST_MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                "hr_text": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "checklist_id": {"type": "keyword"},
            "employee_id": {"type": "keyword"},
            "full_name": {"type": "text", "analyzer": "hr_text", "fields": {"keyword": {"type": "keyword"}}},
            "email": {"type": "keyword"},
            "start_date": {"type": "date", "format": "yyyy-MM-dd"},
            "hire_date": {"type": "date", "format": "yyyy-MM-dd"},
            "position": {"type": "keyword"},
            "department": {"type": "keyword"},
            "manager": {"type": "keyword"},
            "completion_rate": {"type": "float"},
            "overall_status": {"type": "keyword"},
            "additional_notes": {"type": "text"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
            "equipment": {"type": "keyword"},
            "pre_arrival_tasks": {
                "type": "nested",
                "properties": {
                    "task": {"type": "keyword"},
                    "description": {"type": "text"},
                    "phase": {"type": "keyword"},
                    "owner": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "completed_at": {"type": "date"},
                    "assignee": {"type": "keyword"},
                }
            },
            "first_day_tasks": {
                "type": "nested",
                "properties": {
                    "task": {"type": "keyword"},
                    "description": {"type": "text"},
                    "phase": {"type": "keyword"},
                    "owner": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "completed_at": {"type": "date"},
                    "assignee": {"type": "keyword"},
                }
            },
            "first_week_tasks": {
                "type": "nested",
                "properties": {
                    "task": {"type": "keyword"},
                    "description": {"type": "text"},
                    "phase": {"type": "keyword"},
                    "owner": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "completed_at": {"type": "date"},
                    "assignee": {"type": "keyword"},
                }
            },
            "follow_up_tasks": {
                "type": "nested",
                "properties": {
                    "milestone": {"type": "keyword"},
                    "task": {"type": "keyword"},
                    "status": {"type": "keyword"},
                }
            },
            "orientation_schedule": {
                "type": "nested",
                "properties": {
                    "date": {"type": "date", "format": "yyyy-MM-dd"},
                    "topic": {"type": "keyword"},
                    "facilitator": {"type": "keyword"},
                }
            },
        }
    }
}

GUIDE_MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                "guide_text": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "guide_id": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "guide_text", "fields": {"keyword": {"type": "keyword"}}},
            "category": {"type": "keyword"},
            "audience": {"type": "keyword"},
            "content": {"type": "text", "analyzer": "guide_text"},
            "tags": {"type": "keyword"},
            "version": {"type": "keyword"},
            "author": {"type": "keyword"},
            "view_count": {"type": "integer"},
            "helpful_votes": {"type": "integer"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        }
    }
}

TASK_LOG_MAPPING = {
    "mappings": {
        "properties": {
            "log_id": {"type": "keyword"},
            "case_id": {"type": "keyword"},
            "checklist_id": {"type": "keyword"},
            "employee_id": {"type": "keyword"},
            "employee_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "department": {"type": "keyword"},
            "position": {"type": "keyword"},
            "manager": {"type": "keyword"},
            "start_date": {"type": "date", "format": "yyyy-MM-dd"},
            "activity_name": {"type": "keyword"},
            "phase": {"type": "keyword"},
            "owner_team": {"type": "keyword"},
            "assignee": {"type": "keyword"},
            "status": {"type": "keyword"},
            "scheduled_date": {"type": "date"},
            "completed_at": {"type": "date"},
            "duration_hours": {"type": "float"},
            "is_overdue": {"type": "boolean"},
            "blocked_reason": {"type": "text"},
            "ticket_id": {"type": "keyword"},
            "auto_created": {"type": "boolean"},
            "agent_action": {"type": "keyword"},
            "agent_explanation": {"type": "text"},
            "timestamp": {"type": "date"},
        }
    }
}

INDICES = {
    "onboarding_checklists": (CHECKLIST_MAPPING, "onboarding_checklists.json"),
    "new_employee_guides": (GUIDE_MAPPING, "new_employee_guides.json"),
    "task_completion_logs": (TASK_LOG_MAPPING, "task_completion_logs.json"),
}

ID_FIELDS = {
    "onboarding_checklists": "checklist_id",
    "new_employee_guides": "guide_id",
    "task_completion_logs": "log_id",
}


def connect(host: str, api_key: str | None, user: str | None, password: str | None) -> Elasticsearch:
    kwargs = {"hosts": [host]}
    if api_key:
        kwargs["api_key"] = api_key
    elif user and password:
        kwargs["basic_auth"] = (user, password)
    else:
        raise ValueError("Supply either --api-key or --user and --password")

    es = Elasticsearch(**kwargs)
    es.info()
    return es


def create_index(es: Elasticsearch, name: str, mapping: dict, recreate: bool = False):
    if es.indices.exists(index=name):
        if recreate:
            es.indices.delete(index=name)
        else:
            return

    es.indices.create(
        index=name,
        settings=mapping.get("settings"),
        mappings=mapping.get("mappings"),
    )


def bulk_index(es: Elasticsearch, index: str, data_file: str, id_field: str):
    data_path = Path(__file__).parent.parent / "data" / data_file
    with open(data_path) as f:
        docs = json.load(f)

    actions = [
        {"_index": index, "_id": doc[id_field], "_source": doc}
        for doc in docs
    ]
    success, errors = helpers.bulk(es, actions, raise_on_error=False)
    return success, errors


def main():
    parser = argparse.ArgumentParser(description="Set up Elasticsearch indices")
    parser.add_argument("--host", required=True)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--user", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--recreate", action="store_true")
    args = parser.parse_args()

    es = connect(args.host, args.api_key, args.user, args.password)

    for index_name, (mapping, _) in INDICES.items():
        create_index(es, index_name, mapping, recreate=args.recreate)

    total_docs = 0
    for index_name, (_, data_file) in INDICES.items():
        id_field = ID_FIELDS[index_name]
        success, _ = bulk_index(es, index_name, data_file, id_field)
        total_docs += success

    for index_name in INDICES:
        es.count(index=index_name)

    print(f"Done. {total_docs} documents indexed.")


if __name__ == "__main__":
    main()