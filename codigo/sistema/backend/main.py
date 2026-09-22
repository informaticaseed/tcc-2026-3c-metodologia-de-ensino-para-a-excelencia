import database
import bcrypt
import auth
import web

from analise_de_dados import analise_de_dados

#print(auth.login(input("name: "), input("password: ")))
#web.start_server()

analise_de_dados.run_pipeline()

#print(auth.login(auth.get_user_uuid(input("email: ")), input("password: ")))