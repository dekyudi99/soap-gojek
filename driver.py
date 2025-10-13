from zeep import Client
import time
import getpass

SERVICE_WSDL = "http://localhost:8000/?wsdl"
MICRO_WSDL = "http://localhost:8001/?wsdl"
main_client = Client(SERVICE_WSDL)
micro_client = Client(MICRO_WSDL)
current_driver_info = None

def driver_login():
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
            print("Login gagal. Pastikan email, password, dan role Anda benar.")
            return False
    except Exception as e:
        print(f"Error saat login: {e}")
        return False

def check_reviews_as_notification(driver_id):
    """Memeriksa dan menampilkan review baru sebagai notifikasi."""
    try:
        new_reviews = main_client.service.check_for_new_reviews(driver_id)
        if new_reviews:
            print("\n\n--- 🔔 NOTIFIKASI BARU 🔔 ---")
            for review in new_reviews:
                # --- PERBAIKAN: Tampilkan nama pelanggan ---
                print(f"Anda mendapat ulasan baru dari pelanggan: {review.customer_name}!")
                print(f"  Rating  : {'⭐' * int(review.rating)} ({review.rating}/5.0)")
                print(f"  Ulasan  : {review.review or '(Tidak ada komentar)'}")
            print("---------------------------------")
            time.sleep(4)
    except Exception as e:
        print(f"\n(Gagal memeriksa notifikasi review: {e})")

def start_working():
    """Fungsi utama driver untuk mencari dan merespons order."""
    if not current_driver_info:
        print("Sesi tidak valid. Silakan login ulang.")
        return

    print("Mencari orderan masuk... (Tekan Ctrl+C untuk berhenti)")
    try:
        last_review_check = time.time()
        while True:
            if time.time() - last_review_check > 10:
                check_reviews_as_notification(current_driver_info.id)
                last_review_check = time.time()

            pending_orders = micro_client.service.find_pending_orders()
            if not pending_orders:
                print("Belum ada orderan. Mencari lagi...", end='\r')
                time.sleep(5)
                continue

            for order in pending_orders:
                print("\n\n--- ORDERAN BARU DITEMUKAN! ---")
                # --- PERBAIKAN: Tampilkan nama pelanggan ---
                print(f"  Nama Pelanggan: {order.customer_name}")
                print(f"  Lokasi Jemput : {order.pickup}")
                print(f"  Tujuan        : {order.destination}")
                print(f"  Tarif         : Rp {order.total:,.0f}")
                print("---------------------------------")

                action = ""
                while action not in ['y', 'n']:
                    action = input("Ambil orderan ini? (y/n): ").lower()

                if action == 'y':
                    driver_id = current_driver_info.id
                    response = micro_client.service.accept_order(order.id, driver_id)
                    print(f"=> {response}")

                    if "berhasil" in response.lower():
                        while True:
                            print("\n--- Anda sedang dalam perjalanan ---")
                            print("1. Selesaikan Orderan Ini")
                            print("2. (Abaikan, Lanjut Cari Orderan Lain)")
                            manage_choice = input("Pilih aksi (1/2): ")
                            if manage_choice == '1':
                                complete_response = micro_client.service.complete_order(order.id)
                                print(f"=> {complete_response}")
                                print("Order selesai. Kembali mencari orderan baru.")
                                break
                            elif manage_choice == '2':
                                print("Order ini tetap aktif. Anda kembali ke menu pencarian.")
                                break
                            else:
                                print("Pilihan tidak valid.")
                    break
                else:
                    print("=> Order dilewati. Mencari orderan selanjutnya...")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nAnda berhenti bekerja. Sampai jumpa!")
    except Exception as e:
        print(f"\nTerjadi kesalahan: {e}")

def main():
    if driver_login():
        start_working()
    print("Aplikasi ditutup.")

if __name__ == "__main__":
    main()