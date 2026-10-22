from __future__ import annotations

import argparse
import logging

from telegram_noc_bot.client import HttpNocClient, MockNocClient
from telegram_noc_bot.commands import execute
from telegram_noc_bot.config import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger(__name__)
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


def response_chunks(response: str, limit: int = TELEGRAM_MAX_MESSAGE_LENGTH - 100):
    """Split a response into line-based Telegram-safe messages."""
    if len(response) <= limit:
        return [response]
    chunks: list[str] = []
    current = ""
    for line in response.splitlines(keepends=True):
        if current and len(current) + len(line) > limit:
            chunks.append(current.rstrip())
            current = ""
        if len(line) > limit:
            if current:
                chunks.append(current.rstrip())
                current = ""
            chunks.extend(line[index:index + limit] for index in range(0, len(line), limit))
        else:
            current += line
    if current:
        chunks.append(current.rstrip())
    return chunks


def make_client(settings: Settings):
    return MockNocClient() if settings.mode == "mock" else HttpNocClient(settings.noc_api_url, settings.request_timeout)


def authorized(update: Update, settings: Settings) -> bool:
    user = update.effective_user
    return bool(user and user.id in settings.allowed_user_ids)


def build_application(settings: Settings):
    from telegram import Update
    from telegram.constants import ParseMode
    from telegram.ext import Application, CommandHandler, ContextTypes

    if not settings.bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
    if not settings.allowed_user_ids:
        raise RuntimeError("TELEGRAM_ALLOWED_USER_IDS must contain at least one Telegram user ID")
    client = make_client(settings)
    application = Application.builder().token(settings.bot_token).build()

    async def command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not authorized(update, settings):
            await update.effective_message.reply_text("Acceso no autorizado.")
            return
        text = update.effective_message.text or "/help"
        response = execute(text, client)
        for chunk in response_chunks(response):
            await update.effective_message.reply_text(chunk, parse_mode=ParseMode.HTML)

    for name in ("start", "help", "status", "gateways", "sensors", "sensor", "gateway", "alerts"):
        application.add_handler(CommandHandler(name, command))
    return application


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        metavar="COMMAND",
        nargs="+",
        help="execute one command using the configured client",
    )
    args = parser.parse_args()
    settings = Settings()
    client = make_client(settings)
    if args.dry_run:
        print(execute(" ".join(args.dry_run), client))
        return
    from telegram import Update

    build_application(settings).run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
