import database
import bcrypt
import auth

#print(auth.login(input("name: "), input("password: ")))

while True:
    action = input("\n\n\nEscolha uma ação\n\n1 Login\n2 Criar conta\n3 Deletar conta\n4 Procurar conta por nome\n")

    match int(action):
        case 1:
            print(auth.login(input("name: "), input("password: ")))

        case 2:
            auth.create_account(input("name: "), input("password: "))

        case 3:
            auth.delete_account(input("uuid: "))

        case 4:
            print(auth.get_user_by_username(input("name: ")))