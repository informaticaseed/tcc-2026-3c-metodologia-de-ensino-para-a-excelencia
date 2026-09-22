import database
import bcrypt
import auth
import web

#print(auth.login(input("name: "), input("password: ")))
web.start_server()

#print(auth.login(auth.get_user_uuid(input("email: ")), input("password: ")))