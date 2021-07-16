##
## ===========================================
## =============== API CANTINA ===============
## ===========================================
## =======2020/2021 | CTESP - TPSI (OHP)======
## ===========================================
## ===========================================
##
## Authors: 
##   Goncalo Marques <goncalo.marques@estgoh.ipc.pt>
##   Aplicações Móveis (31000582)

from flask import Flask, jsonify, request
import logging, time, psycopg2, jwt, json
from datetime import datetime, timedelta
from functools import wraps
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
    return "Bem vindo à API Cantina!"


##########################################################
## TOKEN INTERCEPTOR
##########################################################
def auth_user(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        content = request.get_json()
        if content is None or "token" not in content or not content["token"]:
            return jsonify({'Erro': 'Token está em falta!', 'Code': UNAUTHORIZED_CODE})

        try:
            token = content["token"]
            data = jwt.decode(token, app.config['SECRET_KEY'])    

            decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
            if(decoded_token["expiration"] < str(datetime.utcnow())):
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

    if "n_identificacao" not in content or "senha" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    get_user_info = """
                SELECT *
                FROM utilizadores
                WHERE n_identificacao = %s AND senha = crypt(%s, senha);
                """

    values = [content["n_identificacao"], content["senha"]]

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_user_info, values)
                rows = cursor.fetchall()
                token = jwt.encode({
                    'id': rows[0][0],
                    'administrador': rows[0][7],
                    'expiration': str(datetime.utcnow() + timedelta(hours=1))
                }, app.config['SECRET_KEY'])
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Utilizador não encontrado"})
    return {"Code": OK_CODE, 'Token': token.decode('utf-8')}
  

##########################################################
## REGISTO DE UTILIZADOR
##########################################################
@app.route("/registar_utilizador", methods=['POST'])
def registar_utilizador():
    content = request.get_json()

    if "n_identificacao" not in content or "nome" not in content or "senha" not in content or "email" not in content or "cargo" not in content: 
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    get_user_info = """
                INSERT INTO utilizadores(n_identificacao, nome, senha, email, cargo, administrador) 
                VALUES(%s, %s, crypt(%s, gen_salt('bf')), %s, %s, FALSE);
                """

    values = [content["n_identificacao"], content["nome"], content["senha"], content["email"], content["cargo"]]

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_user_info, values)
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": str(error)})
    return {"Code": OK_CODE}


##########################################################
## REGISTO DE SOPAS
##########################################################
@app.route("/registar_sopa", methods=['POST'])
@auth_user
def registar_sopa():
    content = request.get_json()

    if "nome" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    get_user_info = """
                INSERT INTO sopas(nome) 
                VALUES(%s);
                """

    values = [content["nome"]]

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    if(not decoded_token['administrador']):
        return jsonify({"Erro": "O utilizador não tem esses privilégios", "Code": FORBIDDEN_CODE})

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_user_info, values)
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Sopa não inserida"})
    return {"Code": OK_CODE}


##########################################################
## REGISTO DE PRATOS
##########################################################
@app.route("/registar_prato", methods=['POST'])
@auth_user
def registar_prato():
    content = request.get_json()

    if "tipo" not in content or "nome" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    get_user_info = """
                INSERT INTO pratos(tipo, nome) 
                VALUES(%s, %s);
                """

    values = [content["tipo"], content["nome"]]

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    if(not decoded_token['administrador']):
        return jsonify({"Erro": "O utilizador não tem esses privilégios", "Code": FORBIDDEN_CODE})


    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_user_info, values)
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Prato não inserido"})
    return {"Code": OK_CODE}


##########################################################
## REGISTO DE SOBREMESAS
##########################################################
@app.route("/registar_sobremesa", methods=['POST'])
@auth_user
def registar_sobremesa():
    content = request.get_json()

    if "nome" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    get_user_info = """
                INSERT INTO sobremesas(nome) 
                VALUES(%s);
                """

    values = [content["nome"]]

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    if(not decoded_token['administrador']):
        return jsonify({"Erro": "O utilizador não tem esses privilégios", "Code": FORBIDDEN_CODE})


    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_user_info, values)
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Sobremesa não inserida"})
    return {"Code": OK_CODE}


