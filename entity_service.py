import os
from wsgiref.simple_server import make_server
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Boolean, ComplexModel, Float, Iterable
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import mysql.connector
from dotenv import load_dotenv

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
    # --- TAMBAHAN: Tambahkan field untuk nama pelanggan ---
    customer_name = Unicode(min_occurs=0)

# Koneksi Ke Database
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
    # ... (fungsi create_user, get_user, create_review, mark_reviews_as_seen tetap sama) ...
    @rpc(Integer, _returns=Iterable(Review))
    def get_unseen_reviews(ctx, driver_id):
        """Mengambil semua review untuk driver yang belum dilihat dan menyertakan nama pelanggan."""
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor(dictionary=True)
            # --- PERBAIKAN: Lakukan JOIN dengan tabel user untuk mendapatkan nama ---
            query = """
                SELECT
                    r.id, r.user_id, r.rating, r.review, u.name as customer_name
                FROM review r
                JOIN user u ON r.user_id = u.id
                WHERE r.driver_id = %s AND r.is_seen = FALSE
            """
            cur.execute(query, (driver_id,))
            reviews = cur.fetchall()
            return [Review(**r) for r in reviews]
        except Exception as e:
            print(f"Gagal mengambil unseen reviews: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # ... (Sisa fungsi lainnya tidak perlu diubah)
    @rpc(Unicode, Unicode, Unicode, Unicode, Unicode, _returns=Boolean)
    def create_user(ctx, name, email, role, password, address):
        conn = None
        cur = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO user (name, email, role, password, address) VALUES (%s, %s, %s, %s, %s)",
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
            query = "INSERT INTO review (user_id, driver_id, rating, review) VALUES (%s, %s, %s, %s)"
            cur.execute(query, (user_id, driver_id, rating, review_text))
            conn.commit()
            return True
        except Exception as e:
            print(f"Gagal menyimpan review: {e}")
            return False
        finally:
            if conn:
                conn.close()
                conn.close()

    @rpc(Integer, _returns=Boolean)
    def mark_reviews_as_seen(ctx, driver_id):
        conn = None
        try:
            conn = connectToDatabase()
            cur = conn.cursor()
            query = "UPDATE review SET is_seen = TRUE WHERE driver_id = %s AND is_seen = FALSE"
            cur.execute(query, (driver_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Gagal menandai review sebagai seen: {e}")
            return False
        finally:
            if conn:
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