import math
from typing import Callable, Dict

def hash_string(s: str) -> int:
    h = 0
    for char in s:
        h = ((h << 5) - h) + ord(char)
        h &= 0xFFFFFFFF
    return abs(h)

def seeded_random(seed: int) -> Callable[[], float]:
    def _rand():
        nonlocal seed
        x = math.sin(seed) * 10000
        seed += 1
        return x - math.floor(x)
    return _rand

def get_random_error_message(rand_val: float) -> str:
    errors = [
        'Connection timeout',
        'Service unavailable',
        'Internal server error',
        'Bad gateway',
        'Too many requests',
        'Connection refused',
        'DNS resolution failed',
        'TLS handshake failed'
    ]
    return errors[math.floor(rand_val * len(errors))]

def enhance_connection_with_metrics(connection: Dict) -> Dict:
    enhanced = connection.copy()

    if connection.get("status") == "blocked":
        return enhanced

    seed = hash_string(f"{connection['source']}-{connection['destination']}")
    rand = seeded_random(seed)

    enhanced["latency"] = math.floor(rand() * 450) + 50
    enhanced["errorRate"] = round(rand() * 0.1, 4)
    enhanced["requestVolume"] = math.floor(rand() * 990) + 10

    if enhanced["errorRate"] > 0.05:
        enhanced["status"] = "degraded"
        enhanced["errorMessage"] = get_random_error_message(rand())
    elif enhanced["errorRate"] > 0:
        enhanced["status"] = "warning"
    elif connection.get("status") == "inferred":
        enhanced["status"] = "healthy"

    return enhanced