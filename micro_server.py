import logging
import mysql.connector
from spyne import Application, rpc, ServiceBase, Integer, Unicode, Float, DateTime, Iterable
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.model.complex import ComplexModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Koneksi Database ---
def connectToDatabase():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="soap_gojek",
            port=3306
        )
    except mysql.connector.Error as err:
        logger.error(f"Gagal terhubung ke database: {err}")
        raise

# --- Model Data Kompleks ---
class Order(ComplexModel):
    __namespace__ = 'gojek.models'
    id = Integer
    user_id = Integer
    driver_id = Integer(min_occurs=0)
    pickup = Unicode
    destination = Unicode
    total = Float
    status = Unicode
    created_at = DateTime
    # --- TAMBAHAN: Tambahkan field untuk nama pelanggan ---
    customer_name = Unicode(min_occurs=0)


# --- Service untuk Logika Order ---
class OrderMicroService(ServiceBase):
    # ... (fungsi create_order, accept_order, complete_order, dll tetap sama) ...

    @rpc(_returns=Iterable(Order))
    def find_pending_orders(ctx):
        """Mencari semua order yang statusnya 'pending' dan menyertakan nama pelanggan."""
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor(dictionary=True)
            # --- PERBAIKAN: Lakukan JOIN dengan tabel user untuk mendapatkan nama ---
            query = """
                SELECT
                    o.id, o.user_id, o.driver_id, o.pickup, o.destination,
                    o.total, o.status, o.created_at, u.name as customer_name
                FROM orders_driver o
                JOIN user u ON o.user_id = u.id
                WHERE o.status = 'pending' AND o.driver_id IS NULL
                ORDER BY o.created_at ASC
            """
            cur.execute(query)
            pending_orders_db = cur.fetchall()
            
            result = []
            for order_dict in pending_orders_db:
                order_dict['total'] = float(order_dict['total'])
                result.append(Order(**order_dict))
            
            logger.info(f"Ditemukan {len(result)} order yang menunggu.")
            return result
        except mysql.connector.Error as err:
            logger.error(f"Database error saat mencari pending orders: {err}")
            raise
        finally:
            if conn:
                conn.close()
    
    # ... (Sisa fungsi lainnya tidak perlu diubah)
    @rpc(Integer, Unicode, Unicode, _returns=Integer)
    def create_order(ctx, user_id, pickup, destination):
        conn = None
        fare = float(abs(len(pickup) - len(destination)) * 2500.0 + 5000)
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            query = "INSERT INTO orders_driver (user_id, pickup, destination, total, status) VALUES (%s, %s, %s, %s, 'pending')"
            cur.execute(query, (user_id, pickup, destination, fare))
            conn.commit()
            order_id = cur.lastrowid
            logger.info(f"Order baru dibuat dengan ID: {order_id} oleh user ID: {user_id}")
            return order_id
        except mysql.connector.Error as err:
            logger.error(f"Database error saat membuat order: {err}")
            raise
        finally:
            if conn:
                conn.close()

    @rpc(Integer, Integer, _returns=Unicode)
    def accept_order(ctx, order_id, driver_id):
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            query = "UPDATE orders_driver SET driver_id = %s, status = 'confirmed' WHERE id = %s AND status = 'pending'"
            cur.execute(query, (driver_id, order_id))
            conn.commit()
            if cur.rowcount > 0:
                logger.info(f"Order ID: {order_id} DIKONFIRMASI oleh Driver ID: {driver_id}")
                return "Order berhasil diambil!"
            else:
                logger.warning(f"Gagal mengkonfirmasi Order ID: {order_id}.")
                return "Maaf, order ini sudah diambil oleh driver lain."
        except mysql.connector.Error as err:
            logger.error(f"Database error saat accept_order: {err}")
            raise
        finally:
            if conn:
                conn.close()

    @rpc(Integer, _returns=Unicode)
    def complete_order(ctx, order_id):
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            query = "UPDATE orders_driver SET status = 'completed' WHERE id = %s AND status = 'confirmed'"
            cur.execute(query, (order_id,))
            conn.commit()
            if cur.rowcount > 0:
                logger.info(f"Order ID: {order_id} SELESAI.")
                return f"Order {order_id} telah diselesaikan."
            else:
                logger.warning(f"Gagal menyelesaikan order {order_id}.")
                return "Gagal menyelesaikan order (status bukan 'confirmed')."
        except mysql.connector.Error as err:
            logger.error(f"Database error saat complete_order: {err}")
            raise
        finally:
            if conn:
                conn.close()

    @rpc(Integer, Integer, _returns=Unicode)
    def reject_order(ctx, order_id, driver_id):
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            query = "UPDATE orders_driver SET status = 'rejected' WHERE id = %s AND status = 'pending'"
            cur.execute(query, (order_id,))
            conn.commit()
            if cur.rowcount > 0:
                 logger.info(f"Order ID: {order_id} DITOLAK.")
                 return f"Order {order_id} ditolak."
            else:
                 return f"Order {order_id} tidak dapat ditolak."
        except mysql.connector.Error as err:
            logger.error(f"Database error saat reject_order: {err}")
            raise
        finally:
            if conn:
                conn.close()

    @rpc(Integer, _returns=Order)
    def get_order_status(ctx, order_id):
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor(dictionary=True)
            query = "SELECT id, user_id, driver_id, pickup, destination, total, status, created_at FROM orders_driver WHERE id = %s"
            cur.execute(query, (order_id,))
            order_data = cur.fetchone()
            if order_data:
                order_data['total'] = float(order_data['total'])
                return Order(**order_data)
            return None
        except mysql.connector.Error as err:
            logger.error(f"Database error saat get_order_status: {err}")
            raise
        finally:
            if conn:
                conn.close()
                
# --- Pengaturan Aplikasi Spyne ---
application = Application(
    [OrderMicroService],
    tns="gojek.microservice.order",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    wsgi_app = WsgiApplication(application)
    server = make_server("0.0.0.0", 8001, wsgi_app)
    logger.info("Microservice berjalan di http://0.0.0.0:8001")
    logger.info("WSDL tersedia di: http://localhost:8001/?wsdl")
    server.serve_forever()