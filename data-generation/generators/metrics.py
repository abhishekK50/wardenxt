"""
Metrics Generator - Creates time-series system metrics
Simulates CPU, memory, network, and application metrics
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass, asdict


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: str
    service: str
    host: str
    metrics: Dict[str, float]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class MetricsGenerator:
    """Generates realistic system and application metrics"""
    
    def __init__(self, start_time: datetime, service: str = "payment-api"):
        """Initialize metrics generator
        
        Args:
            start_time: When to start generating metrics
            service: Service name
        """
        self.start_time = start_time
        self.service = service
        
    def generate_normal_metrics(
        self,
        duration_minutes: int,
        interval_seconds: int = 60
    ) -> List[MetricPoint]:
        """Generate normal operation metrics
        
        Args:
            duration_minutes: How long to generate metrics for
            interval_seconds: Time between metric points
            
        Returns:
            List of metric points
        """
        metrics = []
        num_points = int((duration_minutes * 60) / interval_seconds)
        
        # Baseline values for normal operation
        base_cpu = 25.0  # 25% CPU
        base_memory = 1200  # 1.2GB memory
        base_requests = 150  # 150 req/sec
        base_latency = 45  # 45ms p99
        
        for i in range(num_points):
            timestamp = self.start_time + timedelta(seconds=i * interval_seconds)
            
            # Add natural variation
            cpu = base_cpu + random.uniform(-5, 5)
            memory = base_memory + random.uniform(-100, 100)
            requests = base_requests + random.uniform(-20, 20)
            latency = base_latency + random.uniform(-10, 15)
            error_rate = random.uniform(0, 0.005)  # 0-0.5% errors
            
            metric = MetricPoint(
                timestamp=timestamp.isoformat() + "Z",
                service=self.service,
                host=f"prod-app-{random.randint(1, 3):02d}",
                metrics={
                    "cpu_percent": round(cpu, 2),
                    "memory_mb": round(memory, 2),
                    "requests_per_sec": round(requests, 2),
                    "error_rate": round(error_rate, 4),
                    "latency_p50_ms": round(latency * 0.6, 2),
                    "latency_p95_ms": round(latency * 0.9, 2),
                    "latency_p99_ms": round(latency, 2),
                    "active_connections": random.randint(45, 55),
                    "connection_pool_usage": random.uniform(0.4, 0.6)
                }
            )
            
            metrics.append(metric)
            
        return metrics
    
    def generate_incident_metrics(
        self,
        incident_type: str,
        duration_minutes: int,
        phases: List[Dict[str, float]],
        interval_seconds: int = 60
    ) -> List[MetricPoint]:
        """Generate metrics during an incident
        
        Args:
            incident_type: Type of incident (connection, memory, cpu)
            duration_minutes: Duration of incident
            phases: List of metric adjustments per phase
            interval_seconds: Time between points
            
        Returns:
            List of metric points showing incident
        """
        metrics = []
        num_points = int((duration_minutes * 60) / interval_seconds)
        points_per_phase = num_points // len(phases)
        
        for phase_idx, phase_config in enumerate(phases):
            phase_start = phase_idx * points_per_phase
            phase_end = (phase_idx + 1) * points_per_phase if phase_idx < len(phases) - 1 else num_points
            
            for i in range(phase_start, phase_end):
                timestamp = self.start_time + timedelta(seconds=i * interval_seconds)
                
                # Interpolate within phase
                phase_progress = (i - phase_start) / (phase_end - phase_start)
                
                # Build metrics based on incident type and phase
                if incident_type == "connection_pool":
                    metrics_data = self._connection_pool_metrics(phase_config, phase_progress)
                elif incident_type == "memory_leak":
                    metrics_data = self._memory_leak_metrics(phase_config, phase_progress)
                elif incident_type == "cpu_spike":
                    metrics_data = self._cpu_spike_metrics(phase_config, phase_progress)
                elif incident_type == "bmr_recovery":
                    metrics_data = self._bmr_recovery_metrics(phase_config, phase_progress)
                else:
                    metrics_data = self._generic_degradation_metrics(phase_config, phase_progress)
                
                metric = MetricPoint(
                    timestamp=timestamp.isoformat() + "Z",
                    service=self.service,
                    host=f"prod-app-{random.randint(1, 3):02d}",
                    metrics=metrics_data
                )
                
                metrics.append(metric)
        
        return metrics
    
    def _connection_pool_metrics(
        self,
        config: Dict[str, float],
        progress: float
    ) -> Dict[str, float]:
        """Metrics for connection pool exhaustion"""
        base_connections = config.get("active_connections", 50)
        max_connections = config.get("max_connections", 100)
        pool_usage = config.get("pool_usage", 0.5)
        
        # Connection pool fills up
        connections = int(base_connections + (max_connections - base_connections) * pool_usage)
        
        return {
            "cpu_percent": round(config.get("cpu", 30) + random.uniform(-3, 3), 2),
            "memory_mb": round(config.get("memory", 1800) + random.uniform(-50, 50), 2),
            "requests_per_sec": round(config.get("requests", 120) + random.uniform(-10, 10), 2),
            "error_rate": round(config.get("error_rate", 0.05), 4),
            "latency_p50_ms": round(config.get("latency", 200) * 0.6, 2),
            "latency_p95_ms": round(config.get("latency", 200) * 0.9, 2),
            "latency_p99_ms": round(config.get("latency", 200), 2),
            "active_connections": connections,
            "connection_pool_usage": round(connections / max_connections, 3)
        }
    
    def _memory_leak_metrics(
        self,
        config: Dict[str, float],
        progress: float
    ) -> Dict[str, float]:
        """Metrics for memory leak"""
        base_memory = config.get("memory_base", 1200)
        memory_growth = config.get("memory_growth", 1000)
        
        # Memory grows linearly
        memory = base_memory + (memory_growth * progress)
        
        return {
            "cpu_percent": round(config.get("cpu", 35) + random.uniform(-5, 5), 2),
            "memory_mb": round(memory + random.uniform(-30, 30), 2),
            "requests_per_sec": round(config.get("requests", 100) + random.uniform(-15, 15), 2),
            "error_rate": round(config.get("error_rate", 0.03), 4),
            "latency_p50_ms": round(config.get("latency", 150) * 0.6, 2),
            "latency_p95_ms": round(config.get("latency", 150) * 0.9, 2),
            "latency_p99_ms": round(config.get("latency", 150), 2),
            "gc_count": int(20 + progress * 30),  # GC activity increases
            "gc_pause_ms": round(50 + progress * 200, 2)
        }
    
    def _cpu_spike_metrics(
        self,
        config: Dict[str, float],
        progress: float
    ) -> Dict[str, float]:
        """Metrics for CPU spike"""
        return {
            "cpu_percent": round(config.get("cpu", 80) + random.uniform(-5, 10), 2),
            "memory_mb": round(config.get("memory", 1500) + random.uniform(-50, 50), 2),
            "requests_per_sec": round(config.get("requests", 80) + random.uniform(-10, 10), 2),
            "error_rate": round(config.get("error_rate", 0.02), 4),
            "latency_p50_ms": round(config.get("latency", 300) * 0.6, 2),
            "latency_p95_ms": round(config.get("latency", 300) * 0.9, 2),
            "latency_p99_ms": round(config.get("latency", 300), 2),
            "thread_count": int(config.get("threads", 100)),
            "queue_depth": int(config.get("queue", 50))
        }
    
    def _bmr_recovery_metrics(
        self,
        config: Dict[str, float],
        progress: float
    ) -> Dict[str, float]:
        """Metrics for BMR (Bare Metal Recovery)"""
        # During recovery, service is down or degraded
        is_recovering = config.get("recovering", False)
        
        if not is_recovering:
            # Service is down
            return {
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "requests_per_sec": 0.0,
                "error_rate": 1.0,  # 100% errors
                "latency_p99_ms": 0.0,
                "service_available": False
            }
        else:
            # Service is coming back online
            recovery_progress = progress
            return {
                "cpu_percent": round(10 + recovery_progress * 20, 2),
                "memory_mb": round(500 + recovery_progress * 700, 2),
                "requests_per_sec": round(recovery_progress * 150, 2),
                "error_rate": round((1 - recovery_progress) * 0.5, 4),
                "latency_p99_ms": round(1000 - recovery_progress * 900, 2),
                "service_available": recovery_progress > 0.8
            }
    
    def _generic_degradation_metrics(
        self,
        config: Dict[str, float],
        progress: float
    ) -> Dict[str, float]:
        """Generic degraded performance metrics"""
        return {
            "cpu_percent": round(config.get("cpu", 50) + random.uniform(-5, 5), 2),
            "memory_mb": round(config.get("memory", 1600) + random.uniform(-50, 50), 2),
            "requests_per_sec": round(config.get("requests", 100) + random.uniform(-10, 10), 2),
            "error_rate": round(config.get("error_rate", 0.08), 4),
            "latency_p50_ms": round(config.get("latency", 250) * 0.6, 2),
            "latency_p95_ms": round(config.get("latency", 250) * 0.9, 2),
            "latency_p99_ms": round(config.get("latency", 250), 2)
        }