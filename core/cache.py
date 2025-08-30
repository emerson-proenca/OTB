import time
from typing import Any, Optional
from functools import wraps

class SimpleCache:
    """Cache simples em memória com TTL (Time To Live)"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str, ttl: int = 300) -> Optional[Any]:
        """
        Obtém um item do cache se ainda estiver válido
        
        Args:
            key: Chave do cache
            ttl: Time to live em segundos (padrão: 5 minutos)
        
        Returns:
            Valor do cache ou None se expirado/inexistente
        """
        if key not in self._cache:
            return None
        
        # Verifica se o item expirou
        if time.time() - self._timestamps[key] > ttl:
            self.delete(key)
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """
        Armazena um item no cache
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
        """
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def delete(self, key: str) -> None:
        """Remove um item do cache"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        self._cache.clear()
        self._timestamps.clear()
    
    def size(self) -> int:
        """Retorna o número de itens no cache"""
        return len(self._cache)

# Instância global do cache
cache = SimpleCache()

def cached(ttl: int = 300):
    """
    Decorator para cache de funções
    
    Args:
        ttl: Time to live em segundos
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gera chave baseada no nome da função e argumentos
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Tenta buscar no cache
            result = cache.get(cache_key, ttl)
            if result is not None:
                return result
            
            # Se não estiver em cache, executa função e armazena resultado
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            if result:
                cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator
