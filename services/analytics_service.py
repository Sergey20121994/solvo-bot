from collections import defaultdict
from datetime import datetime

from services.excel_service import load_tasks


# ─────────────────────────────────────────────────────
# BASIC ANALYTICS
# ─────────────────────────────────────────────────────

def get_summary():

    tasks = load_tasks()

    total = len(tasks)

    done = sum(

        1 for t in tasks

        if t["status_solvo"] in (
            "Установлено",
            "Выполнено",
            "Не СОЛВО"
        )

    )

    active = sum(

        1 for t in tasks

        if t["status_solvo"] in (
            "В работе",
            "Разработка",
            "Тестирование",
            "ОПЭ"
        )

    )

    total_hours = sum(
        t["hours"] for t in tasks
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
        "hours": round(total_hours, 1),
        "progress": progress,
    }


# ─────────────────────────────────────────────────────
# HOURS BY CATEGORY
# ─────────────────────────────────────────────────────

def get_hours_by_category():

    tasks = load_tasks()

    stats = defaultdict(float)

    for t in tasks:

        stats[t["category"]] += t["hours"]

    return dict(stats)


# ─────────────────────────────────────────────────────
# TASKS BY STATUS
# ─────────────────────────────────────────────────────

def get_tasks_by_status_stats():

    tasks = load_tasks()

    stats = defaultdict(int)

    for t in tasks:

        status = t["status_solvo"]

        if not status:
            status = "Без статуса"

        stats[status] += 1

    return dict(stats)


# ─────────────────────────────────────────────────────
# TOP CATEGORIES
# ─────────────────────────────────────────────────────

def get_top_categories():

    hours = get_hours_by_category()

    sorted_hours = sorted(

        hours.items(),
        key=lambda x: x[1],
        reverse=True

    )

    return sorted_hours


# ─────────────────────────────────────────────────────
# OVERDUE TASKS
# ─────────────────────────────────────────────────────

def get_overdue_tasks():

    tasks = load_tasks()

    overdue = []

    today = datetime.today()

    for t in tasks:

        deadline = t["deadline"]

        if not deadline:
            continue

        try:

            deadline_date = datetime.strptime(
                str(deadline),
                "%d.%m.%Y"
            )

            if deadline_date < today:

                if t["status_solvo"] not in (
                    "Установлено",
                    "Выполнено"
                ):

                    overdue.append(t)

        except:
            continue

    return overdue


# ─────────────────────────────────────────────────────
# ANALYTICS TEXT
# ─────────────────────────────────────────────────────

def build_analytics_text():

    summary = get_summary()

    top_categories = get_top_categories()

    overdue = get_overdue_tasks()

    text = (

        "📈 АНАЛИТИКА РЕЕСТРА\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"

        f"📌 Всего задач: {summary['total']}\n"
        f"✅ Выполнено: {summary['done']}\n"
        f"⚙️ В работе: {summary['active']}\n"
        f"⏱️ Всего часов: {summary['hours']}\n"
        f"📊 Выполнение: {summary['progress']}%\n\n"

        "👨‍💻 Часы по категориям:\n"

    )

    for category, hours in top_categories[:10]:

        text += (
            f"• {category} — "
            f"{round(hours, 1)} ч\n"
        )

    text += "\n"

    text += (
        f"🔥 Просроченных задач: "
        f"{len(overdue)}"
    )

    return text