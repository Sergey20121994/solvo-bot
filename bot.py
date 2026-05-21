import os
import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from services.excel_service import (
    load_tasks,
    get_task,
    search_tasks,
    get_tasks_by_status,
    get_tasks_by_category,
)

from services.analytics_service import (
    get_summary,
    build_analytics_text,
    get_overdue_tasks,
)

# ─────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────

BOT_TOKEN = os.environ.get("BOT_TOKEN")

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
# FORMAT TASK
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

        f"⏱️ Оценка: {task['hours']} ч/ч"
    )

# ─────────────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────────────

def build_main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "📊 Сводка",
                callback_data="summary"
            ),

            InlineKeyboardButton(
                "📈 Аналитика",
                callback_data="analytics"
            ),
        ],

        [
            InlineKeyboardButton(
                "📂 Категории",
                callback_data="categories"
            ),

            InlineKeyboardButton(
                "🚦 Статусы",
                callback_data="statuses"
            ),
        ],

        [
            InlineKeyboardButton(
                "🔥 Просроченные",
                callback_data="overdue"
            )
        ],

        [
            InlineKeyboardButton(
                "📁 Скачать реестр",
                callback_data="registry"
            )
        ],

        [
            InlineKeyboardButton(
                "🌐 Dashboard",
                url="https://solvo-bot-production.up.railway.app/"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)

# ─────────────────────────────────────────────────────
# START
# ─────────────────────────────────────────────────────

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (

        "👋 Система управления реестром СОЛВО\n\n"

        "Доступные функции:\n\n"

        "📊 Сводка\n"
        "📈 Аналитика\n"
        "📂 Категории\n"
        "🚦 Статусы\n"
        "🔥 Просроченные\n"
        "📁 Скачать Excel\n\n"

        "Можно:\n"
        "• написать номер задачи\n"
        "• использовать /find\n"
        "• использовать кнопки"
    )

    await update.message.reply_text(
        text,
        reply_markup=build_main_menu()
    )

# ─────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────

async def summary(update, context):

    summary_data = get_summary()

    text = (

        "📊 СВОДКА ПО РЕЕСТРУ\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"

        f"📌 Всего задач: {summary_data['total']}\n"
        f"✅ Выполнено: {summary_data['done']}\n"
        f"⚙️ В работе: {summary_data['active']}\n"
        f"⏱️ Всего часов: {summary_data['hours']}\n"
        f"📈 Выполнение: {summary_data['progress']}%"
    )

    await update.message.reply_text(text)

# ─────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────

async def analytics(update, context):

    text = build_analytics_text()

    await update.message.reply_text(text)

# ─────────────────────────────────────────────────────
# FIND
# ─────────────────────────────────────────────────────

async def find(update, context):

    if not context.args:

        await update.message.reply_text(
            "Пример:\n/find контейнер"
        )

        return

    query = " ".join(context.args)

    found = search_tasks(query)

    if not found:

        await update.message.reply_text(
            "❌ Ничего не найдено."
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

        f"🔍 Найдено задач: {len(found)}",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )

# ─────────────────────────────────────────────────────
# TASK
# ─────────────────────────────────────────────────────

async def task(update, context):

    if not context.args:

        await update.message.reply_text(
            "Пример:\n/task 12"
        )

        return

    try:

        task_num = int(context.args[0])

    except:

        await update.message.reply_text(
            "Номер должен быть числом."
        )

        return

    task_data = get_task(task_num)

    if not task_data:

        await update.message.reply_text(
            "❌ Задача не найдена."
        )

        return

    await update.message.reply_text(
        format_task(task_data)
    )

# ─────────────────────────────────────────────────────
# REGISTRY
# ─────────────────────────────────────────────────────

async def registry(update, context):

    if not os.path.exists("registry.xlsx"):

        await update.message.reply_text(
            "❌ registry.xlsx не найден."
        )

        return

    with open("registry.xlsx", "rb") as f:

        await update.message.reply_document(
            document=f,
            filename="registry.xlsx",
            caption="📁 Реестр задач"
        )

# ─────────────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────────────

async def callback_handler(update, context):

    query = update.callback_query

    await query.answer()

    data = query.data

    # SUMMARY
    if data == "summary":

        summary_data = get_summary()

        text = (

            "📊 СВОДКА ПО РЕЕСТРУ\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"

            f"📌 Всего задач: {summary_data['total']}\n"
            f"✅ Выполнено: {summary_data['done']}\n"
            f"⚙️ В работе: {summary_data['active']}\n"
            f"⏱️ Всего часов: {summary_data['hours']}\n"
            f"📈 Выполнение: {summary_data['progress']}%"
        )

        await query.message.reply_text(text)

    # ANALYTICS
    elif data == "analytics":

        await query.message.reply_text(
            build_analytics_text()
        )

    # OVERDUE
    elif data == "overdue":

        overdue = get_overdue_tasks()

        if not overdue:

            await query.message.reply_text(
                "✅ Просроченных задач нет."
            )

            return

        keyboard = []

        for t in overdue:

            keyboard.append([

                InlineKeyboardButton(
                    f"🔥 #{t['num']} {t['name'][:35]}",
                    callback_data=f"task_{t['num']}"
                )

            ])

        await query.message.reply_text(

            f"🔥 Просроченных задач: {len(overdue)}",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

    # CATEGORIES
    elif data == "categories":

        tasks = load_tasks()

        categories = sorted(

            list(set(
                t["category"]
                for t in tasks
            ))

        )

        keyboard = []

        for category in categories:

            keyboard.append([

                InlineKeyboardButton(
                    f"📂 {category}",
                    callback_data=f"category_{category}"
                )

            ])

        await query.message.reply_text(

            "📂 Категории:",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

    # CATEGORY
    elif data.startswith("category_"):

        category = data.replace(
            "category_",
            ""
        )

        found = get_tasks_by_category(
            category
        )

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

        await query.message.reply_text(

            f"📂 {category}",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

    # STATUSES
    elif data == "statuses":

        statuses = [

            "В работе",
            "Разработка",
            "Тестирование",
            "На приемке",
            "ОПЭ",
            "Выполнено",
        ]

        keyboard = []

        for status in statuses:

            keyboard.append([

                InlineKeyboardButton(
                    f"🚦 {status}",
                    callback_data=f"status_{status}"
                )

            ])

        await query.message.reply_text(

            "🚦 Статусы:",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

    # STATUS
    elif data.startswith("status_"):

        status = data.replace(
            "status_",
            ""
        )

        found = get_tasks_by_status(
            status
        )

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

        await query.message.reply_text(

            f"🚦 {status}",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

    # TASK
    elif data.startswith("task_"):

        task_num = int(
            data.replace(
                "task_",
                ""
            )
        )

        task_data = get_task(task_num)

        if not task_data:

            await query.message.reply_text(
                "❌ Задача не найдена."
            )

            return

        await query.message.reply_text(
            format_task(task_data)
        )

    # REGISTRY
    elif data == "registry":

        if not os.path.exists(
            "registry.xlsx"
        ):

            await query.message.reply_text(
                "❌ Файл не найден."
            )

            return

        with open(
            "registry.xlsx",
            "rb"
        ) as f:

            await query.message.reply_document(
                document=f,
                filename="registry.xlsx",
                caption="📁 Реестр задач"
            )

# ─────────────────────────────────────────────────────
# FREE TEXT
# ─────────────────────────────────────────────────────

async def text_handler(update, context):

    text = update.message.text.strip()

    # Номер задачи
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

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # COMMANDS
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("summary", summary)
    )

    app.add_handler(
        CommandHandler("analytics", analytics)
    )

    app.add_handler(
        CommandHandler("find", find)
    )

    app.add_handler(
        CommandHandler("task", task)
    )

    app.add_handler(
        CommandHandler("registry", registry)
    )

    # CALLBACKS
    app.add_handler(
        CallbackQueryHandler(
            callback_handler
        )
    )

    # TEXT
    app.add_handler(

        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            text_handler
        )

    )

    logger.info("Bot started")

    app.run_polling()

# ─────────────────────────────────────────────────────

if __name__ == "__main__":
    main()