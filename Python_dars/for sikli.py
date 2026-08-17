# mevalar = ["Olma, uzum, anor"]
# for meva in mevalar:
#     print(meva)





# for i in range(10):
#     print(i)





# for hafr in "salome":
#     print(hafr)



# for i in range(2):
#     for f in range(3):
#         print(i,f)



#
# for i in range(11):
#     if i == 7:
#         break
#     print(i)
#


# for i in range(11):
# #     if i % 2 == 0:
# #         continue
# #     print(i)




# sonlar = [5, 8, 12, -3, 7, -9, 2]
# for son in sonlar:
#     if son < 0:
#         print("Birinchi manfiy son:", son)
#         break



# for i in range(1, 31):
#     if i > 25:
#         break
#     if i % 3 != 0:
#         continue
#     print(i)
#


soz = "salomlashuvxdavomi"
unlilar = "aoueiAOUEI"
son = 0

for harf in soz:
    if harf == "x":
        break
    if harf not in unlilar:
        continue
    son += 1

print("Unlilar soni:", son)