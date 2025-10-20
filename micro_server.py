import logging
import mysql.connector
from spyne import Application, rpc, ServiceBase, Integer, Unicode, Float, DateTime, Iterable
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.model.complex import ComplexModel
import json
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connectToDatabase():
    """Membuat koneksi ke database dengan autocommit aktif."""
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="soap_gojek",
            port=3306,
            autocommit=True  # Penting untuk konsistensi data antar service
        )
    except mysql.connector.Error as err:
        logger.error(f"Gagal terhubung ke database: {err}")
        raise

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

class OrderMicroService(ServiceBase):
    @rpc(Integer, Unicode, Unicode, _returns=Integer)
    def create_order(ctx, user_id, pickup, destination):
        """
        Membuat order di database, lalu menjadi PUBLISHER
        dengan mengirim pesan notifikasi ke Redpanda/Kafka.
        """
        conn = None
        fare = float(abs(len(pickup) - len(destination)) * 10000.0 + 5000)
        order_id = -1
        
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            
            # 1. Simpan order ke Database
            query = "INSERT INTO orders_driver (user_id, pickup, destination, total, status) VALUES (%s, %s, %s, %s, 'pending')"
            cur.execute(query, (user_id, pickup, destination, fare))
            order_id = cur.lastrowid
            logger.info(f"Order baru dibuat dengan ID: {order_id} oleh user ID: {user_id}")

            # 2. Kirim notifikasi ke Redpanda/Kafka
            try:
                # Inisialisasi Kafka Producer
                producer = KafkaProducer(
                    bootstrap_servers=['localhost:9092'],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )

                # Ambil nama pelanggan untuk disertakan dalam notifikasi
                cur.execute("SELECT name FROM user WHERE id=%s", (user_id,))
                customer_name = cur.fetchone()[0]

                # Siapkan isi pesan notifikasi
                message_payload = {
                    'id': order_id,
                    'customer_name': customer_name,
                    'pickup': pickup,
                    'destination': destination,
                    'total': fare
                }
                
                # Nama "papan pengumuman" atau topic
                topic = 'new-orders'

                # Kirim pesan ke topic
                future = producer.send(topic, value=message_payload)
                record_metadata = future.get(timeout=10) # Menunggu konfirmasi pengiriman
                logger.info(f" [🚀] Pesan order ID {order_id} berhasil dikirim ke topic '{topic}'")

            except KafkaError as e:
                logger.error(f"Gagal mengirim pesan ke Kafka/Redpanda: {e}")
            
            return order_id
        except mysql.connector.Error as err:
            logger.error(f"Database error saat membuat order: {err}")
            raise
        finally:
            if conn:
                cur.close()
                conn.close()

    @rpc(Integer, Integer, _returns=Unicode)
    def accept_order(ctx, order_id, driver_id):
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            query = "UPDATE orders_driver SET driver_id = %s, status = 'confirmed' WHERE id = %s AND status = 'pending'"
            cur.execute(query, (driver_id, order_id))
            if cur.rowcount > 0:
                logger.info(f"Order ID: {order_id} DIKONFIRMASI oleh Driver ID: {driver_id}")
                return "Order berhasil diambil!"
            else:
                return "Maaf, order ini sudah diambil oleh driver lain."
        finally:
            if conn:
                conn.close()

    @rpc(Integer, _returns=Unicode)
    def complete_order(ctx, order_id):
        # ... (Logika tidak berubah)
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            query = "UPDATE orders_driver SET status = 'completed' WHERE id = %s AND status = 'confirmed'"
            cur.execute(query, (order_id,))
            if cur.rowcount > 0:
                return f"Order {order_id} telah diselesaikan."
            else:
                return "Gagal menyelesaikan order (status bukan 'confirmed')."
        finally:
            if conn:
                conn.close()

    @rpc(Integer, _returns=Order)
    def get_order_status(ctx, order_id):
        # ... (Logika tidak berubah)
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