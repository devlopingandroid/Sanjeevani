"""External Notification Provider Architecture (Phase 6).

Provides an abstract interface and concrete implementations for trusted contact alerts:
1. TwilioNotificationProvider (SMS & WhatsApp via REST API)
2. WebhookNotificationProvider (HMAC-signed JSON payload HTTP POST)
3. ConsoleNotificationProvider (Development & local testing fallback logging payload without external calls)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import hmac
import hashlib
import time
import httpx

from app.core.config import settings
from app.core.logging import logger


class NotificationDeliveryError(Exception):
    """Custom exception raised when a provider fails to deliver a notification."""

    def __init__(self, message: str, category: str = "PROVIDER_ERROR", status_code: Optional[int] = None):
        super().__init__(message)
        self.category = category
        self.status_code = status_code


class BaseNotificationProvider(ABC):
    @abstractmethod
    def send_notification(
        self,
        recipient_phone: str,
        message_body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Dispatches a notification to the external delivery provider.

        Returns a dictionary containing delivery details:
        {"delivered": bool, "provider_message_id": Optional[str], "details": Dict}
        Raises NotificationDeliveryError on failure.
        """
        pass


class ConsoleNotificationProvider(BaseNotificationProvider):
    """Development and fallback provider that logs notification details without external calls."""

    def send_notification(
        self,
        recipient_phone: str,
        message_body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        logger.info(
            f"[NOTIFICATION][CONSOLE] Recipient={recipient_phone} | Body='{message_body}' | Metadata={metadata}"
        )
        return {
            "delivered": True,
            "provider_message_id": f"console-stub-{int(time.time()*1000)}",
            "details": {"mode": "console_stdout", "timestamp": time.time()},
        }


class TwilioNotificationProvider(BaseNotificationProvider):
    """Twilio provider for SMS and WhatsApp delivery using official Twilio SDK / REST API."""

    def __init__(self, mode: str = "sms"):
        self.mode = mode  # "sms" or "whatsapp"
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_phone = settings.effective_twilio_from_phone
        self.timeout = settings.NOTIFICATION_TIMEOUT_SECONDS

        if not self.account_sid or not self.auth_token or not self.from_phone:
            raise NotificationDeliveryError(
                "Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_PHONE/TWILIO_FROM_NUMBER) are incomplete.",
                category="PROVIDER_UNCONFIGURED",
            )

    def send_notification(
        self,
        recipient_phone: str,
        message_body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        from_num = self.from_phone
        to_num = recipient_phone
        if self.mode == "whatsapp":
            if not from_num.startswith("whatsapp:"):
                from_num = f"whatsapp:{from_num}"
            if not to_num.startswith("whatsapp:"):
                to_num = f"whatsapp:{to_num}"

        # Attempt sending using Twilio SDK if available, falling back to HTTP REST client
        try:
            try:
                from twilio.rest import Client
                from twilio.base.exceptions import TwilioRestException

                client = Client(self.account_sid, self.auth_token)
                msg = client.messages.create(
                    body=message_body,
                    from_=from_num,
                    to=to_num,
                )
                logger.info(f"[NOTIFICATION][TWILIO] SMS Sent. SID={msg.sid} | Status={msg.status}")
                return {
                    "delivered": True,
                    "provider_message_id": msg.sid,
                    "details": {
                        "status": msg.status,
                        "price": msg.price,
                        "sid": msg.sid,
                        "date_created": str(msg.date_created),
                    },
                }
            except ImportError:
                # Fallback to direct HTTP REST API call if SDK import fails
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
                data = {"From": from_num, "To": to_num, "Body": message_body}
                with httpx.Client(timeout=self.timeout) as http_client:
                    response = http_client.post(url, data=data, auth=(self.account_sid, self.auth_token))

                if response.status_code in (200, 201):
                    res_data = response.json()
                    return {
                        "delivered": True,
                        "provider_message_id": res_data.get("sid"),
                        "details": {"status": res_data.get("status"), "price": res_data.get("price")},
                    }
                elif response.status_code in (401, 403):
                    raise NotificationDeliveryError(
                        f"Twilio authentication failure ({response.status_code})",
                        category="PROVIDER_AUTHENTICATION_ERROR",
                        status_code=response.status_code,
                    )
                else:
                    raise NotificationDeliveryError(
                        f"Twilio API error ({response.status_code}): {response.text}",
                        category="PROVIDER_API_ERROR",
                        status_code=response.status_code,
                    )
        except Exception as exc:
            if isinstance(exc, NotificationDeliveryError):
                raise exc

            err_str = str(exc)
            if self.auth_token:
                err_str = err_str.replace(self.auth_token, "[REDACTED]")

            status_code = getattr(exc, "status", None) or getattr(exc, "status_code", None)
            category = "PROVIDER_API_ERROR"
            if isinstance(exc, (httpx.TimeoutException, TimeoutError)) or "timeout" in err_str.lower():
                category = "NETWORK_TIMEOUT"
            elif status_code in (401, 403):
                category = "PROVIDER_AUTHENTICATION_ERROR"
            elif status_code == 429:
                category = "PROVIDER_429_RATE_LIMIT"

            logger.error(f"[NOTIFICATION][TWILIO] Delivery failure: {err_str}")
            raise NotificationDeliveryError(
                f"Twilio delivery failed: {err_str}",
                category=category,
                status_code=status_code,
            )


class WebhookNotificationProvider(BaseNotificationProvider):
    """Generic HMAC-signed HTTP webhook notification provider."""

    def __init__(self):
        self.webhook_url = settings.NOTIFICATION_WEBHOOK_URL
        self.webhook_secret = settings.NOTIFICATION_WEBHOOK_SECRET
        self.timeout = settings.NOTIFICATION_TIMEOUT_SECONDS

        if not self.webhook_url:
            raise NotificationDeliveryError(
                "NOTIFICATION_WEBHOOK_URL is not configured.",
                category="PROVIDER_UNCONFIGURED",
            )

    def send_notification(
        self,
        recipient_phone: str,
        message_body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "recipient_phone": recipient_phone,
            "message": message_body,
            "timestamp": int(time.time()),
            "metadata": metadata or {},
        }
        headers = {"Content-Type": "application/json"}

        # Sign request if secret is provided
        if self.webhook_secret:
            import json
            serialized = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                self.webhook_secret.encode("utf-8"),
                serialized.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Sanjeevni-Signature"] = signature

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.webhook_url, json=payload, headers=headers)

            if response.status_code in (200, 201, 202, 204):
                return {
                    "delivered": True,
                    "provider_message_id": f"webhook-{int(time.time()*1000)}",
                    "details": {"status_code": response.status_code},
                }
            else:
                raise NotificationDeliveryError(
                    f"Webhook provider endpoint returned HTTP {response.status_code}: {response.text}",
                    category="WEBHOOK_HTTP_ERROR",
                    status_code=response.status_code,
                )
        except httpx.TimeoutException:
            raise NotificationDeliveryError(
                f"Webhook notification request timed out after {self.timeout}s",
                category="NETWORK_TIMEOUT",
            )
        except httpx.RequestError as exc:
            raise NotificationDeliveryError(
                f"Network request error connecting to webhook endpoint: {exc}",
                category="NETWORK_ERROR",
            )


def get_notification_provider() -> BaseNotificationProvider:
    """Factory method resolving the active provider based on application settings."""
    provider_name = (settings.NOTIFICATION_PROVIDER or "console").lower().strip()

    if provider_name in ("twilio", "twilio_sms", "twilio-sms", "sms"):
        return TwilioNotificationProvider(mode="sms")
    elif provider_name in ("twilio_whatsapp", "twilio-whatsapp", "whatsapp"):
        return TwilioNotificationProvider(mode="whatsapp")
    elif provider_name == "webhook":
        return WebhookNotificationProvider()
    elif provider_name == "console":
        return ConsoleNotificationProvider()
    else:
        logger.warning(
            f"Unknown NOTIFICATION_PROVIDER '{provider_name}'. Falling back to ConsoleNotificationProvider."
        )
        return ConsoleNotificationProvider()
