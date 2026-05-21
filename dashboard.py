from flask import Flask, render_template, request

from services.excel_service import load_tasks

from services.analytics_service import (
    get_overdue_tasks,
)

app = Flask(__name__)

# ─────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────

def build_summary(tasks):

    total = len(tasks)

    done = len([

        t for t in tasks

        if t["status_solvo"] in [

            "Выполнено",
            "Установлено"
        ]

    ])

    active = len([

        t for t in tasks

        if t["status_solvo"] not in [

            "Выполнено",
            "Установлено"
        ]

    ])

    hours = sum(

        t["hours"]

        for t in tasks
    )

    progress = 0

    if total > 0:

        progress = round(
            (done / total) * 100,
            1
        )

    return {

        "total": total,
        "done": done,
        "active": active,
        "hours": hours,
        "progress": progress,
    }

# ─────────────────────────────────────────────────────
# MAIN PAGE
# ─────────────────────────────────────────────────────

@app.route("/")

def index():

    tasks = load_tasks()

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

    # SUMMARY УЖЕ ПО ОТФИЛЬТРОВАННЫМ TASKS
    summary = build_summary(tasks)

    # OVERDUE
    overdue = [

        t for t in get_overdue_tasks()

        if (
            not category_filter
            or
            t["category"] == category_filter
        )

    ]

    # CATEGORIES
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