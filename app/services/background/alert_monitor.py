from typing import Dict, List
import logging
from datetime import datetime, timezone
from app.core.di.container import ServiceContainer
from app.domain.services import StockService, TelegramBotService

logger = logging.getLogger(__name__)


class AlertMonitor:
    """
    Monitors price alerts and triggers notifications when conditions are met.
    """

    def __init__(self, container: ServiceContainer):
        self._container = container
        self._stock_service = container.resolve(StockService)
        self._telegram_bot = container.resolve(TelegramBotService)

    async def check_alerts(self) -> List[Dict]:
        from app.database import async_session_factory
        from app.models.document import Alert
        from app.models.user import User
        from sqlalchemy import select

        triggered = []

        async with async_session_factory() as db:
            result = await db.execute(
                select(Alert).where(Alert.is_active == True, Alert.triggered == False)
            )
            alerts = result.scalars().all()

            for alert in alerts:
                try:
                    stock_data = await self._stock_service.get_stock_data(alert.symbol)
                    if not stock_data:
                        continue

                    current_price = stock_data["price"]
                    should_trigger = False

                    if alert.alert_type == "price_above" and current_price >= alert.target_value:
                        should_trigger = True
                    elif alert.alert_type == "price_below" and current_price <= alert.target_value:
                        should_trigger = True
                    elif alert.alert_type == "percent_change":
                        if abs(stock_data["change_percent"]) >= alert.target_value:
                            should_trigger = True

                    if should_trigger:
                        alert.triggered = True
                        alert.triggered_at = datetime.now(timezone.utc)
                        alert.current_value = current_price

                        user_result = await db.execute(
                            select(User).where(User.id == alert.user_id)
                        )
                        user = user_result.scalar_one_or_none()
                        telegram_id = user.telegram_id if user else None

                        triggered.append({
                            "alert_id": alert.id,
                            "user_id": alert.user_id,
                            "telegram_id": telegram_id,
                            "symbol": alert.symbol,
                            "alert_type": alert.alert_type,
                            "target_value": alert.target_value,
                            "current_value": current_price,
                            "message": alert.message,
                        })

                except Exception as e:
                    logger.error(f"Error checking alert {alert.id}: {e}")

            await db.commit()

        return triggered

    async def send_alert_notification(self, alert_data: Dict) -> bool:
        try:
            symbol = alert_data["symbol"]
            current = alert_data["current_value"]
            target = alert_data["target_value"]
            alert_type = alert_data["alert_type"]
            telegram_id = alert_data.get("telegram_id")

            if not telegram_id:
                logger.warning(f"No telegram_id for alert {alert_data.get('alert_id')}, skipping notification")
                return False

            if alert_type == "price_above":
                message = f"<b>🚨 Price Alert: {symbol}</b>\n\n{symbol} has reached <code>${current:.2f}</code>, crossing your target of <code>${target:.2f}</code>!"
            elif alert_type == "price_below":
                message = f"<b>🚨 Price Alert: {symbol}</b>\n\n{symbol} has dropped to <code>${current:.2f}</code>, below your target of <code>${target:.2f}</code>!"
            else:
                message = f"<b>🚨 Price Alert: {symbol}</b>\n\n{symbol} has moved <code>{current:.2f}%</code>!"

            if alert_data.get("message"):
                message += f"\n\n<i>Note: {alert_data['message']}</i>"

            if self._telegram_bot:
                await self._telegram_bot.send_message(
                    chat_id=telegram_id,
                    text=message,
                    parse_mode="HTML",
                )
                logger.info(f"Alert sent to user {telegram_id}: {symbol} {alert_type}")
                return True
            else:
                logger.warning(f"Telegram bot not available, could not send alert to user {telegram_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")
            return False