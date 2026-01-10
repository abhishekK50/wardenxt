"""
Test script to verify Gemini API connectivity
Run this to ensure your API key is working correctly
"""

from google import genai
from google.genai import types
from app.config import settings
from rich.console import Console
from rich.panel import Panel

console = Console()


def test_gemini_connection():
    """Test Gemini API connection and basic functionality"""
    
    console.print("\n[bold cyan]WardenXT - Gemini API Connection Test[/bold cyan]\n")
    
    # Configure Gemini
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        console.print("✓ API key configured", style="green")
        console.print(f"✓ Using model: {settings.gemini_model}", style="cyan")
    except Exception as e:
        console.print(f"✗ Failed to configure API key: {e}", style="red")
        return False
    
    # Test basic generation
    try:
        console.print("\n[bold]Testing Basic Generation:[/bold]")
        
        test_prompt = """You are WardenXT, an AI incident commander. 
        Respond with a brief introduction of your capabilities in 2-3 sentences."""
        
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=test_prompt
        )
        
        console.print(Panel(
            response.text,
            title="Gemini Response",
            border_style="green"
        ))
        console.print("✓ Successfully generated response", style="green")
        
    except Exception as e:
        console.print(f"✗ Failed to generate content: {e}", style="red")
        console.print(f"   Error details: {str(e)}", style="yellow")
        return False
    
    # Test with system instruction
    try:
        console.print("\n[bold]Testing System Instructions:[/bold]")
        
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents="What's your primary function in 10 words?",
            config=types.GenerateContentConfig(
                system_instruction="""You are WardenXT, an elite AI incident commander.
                Your role is to analyze system incidents with precision and provide
                actionable mitigation strategies."""
            )
        )
        
        console.print(f"  Response: {response.text}", style="cyan")
        console.print("✓ System instructions working", style="green")
        
    except Exception as e:
        console.print(f"✗ System instructions test failed: {e}", style="red")
        return False
    
    # Test multimodal capabilities
    try:
        console.print("\n[bold]Testing Advanced Features:[/bold]")
        
        # Test thinking mode
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents="""Analyze this hypothetical incident: 
            Database connection pool exhausted. 
            Think through the root cause step by step.""",
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_mode=types.ThinkingMode.THINKING_MODE_UNSPECIFIED
                )
            )
        )
        
        console.print("✓ Advanced reasoning capabilities available", style="green")
        
    except Exception as e:
        console.print(f"⚠ Advanced features test: {e}", style="yellow")
        console.print("  (This is okay - basic features work!)", style="yellow")
    
    # Success!
    console.print("\n" + "="*60, style="green")
    console.print("[bold green]✓ All critical Gemini API tests passed![/bold green]")
    console.print("[bold green]✓ WardenXT backend is ready to go![/bold green]")
    console.print("="*60 + "\n", style="green")
    
    return True


if __name__ == "__main__":
    success = test_gemini_connection()
    exit(0 if success else 1)