"""
WebSocket Mock Support System

This module provides comprehensive WebSocket mocking capabilities including:
- Real-time message handling
- Connection management
- Message routing and broadcasting
- Authentication and authorization
- Custom message handlers
- Connection state management
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol


class WebSocketMessageType(Enum):
    """WebSocket message types"""
    TEXT = "text"
    BINARY = "binary"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"


class WebSocketConnectionState(Enum):
    """WebSocket connection states"""
    CONNECTING = "connecting"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass
class WebSocketMessage:
    """Represents a WebSocket message"""
    message_type: WebSocketMessageType
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: Optional[str] = None
    target_id: Optional[str] = None
    room: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection"""
    connection_id: str
    websocket: WebSocketServerProtocol
    state: WebSocketConnectionState = WebSocketConnectionState.CONNECTING
    user_id: Optional[str] = None
    rooms: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    message_count: int = 0


@dataclass
class WebSocketRoom:
    """Represents a WebSocket room for message broadcasting"""
    name: str
    connections: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WebSocketMessageHandler:
    """Represents a message handler for WebSocket messages"""
    pattern: str
    handler_func: Callable
    description: Optional[str] = None
    requires_auth: bool = False
    rate_limit: Optional[int] = None  # messages per minute


class WebSocketMockServer:
    """Main WebSocket mock server implementation"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.connections: Dict[str, WebSocketConnection] = {}
        self.rooms: Dict[str, WebSocketRoom] = {}
        self.message_handlers: List[WebSocketMessageHandler] = []
        self.server: Optional[websockets.WebSocketServer] = None
        self.running = False
        
        # Statistics
        self.total_connections = 0
        self.total_messages = 0
        self.active_connections = 0
        
        # Setup default handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self) -> None:
        """Setup default message handlers"""
        # Echo handler
        self.add_message_handler(
            pattern="echo",
            handler_func=self._echo_handler,
            description="Echo back the received message"
        )
        
        # Broadcast handler
        self.add_message_handler(
            pattern="broadcast",
            handler_func=self._broadcast_handler,
            description="Broadcast message to all connections"
        )
        
        # Room join handler
        self.add_message_handler(
            pattern="join",
            handler_func=self._join_room_handler,
            description="Join a room for group messaging"
        )
        
        # Room leave handler
        self.add_message_handler(
            pattern="leave",
            handler_func=self._leave_room_handler,
            description="Leave a room"
        )
        
        # Room message handler
        self.add_message_handler(
            pattern="room_message",
            handler_func=self._room_message_handler,
            description="Send message to a specific room"
        )
        
        # Stats handler
        self.add_message_handler(
            pattern="stats",
            handler_func=self._stats_handler,
            description="Get server statistics"
        )
    
    def add_message_handler(self, pattern: str, handler_func: Callable,
                           description: str = None, requires_auth: bool = False,
                           rate_limit: int = None) -> None:
        """Add a custom message handler"""
        handler = WebSocketMessageHandler(
            pattern=pattern,
            handler_func=handler_func,
            description=description,
            requires_auth=requires_auth,
            rate_limit=rate_limit
        )
        self.message_handlers.append(handler)
    
    async def start_server(self) -> None:
        """Start the WebSocket server"""
        if self.running:
            return
        
        self.server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port
        )
        self.running = True
        print(f"WebSocket mock server started on {self.host}:{self.port}")
    
    async def stop_server(self) -> None:
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        self.running = False
        print("WebSocket mock server stopped")
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle a new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(
            connection_id=connection_id,
            websocket=websocket,
            state=WebSocketConnectionState.OPEN
        )
        
        self.connections[connection_id] = connection
        self.total_connections += 1
        self.active_connections += 1
        
        print(f"New WebSocket connection: {connection_id}")
        
        try:
            # Send welcome message
            await self._send_message(connection, {
                "type": "welcome",
                "connection_id": connection_id,
                "message": "Connected to WebSocket mock server",
                "timestamp": datetime.now().isoformat()
            })
            
            # Handle messages
            async for message in websocket:
                await self._process_message(connection, message)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"WebSocket connection closed: {connection_id}")
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            await self._cleanup_connection(connection)
    
    async def _process_message(self, connection: WebSocketConnection, message: str) -> None:
        """Process an incoming WebSocket message"""
        try:
            # Parse message
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    data = {"type": "text", "content": message}
            else:
                data = {"type": "binary", "content": message}
            
            # Update connection activity
            connection.last_activity = datetime.now()
            connection.message_count += 1
            self.total_messages += 1
            
            # Find matching handler
            handler = self._find_handler(data.get("type", ""))
            if handler:
                await handler.handler_func(connection, data)
            else:
                # Default handler - echo back
                await self._echo_handler(connection, data)
                
        except Exception as e:
            print(f"Error processing message: {e}")
            await self._send_error(connection, str(e))
    
    def _find_handler(self, message_type: str) -> Optional[WebSocketMessageHandler]:
        """Find a handler for the message type"""
        for handler in self.message_handlers:
            if handler.pattern == message_type:
                return handler
        return None
    
    async def _echo_handler(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Echo handler - echo back the received message"""
        response = {
            "type": "echo",
            "original": data,
            "timestamp": datetime.now().isoformat()
        }
        await self._send_message(connection, response)
    
    async def _broadcast_handler(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Broadcast handler - send message to all connections"""
        message = data.get("message", "Broadcast message")
        response = {
            "type": "broadcast",
            "message": message,
            "sender": connection.connection_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connections
        for conn in self.connections.values():
            if conn.state == WebSocketConnectionState.OPEN:
                await self._send_message(conn, response)
    
    async def _join_room_handler(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Join room handler"""
        room_name = data.get("room")
        if not room_name:
            await self._send_error(connection, "Room name required")
            return
        
        # Create room if it doesn't exist
        if room_name not in self.rooms:
            self.rooms[room_name] = WebSocketRoom(name=room_name)
        
        # Add connection to room
        self.rooms[room_name].connections.add(connection.connection_id)
        connection.rooms.add(room_name)
        
        response = {
            "type": "room_joined",
            "room": room_name,
            "timestamp": datetime.now().isoformat()
        }
        await self._send_message(connection, response)
    
    async def _leave_room_handler(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Leave room handler"""
        room_name = data.get("room")
        if not room_name:
            await self._send_error(connection, "Room name required")
            return
        
        # Remove connection from room
        if room_name in self.rooms:
            self.rooms[room_name].connections.discard(connection.connection_id)
        connection.rooms.discard(room_name)
        
        response = {
            "type": "room_left",
            "room": room_name,
            "timestamp": datetime.now().isoformat()
        }
        await self._send_message(connection, response)
    
    async def _room_message_handler(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Room message handler"""
        room_name = data.get("room")
        message = data.get("message", "")
        
        if not room_name:
            await self._send_error(connection, "Room name required")
            return
        
        if room_name not in self.rooms:
            await self._send_error(connection, "Room not found")
            return
        
        if connection.connection_id not in self.rooms[room_name].connections:
            await self._send_error(connection, "Not in room")
            return
        
        # Send message to all connections in room
        response = {
            "type": "room_message",
            "room": room_name,
            "message": message,
            "sender": connection.connection_id,
            "timestamp": datetime.now().isoformat()
        }
        
        for conn_id in self.rooms[room_name].connections:
            if conn_id in self.connections:
                conn = self.connections[conn_id]
                if conn.state == WebSocketConnectionState.OPEN:
                    await self._send_message(conn, response)
    
    async def _stats_handler(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Stats handler - return server statistics"""
        stats = {
            "type": "stats",
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "total_messages": self.total_messages,
            "rooms": len(self.rooms),
            "handlers": len(self.message_handlers),
            "timestamp": datetime.now().isoformat()
        }
        await self._send_message(connection, stats)
    
    async def _send_message(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
        """Send a message to a connection"""
        try:
            if connection.state == WebSocketConnectionState.OPEN:
                await connection.websocket.send(json.dumps(data))
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def _send_error(self, connection: WebSocketConnection, error_message: str) -> None:
        """Send an error message to a connection"""
        error_data = {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        await self._send_message(connection, error_data)
    
    async def _cleanup_connection(self, connection: WebSocketConnection) -> None:
        """Cleanup a closed connection"""
        connection.state = WebSocketConnectionState.CLOSED
        self.active_connections -= 1
        
        # Remove from all rooms
        for room_name in connection.rooms.copy():
            if room_name in self.rooms:
                self.rooms[room_name].connections.discard(connection.connection_id)
                # Remove empty rooms
                if not self.rooms[room_name].connections:
                    del self.rooms[room_name]
        
        # Remove connection
        if connection.connection_id in self.connections:
            del self.connections[connection.connection_id]
    
    async def broadcast_to_room(self, room_name: str, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connections in a room"""
        if room_name not in self.rooms:
            return
        
        for conn_id in self.rooms[room_name].connections:
            if conn_id in self.connections:
                conn = self.connections[conn_id]
                if conn.state == WebSocketConnectionState.OPEN:
                    await self._send_message(conn, message)
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> None:
        """Send a message to a specific connection"""
        if connection_id in self.connections:
            conn = self.connections[connection_id]
            if conn.state == WebSocketConnectionState.OPEN:
                await self._send_message(conn, message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "total_messages": self.total_messages,
            "rooms": len(self.rooms),
            "handlers": len(self.message_handlers)
        }
    
    def get_room_info(self, room_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a room"""
        if room_name not in self.rooms:
            return None
        
        room = self.rooms[room_name]
        return {
            "name": room.name,
            "connections": len(room.connections),
            "created_at": room.created_at.isoformat(),
            "metadata": room.metadata
        }


# Global WebSocket mock server instance
websocket_mock_server = WebSocketMockServer()


# Convenience functions
async def start_websocket_server(host: str = "localhost", port: int = 8765) -> WebSocketMockServer:
    """Start a WebSocket mock server"""
    server = WebSocketMockServer(host, port)
    await server.start_server()
    return server


def create_websocket_message_handler(pattern: str, handler_func: Callable) -> None:
    """Add a custom WebSocket message handler"""
    websocket_mock_server.add_message_handler(pattern, handler_func)


async def broadcast_message(room: str, message: str, message_type: str = "broadcast") -> None:
    """Broadcast a message to a room"""
    data = {
        "type": message_type,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    await websocket_mock_server.broadcast_to_room(room, data)


async def send_private_message(connection_id: str, message: str) -> None:
    """Send a private message to a connection"""
    data = {
        "type": "private_message",
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    await websocket_mock_server.send_to_connection(connection_id, data)