##########################################################
## LISTAGEM SOPA, PRATOS E SOBREMESAS
##########################################################
@app.route("/listar_sps", methods=['POST'])
@auth_user
def listar_sps():
    content = request.get_json()

    get_sopas = """
                SELECT * from sopas ORDER BY nome;
                """

    get_pratos = """
                SELECT * from pratos ORDER BY nome;
                """

    get_sobremesas = """
                    SELECT * from sobremesas ORDER BY nome;
                    """

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    if(not decoded_token['administrador']):
        return jsonify({"Erro": "O utilizador não tem esses privilégios", "Code": FORBIDDEN_CODE})


    try:
        with db_connection() as conn:

            with conn.cursor() as cursor:

                cursor.execute(get_sopas)
                lista_sopas = cursor.fetchall()

                cursor.execute(get_pratos)
                lista_pratos = cursor.fetchall()

                cursor.execute(get_sobremesas)
                lista_sobremesas = cursor.fetchall()         

        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Erro": str(error), "Code": SERVER_ERROR})

    return jsonify(
        {                   
            "Sopas": [{"id_sopa": id_sopa, "nome": nome} for id_sopa, nome in lista_sopas],
            "Pratos": [{"id_prato": id_prato, "tipo": tipo, "nome": nome} for id_prato, tipo, nome in lista_pratos],
            "Sobremesas": [{"id_sobremesa": id_sobremesa, "nome": nome} for id_sobremesa, nome in lista_sobremesas]        
        }
    )


##########################################################
## LISTAGEM SOPAS
##########################################################
@app.route("/listar_sopas", methods=['POST'])
@auth_user
def listar_sopas():

    conn = db_connection()
    cur = conn.cursor()
    content = request.get_json()

    get_sopas = """
                SELECT * from sopas ORDER BY nome;
                """

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    if(not decoded_token['administrador']):
        return jsonify({"Erro": "O utilizador não tem esses privilégios", "Code": FORBIDDEN_CODE})

    cur.execute(get_sopas)
    rows = cur.fetchall()

    payload = []
    for row in rows:
        content = {'id_sopa': row[0], 'nome': row[1]}
        payload.append(content)

    conn.close()
    return jsonify(payload)




##########################################################
## LISTAR SE E ADMIN
##########################################################
@app.route("/isAdmin", methods=['POST'])
@auth_user
def isAdmin():

    conn = db_connection()
    cur = conn.cursor()
    content = request.get_json()

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])

    cur.execute("SELECT administrador FROM utilizadores WHERE id = %s;", (decoded_token["id"],))
    rows = cur.fetchall()
    conn.close()
    return {"admin": rows[0][0]}



