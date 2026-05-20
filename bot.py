"""
Telegram-бот реестра задач СЦ СОЛВО
Полная стабильная версия
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
    filters,
)

# ─────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
EXCEL_PATH = "registry.xlsx"

# ─────────────────────────────────────────────────────
# EMOJI
# ─────────────────────────────────────────────────────

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
}

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
# LOAD EXCEL
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

        # Читаем ВСЕ листы
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

                    # Пропускаем мусор
                    if not name:
                        continue

                    if not isinstance(
                        num,
                        (int, float)
                    ):
                        continue

                    task = {
                        "num": int(num),
                        "ticket": safe_str(row[1]),
                        "name": name,
                        "desc": safe_str(row[3]),
                        "deadline": safe_str(row[4]),
                        "status_sc": safe_str(row[5]),
                        "status_solvo": safe_str(row[6]),
                        "release": safe_str(row[7]),
                        "hours": safe_float(row[8]),
                        "agreed": safe_str(row[9]),

                        # Категория = название листа
                        "category": sheet_name,
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
# FORMATTERS
# ─────────────────────────────────────────────────────

def format_task(task):

    sc_emoji = STATUS_EMOJI.get(
        task["status_sc"],
        "▪️"
    )

    sv_emoji = STATUS_EMOJI.get(
        task["status_solvo"],
        "▪️"
    )

    return (
        f"📋 Задача #{task['num']}\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"

        f"📌 {task['name']}\n\n"

        f"📝 {task['desc']}\n\n"

        f"🎫 Заявка: {task['ticket']}\n"
        f"📂 Категория: {task['category']}\n"
        f"📅 Срок: {task['deadline']}\n"
        f"🚀 Релиз: {task['release']}\n\n"

        f"{sc_emoji} СЦ: {task['status_sc']}\n"
        f"{sv_emoji} СОЛВО: {task['status_solvo']}\n\n"

        f"⏱ Оценка: {task['hours']} ч/ч"
    )


def format_summary(tasks):

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

    return (
        f"📊 СВОДКА ПО РЕЕСТРУ\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"

        f"📌 Всего задач: {total}\n"
        f"✅ Выполнено: {done}\n"
        f"⚙️ В работе: {active}\n"
        f"⏱ Всего часов: {round(total_hours, 1)}"
    )


# ─────────────────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────────────────

async def start(update, context):

    keyboard = [

        [
            InlineKeyboardButton(
                "📊 Сводка",
                callback_data="summary"
            )
        ],

        [
            InlineKeyboardButton(
                "📁 Скачать реестр",
                callback_data="registry"
            )
        ],
    ]

    text = (
        "👋 Привет! Я бот реестра задач СЦ СОЛВО.\n\n"

        "Что умею:\n\n"

        "🔢 /task 1 — карточка задачи\n"
        "🔍 /find контейнер — поиск\n"
        "📊 /summary — сводка\n"
        "📂 /category терминал\n"
        "🚦 /status тестирование\n"
        "📁 /registry — скачать Excel\n\n"

        "Можно просто написать номер задачи."
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# ─────────────────────────────────────────────────────

async def summary(update, context):

    tasks = load_tasks()

    if not tasks:

        await update.message.reply_text(
            "⚠️ Не удалось загрузить реестр."
        )

        return

    await update.message.reply_text(
        format_summary(tasks)
    )


# ─────────────────────────────────────────────────────

async def task(update, context):

    if not context.args:

        await update.message.reply_text(
            "Пример:\n/task 1"
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

    found = [
        t for t in tasks
        if t["num"] == num
    ]

    if not found:

        await update.message.reply_text(
            f"❌ Задача #{num} не найдена."
        )

        return

    await update.message.reply_text(
        format_task(found[0])
    )


# ─────────────────────────────────────────────────────

async def find(update, context):

    if not context.args:

        await update.message.reply_text(
            "Пример:\n/find контейнер"
        )

        return

    query = " ".join(
        context.args
    ).lower()

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
            f"❌ Ничего не найдено: {query}"
        )

        return

    keyboard = []

    for t in found[:20]:

        emoji = STATUS_EMOJI.get(
            t["status_solvo"],
            "▪️"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"{emoji} #{t['num']} {t['name'][:35]}",
                callback_data=f"task_{t['num']}"
            )
        ])

    await update.message.reply_text(
        f"🔍 Найдено задач: {len(found)}\nВыберите задачу:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ─────────────────────────────────────────────────────

async def category(update, context):

    if not context.args:

        await update.message.reply_text(
            "Пример:\n/category Терминал"
        )

        return

    query = " ".join(
        context.args
    ).lower()

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

    keyboard = []

    for t in found:

        emoji = STATUS_EMOJI.get(
            t["status_solvo"],
            "▪️"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"{emoji} #{t['num']} {t['name'][:35]}",
                callback_data=f"task_{t['num']}"
            )
        ])

    await update.message.reply_text(
        f"📂 Раздел: {query}\nВыберите задачу:",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# ─────────────────────────────────────────────────────

async def status(update, context):

    if not context.args:

        await update.message.reply_text(
            "Пример:\n/status тестирование"
        )

        return

    query = " ".join(
        context.args
    ).lower()

    tasks = load_tasks()

    found = [
        t for t in tasks
        if (
            query in t["status_sc"].lower()
            or
            query in t["status_solvo"].lower()
        )
    ]

    if not found:

        await update.message.reply_text(
            f"❌ Статус «{query}» не найден."
        )

        return

    keyboard = []

    for t in found:

        emoji = STATUS_EMOJI.get(
            t["status_solvo"],
            "▪️"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"{emoji} #{t['num']} {t['name'][:35]}",
                callback_data=f"task_{t['num']}"
            )
        ])

    await update.message.reply_text(
        f"🚦 Статус: {query}\nВыберите задачу:",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# ─────────────────────────────────────────────────────

async def registry(update, context):

    try:

        if not os.path.exists(EXCEL_PATH):

            await update.message.reply_text(
                "❌ Файл registry.xlsx не найден."
            )

            return

        with open(EXCEL_PATH, "rb") as f:

            await update.message.reply_document(
                document=f,
                filename="registry.xlsx",
                caption="📁 Реестр задач"
            )

    except Exception:

        logger.error(traceback.format_exc())

        await update.message.reply_text(
            "❌ Ошибка отправки файла."
        )


# ─────────────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────────────

async def callback_handler(update, context):

    query = update.callback_query

    await query.answer()

    data = query.data

    if data == "summary":

        tasks = load_tasks()

        if not tasks:

            await query.message.reply_text(
                "⚠️ Не удалось загрузить реестр."
            )

            return

        await query.message.reply_text(
            format_summary(tasks)
        )

    elif data == "registry":

        if not os.path.exists(EXCEL_PATH):

            await query.message.reply_text(
                "❌ registry.xlsx не найден."
            )

            return

        with open(EXCEL_PATH, "rb") as f:

            await query.message.reply_document(
                document=f,
                filename="registry.xlsx",
                caption="📁 Реестр задач"
            )

    elif data.startswith("task_"):

        num = int(
            data.replace("task_", "")
        )

        tasks = load_tasks()

        found = [
            t for t in tasks
            if t["num"] == num
        ]

        if not found:

            await query.message.reply_text(
                "❌ Задача не найдена"
            )

            return

        await query.message.reply_text(
            format_task(found[0])
        )


# ─────────────────────────────────────────────────────
# FREE TEXT
# ─────────────────────────────────────────────────────

async def text_handler(update, context):

    text = update.message.text.strip()

    # Если номер задачи
    if text.isdigit():

        context.args = [text]

        await task(update, context)

        return

    # Иначе поиск
    context.args = text.split()

    await find(update, context)


# ─────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────

def main():

    if not BOT_TOKEN:

        print("❌ BOT_TOKEN не указан")

        return

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("summary", summary)
    )

    app.add_handler(
        CommandHandler("task", task)
    )

    app.add_handler(
        CommandHandler("find", find)
    )

    app.add_handler(
        CommandHandler("category", category)
    )

    app.add_handler(
        CommandHandler("status", status)
    )

    app.add_handler(
        CommandHandler("registry", registry)
    )

    # Callbacks
    app.add_handler(
        CallbackQueryHandler(callback_handler)
    )

    # Free text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    logger.info("Бот успешно запущен")

    app.run_polling()


# ─────────────────────────────────────────────────────

if __name__ == "__main__":
    main()