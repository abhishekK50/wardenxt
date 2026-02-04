# WardenXT Log Ingestion Architecture

## The Challenge

When an incident alert comes from PagerDuty or ServiceNow, it contains only **metadata**:
- Incident title
- Severity
- Affected service name
- Timestamp

It does NOT contain the actual logs needed for AI root cause analysis.

---

## Current Demo Implementation

```
Demo Flow:
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  Webhook    │────▶│  Incident    │────▶│  Pre-generated│
│  (metadata) │     │  Created     │     │  Synthetic    │
└─────────────┘     └──────────────┘     │  Logs (demo)  │
                                          └───────────────┘
```

**For the hackathon demo**, we use pre-generated realistic incident data that simulates what real logs would look like. This allows us to demonstrate Gemini's analysis capabilities.

---

## Production Architecture (How It Would Work)

```
Production Flow:
┌─────────────────────────────────────────────────────────────────┐
│                     LOG AGGREGATORS                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ Datadog  │  │ Splunk   │  │   ELK    │  │ CloudWatch   │    │
│  │  Logs    │  │  Logs    │  │  Stack   │  │    Logs      │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘    │
│       │             │             │               │             │
│       └─────────────┴─────────────┴───────────────┘             │
│                           │                                      │
│                     Log Source API                               │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       WARDENXT                                   │
│                                                                  │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────────┐    │
│  │ Webhook  │────▶│ Log Fetcher  │────▶│  Gemini Analysis │    │
│  │ Receiver │     │ (queries     │     │  (root cause)    │    │
│  │          │     │  aggregator) │     │                  │    │
│  └──────────┘     └──────────────┘     └──────────────────┘    │
│       │                  │                                       │
│       │           ┌──────┴──────┐                               │
│       │           │   Service   │                               │
│       └──────────▶│   Mapping   │                               │
│                   │   Config    │                               │
│                   └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Log Source Adapters (Extensible Design)

### Interface Design

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

class LogSourceAdapter(ABC):
    """Base class for log source integrations"""

    @abstractmethod
    async def fetch_logs(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
        severity_filter: Optional[List[str]] = None,
        max_logs: int = 1000
    ) -> List[Dict]:
        """Fetch logs from the source"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if source is reachable"""
        pass
```

### Datadog Adapter Example

```python
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.logs_api import LogsApi

class DatadogAdapter(LogSourceAdapter):
    def __init__(self, api_key: str, app_key: str):
        self.config = Configuration()
        self.config.api_key["apiKeyAuth"] = api_key
        self.config.api_key["appKeyAuth"] = app_key

    async def fetch_logs(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
        severity_filter: Optional[List[str]] = None,
        max_logs: int = 1000
    ) -> List[Dict]:
        with ApiClient(self.config) as client:
            api = LogsApi(client)

            # Build query
            query = f"service:{service_name}"
            if severity_filter:
                severity_str = " OR ".join(severity_filter)
                query += f" status:({severity_str})"

            response = api.list_logs(
                filter_query=query,
                filter_from=start_time,
                filter_to=end_time,
                page_limit=max_logs
            )

            return [self._transform_log(log) for log in response.data]

    def _transform_log(self, datadog_log) -> Dict:
        """Transform Datadog log to WardenXT format"""
        return {
            "timestamp": datadog_log.attributes.timestamp,
            "level": datadog_log.attributes.status.upper(),
            "service": datadog_log.attributes.service,
            "host": datadog_log.attributes.host,
            "message": datadog_log.attributes.message,
            "metadata": datadog_log.attributes.attributes
        }
```

### AWS CloudWatch Adapter Example

```python
import boto3
from datetime import datetime

class CloudWatchAdapter(LogSourceAdapter):
    def __init__(self, region: str = "us-east-1"):
        self.client = boto3.client("logs", region_name=region)
        self.log_group_mapping = {}  # service -> log group

    async def fetch_logs(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
        severity_filter: Optional[List[str]] = None,
        max_logs: int = 1000
    ) -> List[Dict]:
        log_group = self.log_group_mapping.get(
            service_name,
            f"/aws/ecs/{service_name}"
        )

        response = self.client.filter_log_events(
            logGroupName=log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            limit=max_logs
        )

        return [self._transform_log(event) for event in response["events"]]

    def _transform_log(self, cw_event) -> Dict:
        return {
            "timestamp": datetime.fromtimestamp(
                cw_event["timestamp"] / 1000
            ).isoformat() + "Z",
            "level": self._extract_level(cw_event["message"]),
            "service": "cloudwatch",
            "host": cw_event.get("logStreamName", "unknown"),
            "message": cw_event["message"]
        }
```

### Splunk Adapter Example

