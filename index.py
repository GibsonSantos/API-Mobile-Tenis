##
## ===========================================
## =============== API TESTE ===============
## ===========================================
## =======2020/2021 ==============================
## ===========================================
## ===========================================
##
## Authors: 
##   Goncalo Marques
import base64

from flask import Flask, jsonify, request
import logging, time, psycopg2, jwt, json
from datetime import datetime, timedelta
from functools import wraps
from cryptography.fernet import Fernet
import bcrypt
import os
  
app = Flask(__name__)   

app.config['SECRET_KEY'] = 'it\xb5u\xc3\xaf\xc1Q\xb9\n\x92W\tB\xe4\xfe__\x87\x8c}\xe9\x1e\xb8\x0f'

NOT_FOUND_CODE = 400
OK_CODE = 200
SUCCESS_CODE = 201
BAD_REQUEST_CODE = 400
UNAUTHORIZED_CODE = 401
FORBIDDEN_CODE = 403
NOT_FOUND = 404
SERVER_ERROR = 500
  
@app.route('/', methods = ["GET"])
def home():
    return "Bem vindo à API!"


##########################################################
## TOKEN INTERCEPTOR
##########################################################
def auth_user(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({'Erro': 'Token está em falta!', 'Code': UNAUTHORIZED_CODE})

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])    

            decoded_token = jwt.decode(token, app.config['SECRET_KEY'])
            if(decoded_token["expiration"] < str(datetime.utcnow())):
                decoded_token = jwt.decode(token, app.config['SECRET_KEY'])
                print(decoded_token["id"])
                return jsonify({"Erro": "O Token expirou!", "Code": NOT_FOUND_CODE})

        except Exception as e:
            return jsonify({'Erro': 'Token inválido', 'Code': FORBIDDEN_CODE})
        return func(*args, **kwargs)
    return decorated


##########################################################
## LOGIN
##########################################################
@app.route("/login", methods=['POST'])
def login():
    content = request.get_json()

    if "name" not in content or "password" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    get_user_info = """
                SELECT *
                FROM utilizadores
                WHERE u_name = %s AND u_password = crypt(%s, u_password);
                """
    values = [content["name"],content["password"]]
    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_user_info, values)
                rows = cursor.fetchall()
                token = jwt.encode({
                    'id': rows[0][0],
                    'expiration': str(datetime.utcnow() + timedelta(hours=1))
                }, app.config['SECRET_KEY'])

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Utilizador não encontrado"})
    return jsonify({"Code": OK_CODE, 'Token': token.decode('utf-8')})

  

##########################################################
## REGISTO DE UTILIZADOR
##########################################################
@app.route("/registar_utilizador", methods=['POST'])
def registar_utilizador():
    content = request.get_json()

    if "name" not in content or "password" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})


    get_user_info = """
                INSERT INTO utilizadores(u_name, u_password) 
                VALUES(%s,crypt(%s,gen_salt('bf')));
                """

    valuesInsert = [content["name"], content["password"]]

    check_unique_name = """
                SELECT * from utilizadores 
                WHERE u_name = %s
                """

    valuesCheck = [content['name']];


    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(check_unique_name, valuesCheck)
                if cursor.fetchone():
                    return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Nome já está a ser utilizado"})
                cursor.execute(get_user_info, valuesInsert)
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": str(error)})
    return jsonify({"Code": OK_CODE})


##########################################################
## INSERIR JOGO
##########################################################
@app.route("/start_game", methods=['POST'])
@auth_user
def start_game():
    content = request.get_json()

    token = request.headers.get("Authorization")

    if "g_name" not in content or "g_name_player1" not in content or "g_name_player2" not in content or "g_date" not in content or "g_versao" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parametros invalidos"})

    insertGame = "INSERT into games(g_name, g_date,g_name_player1,g_name_player2, g_versao, g_u_id) VALUES(%s, %s, %s,%s,%s,%s)"

    decoded_token = jwt.decode(token, app.config['SECRET_KEY'])

    values = [content["g_name"], content["g_date"], content["g_name_player1"],content["g_name_player2"],content["g_versao"], decoded_token["id"]]

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(insertGame,values)
                cursor.execute("SELECT MAX(g_id) from games")
                game_id = cursor.fetchone()[0]
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": str(error)})
    return jsonify({"Code": OK_CODE, "game_id":game_id})

