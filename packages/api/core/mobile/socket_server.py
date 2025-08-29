import socketio
import logging
from typing import Dict, Any
from datetime import datetime
import json
import asyncio
import aiohttp
from aiohttp import web

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NEURA.SocketServer")

class NeuraSocketServer:
    """Socket.io server for real-time mobile communication"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.sio = socketio.AsyncServer(
            async_mode='aiohttp',
            cors_allowed_origins='*'
        )
        self.app = web.Application()
        self.sio.attach(self.app)
        self.connected_clients: Dict[str, Dict] = {}
        
        # Register event handlers
        self.setup_event_handlers()
        
    def setup_event_handlers(self):
        """Setup Socket.io event handlers"""
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection"""
            logger.info(f"Client connected: {sid}")
            self.connected_clients[sid] = {
                "connected_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat()
            }
            await self.sio.emit('welcome', {'status': 'connected'}, room=sid)
            
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            logger.info(f"Client disconnected: {sid}")
            if sid in self.connected_clients:
                del self.connected_clients[sid]
                
        @self.sio.event
        async def get_system_status(sid):
            """Get current system status"""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.api_url}/health") as response:
                        status = await response.json()
                        await self.sio.emit('system_status', status, room=sid)
            except Exception as e:
                logger.error(f"Error getting system status: {str(e)}")
                await self.sio.emit('error', {'message': str(e)}, room=sid)
                
        @self.sio.event
        async def get_agents(sid):
            """Get list of agents"""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.api_url}/agents") as response:
                        agents = await response.json()
                        await self.sio.emit('agents_list', agents, room=sid)
            except Exception as e:
                logger.error(f"Error getting agents: {str(e)}")
                await self.sio.emit('error', {'message': str(e)}, room=sid)
                
        @self.sio.event
        async def create_task(sid, data):
            """Create a new task"""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_url}/tasks",
                        json=data
                    ) as response:
                        result = await response.json()
                        await self.sio.emit('task_created', result, room=sid)
            except Exception as e:
                logger.error(f"Error creating task: {str(e)}")
                await self.sio.emit('error', {'message': str(e)}, room=sid)
                
        @self.sio.event
        async def subscribe_updates(sid, data):
            """Subscribe to real-time updates"""
            try:
                update_type = data.get('type', 'all')
                self.connected_clients[sid]['subscriptions'] = update_type
                await self.sio.emit(
                    'subscribed',
                    {'type': update_type},
                    room=sid
                )
            except Exception as e:
                logger.error(f"Error in subscription: {str(e)}")
                await self.sio.emit('error', {'message': str(e)}, room=sid)
                
    async def broadcast_update(self, event: str, data: Dict):
        """Broadcast updates to all connected clients"""
        try:
            await self.sio.emit(event, data)
            logger.info(f"Broadcasted {event} to all clients")
        except Exception as e:
            logger.error(f"Error broadcasting update: {str(e)}")
            
    async def start_server(self, host: str = '0.0.0.0', port: int = 8001):
        """Start the Socket.io server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Socket.io server running on http://{host}:{port}")
        
    async def start_update_loop(self):
        """Start periodic update loop"""
        while True:
            try:
                # Get system metrics
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.api_url}/metrics"
                    ) as response:
                        metrics = await response.json()
                        await self.broadcast_update('metrics_update', metrics)
                        
                # Wait before next update
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in update loop: {str(e)}")
                await asyncio.sleep(5)

# Example usage
if __name__ == "__main__":
    server = NeuraSocketServer()
    
    async def main():
        await server.start_server()
        await server.start_update_loop()
        
    asyncio.run(main())
