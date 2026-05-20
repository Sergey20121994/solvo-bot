"""
Telegram-бот для просмотра реестра задач СЦ СОЛВО.
Стабильная версия без падений Markdown.
"""

import os
import logging
import traceback

from openpyxl import load_workbook

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ──────────────────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────

BOT_TOKEN = os.environ.get("BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")
EXCEL_PATH = os.environ.get("EXCEL_PATH", "registry.xlsx")

# ──────────────────────────────────────────────────────────────────────────────
# EMOJI
# ──────────────────────────────────────────────────────────────────────────────

STATUS_EMOJI = {
    "Установлено": "✅",
    "Выполнено": "✅",
    "Не СОЛВО": "☑️",
    "ОПЭ": "🔄",
    "Тестирование": "🧪",
    "На приемке": "📥",
    "В работе": "⚙️",
    "Разработка": "👨‍💻",
    "Аналитика": "🔍",
    "Оценка": "📊",
    "Ожидает рассмотрения": "⏳",
    "Приостановлена": "⏸️",
    "Выставлено": "📤",
}

PRIORITY_EMOJI = {
    "Высокий": "🔴",
    "Средний": "🟡",
    "Низкий": "🟢",
}

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def safe_str(value):

    if value is None:
        return ""

    return str(value).strip()


def safe_float(value):

    if value in (None, "", "—", "-"):
        return 0

    try:
        return float(value)

    except:
        return 0


# ──────────────────────────────────────────────────────────────────────────────
# LOAD TASKS
# ──────────────────────────────────────────────────────────────────────────────

def load_tasks():

    try:

        wb = load_workbook(EXCEL_PATH, data_only=True)
        ws = wb["📋 Реестр"]

    except Exception:

        logger.error(traceback.format_exc())

        return []

    tasks = []

    for row in ws.iter_rows(min_row=4, values_only=True):

        try:

            num = row[0]

            # Excel может хранить как float
            if not isinstance(num, (int, float)):
                continue

            num = int(num)

            task = {
                "num": num,
                "ticket": safe_str(row[1]),
                "name": safe_str(row[2]),
                "desc": safe_str(row[3]),
                "deadline": safe_str(row[4]),
                "status_sc": safe_str(row[5]),
                "status_solvo": safe_str(row[6]),
                "release": safe_str(row[7]),
                "hours": safe_float(row[8]),
                "agreed": safe_str(row[9]),
                "category": safe_str(row[10]),
                "priority": safe_str(row[12]) if len(row) > 12 else "",
                "notes": "",
            }

            tasks.append(task)

        except Exception:

            logger.error(traceback.format_exc())

    logger.info(f"Загружено задач: {len(tasks)}")

    return tasks


# ──────────────────────────────────────────────────────────────────────────────
# FORMAT TASK
# ──────────────────────────────────────────────────────────────────────────────

