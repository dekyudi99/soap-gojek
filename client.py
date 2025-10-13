from zeep import Client

SERVICE_WSDL = "http://localhost:8000/?wsdl"
USER_WSDL = "http://localhost:8002/?wsdl"

client = Client(SERVICE_WSDL)
user = Client(USER_WSDL)

# Daftar Service
service = (
    "1. Daftar",
    "2. Masuk",
    "3. Pesan",
    "4. Profil",
    "0. Gak Jadi"
)

auth = False

while True: 
    for x in service:
        print(x)

    # Pilih Service
    choose = int(input("Apa yang ingin anda lakukan (Masukkan angka): "))

    if (choose == 1):
        name = input("Masukkan Nama: ")
        email = input("Masukkan Email: ")
        role = input("Pilih Role: ")
        password = input("Masukkan Password: ")
        address = input("Masukkan Alamat Anda: ")
        register = client.service.register(name, email, role, password, address)
        print(register)
    elif (choose == 2 ):
        email = input("Masukkan Email: ")
        password = input("Masukkan Password: ")
        try:
            result = client.service.login(email, password)
            auth = result.success
            print(result.message)
            print(result.token)
        except Exception as e:
            print("GAGALLLL, ", e)
    elif (choose == 3 ):
        if (auth == True):
            print("Berhasil Wokkk")
        else:
            print("Gagal Wokkk!")
    elif (choose == 0 ):
        break
    else: 
        print("Not Found BRO!, Pilih yang bener")