##########################################################
## LISTAGEM SOBREMESAS
##########################################################
@app.route("/listar_sobremesas", methods=['POST'])
@auth_user
def listar_sobremesas():

    conn = db_connection()
    cur = conn.cursor()
    content = request.get_json()

    get_sopas = """
                SELECT * from sobremesas ORDER BY nome;
                """

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    if(not decoded_token['administrador']):
        return jsonify({"Erro": "O utilizador não tem esses privilégios", "Code": FORBIDDEN_CODE})

    cur.execute(get_sopas)
    rows = cur.fetchall()

    payload = []
    for row in rows:
        content = {'id_sobremesa': row[0], 'nome': row[1]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

##########################################################
## LISTAGEM PRATOS
##########################################################
@app.route("/listar_pratos", methods=['POST'])
@auth_user
def listar_pratos():

    conn = db_connection()
    cur = conn.cursor()
    content = request.get_json()

    get_sopas = """
                SELECT * from pratos ORDER BY nome;
                """

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    if(not decoded_token['administrador']):
        return jsonify({"Erro": "O utilizador não tem esses privilégios", "Code": FORBIDDEN_CODE})

    cur.execute(get_sopas)
    rows = cur.fetchall()

    payload = []
    for row in rows:
        content = {'id_prato': row[0], 'nome': row[1], 'tipo': row[2]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

##########################################################
## CRIAR EMENTA
##########################################################
@app.route("/criar_ementa", methods=['POST'])
@auth_user
def criar_ementa():
    content = request.get_json()

    if "preco" not in content or "sobremesas_id_sobremesa" not in content or "sopas_id_sopa" not in content or "pratos_id_prato" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    get_user_info = """
                INSERT INTO ementas(preco, utilizadores_id, sobremesas_id_sobremesa, sopas_id_sopa, pratos_id_prato) 
                VALUES(%s, %s, %s, %s, %s) RETURNING id_ementa;
                """

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    if(not decoded_token['administrador']):
        return jsonify({"Erro": "O utilizador não tem esses privilégios", "Code": FORBIDDEN_CODE})

    values = [content["preco"], decoded_token['id'], content["sobremesas_id_sobremesa"], content["sopas_id_sopa"], content["pratos_id_prato"]]

    query = ""

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_user_info, values)
                query = cursor.fetchone()[0]
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Ementa não inserida"})
    return "%s" % (query)


##########################################################
## LISTAR EMENTAS
##########################################################
@app.route("/listar_ementas", methods=['POST'])
@auth_user
def listar_ementas():
    content = request.get_json()
    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT sopas.nome, pratos.nome, sobremesas.nome, preco, ementas.id_ementa FROM ementas, sopas, pratos, sobremesas WHERE ementas.sopas_id_sopa = sopas.id_sopa AND ementas.pratos_id_prato = pratos.id_prato AND ementas.sobremesas_id_sobremesa = sobremesas.id_sobremesa;")
    rows = cur.fetchall()

    payload = []
    for row in rows:
        content = {'sopa': row[0], 'pratos': row[1], 'sobremesa': row[2], 'preco': row[3], 'Id': row[4]}
        payload.append(content)

    conn.close()
    return jsonify(payload)


##########################################################
## ACTUALIZAR UTILIZADOR
##########################################################
@app.route("/actualizar_utilizador", methods=['POST'])
@auth_user
def actualizar_utilizador():
    content = request.get_json()

    if "nome" not in content or "email" not in content: 
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    get_user_info = """
                UPDATE utilizadores SET nome = %s, email = %s WHERE id = %s;
                """
    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    values = [content["nome"], content["email"], decoded_token["id"]]

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_user_info, values)
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Utilizador não actualizado!"})
    return {"Code": OK_CODE}


##########################################################
## CARREGAR SALDO
##########################################################
@app.route("/carregar_saldo", methods=['POST'])
@auth_user
def carregar_saldo():
    content = request.get_json()

    if "n_identificacao" not in content or "saldo" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    get_user_info = """
                UPDATE utilizadores SET saldo = saldo + %s WHERE n_identificacao = %s;
                """

    values = [content["saldo"], content["n_identificacao"]]

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    if(not decoded_token['administrador']):
        return jsonify({"Erro": "O utilizador não tem esses privilégios", "Code": FORBIDDEN_CODE})

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_user_info, values)
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Saldo não carregado"})
    return {"Code": OK_CODE}



##########################################################
## REGISTAR EMENTA
##########################################################
@app.route("/registar_ementa", methods=['POST'])
@auth_user
def registar_ementa():
    content = request.get_json()

    if "data" not in content or "ementas_id_ementa" not in content or "tipo" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    get_user_info = """
                INSERT INTO registo_ementas(data, ementas_id_ementa, tipo) VALUES(%s, %s, %s);
                """

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    if(not decoded_token['administrador']):
        return jsonify({"Erro": "O utilizador não tem esses privilégios", "Code": FORBIDDEN_CODE})

    values = [content["data"], content["ementas_id_ementa"], content["tipo"]]

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_user_info, values)
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Ementa não registada"})
    return {"Code": OK_CODE}


