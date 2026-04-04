import random
import time


def generate_tracking_code() -> str:
    """Generar un código de tracking único"""
    random_num = random.randint(100000, 999999)
    timestamp = int(time.time()) % 10000
    return f"TRK-{random_num}-{timestamp}"
