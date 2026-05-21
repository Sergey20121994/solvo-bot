import os
import logging
import traceback

from openpyxl import load_workbook

logger = logging.getLogger(__name__)

EXCEL_PATH = "registry.xlsx"


# ─────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────

def safe_str(value):

    if value is None:
        return ""

    return str(value).strip()


def safe_float(value):

    if value in (None, "", "-", "—"):
        return 0

    try:
        return float(value)

    except:
        return 0


# ─────────────────────────────────────────────────────
# LOAD TASKS
# ─────────────────────────────────────────────────────

def load_tasks():

    try:

        if not os.path.exists(EXCEL_PATH):

            logger.error(
                f"Файл не найден: {EXCEL_PATH}"
            )

            return []

        wb = load_workbook(
            EXCEL_PATH,
            data_only=True
        )

        tasks = []

        unique_tasks = set()

        for sheet_name in wb.sheetnames:

            ws = wb[sheet_name]

            logger.info(
                f"Читаем лист: {sheet_name}"
            )

            header_row = None

            # Ищем строку заголовков
            for i in range(1, 15):

                row_values = [

                    safe_str(cell.value).lower()
                    for cell in ws[i]

                ]

                if (
                    "номер заявки" in row_values
                    or "наименование" in " ".join(row_values)
                ):

                    header_row = i
                    break

            if not header_row:
                continue

            start_row = header_row + 1

            for row in ws.iter_rows(
                min_row=start_row,
                values_only=True
            ):

                try:

                    if not row:
                        continue

                    num = row[0]
                    name = safe_str(row[2])

                    # Пропускаем пустые строки
                    if not name:
                        continue

                    # Только задачи
                    if not isinstance(
                        num,
                        (int, float)
                    ):
                        continue

                    num = int(num)

                    # Антидубли
                    unique_key = (
                        num,
                        name.lower()
                    )

                    if unique_key in unique_tasks:
                        continue

                    unique_tasks.add(unique_key)

                    task = {

                        "num": num,

                        "ticket": safe_str(row[1]),

                        "name": name,

                        "desc": safe_str(row[3]),

                        "deadline": safe_str(row[4]),

                        "status_sc": safe_str(row[5]),

                        "status_solvo": safe_str(row[6]),

                        "release": safe_str(row[7]),

                        "hours": safe_float(row[8]),

                        "agreed": safe_str(row[9]),

                        "category": safe_str(row[10]),
                    }

                    tasks.append(task)

                except Exception:

                    logger.error(
                        traceback.format_exc()
                    )

        logger.info(
            f"Загружено задач: {len(tasks)}"
        )

        return tasks

    except Exception:

        logger.error(traceback.format_exc())

        return []


# ─────────────────────────────────────────────────────
# GET TASK
# ─────────────────────────────────────────────────────

def get_task(task_num):

    tasks = load_tasks()

    found = [

        t for t in tasks
        if t["num"] == task_num

    ]

    if not found:
        return None

    return found[0]


# ─────────────────────────────────────────────────────
# SEARCH TASKS
# ─────────────────────────────────────────────────────

def search_tasks(query):

    query = query.lower()

    tasks = load_tasks()

    found = []

    for t in tasks:

        text = " ".join([

            t["name"],
            t["desc"],
            t["ticket"],
            t["category"],
            t["status_solvo"],
            t["status_sc"]

        ]).lower()

        if query in text:
            found.append(t)

    return found


# ─────────────────────────────────────────────────────
# FILTER BY STATUS
# ─────────────────────────────────────────────────────

def get_tasks_by_status(status):

    status = status.lower()

    tasks = load_tasks()

    return [

        t for t in tasks

        if (
            status in t["status_sc"].lower()
            or
            status in t["status_solvo"].lower()
        )

    ]


# ─────────────────────────────────────────────────────
# FILTER BY CATEGORY
# ─────────────────────────────────────────────────────

def get_tasks_by_category(category):

    category = category.lower()

    tasks = load_tasks()

    return [

        t for t in tasks

        if category in t["category"].lower()

    ]