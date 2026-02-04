"""
Gemini Client Wrapper
Handles all interactions with Gemini 3 API
"""

from google import genai
from google.genai import types
from app.config import settings, validate_gemini_key
from typing import Optional, Dict, List, Any
import json
import asyncio


class GeminiClient:
    """Wrapper for Gemini 3 API with WardenXT-specific configurations"""
    
    SYSTEM_INSTRUCTION = """You are WardenXT, an elite AI incident commander specialized in analyzing 
system outages and operational incidents. Your role is to:

1. Analyze incident data with surgical precision
2. Identify root causes through deep reasoning
3. Provide actionable mitigation strategies
4. Communicate clearly and concisely

You have access to:
- Application logs (potentially thousands of entries)
- System metrics (CPU, memory, network, application performance)
- Incident timelines
- Historical incident patterns

Your responses should be:
- Data-driven and evidence-based
- Confident but acknowledge uncertainty when appropriate
- Actionable with specific next steps
- Professional but accessible

When analyzing incidents:
1. First, scan ALL provided data to understand the full context
2. Identify patterns and anomalies
3. Correlate logs with metrics to find causation
4. Consider both technical and business impact
5. Prioritize mitigation actions by impact and feasibility"""
    
    def __init__(self):
        """Initialize Gemini client"""
        # Validate API key only when client is actually created
        validate_gemini_key()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model
        
    def generate_incident_brief(
        self,
        incident_summary: Dict,
        logs_sample: List[Dict],
        metrics_sample: List[Dict],
        timeline: List[Dict]
    ) -> str:
        """Generate comprehensive incident brief using Total Recall context
        
        Args:
            incident_summary: Incident metadata
            logs_sample: Application logs
            metrics_sample: System metrics
            timeline: Timeline events
            
        Returns:
            Generated incident brief as text
        """
        
        # Build comprehensive context (Total Recall feature!)
        context = self._build_total_recall_context(
            incident_summary,
            logs_sample,
            metrics_sample,
            timeline
        )
        
        # Create prompt for analysis
        prompt = f"""Analyze this production incident and provide a comprehensive brief.

{context}

Generate a detailed incident brief in the following JSON format:
{{
    "executive_summary": "2-3 sentence overview of the incident",
    "root_cause": {{
        "primary_cause": "Main root cause identified",
        "confidence": 0.0-1.0,
        "evidence": ["specific evidence from logs/metrics"],
        "contributing_factors": ["secondary factors if any"]
    }},
    "impact": {{
        "users_affected": "estimated number/description",
        "estimated_cost": "financial impact estimate",
        "services_impacted": ["list of affected services"],
        "severity_justification": "why this severity level"
    }},
    "recommended_actions": [
        {{
            "priority": "HIGH/MEDIUM/LOW",
            "action": "specific action to take",
            "estimated_time": "time estimate",
            "risk_level": "risk assessment"
        }}
    ],
    "timeline_summary": "brief narrative of incident progression"
}}

Focus on being precise, evidence-based, and actionable."""
        
        # Generate response
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.SYSTEM_INSTRUCTION,
                    temperature=0.2,  # Lower temperature for more consistent analysis
                    max_output_tokens=4096
                )
            )
            
            return response.text
            
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
    def _build_total_recall_context(
        self,
        summary: Dict,
        logs: List[Dict],
        metrics: List[Dict],
        timeline: List[Dict]
    ) -> str:
        """Build comprehensive context using all available data
        
        This is our "Total Recall" feature - feeding massive context to Gemini 3
        """
        
        context_parts = []
        
        # Incident metadata
        context_parts.append("## INCIDENT METADATA")
        context_parts.append(f"ID: {summary.get('incident_id')}")
        context_parts.append(f"Title: {summary.get('title')}")
        context_parts.append(f"Severity: {summary.get('severity')}")
        context_parts.append(f"Duration: {summary.get('duration_minutes')} minutes")
        context_parts.append(f"Services: {', '.join(summary.get('services_affected', []))}")
        context_parts.append("")
        
        # Timeline
        if timeline:
            context_parts.append("## INCIDENT TIMELINE")
            for event in timeline:
                context_parts.append(f"[{event.get('time')}] {event.get('event')}")
                context_parts.append(f"  Impact: {event.get('impact')}")
            context_parts.append("")
        
        # Metrics summary
        if metrics:
            context_parts.append("## SYSTEM METRICS")
            context_parts.append(f"Total metric points: {len(metrics)}")
            
            # Sample first, middle, and last metrics to show progression
            sample_indices = [0, len(metrics)//2, -1]
            for idx in sample_indices:
                if idx < len(metrics):
                    m = metrics[idx]
                    context_parts.append(f"\n[{m.get('timestamp')}]")
                    for key, value in m.get('metrics', {}).items():
                        context_parts.append(f"  {key}: {value}")
            context_parts.append("")
        
        # Logs - provide sample with focus on errors
        if logs:
            context_parts.append("## APPLICATION LOGS")
            context_parts.append(f"Total log entries: {len(logs)}")
            context_parts.append("\nCritical/Error logs:")
            
            # Extract error logs
            error_logs = [
                log for log in logs 
                if log.get('level') in ['ERROR', 'CRITICAL']
            ]
            
            # Show up to 20 error logs
            for log in error_logs[:20]:
                context_parts.append(f"\n[{log.get('timestamp')}] {log.get('level')}")
                context_parts.append(f"Service: {log.get('service')} | Host: {log.get('host')}")
                context_parts.append(f"Message: {log.get('message')}")
                if log.get('stack_trace'):
                    context_parts.append(f"Stack: {log.get('stack_trace')[:200]}...")
            
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def analyze_root_cause(
        self,
        logs: List[Dict],
        metrics: List[Dict]
    ) -> Dict:
        """Focused root cause analysis
        
        Args:
            logs: Application logs
            metrics: System metrics
            
        Returns:
            Root cause analysis dictionary
        """
        
        # Build focused prompt
        error_logs = [log for log in logs if log.get('level') in ['ERROR', 'CRITICAL']]
        
        prompt = f"""Analyze these error logs and metrics to identify the root cause.

ERROR LOGS ({len(error_logs)} entries):
{json.dumps(error_logs[:50], indent=2)}

METRICS TRENDS:
{json.dumps(metrics[:10], indent=2)}

Identify:
1. The primary root cause
2. Your confidence level (0.0-1.0)
3. Specific evidence supporting your conclusion
4. Any contributing factors

Respond in JSON format."""
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.SYSTEM_INSTRUCTION,
                    temperature=0.1
                )
            )
            
            # Parse JSON response
            result_text = response.text.strip()
            # Remove markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
            
            return json.loads(result_text)

        except Exception as e:
            raise RuntimeError(f"Root cause analysis failed: {str(e)}")

    async def generate_content_async(self, prompt: str, temperature: float = 0.3) -> Any:
        """Generate content asynchronously

        Args:
            prompt: Prompt text
            temperature: Temperature for generation

        Returns:
            Generated response object
        """
        try:
            # Run synchronous call in executor for async compatibility
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self.SYSTEM_INSTRUCTION,
                        temperature=temperature,
                        max_output_tokens=8192
                    )
                )
            )
            return response
        except Exception as e:
            raise RuntimeError(f"Gemini async generation failed: {str(e)}")


# Global instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create global Gemini client instance

    Returns:
        GeminiClient instance
    """
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client