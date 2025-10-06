from zeep import Client

ORDER_WSDL = "http://localhost:8000/?wsdl"
client = Client(ORDER_WSDL)

pickup = input("Masukkan Lokasi Anda: ")
destination = input("Masukkan Tujuan Anda: ")

order = client.service.request_driver(pickup, destination)

print("Order Summary:")
print(f"Order ID   : {order.orderId}")
print(f"Driver     : {order.driver}")
print(f"Pickup     : {order.pickup}")
print(f"Destination: {order.destination}")
print(f"Fare       : Rp {order.fare}")
