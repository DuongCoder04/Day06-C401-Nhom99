from services.cart_service import CartService
from services.intent_service import IntentService
from services.menu_service import MenuService
from services.recommender import Recommender

menu_service = MenuService()
cart_service = CartService()
intent_service = IntentService()
recommender = Recommender(menu_service)
