# users = ["anna", "max", "jack"]
# password = "root"
#
# while True:
#     ism = input("Ismingizni kirting: ")
#     parol = input("Parol kiiting: ")
#
#     if ism in users and parol == password:
#         print("ruxsat etildi ")
#         break
#     else:
#         print("kirishga ruhsat yoq ")

users = ["anna", "max", "jack"]
password = "root"

while True:
    ism = input("Ismingizni kiriting: ")
    parol = input("Parolni kiriting: ")

    if ism in users and parol == password:
        print("Ruxsat etildi")
        break
    else:
        print("Kirishga ruhsat yo'q")