import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class Storage:
    WELCOME_IMAGE_FILE = "welcome_image.json"
    SERVICES_FILE = "services.json"

    def __init__(self):
        self.orders: Dict[str, Dict] = {}
        self.feedback: List[Dict] = []
        self.user_sessions: Dict[int, Dict] = {}
        self._welcome_image_file_id: Optional[str] = None
        self._services: Dict[str, float] = {}

        # Ensure storage files exist
        self._initialize_storage()
        self._load_welcome_image()
        self._load_services()
        logger.info("Storage initialized with services: %s", self._services)

    def _initialize_storage(self):
        """Initialize storage files if they don't exist."""
        try:
            # Initialize services file if it doesn't exist
            if not os.path.exists(self.SERVICES_FILE):
                default_services = {
                    "Telegram Premium - 1 Month": 4.99,
                    "Telegram Premium - 3 Months": 12.99,
                    "Telegram Premium - 6 Months": 24.99,
                    "Telegram Premium - 1 Year": 45.99,
                    "Telegram Stars": 9.99  # Added Telegram Stars service
                }
                with open(self.SERVICES_FILE, 'w') as f:
                    json.dump(default_services, f, indent=2)
                logger.info("Created new services file with default services")

            # Initialize welcome image file if it doesn't exist
            if not os.path.exists(self.WELCOME_IMAGE_FILE):
                with open(self.WELCOME_IMAGE_FILE, 'w') as f:
                    json.dump({"file_id": None}, f)
                logger.info("Created new welcome image file")

        except Exception as e:
            logger.error(f"Error initializing storage: {e}")
            # Ensure we have at least empty dictionaries
            self._services = {}
            self._welcome_image_file_id = None

    def _load_welcome_image(self) -> None:
        """Load welcome image file_id from persistent storage."""
        try:
            if os.path.exists(self.WELCOME_IMAGE_FILE):
                with open(self.WELCOME_IMAGE_FILE, 'r') as f:
                    data = json.load(f)
                    self._welcome_image_file_id = data.get('file_id')
        except Exception as e:
            logger.error(f"Error loading welcome image: {e}")

    def _save_welcome_image(self) -> bool:
        """Save welcome image file_id to persistent storage."""
        try:
            with open(self.WELCOME_IMAGE_FILE, 'w') as f:
                json.dump({'file_id': self._welcome_image_file_id}, f)
            return True
        except Exception as e:
            logger.error(f"Error saving welcome image: {e}")
            return False

    def _load_services(self) -> None:
        """Load services and prices from persistent storage."""
        try:
            logger.info(f"Attempting to load services from: {self.SERVICES_FILE}")
            if os.path.exists(self.SERVICES_FILE):
                with open(self.SERVICES_FILE, 'r') as f:
                    data = f.read().strip()
                    if data:  # Check if file is not empty
                        self._services = json.loads(data)
                        logger.info(f"Successfully loaded services: {self._services}")
                    else:
                        logger.warning("Services file is empty, initializing with defaults")
                        self._initialize_storage()  # This will create default services
                        self._load_services()  # Reload after initialization
            else:
                logger.warning(f"Services file not found: {self.SERVICES_FILE}")
                self._initialize_storage()  # This will create the file with default services
                self._load_services()  # Reload after initialization
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error loading services: {str(e)}")
            self._initialize_storage()  # Recreate file with default services
            self._load_services()  # Reload after initialization
        except Exception as e:
            logger.error(f"Error loading services: {str(e)}")
            self._services = {}

    def _save_services(self) -> bool:
        """Save services and prices to persistent storage."""
        try:
            logger.info(f"Attempting to save services: {self._services}")
            # Create a temporary file first
            temp_file = f"{self.SERVICES_FILE}.temp"
            with open(temp_file, 'w') as f:
                json.dump(self._services, f, indent=2)

            # Rename temp file to actual file (atomic operation)
            os.replace(temp_file, self.SERVICES_FILE)
            logger.info(f"Successfully saved services to file: {self._services}")
            return True
        except Exception as e:
            logger.error(f"Error saving services: {str(e)}")
            if os.path.exists(f"{self.SERVICES_FILE}.temp"):
                try:
                    os.remove(f"{self.SERVICES_FILE}.temp")
                except:
                    pass
            return False

    def add_service(self, name: str, price: float) -> bool:
        """Add a new service or update existing one."""
        try:
            if not name or not isinstance(price, (int, float)):
                logger.error(f"Invalid service data - name: {name}, price: {price}")
                return False

            logger.info(f"Adding/updating service: {name} with price ${price}")
            self._services[name] = float(price)
            success = self._save_services()

            if success:
                logger.info(f"Successfully added service: {name} at price ${price}")
            else:
                logger.error(f"Failed to save service: {name}")
            return success
        except Exception as e:
            logger.error(f"Error adding service: {str(e)}")
            return False

    def remove_service(self, name: str) -> bool:
        """Remove a service."""
        try:
            if name in self._services:
                del self._services[name]
                logger.info(f"Removed service: {name}")
                return self._save_services()
            logger.warning(f"Service not found for removal: {name}")
            return False
        except Exception as e:
            logger.error(f"Error removing service: {e}")
            return False

    def get_services(self) -> Dict[str, float]:
        """Get all services and their prices."""
        try:
            self._load_services()  # Reload to ensure we have the latest data
            if not self._services:
                logger.warning("No services found in storage")
                # Re-initialize if empty
                self._initialize_storage()
                self._load_services()

            logger.info(f"Retrieved services: {self._services}")
            return dict(self._services)  # Return a copy to prevent modifications
        except Exception as e:
            logger.error(f"Error getting services: {str(e)}")
            return {}

    def get_service_price(self, name: str) -> Optional[float]:
        """Get price for a specific service."""
        self._load_services()  # Reload to ensure we have the latest data
        price = self._services.get(name)
        logger.info(f"Retrieved price for service {name}: ${price if price is not None else 'Not found'}")
        return price

    def set_welcome_image(self, file_id: str) -> bool:
        """Store the welcome image file_id."""
        if not file_id:
            return False
        try:
            self._welcome_image_file_id = file_id
            return self._save_welcome_image()
        except Exception as e:
            logger.error(f"Error setting welcome image: {e}")
            return False

    def get_welcome_image(self) -> Optional[str]:
        """Get the stored welcome image file_id."""
        return self._welcome_image_file_id

    def create_order(self, user_id: int, service: str) -> str:
        order_id = f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id}"
        self.orders[order_id] = {
            "user_id": user_id,
            "service": service,
            "status": "pending",
            "payment_status": None,
            "payment_method": None,
            "created_at": datetime.now()
        }
        return order_id

    def get_order(self, order_id: str) -> Dict:
        """Get order details with payment information."""
        order = self.orders.get(order_id, {})
        if order:
            if "payment_status" not in order:
                order["payment_status"] = None
            if "payment_confirmation_time" not in order:
                order["payment_confirmation_time"] = None
        return order

    def update_order_status(self, order_id: str, status: str) -> bool:
        if order_id in self.orders:
            self.orders[order_id]["status"] = status
            return True
        return False

    def update_payment_method(self, order_id: str, payment_method: str) -> bool:
        """Update payment method and initialize payment status."""
        if order_id in self.orders:
            self.orders[order_id].update({
                "payment_method": payment_method,
                "payment_status": "pending",
                "payment_confirmation_time": None,
                "last_updated": datetime.now()
            })
            return True
        return False

    def update_payment_status(self, order_id: str, status: str) -> bool:
        """Update payment status with timestamp."""
        if order_id in self.orders:
            self.orders[order_id].update({
                "payment_status": status,
                "payment_confirmation_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'confirmed' else None,
                "last_updated": datetime.now()
            })
            return True
        return False

    def get_user_orders(self, user_id: int) -> Dict[str, Dict]:
        return {k: v for k, v in self.orders.items() if v["user_id"] == user_id}

    def get_user_pending_orders(self, user_id: int) -> Dict[str, Dict]:
        return {k: v for k, v in self.orders.items()
                if v["user_id"] == user_id and v["status"] == "pending"}

    def add_feedback(self, user_id: int, feedback_text: str) -> int:
        feedback_id = len(self.feedback)
        self.feedback.append({
            "id": feedback_id,
            "user_id": user_id,
            "text": feedback_text,
            "status": "pending",
            "created_at": datetime.now()
        })
        return feedback_id

    def get_pending_feedback(self) -> List[Dict]:
        return [f for f in self.feedback if f["status"] == "pending"]

    def update_feedback_status(self, feedback_id: int, status: str) -> bool:
        if 0 <= feedback_id < len(self.feedback):
            self.feedback[feedback_id]["status"] = status
            return True
        return False

    def set_user_session(self, user_id: int, key: str, value: Any) -> None:
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        self.user_sessions[user_id][key] = value

    def get_user_session(self, user_id: int, key: str) -> Any:
        return self.user_sessions.get(user_id, {}).get(key)

    def clear_user_session(self, user_id: int) -> None:
        self.user_sessions.pop(user_id, None)