def format_task_card(t):

    sc_ico = STATUS_EMOJI.get(t["status_sc"], "▪️")
    sv_ico = STATUS_EMOJI.get(t["status_solvo"], "▪️")

    # Автоприоритет
    if not t["priority"]:

        sv = t["status_solvo"]

        if sv in (
            "Тестирование",
            "Разработка",
            "На приемке"
        ):
            t["priority"] = "Высокий"

        elif sv in (
            "В работе",
            "Аналитика",
            "Оценка",
            "ОПЭ"
        ):
            t["priority"] = "Средний"

        else:
            t["priority"] = "Низкий"

    pr_ico = PRIORITY_EMOJI.get(t["priority"], "▪️")

    agreed = "✅ Да" if t["agreed"] == "Да" else "❌ Нет"

    release = t["release"] if t["release"] else "—"

    hours = (
        f"{round(t['hours'], 1)} ч/ч"
        if t["hours"] else "—"
    )

    ticket = (
        f"\n🎫 Заявка: {t['ticket']}"
        if t["ticket"] else ""
    )

    notes = (
        f"\n💬 Примечание: {t['notes']}"
        if t["notes"] else ""
    )

    return (
        f"📋 Задача #{t['num']}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{t['name']}\n\n"
        f"📝 {t['desc']}\n"
        f"{ticket}\n\n"
        f"📂 Категория: {t['category']}\n"
        f"📅 Срок: {t['deadline']}\n"
        f"🚀 Релиз: {release}\n\n"
        f"{sc_ico} Статус СЦ: {t['status_sc']}\n"
        f"{sv_ico} Статус СОЛВО: {t['status_solvo']}\n\n"
        f"⏱ Оценка: {hours}\n"
        f"💰 Оценена: {agreed}\n"
        f"{pr_ico} Приоритет: {t['priority']}"
        f"{notes}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────────────────────

def format_summary():

    tasks = load_tasks()

    if not tasks:
        return "⚠️ Не удалось загрузить реестр."

    total = len(tasks)

    done = sum(
        1 for t in tasks
        if t["status_solvo"] in (
            "Установлено",
            "Не СОЛВО",
            "Выполнено"
        )
    )

    active = sum(
        1 for t in tasks
        if t["status_solvo"] in (
            "В работе",
            "Тестирование",
            "Разработка",
            "ОПЭ",
            "На приемке"
        )
    )

    paused = sum(
        1 for t in tasks
        if t["status_solvo"] == "Приостановлена"
    )

    total_hours = sum(t["hours"] for t in tasks)

    pct = round(done / total * 100) if total else 0

    return (
        f"📊 СВОДКА ПО РЕЕСТРУ\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Всего задач: {total}\n"
        f"✅ Выполнено: {done} ({pct}%)\n"
        f"⚙️ В работе: {active}\n"
        f"⏸️ Приостановлено: {paused}\n"
        f"⏱ Суммарная оценка: {round(total_hours,1)} ч/ч"
    )


# ──────────────────────────────────────────────────────────────────────────────
# COMMANDS
# ──────────────────────────────────────────────────────────────────────────────

async def cmd_start(update, context):

    text = (
        "👋 Привет! Я бот реестра задач СЦ СОЛВО.\n\n"
        "Что умею:\n"
        "🔢 /task 14 — карточка задачи\n"
        "🔍 /find букинг — поиск\n"
        "📊 /summary — сводка\n"
        "📂 /category терминал\n"
        "🚦 /status тестирование\n\n"
        "Можно просто написать номер или слово."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📊 Сводка",
                callback_data="summary"
            )
        ],
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cmd_task(update, context):

    if not context.args:

        await update.message.reply_text(
            "Пример:\n/task 14"
        )

        return

    try:
        num = int(context.args[0])

    except:

        await update.message.reply_text(
            "Номер должен быть числом."
        )

        return

    tasks = load_tasks()

    found = [t for t in tasks if t["num"] == num]

    if not found:

        await update.message.reply_text(
            f"❌ Задача #{num} не найдена."
        )

        return

    await update.message.reply_text(
        format_task_card(found[0])
    )


async def cmd_find(update, context):

    if not context.args:

        await update.message.reply_text(
            "Пример:\n/find букинг"
        )

        return

    query = " ".join(context.args).lower().strip()

    tasks = load_tasks()

    found = []

    for t in tasks:

        text = " ".join([
            t["name"],
            t["desc"],
            t["ticket"],
            t["category"]
        ]).lower()

        if query in text:
            found.append(t)

    if not found:

        await update.message.reply_text(
            f"❌ По запросу «{query}» ничего не найдено."
        )

        return

    if len(found) == 1:

        await update.message.reply_text(
            format_task_card(found[0])
        )

        return

    text = (
        f"🔍 Найдено задач: {len(found)}\n\n"
        f"Выбери задачу:"
    )

    keyboard = []

    for t in found[:10]:

        sv_ico = STATUS_EMOJI.get(
            t["status_solvo"],
            "▪️"
        )

        label = (
            f"#{t['num']} "
            f"{t['name'][:35]} "
            f"{sv_ico}"
        )

        keyboard.append([
            InlineKeyboardButton(
                label,
                callback_data=f"task_{t['num']}"
            )
        ])

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cmd_summary(update, context):

    await update.message.reply_text(
        format_summary()
    )


