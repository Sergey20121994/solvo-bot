from flask import Flask, render_template

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

    hours_by_category = (
        get_hours_by_category()
    )

    status_stats = (
        get_tasks_by_status_stats()
    )

    overdue = get_overdue_tasks()

    return render_template(

        "index.html",

        tasks=tasks,

        summary=summary,

        hours_by_category=hours_by_category,

        status_stats=status_stats,

        overdue=overdue,
    )

# ─────────────────────────────────────────────────────

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )