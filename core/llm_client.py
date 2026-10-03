"""
LLM Client - FreeLLMAPI integration for free model access

Provides unified interface to call free LLM models via freellmapi
without requiring any API keys or paid subscriptions.
"""

from __future__ import annotations

import json
import os
from typing import Optional
import requests

class LLMClient:
    """Client for calling free LLM models via freellmapi"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8080/v1",
        api_key: str = "free",
        model: str = "llama-2-70b-chat",
        timeout: int = 30,
    ):
        """
        Initialize LLM client
        
        Args:
            base_url: FreeLLMAPI server URL (default: local)
            api_key: API key (default: "free" for public endpoints)
            model: Model name to use (will verify on init)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("FREELLMAPI_BASE_URL", "http://localhost:8080/v1")
        self.api_key = api_key or os.getenv("FREELLMAPI_KEY", "free")
        self.model = model or os.getenv("FREELLMAPI_MODEL", "llama-2-70b-chat")
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Verify connection on init
        self._verify_connection()
    
    def _verify_connection(self) -> None:
        """Verify that freellmapi is running and accessible"""
        try:
            resp = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(
                f"Cannot connect to freellmapi at {self.base_url}. "
                f"Make sure it's running: freellmapi serve --host 0.0.0.0 --port 8080\n"
                f"Error: {e}"
            )
    
    def get_available_models(self) -> list[str]:
        """Get list of available models from freellmapi"""
        try:
            resp = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            
            if isinstance(data, dict) and "data" in data:
                return [m.get("id", str(m)) for m in data["data"]]
            elif isinstance(data, list):
                return [m.get("id", str(m)) for m in data]
            return []
        except Exception as e:
            print(f"Warning: Could not fetch model list: {e}")
            return []
    
    def chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
        top_p: float = 0.95,
        model: Optional[str] = None,
    ) -> str:
        """
        Call LLM for chat completion
        
        Args:
            messages: List of message dicts with "role" and "content"
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Max tokens in response
            top_p: Nucleus sampling parameter
            model: Override default model for this call
        
        Returns:
            Generated text response
        """
        model = model or self.model
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }
        
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0].get("message", {}).get("content", "")
            
            return ""
        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"LLM request timed out after {self.timeout}s. "
                "Consider increasing timeout or using a faster model."
            )
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to freellmapi at {self.base_url}. "
                "Make sure it's running."
            )
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}")
    
    def summarize(
        self,
        text: str,
        max_tokens: int = 300,
        language: str = "English",
    ) -> str:
        """Summarize text using LLM"""
        prompt = f"""Please provide a concise summary of the following text in {language}. 
Keep it brief and focus on key points.

TEXT:
{text}

SUMMARY:"""
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that summarizes text concisely."},
            {"role": "user", "content": prompt},
        ]
        
        return self.chat_completion(messages, max_tokens=max_tokens, temperature=0.3)
    
    def analyze_risk(
        self,
        project_info: str,
        risk_keywords: list[str],
        language: str = "English",
    ) -> dict:
        """Analyze risk level for project using LLM"""
        keywords_text = ", ".join(risk_keywords) if risk_keywords else "None"
        
        prompt = f"""Analyze the following project for risk. Return your analysis as JSON.

PROJECT INFO:
{project_info}

KNOWN RISK KEYWORDS: {keywords_text}

Provide your analysis in this exact JSON format:
{{
  "risk_level": "low|medium|high",
  "confidence": 0-100,
  "key_risks": ["risk1", "risk2", ...],
  "recommendation": "brief recommendation"
}}

ANALYSIS:"""
        
        messages = [
            {"role": "system", "content": "You are an expert in international trade risk analysis. Respond only with valid JSON."},
            {"role": "user", "content": prompt},
        ]
        
        response = self.chat_completion(messages, max_tokens=400, temperature=0.3)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "risk_level": "medium",
                "confidence": 50,
                "key_risks": [],
                "recommendation": response,
            }
    
    def generate_brief(
        self,
        project_title: str,
        country: str,
        counterparty: str,
        risk_level: str,
        triggers: list[str],
        language: str = "English",
    ) -> str:
        """Generate intelligence brief for project"""
        triggers_text = ", ".join(triggers) if triggers else "None identified"
        
        prompt = f"""Generate a professional intelligence brief for the following project.
Use {language} for response.

PROJECT: {project_title}
COUNTRY: {country}
COUNTERPARTY: {counterparty}
RISK LEVEL: {risk_level}
RISK TRIGGERS: {triggers_text}

Please generate a brief covering:
1. Key Risk Assessment
2. Compliance Considerations
3. Recommended Actions
4. Monitoring Points

BRIEF:"""
        
        messages = [
            {"role": "system", "content": "You are an expert intelligence analyst specializing in international engineering trade."},
            {"role": "user", "content": prompt},
        ]
        
        return self.chat_completion(messages, max_tokens=600, temperature=0.5)
    
    def generate_video_script(
        self,
        project_title: str,
        key_points: list[str],
        language: str = "English",
        duration_seconds: int = 60,
    ) -> str:
        """Generate short video script"""
        points_text = "\n".join([f"- {p}" for p in key_points])
        target_words = int(duration_seconds * 2.5)  # ~150 words per minute
        
        prompt = f"""Generate a concise video script for the following project.
Use {language} for response.
Target length: approximately {target_words} words (for {duration_seconds} second video).

PROJECT: {project_title}

KEY POINTS TO COVER:
{points_text}

Please generate a script that:
1. Opens with a hook
2. Covers each key point clearly
3. Ends with a call to action or takeaway

VIDEO SCRIPT:"""
        
        messages = [
            {"role": "system", "content": "You are a professional video scriptwriter specializing in business intelligence content."},
            {"role": "user", "content": prompt},
        ]
        
        return self.chat_completion(messages, max_tokens=int(target_words * 1.3), temperature=0.6)


# Global client instance
_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    """Get or create global LLM client"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client

def call_llm(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> str:
    """Quick convenience function to call LLM"""
    return get_llm_client().chat_completion(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