async def cmd_category(update, context):

    if not context.args:

        await update.message.reply_text(
            "Пример:\n/category терминал"
        )

        return

    query = " ".join(context.args).lower()

    tasks = load_tasks()

    found = [
        t for t in tasks
        if query in t["category"].lower()
    ]

    if not found:

        await update.message.reply_text(
            f"❌ Раздел «{query}» не найден."
        )

        return

    lines = [
        f"📂 {query} — {len(found)} задач\n"
    ]

    for t in found:

        sv_ico = STATUS_EMOJI.get(
            t["status_solvo"],
            "▪️"
        )

        lines.append(
            f"{sv_ico} #{t['num']} {t['name']}"
        )

    await update.message.reply_text(
        "\n".join(lines[:50])
    )


async def cmd_status(update, context):

    if not context.args:

        await update.message.reply_text(
            "Пример:\n/status тестирование"
        )

        return

    query = " ".join(context.args).lower()

    tasks = load_tasks()

    found = [
        t for t in tasks
        if (
            query in t["status_sc"].lower()
            or query in t["status_solvo"].lower()
        )
    ]

    if not found:

        await update.message.reply_text(
            f"❌ Статус «{query}» не найден."
        )

        return

    lines = [
        f"🚦 Найдено задач: {len(found)}\n"
    ]

    for t in found:

        sv_ico = STATUS_EMOJI.get(
            t["status_solvo"],
            "▪️"
        )

        lines.append(
            f"{sv_ico} #{t['num']} {t['name']}"
        )

    await update.message.reply_text(
        "\n".join(lines[:50])
    )


async def cmd_registry(update, context):

    if not os.path.exists(EXCEL_PATH):

        await update.message.reply_text(
            "Файл реестра не найден."
        )

        return

    await update.message.reply_text(
        "Отправляю реестр..."
    )

    with open(EXCEL_PATH, "rb") as f:

        await update.message.reply_document(
            document=f,
            filename="registry.xlsx",
            caption="Реестр задач СЦ СОЛВО"
        )


# ──────────────────────────────────────────────────────────────────────────────
# TEXT INPUT
# ──────────────────────────────────────────────────────────────────────────────

async def handle_text(update, context):

    text = update.message.text.strip()

    if text.isdigit():

        context.args = [text]

        await cmd_task(update, context)

        return

    context.args = text.split()

    await cmd_find(update, context)


# ──────────────────────────────────────────────────────────────────────────────
# CALLBACKS
# ──────────────────────────────────────────────────────────────────────────────

async def handle_callback(update, context):

    query = update.callback_query

    await query.answer()

    data = query.data

    if data == "summary":

        await query.message.reply_text(
            format_summary()
        )

    elif data.startswith("task_"):

        num = int(data.split("_")[1])

        tasks = load_tasks()

        found = [
            t for t in tasks
            if t["num"] == num
        ]

        if found:

            await query.message.reply_text(
                format_task_card(found[0])
            )


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():

    if BOT_TOKEN == "PASTE_YOUR_TOKEN_HERE":

        print("❌ Укажи BOT_TOKEN")

        return

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("task", cmd_task))
    app.add_handler(CommandHandler("find", cmd_find))
    app.add_handler(CommandHandler("summary", cmd_summary))
    app.add_handler(CommandHandler("category", cmd_category))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("registry", cmd_registry))

    app.add_handler(
        CallbackQueryHandler(handle_callback)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    logger.info("Бот успешно запущен")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()