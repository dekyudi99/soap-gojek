from zeep import Client, exceptions
import getpass
import time

SERVICE_WSDL = "http://localhost:8000/?wsdl"

try:
    client = Client(SERVICE_WSDL)
except Exception as e:
    print(f"Gagal terhubung ke server SOAP. Pastikan semua server berjalan.\nError: {e}")
    exit()

# Variabel global untuk menyimpan data pengguna yang sedang login
current_user = None

def main_menu():
    """Menampilkan menu utama sebelum login."""
    print("\n===== Selamat Datang di Gojek =====")
    print("1. Daftar Akun")
    print("2. Masuk")
    print("0. Keluar")
    return input("Pilih opsi: ")

def user_menu():
    """Menampilkan menu setelah pengguna berhasil login."""
    # --- PERBAIKAN DI SINI ---
    print(f"\n===== Menu Utama (Login sebagai {current_user.name}) =====")
    print("1. Pesan GoRide (Pesan Driver)")
    print("2. Beri Ulasan untuk Perjalanan Selesai")
    print("3. Logout")
    return input("Pilih opsi: ")

def register():
    """Fungsi untuk registrasi pengguna."""
    name = input("Masukkan Nama: ")
    email = input("Masukkan Email: ")
    role = ""
    while not role:
        print("Pilih Role Anda:\n1. Pelanggan (user)\n2. Pengemudi (driver)")
        role_choice = input("Masukkan pilihan (1/2): ")
        if role_choice == '1': role = 'user'
        elif role_choice == '2': role = 'driver'
        else: print("Pilihan tidak valid.")
    password = getpass.getpass("Masukkan Password: ")
    address = input("Masukkan Alamat Anda: ")
    try:
        result = client.service.register(name, email, role, password, address)
        print(f"SERVER: {result}")
    except exceptions.Fault as e:
        print(f"Error: {e.message}")

def login():
    """Fungsi untuk login pengguna."""
    global current_user
    email = input("Masukkan Email: ")
    password = getpass.getpass("Masukkan Password: ")
    try:
        response = client.service.login(email, password)
        if response and response.status:
            current_user = response
            print(f"Login berhasil! Selamat datang, {current_user.name}.")
        else:
            print("Login gagal. Email atau password salah.")
    except exceptions.Fault as e:
        print(f"Error: {e.message}")

def order_driver():
    """Fungsi untuk memesan driver."""
    if not current_user:
        print("Anda harus login untuk memesan.")
        return

    print("\n--- Pesan GoRide ---")
    pickup = input("Masukkan lokasi penjemputan: ")
    destination = input("Masukkan lokasi tujuan: ")

    try:
        print("Mencari driver, mohon tunggu...")
        # --- PERBAIKAN DI SINI ---
        result = client.service.request_driver(current_user.id, pickup, destination)
        
        if "Tidak ada" in result.driver:
            print("\nMohon maaf, tidak ada driver yang tersedia saat ini. Silakan coba lagi.")
        else:
            print("\n--- Driver Ditemukan! ---")
            print(f"  Nama Driver : {result.driver}")
            print(f"  Tarif       : Rp {result.fare:,.0f}")
            print(f"  Order ID    : {result.orderId}")
            print("Driver akan segera menjemput Anda.")
    except exceptions.Fault as e:
        print(f"Error saat memesan: {e.message}")

def give_review():
    """Fungsi untuk memberi ulasan."""
    if not current_user:
        print("Anda harus login untuk memberi ulasan.")
        return

    try:
        print("\nMencari perjalanan yang telah selesai...")
        # --- PERBAIKAN DI SINI ---
        completed_orders = client.service.get_completed_orders(current_user.id)
        
        if not completed_orders:
            print("Anda tidak memiliki riwayat perjalanan yang bisa diberi ulasan.")
            return

        print("\n--- Pilih Perjalanan untuk Diberi Ulasan ---")
        for i, order in enumerate(completed_orders):
            print(f"{i + 1}. Driver: {order.driver_name}, Dari: {order.pickup}, Ke: {order.destination}")
        
        choice = -1
        while choice < 0 or choice >= len(completed_orders):
            try:
                choice = int(input(f"Pilih nomor perjalanan (1-{len(completed_orders)}): ")) - 1
            except ValueError:
                print("Input tidak valid.")

        selected_order = completed_orders[choice]
        
        rating = 0.0
        while rating < 1.0 or rating > 5.0:
            try:
                rating = float(input("Beri rating (1.0 - 5.0): "))
            except ValueError:
                print("Rating harus berupa angka.")

        review_text = input("Tulis ulasan Anda (opsional): ")
        
        # --- PERBAIKAN DI SINI ---
        result = client.service.give_review(
            user_id=current_user.id,
            driver_id=selected_order.driver_id,
            rating=rating,
            review_text=review_text
        )
        print(f"\nSERVER: {result}")

    except exceptions.Fault as e:
        print(f"Error saat memberi ulasan: {e.message}")


# --- Alur Utama Aplikasi ---
if __name__ == "__main__":
    while True:
        if not current_user:
            choice = main_menu()
            if choice == '1':
                register()
            elif choice == '2':
                login()
            elif choice == '0':
                break
            else:
                print("Pilihan tidak valid.")
        else:
            # --- PERBAIKAN DI SINI ---
            if current_user.role == 'user':
                choice = user_menu()
                if choice == '1':
                    order_driver()
                elif choice == '2':
                    give_review()
                elif choice == '3':
                    current_user = None
                    print("Anda telah logout.")
                else:
                    print("Pilihan tidak valid.")
            elif current_user.role == 'driver':
                print("\nAnda login sebagai Driver. Silakan gunakan aplikasi khusus Driver.")
                current_user = None