##########################################################
## COMPRAR EMENTA
##########################################################
@app.route("/comprar_ementa", methods=['POST'])
@auth_user
def comprar_ementa():
    content = request.get_json()

    if "registo_ementas_id_registo" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    get_user_info = """
                    INSERT INTO registo_reservas(data, registo_ementas_id_registo, utilizadores_id) VALUES(now(), %s, %s) RETURNING registo_ementas_id_registo;
                """

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    if(not decoded_token['administrador']):
        return jsonify({"Erro": "O utilizador não tem esses privilégios", "Code": FORBIDDEN_CODE})

    values = [content["registo_ementas_id_registo"], decoded_token["id"]]

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(get_user_info, values)
                preco_refeicao = cursor.fetchone()[0]
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Ementa não comprada"})
    return {"Code": OK_CODE}


##########################################################
## LISTAR EMENTAS COMPRADAS
##########################################################
@app.route("/listar_ementas_compradas", methods=['POST'])
@auth_user
def listar_ementas_compradas():
    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])

    cur.execute("SELECT registo_reservas.data, registo_ementas.tipo, registo_ementas.data, ementas.preco, sobremesas.nome, sopas.nome, pratos.nome, pratos.tipo, registo_reservas.id_reserva FROM registo_reservas, registo_ementas, ementas, sobremesas, sopas, pratos WHERE registo_reservas.utilizadores_id = %s AND registo_reservas.registo_ementas_id_registo = registo_ementas.id_registo AND registo_ementas.ementas_id_ementa = ementas.id_ementa AND ementas.sobremesas_id_sobremesa = sobremesas.id_sobremesa AND ementas.sopas_id_sopa = sopas.id_sopa AND ementas.pratos_id_prato = pratos.id_prato;", (decoded_token["id"],))
    rows = cur.fetchall()

    payload = []

    for row in rows:
        content = {"Id": row[8],"Data da Compra": row[0], "Tipo de Refeição": row[1], "Data da Refeição": row[2], "Preço": row[3], "Sobremesa": row[4], "Sopa": row[5], "Prato": row[6], "Tipo": row[7]}
        payload.append(content)

    conn.close()
    return jsonify(payload)



##########################################################
## LISTAR EMENTAS POR INDICACAO DE COMPRA POR DATA
##########################################################

@app.route("/listar_ementas_compradas_data", methods=['POST'])
@auth_user
def listar_ementas_compradas_data():

    content = request.get_json()

    if "data" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    conn = db_connection()
    cur = conn.cursor()

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])

    cur.execute("SELECT  registo_ementas.id_registo, registo_ementas.tipo, registo_ementas.data, ementas.preco, sobremesas.nome, sopas.nome, pratos.nome, pratos.tipo, CASE WHEN registo_ementas.id_registo in (SELECT registo_ementas_id_registo from registo_reservas where utilizadores_id = %s) THEN true ELSE false END AS COMPRADA, registo_ementas.id_registo FROM registo_ementas, ementas, sobremesas, sopas, pratos WHERE registo_ementas.ementas_id_ementa = ementas.id_ementa AND ementas.sobremesas_id_sobremesa = sobremesas.id_sobremesa AND ementas.sopas_id_sopa = sopas.id_sopa AND ementas.pratos_id_prato = pratos.id_prato AND registo_ementas.data = %s;", (decoded_token["id"], content["data"],))

    rows = cur.fetchall()

    payload = []
    for row in rows:
        content = {"Id": row[0], "Tipo de Refeição": row[1], "Data da Refeição": row[2], "Preço": row[3], "Sobremesa": row[4], "Sopa": row[5], "Prato": row[6], "Tipo": row[7], "Comprado": row[8], "Id": row[9]}
        payload.append(content)

    conn.close()
    return jsonify(payload)


##########################################################
## LISTAR EMENTAS Registadas
##########################################################
@app.route("/listar_ementas_registadas", methods=['POST'])
@auth_user
def listar_ementas_registadas():

    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])

    cur.execute("SELECT registo_ementas.tipo, registo_ementas.data, ementas.preco, sobremesas.nome, sopas.nome, pratos.nome, pratos.tipo, registo_ementas.id_registo FROM registo_ementas, ementas, sobremesas, sopas, pratos WHERE registo_ementas.ementas_id_ementa = ementas.id_ementa AND ementas.sobremesas_id_sobremesa = sobremesas.id_sobremesa AND ementas.sopas_id_sopa = sopas.id_sopa AND ementas.pratos_id_prato = pratos.id_prato")
    rows = cur.fetchall()

    payload = []
    for row in rows:
        content = {"Data da Refeição": row[1], "Tipo de Refeição": row[0], "Preço": row[2], "Sobremesa": row[3], "Sopa": row[4], "Prato": row[5], "Tipo": row[6], "Id": row[7]}
        payload.append(content) 

    conn.close()
    return jsonify(payload)


##########################################################
## TOTAL GASTOS
##########################################################
@app.route("/total_gastos", methods=['POST'])
@auth_user
def total_gastos():

    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])

    cur.execute("SELECT SUM(ementas.preco) AS soma_gastos FROM registo_reservas, registo_ementas, ementas, sobremesas, sopas, pratos WHERE registo_reservas.utilizadores_id = %s AND registo_reservas.registo_ementas_id_registo = registo_ementas.id_registo AND registo_ementas.ementas_id_ementa = ementas.id_ementa AND ementas.sobremesas_id_sobremesa = sobremesas.id_sobremesa AND ementas.sopas_id_sopa = sopas.id_sopa AND ementas.pratos_id_prato = pratos.id_prato;", (decoded_token["id"],))
    rows = cur.fetchall()

    payload = []

    for row in rows:
        content = {"Total dos Gastos": row[0]}
        payload.append(content)

    conn.close()
    return jsonify(payload)


##########################################################
## CONSULTAR SALDO
##########################################################
@app.route("/consultar_saldo", methods=['POST'])
@auth_user
def consultar_saldo():

    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])

    cur.execute("SELECT CAST(CAST(saldo AS NUMERIC(8,2)) AS VARCHAR) FROM utilizadores WHERE id = %s;", (decoded_token["id"],))
    rows = cur.fetchall()
    conn.close()
    return {"Saldo": rows[0][0]}



##########################################################
## CONSULTAR UTILIZADOR
##########################################################
@app.route("/consultar_utilizador", methods=['POST'])
@auth_user
def consultar_utilizador():
    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])

    cur.execute("SELECT * FROM utilizadores WHERE id = %s;", (decoded_token["id"],))
    rows = cur.fetchall()

    conn.close()
    return jsonify({"Id": rows[0][1], "nome": rows[0][2], "e-mail": rows[0][4], "cargo": rows[0][6]})



##########################################################
## ENVIAR REPORTS
##########################################################
@app.route("/enviar_report", methods=['POST'])
@auth_user
def enviar_report():
    content = request.get_json()

    if "assunto" not in content or "mensagem" not in content or "info" not in content or "anonimo" not in content:
        return jsonify({"Code": BAD_REQUEST_CODE, "Erro": "Parâmetros inválidos"})

    insert_report = """
                INSERT INTO report(assunto, mensagem, utilizador_id, info_dispositivo, data_envio) VALUES(%s, %s, %s, %s, now());
                """

    decoded_token = jwt.decode(content['token'], app.config['SECRET_KEY'])
    
    if content["anonimo"] == "True":
        user = None
    else:
        user = decoded_token["id"]

    values = [content["assunto"], content["mensagem"], user, content["info"]]

    try:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(insert_report, values)
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify({"Code": NOT_FOUND_CODE, "Erro": "Report não registado"})
    return {"Code": OK_CODE}



##########################################################
## DATABASE ACCESS
##########################################################
def db_connection():
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    db = psycopg2.connect(DATABASE_URL)
    return db


if __name__ == "__main__":

    time.sleep(1) # just to let the DB start before this print :-)

    app.run(port=8080, debug=True, threaded=True)