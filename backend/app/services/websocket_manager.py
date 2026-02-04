"""WebSocket Manager - Real-time Notifications.

Provides:
- WebSocket connection management
- Real-time market data push
- Alert notifications
- Chat streaming
"""

import json
import logging
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    # Market data
    MARKET_QUOTE = "market_quote"
    MARKET_ALERT = "market_alert"
    PRICE_CHANGE = "price_change"

    # Chat
    CHAT_STREAM = "chat_stream"
    CHAT_DONE = "chat_done"

    # System
    HEARTBEAT = "heartbeat"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    ERROR = "error"
    CONNECTED = "connected"


@dataclass
class ClientInfo:
    """Connected client information."""
    client_id: str
    websocket: WebSocket
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)


class ConnectionManager:
    """WebSocket connection manager for real-time updates."""

    def __init__(self):
        self.active_connections: Dict[str, ClientInfo] = {}
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # topic -> client_ids

    async def connect(
        self, websocket: WebSocket, client_id: Optional[str] = None
    ) -> str:
        """Accept new WebSocket connection."""
        await websocket.accept()

        if not client_id:
            client_id = f"client_{len(self.active_connections) + 1}"

        client = ClientInfo(client_id=client_id, websocket=websocket)
        self.active_connections[client_id] = client

        logger.info(f"WebSocket client connected: {client_id}")

        # Send welcome message
        await self.send_personal_message(
            client_id,
            {
                "type": MessageType.CONNECTED.value,
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return client_id

    async def disconnect(self, client_id: str):
        """Handle client disconnection."""
        if client_id in self.active_connections:
            client = self.active_connections[client_id]

            # Remove from all subscriptions
            for topic in client.subscriptions:
                self.subscriptions[topic].discard(client_id)

            del self.active_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")

    async def send_personal_message(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client."""
        if client_id in self.active_connections:
            client = self.active_connections[client_id]
            try:
                await client.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                await self.disconnect(client_id)

    async def broadcast(
        self,
        message: Dict[str, Any],
        topic: Optional[str] = None,
        exclude: Optional[List[str]] = None,
    ):
        """Broadcast message to clients."""
        exclude = exclude or []

        if topic:
            # Send to subscribed clients
            for client_id in self.subscriptions.get(topic, set()):
                if client_id not in exclude and client_id in self.active_connections:
                    await self.send_personal_message(client_id, message)
        else:
            # Send to all clients
            for client_id in self.active_connections:
                if client_id not in exclude:
                    await self.send_personal_message(client_id, message)

    async def subscribe(self, client_id: str, topic: str):
        """Subscribe client to a topic."""
        if client_id in self.active_connections:
            client = self.active_connections[client_id]
            client.subscriptions.add(topic)
            self.subscriptions[topic].add(client_id)

            await self.send_personal_message(
                client_id,
                {
                    "type": MessageType.SUBSCRIBE.value,
                    "topic": topic,
                    "success": True,
                }
            )

    async def unsubscribe(self, client_id: str, topic: str):
        """Unsubscribe client from a topic."""
        if client_id in self.active_connections:
            client = self.active_connections[client_id]
            client.subscriptions.discard(topic)
            self.subscriptions[topic].discard(client_id)

            await self.send_personal_message(
                client_id,
                {
                    "type": MessageType.UNSUBSCRIBE.value,
                    "topic": topic,
                    "success": True,
                }
            )

    async def handle_message(self, client_id: str, message: Dict[str, Any]):
        """Handle incoming message from client."""
        msg_type = message.get("type")

        if msg_type == MessageType.SUBSCRIBE.value:
            topic = message.get("topic")
            if topic:
                await self.subscribe(client_id, topic)

        elif msg_type == MessageType.UNSUBSCRIBE.value:
            topic = message.get("topic")
            if topic:
                await self.unsubscribe(client_id, topic)

        elif msg_type == MessageType.HEARTBEAT.value:
            # Update last active time
            if client_id in self.active_connections:
                self.active_connections[client_id].last_active = datetime.utcnow()
                await self.send_personal_message(
                    client_id,
                    {"type": "heartbeat_ack", "timestamp": datetime.utcnow().isoformat()}
                )

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "topics": {
                topic: len(clients) for topic, clients in self.subscriptions.items()
            },
        }


class MarketDataBroadcaster:
    """Broadcasts market data to connected clients."""

    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def push_quote(self, quote: Dict[str, Any]):
        """Push real-time quote to subscribers."""
        topic = f"quote:{quote.get('code', 'all')}"
        await self.manager.broadcast(
            {
                "type": MessageType.MARKET_QUOTE.value,
                "data": quote,
                "timestamp": datetime.utcnow().isoformat(),
            },
            topic=topic,
        )

    async def push_price_alert(
        self,
        code: str,
        current_price: float,
        target_price: float,
        alert_type: str,
    ):
        """Push price alert to client subscribed to this stock."""
        topic = f"quote:{code}"
        await self.manager.broadcast(
            {
                "type": MessageType.MARKET_ALERT.value,
                "data": {
                    "code": code,
                    "current_price": current_price,
                    "target_price": target_price,
                    "alert_type": alert_type,
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
            topic=topic,
        )

    async def push_price_change(
        self, code: str, old_price: float, new_price: float
    ):
        """Push significant price change."""
        topic = f"quote:{code}"
        change_pct = (new_price - old_price) / old_price * 100 if old_price > 0 else 0

        await self.manager.broadcast(
            {
                "type": MessageType.PRICE_CHANGE.value,
                "data": {
                    "code": code,
                    "old_price": old_price,
                    "new_price": new_price,
                    "change_pct": change_pct,
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
            topic=topic,
        )

    async def push_market_summary(self, summary: Dict[str, Any]):
        """Push market summary to all clients."""
        await self.manager.broadcast(
            {
                "type": "market_summary",
                "data": summary,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


class AlertManager:
    """Manages price alerts and notifications."""

    def __init__(self, broadcaster: MarketDataBroadcaster):
        self.broadcaster = broadcaster
        self.alerts: Dict[str, List[Dict]] = defaultdict(list)

    def add_alert(
        self,
        client_id: str,
        code: str,
        target_price: float,
        alert_type: str = "above",
    ):
        """Add a new price alert."""
        self.alerts[code].append({
            "client_id": client_id,
            "target_price": target_price,
            "alert_type": alert_type,
            "created_at": datetime.utcnow().isoformat(),
        })

    def remove_alert(self, client_id: str, code: str, target_price: float):
        """Remove an alert."""
        alerts = self.alerts.get(code, [])
        self.alerts[code] = [
            a for a in alerts
            if not (a["client_id"] == client_id and a["target_price"] == target_price)
        ]

    async def check_price(self, code: str, current_price: float):
        """Check if any alerts should trigger."""
        triggered = []

        for alert in self.alerts.get(code, []):
            target = alert["target_price"]
            alert_type = alert["alert_type"]

            should_trigger = (
                (alert_type == "above" and current_price >= target) or
                (alert_type == "below" and current_price <= target)
            )

            if should_trigger:
                triggered.append(alert)
                await self.broadcaster.push_price_alert(
                    code, current_price, target, alert_type
                )

        # Remove triggered alerts
        for alert in triggered:
            self.alerts[code].remove(alert)

        return triggered

    def get_alerts(self, code: Optional[str] = None) -> List[Dict]:
        """Get alerts for a specific code or all."""
        if code:
            return self.alerts.get(code, [])
        return [alert for alerts in self.alerts.values() for alert in alerts]


# Global instances
ws_manager = ConnectionManager()
market_broadcaster = MarketDataBroadcaster(ws_manager)
alert_manager = AlertManager(market_broadcaster)


async def handle_websocket_client(websocket: WebSocket, client_id: str):
    """Handle individual WebSocket client."""
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await ws_manager.handle_message(client_id, message)

    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)
    except json.JSONDecodeError:
        await ws_manager.send_personal_message(
            client_id,
            {"type": MessageType.ERROR.value, "message": "Invalid JSON format"},
        )
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(client_id)


async def broadcast_market_update(quotes: List[Dict[str, Any]]):
    """Broadcast market data update."""
    for quote in quotes:
        await market_broadcaster.push_quote(quote)
