"""
Routes Package - All API route modules
"""
from .auth import router as auth_router
from .customers import router as customers_router
from .suppliers import router as suppliers_router
from .warehouses import router as warehouses_router
from .sales import router as sales_router
from .purchases import router as purchases_router
from .saas import router as saas_router
from .reports import router as reports_router

__all__ = [
    'auth_router',
    'customers_router', 
    'suppliers_router',
    'warehouses_router',
    'sales_router',
    'purchases_router',
    'saas_router',
    'reports_router'
]