##########################################################
## CONSULTAR JOGOS
##########################################################
@app.route("/consultar_jogos", methods=['GET'])
@auth_user
def consultar_jogos():
    query = """
        SELECT * from games ORDER BY g_id
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                games = [{col[0]: row[id] for id, col in enumerate(cursor.description)} for row in cursor.fetchall()]
                return jsonify(games);
    except(Exception,psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"Code": NOT_FOUND_CODE, "ERROR": "Erro ao buscar os jogos!"})

##########################################################
## CONSULTAR JOGOS
##########################################################
@app.route("/live_game/<g_id>", methods=['GET'])
@auth_user
def live_game(g_id):
    query = """
        SELECT * from games where g_id = %s ORDER BY g_id
    """

    values = [g_id]
    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query,values)
                columns = [col[0] for col in cursor.description]
                game = dict(zip(columns, cursor.fetchone()))
                return jsonify(game)
    except(Exception,psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"Code": NOT_FOUND_CODE, "ERROR": "Erro ao busca o jogo!"})


##########################################################
## EDITAR JOGO (Nome, nome de jogador,...)
##########################################################
@app.route("/editar_jogo", methods=['PUT'])
@auth_user
def editar_jogo():
    content = request.get_json()

    query = """
         UPDATE games
         SET g_name = %s, g_name_player1 = %s, g_name_player2 = %s 
         WHERE g_id = %s AND g_u_id = %s
    """

    decoded_token = jwt.decode(content["token"], app.config['SECRET_KEY'])

    values = [content["g_name"], content["g_name_player1"], content["g_name_player2"], content["g_id"], decoded_token["id"]]
    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query,values)
                rows_update = cursor.rowcount
    except(Exception,psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": str(error)})
    if rows_update > 0:
        return jsonify({"Code": OK_CODE})
    else:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Atualização proibida"})

##########################################################
## EDITAR JOGO (Nome, nome de jogador,...)
##########################################################
@app.route("/update_score", methods=['PUT'])
@auth_user
def update_score():
    content = request.get_json()

    token = request.headers.get("Authorization")

    if "column" not in content or "versaoGame" not in content or "scoreSet" not in content :
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parametros invalidos"})

    decoded_token = jwt.decode(token, app.config['SECRET_KEY'])

    values = [content["column"].strip("'"),"'"+ content["scoreSet"] +"'",content["versaoGame"] ,decoded_token["id"]]

    query = """UPDATE games SET {} = {}, g_versao = {}
               WHERE g_id = (SELECT g_id FROM games
                            WHERE g_u_id = {}
                            ORDER BY g_id DESC
                            LIMIT 1)""".format(*values)

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query,values)
                rows_update = cursor.rowcount
    except(Exception,psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": str(error)})
    if rows_update > 0:
        return jsonify({"Code": OK_CODE})
    else:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Atualização proibida"})

@app.route("/delete_game/<g_id>", methods=['DELETE'])
@auth_user
def delete_game(g_id):
    token = request.headers.get("Authorization")
    query = """     
            DELETE FROM games
            where g_id = %s AND g_u_id = %s
    """

    decoded_token = jwt.decode(token, app.config["SECRET_KEY"])

    values = [g_id,decoded_token["id"]]

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query,values)
                rows_deleted = cursor.rowcount
    except(Exception,psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"Code": NOT_FOUND_CODE, "Error": str(error)})
    if rows_deleted > 0:
        return jsonify({"Code": OK_CODE})
    else:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Deleção proibida"}),400




##########################################################
## DATABASE ACCESS
##########################################################
def db_connection():
    db = psycopg2.connect("dbname=db2020127699 user=a2020127699 password=Gibsonoliveira10 host=aid.estgoh.ipc.pt port=5432")
    return db


if __name__ == "__main__":

    app.run(port=8080, debug=True, threaded=True)