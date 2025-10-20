import json
import getpass
import threading
from zeep import Client
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

# Koneksi ke service SOAP tetap dibutuhkan
SERVICE_WSDL = "http://localhost:8000/?wsdl"
MICRO_WSDL = "http://localhost:8001/?wsdl"
main_client = Client(SERVICE_WSDL)
micro_client = Client(MICRO_WSDL)
current_driver_info = None

def driver_login():
    """Fungsi otentikasi driver."""
    global current_driver_info
    print("\n--- Silakan Login ---")
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    try:
        response = main_client.service.login(email, password)
        if response and response.status and response.role == 'driver':
            current_driver_info = response
            print(f"\nSelamat datang, Driver {current_driver_info.name}!")
            return True
        else:
            print("Login gagal.")
            return False
    except Exception as e:
        print(f"Error saat login: {e}")
        return False

def on_order_received(order_data):
    """Callback untuk menampilkan dan merespons order baru."""
    print("\n\n--- 🔔 ORDERAN BARU DITERIMA! 🔔 ---")
    print(f"  Nama Pelanggan: {order_data['customer_name']}")
    print(f"  Lokasi Jemput : {order_data['pickup']}")
    print(f"  Tujuan        : {order_data['destination']}")
    print(f"  Tarif         : Rp {order_data['total']:,.0f}")
    print("------------------------------------")
    
    action = ""
    while action not in ['y', 'n']:
        action = input("Ambil orderan ini? (y/n): ").lower()

    if action == 'y':
        response = micro_client.service.accept_order(order_data['id'], current_driver_info.id)
        print(f"=> {response}")
        if "berhasil" in response.lower():
            input("Tekan Enter jika orderan sudah selesai...")
            complete_response = micro_client.service.complete_order(order_data['id'])
            print(f"=> {complete_response}")
            print("Order selesai. Kembali mendengarkan...")
    else:
        print("=> Order dilewati. Kembali mendengarkan...")

def on_review_received(review_data):
    """Callback untuk menampilkan notifikasi review baru."""
    # Pastikan notifikasi ini hanya untuk driver yang sedang login
    if review_data['driver_id'] == current_driver_info.id:
        print("\n\n--- 🔔 NOTIFIKASI BARU 🔔 ---")
        print(f"Anda mendapat ulasan baru dari {review_data['customer_name']}!")
        print(f"  Rating: {'⭐' * int(review_data['rating'])} ({review_data['rating']}/5.0)")
        print(f"  Ulasan: {review_data['review'] or '(Tidak ada komentar)'}")
        print("-----------------------------")

def start_consuming(topic, callback_function):
    """Fungsi generik untuk mendengarkan pesan dari sebuah topic Kafka."""
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        print(f"[*] Mendengarkan topic '{topic}'...")
        for message in consumer:
            callback_function(message.value)
    except NoBrokersAvailable:
        print(f"\n[!] Gagal terhubung ke Redpanda/Kafka saat mencoba mendengarkan topic '{topic}'.")
    except Exception as e:
        print(f"\nTerjadi kesalahan pada listener '{topic}': {e}")

def main():
    """Fungsi utama untuk menjalankan aplikasi driver."""
    if driver_login():
        try:
            # Buat satu thread untuk mendengarkan order
            order_thread = threading.Thread(target=start_consuming, args=('new-orders', on_order_received))
            
            # Buat thread kedua untuk mendengarkan review
            review_thread = threading.Thread(target=start_consuming, args=('new-reviews', on_review_received))

            # Jalankan kedua thread di latar belakang
            order_thread.start()
            review_thread.start()

            # Jaga agar program utama tetap berjalan
            order_thread.join()
            review_thread.join()

        except KeyboardInterrupt:
            print("\nAnda berhenti bekerja. Sampai jumpa!")
    
    print("Aplikasi ditutup.")

if __name__ == "__main__":
    main()