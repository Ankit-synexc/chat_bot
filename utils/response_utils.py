from typing import Any, Dict, List

def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Helper formatting for consistent 200 OK wrapper objects."""
    return {
        "success": True,
        "message": message,
        "data": data
    }

def error_response(message: str, code: int = 400) -> Dict[str, Any]:
    """Helper format for expected 4xx/5xx API exception bodies."""
    return {
        "success": False,
        "message": message,
        "error_code": code
    }

def paginate(items: List[Any], page: int, page_size: int) -> Dict[str, Any]:
    """Slices an in-memory list into paginated format."""
    total = len(items)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = items[start_idx:end_idx]
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return {
        "items": paginated_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }
