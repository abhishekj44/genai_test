from dataclasses import dataclass


@dataclass
class ModelParams:
    prompt_cost_per_1M_tokens: float
    completion_cost_per_1M_tokens: float
    token_limit: int


model_params = {
    "gpt-4": ModelParams(30, 60, 8192),
    "gpt-4-32k": ModelParams(60, 120, 32768),
    "gpt-35-turbo": ModelParams(0.5, 1.5, 16385),
    "gpt-35-turbo-16k": ModelParams(0.5, 1.5, 16385),
    "gpt-35-turbo-32k": ModelParams(0.5, 1.5, 32768),
    "text-embedding-ada-002": ModelParams(0.1, 0.1, 1536),
}
