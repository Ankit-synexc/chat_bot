from routers.document_router import router as document_router
from routers.query_router import router as query_router
from routers.history_router import router as history_router

all_routers = [
    document_router,
    query_router,
    history_router,
]
