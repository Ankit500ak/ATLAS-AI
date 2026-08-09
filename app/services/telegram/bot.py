import logging
from typing import Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatAction
from app.config import settings
from app.database import async_session_factory
from app.services.ai.orchestrator import AIOrchestrator
from app.models.user import User
from sqlalchemy import select

logger = logging.getLogger(__name__)


class TelegramBot:
    """
    Telegram bot handler that processes user messages and routes them
    through the AI orchestrator. Supports text, voice, images, and documents.
    """

    MAX_MESSAGE_LENGTH = 4096

    def __init__(self):
        self.orchestrator = AIOrchestrator()
        self.app = None

    async def safe_send(self, chat_or_msg, text: str, parse_mode: str = "Markdown",
                        reply_to=None, retry: bool = True) -> bool:
        """Send a message with automatic markdown fallback and length handling."""
        from app.utils.formatters import chunk_message

        chunks = chunk_message(text, max_length=self.MAX_MESSAGE_LENGTH - 50)
        all_success = True

        for i, chunk in enumerate(chunks):
            msg_to_send = chunk
            sent = False

            if parse_mode == "Markdown":
                try:
                    if hasattr(chat_or_msg, 'reply_text'):
                        await chat_or_msg.reply_text(msg_to_send, parse_mode="Markdown",
                                                     reply_to_message_id=reply_to)
                    else:
                        await chat_or_msg.send_message(msg_to_send, parse_mode="Markdown")
                    sent = True
                except Exception as md_err:
                    logger.debug(f"Markdown parse failed, retrying without: {md_err}")
                    try:
                        if hasattr(chat_or_msg, 'reply_text'):
                            await chat_or_msg.reply_text(msg_to_send, reply_to_message_id=reply_to)
                        else:
                            await chat_or_msg.send_message(msg_to_send)
                        sent = True
                    except Exception as plain_err:
                        logger.error(f"Plain text send also failed: {plain_err}")
                        sent = False

            if not sent and parse_mode != "Markdown":
                try:
                    if hasattr(chat_or_msg, 'reply_text'):
                        await chat_or_msg.reply_text(msg_to_send, reply_to_message_id=reply_to)
                    else:
                        await chat_or_msg.send_message(msg_to_send)
                    sent = True
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    sent = False

            if not sent:
                all_success = False

        return all_success

    async def safe_edit(self, message, text: str, parse_mode: str = "Markdown") -> bool:
        """Edit a message with automatic markdown fallback."""
        try:
            await message.edit_text(text, parse_mode="Markdown")
            return True
        except Exception:
            try:
                await message.edit_text(text)
                return True
            except Exception as e:
                logger.error(f"Failed to edit message: {e}")
                return False

    async def update_thinking(self, message, text: str) -> bool:
        """Update the thinking indicator with actual response."""
        from app.utils.formatters import chunk_message
        chunks = chunk_message(text, max_length=self.MAX_MESSAGE_LENGTH - 50)
        if not chunks:
            return False

        success = await self.safe_edit(message, chunks[0])
        return success

    def build_app(self) -> Application:
        self.app = (
            Application.builder()
            .token(settings.telegram_bot_token)
            .build()
        )

        self.app.add_handler(CommandHandler("start", self.handle_start))

        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        self.app.add_handler(
            MessageHandler(filters.VOICE | filters.AUDIO, self.handle_voice)
        )
        self.app.add_handler(
            MessageHandler(filters.PHOTO, self.handle_photo)
        )
        self.app.add_handler(
            MessageHandler(filters.Document.PDF, self.handle_document)
        )

        self.app.add_error_handler(self.handle_error)

        return self.app

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.chat.send_action(ChatAction.TYPING)

        async with async_session_factory() as db:
            result = await db.execute(
                select(User).where(User.telegram_id == user.id)
            )
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                new_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    onboarding_step=0,
                )
                db.add(new_user)
                await db.commit()

                from app.services.ai.prompts import PromptTemplates
                welcome = (
                    f"Hello {user.first_name}! I'm Atlas, your AI Financial Assistant.\n\n"
                    "I help finance professionals stay informed, research companies, "
                    "and make better decisions through natural conversations.\n\n"
                    f"{PromptTemplates.ONBOARDING_STEP_1}"
                )
            else:
                welcome = (
                    f"Welcome back, {user.first_name}! 👋\n\n"
                    "I'm Atlas, your AI Financial Assistant. How can I help you today?\n\n"
                    "Just ask me anything naturally:\n"
                    "• What's happening in the market?\n"
                    "• Analyze Apple's latest earnings\n"
                    "• Compare Microsoft and Google\n"
                    "• Add NVDA to my watchlist\n"
                    "• Show me upcoming earnings\n"
                    "• Check my emails\n"
                    "• What meetings do I have today?"
                )

        await update.message.reply_text(welcome)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        message = update.message.text

        try:
            import random
            thinking_messages = [
                "Analyzing your question...",
                "Looking into it...",
                "Researching this for you...",
                "Crunching the numbers...",
                "Checking the markets...",
                "Thinking about this...",
                "Let me analyze this...",
            ]
            thinking_msg = await update.message.reply_text(random.choice(thinking_messages))

            async with async_session_factory() as db:
                result = await db.execute(
                    select(User).where(User.telegram_id == user.id)
                )
                db_user = result.scalar_one_or_none()

                if not db_user:
                    await self.safe_send(update.message, "Please start the conversation first by typing /start")
                    return

                if db_user.onboarding_step < 6 and not db_user.onboarding_completed:
                    response = await self.orchestrator.process_message(
                        user_id=user.id,
                        message=message,
                        db=db,
                    )
                    reply = response.get("response", "I encountered an error processing your request.")
                    if not await self.safe_edit(thinking_msg, reply):
                        await self.safe_send(update.message, reply)
                    return

                from app.services.personalization.watchlist_manager import watchlist_manager
                watchlist_cmd = await watchlist_manager.parse_watchlist_command(message)

                if watchlist_cmd["action"] == "add" and watchlist_cmd.get("tickers"):
                    res = await watchlist_manager.add_to_watchlist(
                        user.id, watchlist_cmd["tickers"], db
                    )
                    reply = await watchlist_manager.format_watchlist_response(res, "add")
                    await self.safe_edit(thinking_msg, reply)
                    return

                if watchlist_cmd["action"] == "remove" and watchlist_cmd.get("tickers"):
                    res = await watchlist_manager.remove_from_watchlist(
                        user.id, watchlist_cmd["tickers"], db
                    )
                    reply = await watchlist_manager.format_watchlist_response(res, "remove")
                    await self.safe_edit(thinking_msg, reply)
                    return

                response = await self.orchestrator.process_message(
                    user_id=user.id,
                    message=message,
                    db=db,
                )

            reply = response.get("response", "I encountered an error processing your request.")

            try:
                from app.services.personalization.proactive_suggestor import proactive_suggestor
                suggestions = await proactive_suggestor.generate_follow_up_questions(
                    reply, response.get("intent", ""), {}
                )
                if suggestions:
                    reply += "\n\n**You might also ask:**\n"
                    for s in suggestions[:2]:
                        reply += f"  {s}\n"
            except Exception as e:
                logger.debug(f"Suggestion generation skipped: {e}")

            if not await self.safe_edit(thinking_msg, reply):
                await thinking_msg.delete()
                await self.safe_send(update.message, reply)

        except Exception as e:
            logger.error(f"Error handling message from {user.id}: {e}", exc_info=True)
            await self.safe_send(update.message, "I encountered an error processing your request. Please try again.")

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        file_path = None
        try:
            await update.message.chat.send_action(ChatAction.TYPING)

            await self.safe_send(update.message, "Transcribing your voice message...")

            voice = update.message.voice or update.message.audio
            file = await voice.get_file()
            file_path = f"data/cache/{user.id}_voice.ogg"
            await file.download_to_drive(file_path)

            from app.services.telegram.voice_processor import voice_processor
            result = await voice_processor.process_voice(file_path)

            if result["success"]:
                transcribed = result["text"]
                await self.safe_send(update.message, f"**Transcribed:** {transcribed}\n\nProcessing...")

                async with async_session_factory() as db:
                    response = await self.orchestrator.process_message(
                        user_id=user.id,
                        message=transcribed,
                        db=db,
                    )

                reply = response.get("response", "Could not process your request.")
                await self.safe_send(update.message, reply)
            else:
                await self.safe_send(update.message,
                    "Sorry, I couldn't transcribe your voice message. Please try again or type your message."
                )
        except Exception as e:
            logger.error(f"Error handling voice from {user.id}: {e}", exc_info=True)
            await self.safe_send(update.message, "I encountered an error processing your voice message. Please try again.")
        finally:
            if file_path:
                import os
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        file_path = None
        try:
            await update.message.chat.send_action(ChatAction.TYPING)

            await self.safe_send(update.message, "Analyzing your image...")

            photo = update.message.photo[-1]
            file = await photo.get_file()
            file_path = f"data/cache/{user.id}_photo.jpg"
            await file.download_to_drive(file_path)

            from app.services.telegram.voice_processor import voice_processor
            result = await voice_processor.process_image(file_path)

            if result["success"] and result.get("analysis") != "Image analysis unavailable":
                from app.utils.formatters import escape_markdown
                analysis = escape_markdown(result["analysis"])
                reply = f"**Image Analysis:**\n\n{analysis}"

                if update.message.caption:
                    caption = escape_markdown(update.message.caption)
                    reply += f"\n\n**Your question:** {caption}"

                await self.safe_send(update.message, reply)
            else:
                await self.safe_send(update.message,
                    "Sorry, I couldn't analyze this image. Please try a clearer image."
                )
        except Exception as e:
            logger.error(f"Error handling photo from {user.id}: {e}", exc_info=True)
            await self.safe_send(update.message, "I encountered an error analyzing this image. Please try again.")
        finally:
            if file_path:
                import os
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        file_path = None
        try:
            await update.message.chat.send_action(ChatAction.TYPING)

            document = update.message.document
            if not document:
                await update.message.reply_text("Please send a document to analyze.")
                return

            if document.file_size and document.file_size > 20 * 1024 * 1024:
                await update.message.reply_text("Document too large. Please send a file under 20MB.")
                return

            import re
            safe_name = re.sub(r'[^\w\-.]', '_', document.file_name or 'document')
            safe_name = safe_name.lstrip('.').replace('..', '_')

            file = await document.get_file()
            file_path = f"data/documents/{user.id}_{safe_name}"
            await file.download_to_drive(file_path)

            await update.message.reply_text(
                f"Received: {safe_name}\n\n"
                "I'm processing this document. This may take a moment..."
            )

            from app.services.document.processor import DocumentProcessor
            processor = DocumentProcessor()
            result = await processor.process_document(file_path, user.id)

            if result.get("success"):
                from app.models.document import Document
                from app.database import async_session_factory
                from app.models.user import User as UserModel
                from sqlalchemy import select
                from datetime import datetime, timezone

                async with async_session_factory() as db:
                    user_result = await db.execute(
                        select(UserModel).where(UserModel.telegram_id == user.id)
                    )
                    db_user = user_result.scalar_one_or_none()
                    if not db_user:
                        reply = "Please start the conversation first by typing /start"
                        from app.utils.formatters import chunk_message
                        for chunk in chunk_message(reply):
                            await update.message.reply_text(chunk, parse_mode="Markdown")
                        return

                    doc_record = Document(
                        user_id=db_user.id,
                        filename=safe_name,
                        file_path=file_path,
                        document_type=document.mime_type or "application/pdf",
                        file_size=document.file_size or 0,
                        summary=result.get("summary", ""),
                        content=result.get("content", ""),
                        key_insights=result.get("key_insights", []),
                        chunk_count=result.get("chunk_count", 0),
                        status="processed",
                        processed_at=datetime.now(timezone.utc),
                    )
                    db.add(doc_record)
                    await db.commit()

                from app.utils.formatters import escape_markdown
                summary = escape_markdown(result.get('summary', 'N/A'))
                reply = (
                    f"**Document Processed: {safe_name}**\n\n"
                    f"**Summary:**\n{summary}\n\n"
                    f"**Key Insights:**\n"
                )
                for insight in result.get("key_insights", [])[:5]:
                    reply += f"• {escape_markdown(insight)}\n"
                reply += "\nYou can now ask me questions about this document."
            else:
                reply = "I had trouble processing this document. Please try again or send a different file."

            from app.utils.formatters import chunk_message
            for chunk in chunk_message(reply):
                await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error handling document from {user.id}: {e}", exc_info=True)
            try:
                await update.message.reply_text(
                    "I encountered an error processing this document. Please try again."
                )
            except Exception:
                pass
        finally:
            if file_path:
                import os
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    async def handle_error(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Exception while handling an update: {context.error}")

        if update and hasattr(update, "message") and update.message:
            await self.safe_send(update.message, "I encountered an error. Please try again.")
