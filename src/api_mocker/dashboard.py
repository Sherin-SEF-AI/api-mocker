"""
Web dashboard for api-mocker analytics and monitoring.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import aiofiles
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from .analytics import AnalyticsManager

class DashboardManager:
    """Manages the web dashboard for analytics visualization."""
    
    def __init__(self, analytics_manager: AnalyticsManager, port: int = 8080):
        self.analytics = analytics_manager
        self.port = port
        self.app = FastAPI(title="API-Mocker Dashboard", version="1.0.0")
        self.active_connections: List[WebSocket] = []
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup dashboard routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Main dashboard page."""
            return self._get_dashboard_html()
            
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get current server metrics."""
            return self.analytics.get_server_metrics()
            
        @self.app.get("/api/analytics")
        async def get_analytics(hours: int = 24):
            """Get analytics summary."""
            return self.analytics.get_analytics_summary(hours)
            
        @self.app.get("/api/endpoints")
        async def get_endpoints():
            """Get endpoint statistics."""
            summary = self.analytics.get_analytics_summary(24)
            return {
                "popular_endpoints": summary["popular_endpoints"],
                "slowest_endpoints": summary["slowest_endpoints"]
            }
            
        @self.app.get("/api/requests")
        async def get_recent_requests(limit: int = 50):
            """Get recent requests."""
            # TODO: Implement recent requests endpoint
            return {"requests": []}
            
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.active_connections.append(websocket)
            try:
                while True:
                    # Send real-time metrics every 5 seconds
                    metrics = self.analytics.get_server_metrics()
                    await websocket.send_text(json.dumps({
                        "type": "metrics",
                        "data": {
                            "uptime": metrics.uptime_seconds,
                            "total_requests": metrics.total_requests,
                            "requests_per_minute": metrics.requests_per_minute,
                            "average_response_time": metrics.average_response_time_ms,
                            "error_rate": metrics.error_rate,
                            "memory_usage": metrics.memory_usage_mb,
                            "cpu_usage": metrics.cpu_usage_percent
                        }
                    }))
                    await asyncio.sleep(5)
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
                
    def _get_dashboard_html(self) -> str:
        """Generate the dashboard HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API-Mocker Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 20px;
        }
        .metric-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            color: #6c757d;
            margin-top: 5px;
        }
        .charts-section {
            padding: 20px;
        }
        .chart-container {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .chart-title {
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #333;
        }
        .endpoints-list {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
        }
        .endpoint-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }
        .endpoint-item:last-child {
            border-bottom: none;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .status-healthy { background: #28a745; }
        .status-warning { background: #ffc107; }
        .status-error { background: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 API-Mocker Dashboard</h1>
            <p>Real-time analytics and monitoring</p>
        </div>
        
        <div class="metrics-grid" id="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="uptime">--</div>
                <div class="metric-label">Uptime</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="total-requests">--</div>
                <div class="metric-label">Total Requests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="requests-per-minute">--</div>
                <div class="metric-label">Requests/Min</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="avg-response-time">--</div>
                <div class="metric-label">Avg Response Time (ms)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="error-rate">--</div>
                <div class="metric-label">Error Rate (%)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="memory-usage">--</div>
                <div class="metric-label">Memory Usage (%)</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">Request Methods Distribution</div>
                <canvas id="methods-chart" width="400" height="200"></canvas>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">Status Codes Distribution</div>
                <canvas id="status-chart" width="400" height="200"></canvas>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">Most Popular Endpoints</div>
                <div id="popular-endpoints" class="endpoints-list"></div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">Slowest Endpoints</div>
                <div id="slowest-endpoints" class="endpoints-list"></div>
            </div>
        </div>
    </div>

    <script>
        // Initialize charts
        const methodsChart = new Chart(document.getElementById('methods-chart'), {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        const statusChart = new Chart(document.getElementById('status-chart'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Requests',
                    data: [],
                    backgroundColor: '#36A2EB'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // WebSocket connection for real-time updates
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'metrics') {
                updateMetrics(data.data);
            }
        };

        function updateMetrics(metrics) {
            document.getElementById('uptime').textContent = formatUptime(metrics.uptime);
            document.getElementById('total-requests').textContent = metrics.total_requests;
            document.getElementById('requests-per-minute').textContent = metrics.requests_per_minute.toFixed(1);
            document.getElementById('avg-response-time').textContent = metrics.average_response_time.toFixed(1);
            document.getElementById('error-rate').textContent = metrics.error_rate.toFixed(1);
            document.getElementById('memory-usage').textContent = metrics.memory_usage.toFixed(1);
        }

        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }

        // Load initial data
        async function loadInitialData() {
            try {
                const [analytics, endpoints] = await Promise.all([
                    fetch('/api/analytics').then(r => r.json()),
                    fetch('/api/endpoints').then(r => r.json())
                ]);

                // Update methods chart
                methodsChart.data.labels = Object.keys(analytics.methods);
                methodsChart.data.datasets[0].data = Object.values(analytics.methods);
                methodsChart.update();

                // Update status chart
                statusChart.data.labels = Object.keys(analytics.status_codes);
                statusChart.data.datasets[0].data = Object.values(analytics.status_codes);
                statusChart.update();

                // Update endpoints lists
                updateEndpointsList('popular-endpoints', analytics.popular_endpoints);
                updateEndpointsList('slowest-endpoints', analytics.slowest_endpoints);
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }

        function updateEndpointsList(elementId, endpoints) {
            const container = document.getElementById(elementId);
            container.innerHTML = '';
            
            Object.entries(endpoints).forEach(([endpoint, value]) => {
                const item = document.createElement('div');
                item.className = 'endpoint-item';
                item.innerHTML = `
                    <span>${endpoint}</span>
                    <span>${typeof value === 'number' ? value.toFixed(2) : value}</span>
                `;
                container.appendChild(item);
            });
        }

        // Load data on page load
        loadInitialData();
        
        // Refresh data every 30 seconds
        setInterval(loadInitialData, 30000);
    </script>
</body>
</html>
        """
        
    def start(self, host: str = "127.0.0.1"):
        """Start the dashboard server."""
        uvicorn.run(self.app, host=host, port=self.port)
        
    async def broadcast_metrics(self):
        """Broadcast metrics to all connected WebSocket clients."""
        metrics = self.analytics.get_server_metrics()
        message = {
            "type": "metrics",
            "data": {
                "uptime": metrics.uptime_seconds,
                "total_requests": metrics.total_requests,
                "requests_per_minute": metrics.requests_per_minute,
                "average_response_time": metrics.average_response_time_ms,
                "error_rate": metrics.error_rate,
                "memory_usage": metrics.memory_usage_mb,
                "cpu_usage": metrics.cpu_usage_percent
            }
        }
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                self.active_connections.remove(connection) 