"""
Log Generator - Creates realistic application logs
Generates logs with different severity levels and patterns
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """Log severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Single log entry structure"""
    timestamp: str
    level: str
    service: str
    host: str
    message: str
    thread_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class LogGenerator:
    """Generates realistic application logs for incidents"""
    
    # Service names for different microservices
    SERVICES = [
        "payment-api",
        "user-service", 
        "order-processing",
        "inventory-service",
        "notification-service",
        "auth-service",
        "database-service",
        "cache-service"
    ]
    
    # Host naming patterns
    HOST_PREFIX = ["prod-app", "prod-db", "prod-cache", "prod-lb"]
    
    # Common error messages
    ERROR_MESSAGES = {
        "connection": [
            "Connection pool exhausted: timeout acquiring connection",
            "Failed to connect to database: connection refused",
            "Connection timeout after 30000ms",
            "Too many connections: max pool size reached",
            "Connection reset by peer"
        ],
        "memory": [
            "OutOfMemoryError: Java heap space",
            "Memory allocation failed: insufficient memory",
            "GC overhead limit exceeded",
            "Native memory allocation failed",
            "Memory leak detected: heap growing unbounded"
        ],
        "timeout": [
            "Request timeout after 5000ms",
            "Read timeout: no data received",
            "Gateway timeout: upstream server not responding",
            "Lock wait timeout exceeded",
            "Transaction timeout: rolling back"
        ],
        "general": [
            "Unexpected error during request processing",
            "Internal server error: null pointer exception",
            "Service unavailable: circuit breaker open",
            "Rate limit exceeded: too many requests",
            "Authentication failed: invalid token"
        ]
    }
    
    # Normal operation messages
    INFO_MESSAGES = [
        "Request processed successfully",
        "User authentication successful",
        "Database query executed",
        "Cache hit for key",
        "API endpoint called",
        "Background job completed",
        "Health check passed",
        "Configuration reloaded"
    ]
    
    def __init__(self, start_time: datetime, service: str = "payment-api"):
        """Initialize log generator
        
        Args:
            start_time: When to start generating logs
            service: Primary service name
        """
        self.start_time = start_time
        self.service = service
        self.current_time = start_time
        
    def generate_normal_logs(
        self,
        duration_minutes: int,
        entries_per_minute: int = 10
    ) -> List[LogEntry]:
        """Generate normal operation logs
        
        Args:
            duration_minutes: How long to generate logs for
            entries_per_minute: Number of log entries per minute
            
        Returns:
            List of log entries
        """
        logs = []
        total_entries = duration_minutes * entries_per_minute
        
        for i in range(total_entries):
            # Calculate timestamp
            seconds_offset = (i / entries_per_minute) * 60
            log_time = self.start_time + timedelta(seconds=seconds_offset)
            
            # Mostly INFO, some DEBUG, rare WARN
            level_choice = random.choices(
                [LogLevel.INFO, LogLevel.DEBUG, LogLevel.WARN],
                weights=[0.8, 0.15, 0.05]
            )[0]
            
            log = LogEntry(
                timestamp=log_time.isoformat() + "Z",
                level=level_choice.value,
                service=self.service,
                host=self._random_host(),
                message=random.choice(self.INFO_MESSAGES),
                thread_id=f"worker-{random.randint(1, 20)}",
                request_id=self._generate_request_id(),
                user_id=f"user-{random.randint(1000, 9999)}"
            )
            
            logs.append(log)
            
        return logs
    
    def generate_incident_logs(
        self,
        incident_type: str,
        duration_minutes: int,
        severity_progression: List[float]
    ) -> List[LogEntry]:
        """Generate logs during an incident
        
        Args:
            incident_type: Type of incident (connection, memory, timeout)
            duration_minutes: Duration of incident
            severity_progression: List of error rates (0.0-1.0) for each phase
            
        Returns:
            List of log entries showing incident progression
        """
        logs = []
        entries_per_minute = 20  # More logs during incidents
        
        # Get relevant error messages
        error_messages = self.ERROR_MESSAGES.get(
            incident_type,
            self.ERROR_MESSAGES["general"]
        )
        
        phase_duration = duration_minutes / len(severity_progression)
        
        for phase_idx, error_rate in enumerate(severity_progression):
            phase_start = phase_idx * phase_duration
            phase_end = (phase_idx + 1) * phase_duration
            phase_entries = int(phase_duration * entries_per_minute)
            
            for i in range(phase_entries):
                # Calculate timestamp
                minutes_into_phase = (i / phase_entries) * phase_duration
                total_minutes = phase_start + minutes_into_phase
                log_time = self.start_time + timedelta(minutes=total_minutes)
                
                # Determine if this should be an error based on error_rate
                is_error = random.random() < error_rate
                
                if is_error:
                    level = random.choice([LogLevel.ERROR, LogLevel.CRITICAL])
                    message = random.choice(error_messages)
                    
                    # Add stack trace for errors
                    stack_trace = self._generate_stack_trace() if level == LogLevel.ERROR else None
                    
                    log = LogEntry(
                        timestamp=log_time.isoformat() + "Z",
                        level=level.value,
                        service=self.service,
                        host=self._random_host(),
                        message=message,
                        thread_id=f"worker-{random.randint(1, 20)}",
                        request_id=self._generate_request_id(),
                        stack_trace=stack_trace,
                        metadata={
                            "error_code": random.choice(["500", "503", "504"]),
                            "retry_count": random.randint(0, 3)
                        }
                    )
                else:
                    # Normal log entry
                    log = LogEntry(
                        timestamp=log_time.isoformat() + "Z",
                        level=LogLevel.INFO.value,
                        service=self.service,
                        host=self._random_host(),
                        message=random.choice(self.INFO_MESSAGES),
                        thread_id=f"worker-{random.randint(1, 20)}",
                        request_id=self._generate_request_id()
                    )
                
                logs.append(log)
        
        return logs
    
    def _random_host(self) -> str:
        """Generate random host name"""
        prefix = random.choice(self.HOST_PREFIX)
        number = random.randint(1, 5)
        return f"{prefix}-{number:02d}"
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return f"req-{uuid.uuid4().hex[:12]}"
    
    def _generate_stack_trace(self) -> str:
        """Generate realistic stack trace"""
        traces = [
            "  at com.wardenxt.payment.PaymentService.processPayment(PaymentService.java:142)",
            "  at com.wardenxt.api.PaymentController.handleRequest(PaymentController.java:89)",
            "  at com.wardenxt.db.ConnectionPool.acquireConnection(ConnectionPool.java:234)"
        ]
        return "\n".join(traces)