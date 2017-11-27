import pymysql
from  bottle import Bottle, route, run, get, template, post, request
import os
import datetime
import python_jwt as jwt
import Crypto.PublicKey.RSA as RSA
import logging

##create logger with auth-svc
logger = logging.getLogger('auth-svc')
logger.setLevel(logging.DEBUG)
logger.propagate = False

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

## en la veriable app guardo una instancia de bootle
app = Bottle()

mysql_config = {
    'host' : os.environ['MYSQL_ENDPOINT'],
    'db' : os.environ['MYSQL_DATABASE'],
    'user' : os.environ['MYSQL_USER'],
    'passwd': os.environ['MYSQL_PASSWORD']
}

#clave privada, para crear token
private_key_file = os.path.join(os.path.dirname(__file__), 'key', 'key')
with open(private_key_file, 'r') as fd:
    private_key = RSA.importKey(fd.read())
#clave publica para verificar token
public_key_file = os.path.join(os.path.dirname(__file__), 'key', 'key.pub')
with open(public_key_file, 'r') as fd:
    public_key = RSA.importKey(fd.read())

def init_db():
    logger.info('Processing init database')

    cnx = None
    try:
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()

        create_table = "create table if not exists spt.log(usuario varchar(50), password(50))"
        cursor.execute(create_table)
        cursor.close

    except pymysql.Error as err:
        msg = "Failed init database{}".format(err)
        logger.error(msg)
    finally:
        if cnx:
            cnx.close()
    return


@app.route('/hello',method="GET")
def hello():
    return "Hello World!"
## lo mismo que route pero definis @app.get que es mas rapido y legible para especificar
## el metodo
@app.get('/auth-svc/')
@app.get('/auth-svc/hello/<name>')
## reconoce que la funcion para la ruta '/hello/<name>' y '/'es greet() porque
## es la primer funcion escrita a continuacion de las rutas
def greet(name='Stranger'):
    return template('Hello {{name2}}', name2=name)

#funcion que testea si se recibio token
@app.get('/test')
def test():
    data = request.headers['Authorization']
    print "funcion test \n header:"
    print data
    ret = {"status": "OK", "token": data}
    return ret

@app.post('/auth-svc/param')
def hello_json():
    data = request.json
    param = data['param']
    ret = {"status":"OK", "param": param}
    return ret

@app.post('/auth-svc/login')
def login():
    logger.info('Processing login')
    data = request.json
    param = data['user']
    param2 = data['pass']
    logger.info('data : %s', data)
    cnx = None
    try:
        logger.info('connect : %s', mysql_config)
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()
        # insert_test = "SELECT 'usuario' FROM 'log' WHERE 'usuario' = %s AND 'password' = %s"
        insert_test = "SELECT `usuario` FROM `log` WHERE `usuario` = %s AND `password` = %s"
        data = (param, param2) # tupla s
        cursor.execute(insert_test, data)
        results = cursor.fetchone()
        #return results
        for row in results:
            if row[0] == None:
                print "Failed row == none "
            else:
                payload = {"userid" : results};
                token = jwt.generate_jwt(payload, private_key, 'RS256',datetime.timedelta(minutes=5))
                # retdata = {
                # "status" : "OK",
                # "token" : token
                # }
                return {"status":"OK", "token":token}
        cnx.commit()
        cursor.close()
    except pymysql.Error as err:
        logger.info('error : %s', err)
        print "Failed to log data: {}".format
        ret = {"status": "FAIL", "msg": err}
        return ret
    finally:
        if cnx:
            cnx.close()

@app.post('/auth-svc/register')
def register():
    data = request.json
    param = data['username']
    param2 = data['pass']
    cnx = None
    try:
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()
        insert_test = "SELECT `usuario` FROM `log` WHERE `usuario` = %s"
        data = (param) # tupla s
        cursor.execute(insert_test, data)
        results = cursor.fetchone()

        if(not results):
            #el usuario no existe en la bd, entonces puedo crearlo
            insert = "INSERT INTO log (usuario, password) VALUES (%s, %s)"
            usuario = (param, param2)
            cursor.execute(insert, usuario)
            cnx.commit()
            cursor.close()
            payload = {"userid" : param};
            token = jwt.generate_jwt(payload, private_key, 'RS256',datetime.timedelta(minutes=5))
            ret = {"status": "OK",
                   "msg": "usuario creado correctamente",
                   "token": token
                   }
            return ret
        else:
            print ("usuario existe en la base de datos")
            cnx.commit()
            cursor.close()
            ret = {"status": "FAIL", "msg": "usuario ya existe."}
            return ret
        cursor.close()
    except pymysql.Error as err:
        print "Failed to insert data: {}".format(err)
        ret = {"status": "FAIL", "msg": err}
        return ret
    finally:
        if cnx:
            cnx.close()

init_db()
run(app, host='0.0.0.0', port=8081)
