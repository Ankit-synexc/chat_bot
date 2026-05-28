import time
from collections import deque
from typing import Dict

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Dict storing deques for each key hash
        self.requests: Dict[str, deque] = {}

    def is_allowed(self, key_hash: str) -> bool:
        now = time.time()
        
        if key_hash not in self.requests:
            self.requests[key_hash] = deque()
            
        # Evict timestamps outside the window
        while self.requests[key_hash] and self.requests[key_hash][0] < now - self.window_seconds:
            self.requests[key_hash].popleft()
            
        if len(self.requests[key_hash]) < self.max_requests:
            self.requests[key_hash].append(now)
            return True
            
        return False

    def get_stats(self, key_hash: str) -> Dict[str, int]:
        now = time.time()
        if key_hash in self.requests:
            # Clean up old entries before reporting stats
            while self.requests[key_hash] and self.requests[key_hash][0] < now - self.window_seconds:
                self.requests[key_hash].popleft()
            current_requests = len(self.requests[key_hash])
        else:
            current_requests = 0
            
        return {
            "requests_in_window": current_requests,
            "limit": self.max_requests,
            "window_seconds": self.window_seconds
        }

# Initialize singleton based on settings
from config.settings import settings
rate_limiter = RateLimiter(settings.RATE_LIMIT_REQUESTS, settings.RATE_LIMIT_WINDOW_SECONDS)
