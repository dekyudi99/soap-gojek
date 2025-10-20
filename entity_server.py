import os
from wsgiref.simple_server import make_server
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Boolean, ComplexModel, Float, Iterable
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import mysql.connector
from dotenv import load_dotenv
import json
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

#-------------------------------------------
# Entities
#-------------------------------------------
class User(ComplexModel):
    __namespace__ = 'gojek.models'
    id = Integer
    name = Unicode
    email = Unicode
    role = Unicode
    address = Unicode

class Review(ComplexModel):
    __namespace__ = 'gojek.models'
    id = Integer
    user_id = Integer
    rating = Float
    review = Unicode
    customer_name = Unicode(min_occurs=0)

def connectToDatabase():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE"),
    )

#--------------------------------------------
# Entity Service
#--------------------------------------------
class EntityService(ServiceBase):
    @rpc(Unicode, Unicode, Unicode, Unicode, Unicode, _returns=Boolean)
    def create_user(ctx, name, email, role, password, address):
        conn = None
        cur = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO user (name, email, role, password, address) VALUES (%s, %s, %s, SHA2(%s, 256), %s)",
                (name, email, role, password, address),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Gagal Menyimpan Data di EntityService: {e}")
            return False
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    @rpc (Integer, _returns=User)
    def get_user(ctx, user_id):
        conn = None
        cur = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, email, role, address FROM user WHERE id=%s",
                (user_id,),
            )
            user_data = cur.fetchone()
            if user_data:
                return User(
                    id=user_data[0],
                    name=user_data[1],
                    email=user_data[2],
                    role=user_data[3],
                    address=user_data[4]
                )
            else:
                return None
        except Exception as e:
            print(f"Gagal mengambil data user di EntityService: {e}")
            raise
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    
    @rpc(Integer, Integer, Float, Unicode, _returns=Boolean)
    def create_review(ctx, user_id, driver_id, rating, review_text):
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            
            # 1. Simpan review ke Database
            query = "INSERT INTO review (user_id, driver_id, rating, review) VALUES (%s, %s, %s, %s)"
            cur.execute(query, (user_id, driver_id, rating, review_text))
            
            # 2. Kirim notifikasi ke Redpanda/Kafka
            try:
                producer = KafkaProducer(
                    bootstrap_servers=['localhost:9092'],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                
                # Ambil nama pelanggan untuk disertakan di notifikasi
                cur.execute("SELECT name FROM user WHERE id=%s", (user_id,))
                customer_name = cur.fetchone()[0]

                # Siapkan isi pesan
                message_payload = {
                    'driver_id': driver_id,
                    'customer_name': customer_name,
                    'rating': rating,
                    'review': review_text
                }
                
                topic = 'new-reviews'
                future = producer.send(topic, value=message_payload)
                future.get(timeout=10)
                logger.info(f" [🚀] Pesan review untuk driver ID {driver_id} berhasil dikirim ke topic '{topic}'")

            except KafkaError as e:
                logger.error(f"Gagal mengirim pesan review ke Kafka/Redpanda: {e}")

            return True
        except Exception as e:
            print(f"Gagal menyimpan review: {e}")
            return False
        finally:
            if conn:
                cur.close()
                conn.close()

# --- Pengaturan Aplikasi Spyne ---
application = Application(
    [EntityService],
    tns="entity.service",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11()
)

if __name__ == "__main__":
    server = make_server("0.0.0.0", 8002, WsgiApplication(application))
    print("Entity Service running on http://localhost:8002/?wsdl")
    server.serve_forever()