from zeep import Client

DRIVER_WSDL = "http://localhost:8001/?wsdl"
client = Client(DRIVER_WSDL)

order_id = int(input("Masukkan Order ID yang ingin Anda proses: "))
action = input("Konfirmasi atau Tolak? (Y/T): ").upper()

if action == "Y":
    response = client.service.confirm_order(order_id)
    print(f"Response from server: {response}")
elif action == "T":
    response = client.service.reject_order(order_id)
    print(f"Response from server: {response}")
else:
    print("Pilihan tidak valid.")