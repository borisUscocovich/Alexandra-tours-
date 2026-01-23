import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class UsageMetrics:
    """Trackea costos y uso para optimizar."""

    llm_calls: int = 0
    llm_tokens_in: int = 0
    llm_tokens_out: int = 0
    api_calls: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    cache_hits: int = 0
    cache_misses: int = 0
    bypassed_requests: int = 0
    total_requests: int = 0
    requests_by_tier: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record_llm_call(self, tokens_in: int, tokens_out: int):
        self.llm_calls += 1
        self.llm_tokens_in += tokens_in
        self.llm_tokens_out += tokens_out

    def record_api_call(self, api_name: str):
        self.api_calls[api_name] += 1

    def record_bypass(self):
        self.bypassed_requests += 1

    def record_request(self, tier: str):
        self.total_requests += 1
        self.requests_by_tier[tier] += 1

    def estimate_costs(self) -> dict:
        """Estima costos basado en pricing conocido."""

        # Precios aproximados
        LLM_COST_PER_1K_IN = 0.003   # $3/M input
        LLM_COST_PER_1K_OUT = 0.015  # $15/M output
        ELEVENLABS_PER_CHAR = 0.00003  # ~$30/M chars

        llm_cost = (
            (self.llm_tokens_in / 1000 * LLM_COST_PER_1K_IN) +
            (self.llm_tokens_out / 1000 * LLM_COST_PER_1K_OUT)
        )

        # Estimar chars de voz (aprox 5 chars por token output)
        voice_chars = self.llm_tokens_out * 5
        voice_cost = voice_chars * ELEVENLABS_PER_CHAR

        return {
            "llm_cost_usd": round(llm_cost, 4),
            "voice_cost_usd": round(voice_cost, 4),
            "total_cost_usd": round(llm_cost + voice_cost, 4),
            "cost_per_request": round((llm_cost + voice_cost) / max(self.total_requests, 1), 6),
            "bypass_rate": f"{(self.bypassed_requests / max(self.total_requests, 1) * 100):.1f}%",
            "cache_hit_rate": f"{(self.cache_hits / max(self.cache_hits + self.cache_misses, 1) * 100):.1f}%"
        }

    def to_dict(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "llm_calls": self.llm_calls,
            "bypassed": self.bypassed_requests,
            "tokens": {"in": self.llm_tokens_in, "out": self.llm_tokens_out},
            "by_tier": dict(self.requests_by_tier),
            "costs": self.estimate_costs()
        }

metrics = UsageMetrics()
