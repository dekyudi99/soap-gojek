from zeep import Client

MAIN_WSDL = "http://localhost:8000/?wsdl"
ENTITY_WSDL = "http://localhost:8002/?wsdl"
client = Client(MAIN_WSDL)
entity = Client(ENTITY_WSDL)

print("=== LOGIN DRIVER ===")
email = input("Masukkan Email: ")
password = input("Masukkan Password: ")

try:
    login_result = client.service.login(email, password)

    if login_result.success:
        print(login_result.message)
        token = login_result.token
    else:
        print("Login gagal:", login_result.message)
        exit()

except Exception as e:
    print("Gagal login:", e)
    exit()

while True:
    print("\n=== MENU DRIVER ===")
    print("1. Tampilkan Semua Pesanan")
    print("2. Konfirmasi / Tolak Pesanan")
    print("0. Keluar")

    pilih = input("Pilih menu: ")

    if pilih == "1":
        try:
            orders = entity.service.get_all_orders()
            if not orders:
                print("Tidak ada pesanan yang tersedia.")
            else:
                print("\nDaftar Pesanan:")
                for o in orders:
                    print(
                        f"[ID: {o.id}] {o.pickup} -> {o.destination} | Rp {o.total} | Status: {o.status}"
                    )
        except Exception as e:
            print("Gagal mengambil pesanan:", e)

    elif pilih == "2":
        order_id = int(input("Masukkan ID Order: "))
        confirm = input("Konfirmasi atau Tolak (confirmed/rejected): ").lower()

        if confirm not in ["confirmed", "rejected"]:
            print("Pilihan tidak valid! Harus 'confirmed' atau 'rejected'")
            continue

        try:
            result = client.service.konfirmasi_order(token, confirm, order_id)
            if result:
                print("Order berhasil dikonfirmasi!")
            else:
                print("Gagal mengonfirmasi order!")
        except Exception as e:
            print("Error konfirmasi:", e)

    elif pilih == "0":
        print("Keluar...")
        break

    else:
        print("Pilihan tidak valid.")
