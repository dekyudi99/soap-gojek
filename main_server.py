import logging
import mysql.connector
import os
import time
from spyne import Application, rpc, ServiceBase, Integer, Unicode, Float, Boolean, Iterable
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.model.complex import ComplexModel
from zeep import Client as ZeepClient
from zeep.transports import Transport
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
transport = Transport(cache=None)

try:
    ENTITY_WSDL = "http://localhost:8002/?wsdl"
    MICRO_WSDL = "http://localhost:8001/?wsdl"
    entity_client = ZeepClient(ENTITY_WSDL, transport=transport)
    micro_client = ZeepClient(MICRO_WSDL, transport=transport)
    logger.info("Berhasil terhubung ke Entity Service dan Micro Service (Cache dinonaktifkan).")
except Exception as e:
    logger.error(f"Gagal terhubung ke WSDL service lain. Pastikan service tersebut berjalan. Error: {e}")
    exit()

class UserLoginResponse(ComplexModel):
    __namespace__ = 'gojek.models'
    status = Boolean
    id = Integer
    name = Unicode
    role = Unicode

class OrderSummary(ComplexModel):
    __namespace__ = 'gojek.models'
    orderId = Integer
    driver = Unicode
    fare = Float
    pickup = Unicode
    destination = Unicode

class OrderHistoryItem(ComplexModel):
    __namespace__ = 'gojek.models'
    id = Integer
    driver_id = Integer
    driver_name = Unicode
    pickup = Unicode
    destination = Unicode
    total = Float
    status = Unicode

def connectToDatabase():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE"),
    )

#--------------------------------------------
# Utility Service (Autentikasi)
#--------------------------------------------
class AuthService(ServiceBase):
    
    @rpc(Unicode, Unicode, Unicode, Unicode, Unicode, _returns=Unicode)
    def register(ctx, name, email, role, password, address):
        try:
            success = entity_client.service.create_user(name, email, role, password, address)
            if success:
                logger.info(f"User baru berhasil didaftarkan: {email}")
                return "Registrasi Berhasil, Silakan login!"
            else:
                return "Registrasi Gagal. Email mungkin sudah terdaftar."
        except Exception as e:
            logger.error(f"Error saat registrasi untuk {email}: {e}")
            return "Terjadi kesalahan di server saat registrasi."

    @rpc(Unicode, Unicode, _returns=UserLoginResponse)
    def login(ctx, email, password):
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, name, role, password FROM user WHERE email=%s AND password=SHA2(%s, 256)", (email, password))
            user = cur.fetchone()
            if user and user['password'] == password:
                logger.info(f"Login berhasil untuk user: {email}")
                return UserLoginResponse(status=True, id=user['id'], name=user['name'], role=user['role'])
            else:
                logger.warning(f"Login gagal untuk user: {email}")
                return UserLoginResponse(status=False)
        except Exception as e:
            logger.error(f"Database error saat login: {e}")
            return UserLoginResponse(status=False)
        finally:
            if conn:
                conn.close()

#--------------------------------------------
# Task Service
#--------------------------------------------
class UserService(ServiceBase):  
    @rpc(Integer, Unicode, Unicode, _returns=OrderSummary)
    def request_driver(ctx, user_id, pickup, destination):
        try:
            logger.info(f"Menerima permintaan dari User ID: {user_id} dari {pickup} ke {destination}")
            order_id = micro_client.service.create_order(user_id, pickup, destination)
            logger.info(f"Order dibuat dengan ID: {order_id}. Mencari driver...")

            start_time = time.time()
            timeout_seconds = 60
            while time.time() - start_time < timeout_seconds:
                order_details = micro_client.service.get_order_status(order_id)
                if order_details and order_details.status == 'confirmed':
                    driver_info = entity_client.service.get_user(order_details.driver_id)
                    driver_name = driver_info.name if driver_info else "Driver"
                    logger.info(f"Driver ditemukan untuk Order ID {order_id}: {driver_name}")
                    fare_float = float(order_details.total)
                    return OrderSummary(
                        orderId=order_id,
                        driver=driver_name,
                        fare=fare_float,
                        pickup=pickup,
                        destination=destination
                    )
                time.sleep(3)

            logger.warning(f"Timeout untuk Order ID {order_id}. Tidak ada driver yang mengambil.")
            micro_client.service.reject_order(order_id, user_id)
            return OrderSummary(orderId=order_id, driver="Tidak ada driver tersedia", fare=0.0)
        except Exception as e:
            logger.error(f"Error di request_driver: {e}")
            raise

    @rpc(Integer, _returns=Iterable(OrderHistoryItem))
    def get_completed_orders(ctx, user_id):
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor(dictionary=True)
            query = "SELECT o.id, o.driver_id, u.name as driver_name, o.pickup, o.destination, o.total, o.status FROM orders_driver o JOIN user u ON o.driver_id = u.id WHERE o.user_id = %s AND o.status = 'completed'"
            cur.execute(query, (user_id,))
            orders_db = cur.fetchall()
            result_list = []
            for order_dict in orders_db:
                order_dict['total'] = float(order_dict['total'])
                result_list.append(OrderHistoryItem(**order_dict))
            return result_list
        except Exception as e:
            logger.error(f"Error saat mengambil riwayat: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @rpc(Integer, Integer, Float, Unicode, _returns=Unicode)
    def give_review(ctx, user_id, driver_id, rating, review_text):
        try:
            success = entity_client.service.create_review(user_id, driver_id, rating, review_text)
            if success:
                return "Terima kasih atas ulasan Anda!"
            else:
                return "Gagal mengirim ulasan. Coba lagi nanti."
        except Exception as e:
            logger.error(f"Error di give_review: {e}")
            return "Terjadi kesalahan pada server saat memberi ulasan."
# --- Pengaturan Aplikasi Spyne ---
application = Application(
    [AuthService, UserService],
    tns="gojek.service.main",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    server = make_server("0.0.0.0", 8000, WsgiApplication(application))
    logger.info("Main Server berjalan di http://0.0.0.0:8000")
    logger.info("WSDL tersedia di: http://localhost:8000/?wsdl")
    server.serve_forever()