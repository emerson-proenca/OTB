import time
from collections import defaultdict
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class RateLimiter:
    """Rate limiter simples baseado em IP"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        """
        Verifica se o IP pode fazer mais requisições
        
        Args:
            client_ip: IP do cliente
            
        Returns:
            True se permitido, False caso contrário
        """
        now = time.time()
        
        # Remove requisições antigas (fora da janela de tempo)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window_seconds
        ]
        
        # Verifica se excedeu o limite
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # Adiciona a requisição atual
        self.requests[client_ip].append(now)
        return True
    
    def get_remaining_requests(self, client_ip: str) -> int:
        """Retorna quantas requisições restam para o IP"""
        current_requests = len(self.requests[client_ip])
        return max(0, self.max_requests - current_requests)

# Instância global do rate limiter
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

async def rate_limit_middleware(request: Request, call_next):
    """Middleware de rate limiting"""
    # Obtém IP do cliente
    client_ip = request.client.host
    
    # Verifica rate limit
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Muitas requisições. Tente novamente em alguns segundos.",
                "retry_after": rate_limiter.window_seconds
            },
            headers={"Retry-After": str(rate_limiter.window_seconds)}
        )
    
    # Adiciona headers informativos
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(rate_limiter.get_remaining_requests(client_ip))
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + rate_limiter.window_seconds)
    
    return response