```python
import splunklib.client as client
import splunklib.results as results

class SplunkAdapter(LogSourceAdapter):
    def __init__(self, host: str, port: int, username: str, password: str):
        self.service = client.connect(
            host=host,
            port=port,
            username=username,
            password=password
        )

    async def fetch_logs(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime,
        severity_filter: Optional[List[str]] = None,
        max_logs: int = 1000
    ) -> List[Dict]:
        query = f"""
        search index=* sourcetype=*{service_name}*
        earliest={start_time.strftime('%Y-%m-%dT%H:%M:%S')}
        latest={end_time.strftime('%Y-%m-%dT%H:%M:%S')}
        | head {max_logs}
        """

        job = self.service.jobs.create(query)
        while not job.is_done():
            await asyncio.sleep(0.5)

        reader = results.JSONResultsReader(job.results(output_mode="json"))
        return [self._transform_log(result) for result in reader]
```

---

## Service-to-Log-Source Mapping

### Configuration

```yaml
# config/log_sources.yaml
log_sources:
  datadog:
    enabled: true
    api_key: ${DATADOG_API_KEY}
    app_key: ${DATADOG_APP_KEY}

  cloudwatch:
    enabled: true
    region: us-east-1
    log_groups:
      payment-api: /aws/ecs/payment-service
      user-service: /aws/ecs/user-service

  splunk:
    enabled: false
    host: splunk.company.com
    port: 8089

service_mapping:
  # Service name -> which log source to query
  payment-api:
    primary: datadog
    fallback: cloudwatch
  user-service:
    primary: cloudwatch
  database:
    primary: datadog
    query_filter: "service:postgresql"
```

### Runtime Selection

```python
class LogFetcher:
    def __init__(self, adapters: Dict[str, LogSourceAdapter], config: Dict):
        self.adapters = adapters
        self.service_mapping = config["service_mapping"]

    async def fetch_logs_for_incident(
        self,
        incident: Incident
    ) -> List[Dict]:
        all_logs = []

        for service in incident.summary.services_affected:
            mapping = self.service_mapping.get(service, {})
            primary = mapping.get("primary", "datadog")

            adapter = self.adapters.get(primary)
            if adapter:
                logs = await adapter.fetch_logs(
                    service_name=service,
                    start_time=incident.summary.start_time - timedelta(minutes=30),
                    end_time=incident.summary.start_time + timedelta(hours=1),
                    max_logs=500
                )
                all_logs.extend(logs)

        return all_logs
```

---

## Webhook-Triggered Log Fetch Flow

```
1. PagerDuty Alert
   └── Webhook payload: {service: "payment-api", severity: "high"}

2. WardenXT Receives Webhook
   └── Creates incident with metadata
   └── Identifies service: "payment-api"

3. Log Fetcher Activated
   └── Looks up mapping: payment-api → Datadog
   └── Queries Datadog API for logs
   └── Time range: alert_time - 30min to alert_time + 1hr

4. Logs Retrieved
   └── 1000+ log entries from Datadog
   └── Transformed to WardenXT format

5. Gemini Analysis
   └── Receives incident + fetched logs
   └── Performs root cause analysis
```

---

## For Hackathon Demo

The demo uses **pre-generated synthetic logs** that simulate realistic incident data:

```python
# data-generation/generators/logs.py
# Generates realistic log patterns for different incident types:
# - Database failures
# - API latency spikes
# - Memory exhaustion
# - Deployment rollbacks
```

This allows us to demonstrate:
- Gemini's ability to analyze complex log patterns
- Root cause identification across multiple services
- Timeline construction from log timestamps

**In production**, these synthetic logs would be replaced by real logs fetched from:
- Datadog (primary for cloud-native apps)
- AWS CloudWatch (for AWS infrastructure)
- Splunk (for enterprise environments)
- ELK Stack (for self-hosted logging)

---

## Implementation Roadmap

### Phase 1: Basic Integration (2 weeks)
- [ ] Implement LogSourceAdapter interface
- [ ] Add Datadog adapter
- [ ] Add service-to-source mapping config
- [ ] Modify analyzer to fetch logs on-demand

### Phase 2: Multi-Source Support (2 weeks)
- [ ] Add CloudWatch adapter
- [ ] Add Splunk adapter
- [ ] Implement fallback logic
- [ ] Add log source health checks

### Phase 3: Advanced Features (4 weeks)
- [ ] Real-time log streaming
- [ ] Log caching layer
- [ ] Custom field mapping
- [ ] Log deduplication

---

## Environment Variables Required

```bash
# Datadog
DATADOG_API_KEY=your-api-key
DATADOG_APP_KEY=your-app-key

# AWS CloudWatch
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# Splunk
SPLUNK_HOST=splunk.company.com
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=your-password
```

---

## Summary

| Aspect | Demo (Hackathon) | Production |
|--------|------------------|------------|
| Log Source | Pre-generated files | Datadog, CloudWatch, Splunk, ELK |
| Trigger | Manual + webhook | Webhook auto-fetches |
| Latency | Instant (pre-loaded) | 5-15 sec (API query) |
| Data | Synthetic realistic | Real production logs |

The architecture is designed for easy extension—adding a new log source requires implementing one adapter class.
