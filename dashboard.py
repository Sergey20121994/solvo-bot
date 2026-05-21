from flask import Flask, render_template, request

from services.excel_service import load_tasks

from services.analytics_service import (
    get_summary,
    get_hours_by_category,
    get_tasks_by_status_stats,
    get_overdue_tasks,
)

app = Flask(__name__)

# ─────────────────────────────────────────────────────
# MAIN PAGE
# ─────────────────────────────────────────────────────

@app.route("/")

def index():

    tasks = load_tasks()

    summary = get_summary()

    overdue = get_overdue_tasks()

    # SEARCH
    search = request.args.get(
        "search",
        ""
    ).lower()

    if search:

        tasks = [

            t for t in tasks

            if (
                search in t["name"].lower()
                or
                search in t["desc"].lower()
                or
                search in t["category"].lower()
            )

        ]

    # CATEGORY FILTER
    category_filter = request.args.get(
        "category",
        ""
    )

    if category_filter:

        tasks = [

            t for t in tasks

            if t["category"] == category_filter

        ]

    # UNIQUE CATEGORIES
    categories = sorted(

        list(set(

            t["category"]

            for t in load_tasks()

            if t["category"]

        ))

    )

    return render_template(

        "index.html",

        tasks=tasks,

        summary=summary,

        overdue=overdue,

        categories=categories,

        current_category=category_filter,
    )

# ─────────────────────────────────────────────────────

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )