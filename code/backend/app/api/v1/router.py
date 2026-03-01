"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, users, wallet, topics, trading, settlements, products, admin, moderation, audit, devices, terms, notifications, settlements_announcements, announcements, system_config

router = APIRouter()

# Include module routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(wallet.router, prefix="/wallet", tags=["Wallet"])
router.include_router(topics.router, prefix="/topics", tags=["Topics"])
router.include_router(trading.router, prefix="/trading", tags=["Trading"])
router.include_router(settlements.router, prefix="/settlements", tags=["Settlements"])
router.include_router(products.router, prefix="/products", tags=["Products"])
router.include_router(admin.router, prefix="/admin", tags=["Admin"])
router.include_router(moderation.router, prefix="/moderation", tags=["Content Moderation"])
router.include_router(audit.router, prefix="", tags=["Audit Logs"])
router.include_router(devices.router, prefix="/auth", tags=["Devices"])
router.include_router(terms.router, prefix="/auth", tags=["Terms"])
router.include_router(notifications.router, prefix="", tags=["Notifications"])
router.include_router(settlements_announcements.router, prefix="/settlements", tags=["Settlement Announcements"])
router.include_router(announcements.router, prefix="", tags=["Announcements"])
router.include_router(system_config.router, prefix="/admin", tags=["System Config"])
