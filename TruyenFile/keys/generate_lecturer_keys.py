from Crypto.PublicKey import RSA

# Tạo khóa RSA 2048-bit
key = RSA.generate(2048)

# Trích xuất khóa
private_key = key.export_key()
public_key = key.publickey().export_key()

# Ghi vào file
with open("lecturer_private.pem", "wb") as f:
    f.write(private_key)

with open("lecturer_public.pem", "wb") as f:
    f.write(public_key)

print("Đã tạo xong lecturer_private.pem và lecturer_public.pem")
