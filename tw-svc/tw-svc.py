from bottle import Bottle, route, run, get, template, post, request
# from cred import cred_consumer_key, cred_consumer_secret, cred_access_token, cred_access_token_secret
import pymysql
import time
# import tweepy
import json
import os
import datetime
import python_jwt as jwt
import Crypto.PublicKey.RSA as RSA
import logging
import jws
import pika

time.sleep(15)

mysql_config = {
    'host' : os.environ['MYSQL_ENDPOINT'],
    'db' : os.environ['MYSQL_DATABASE'],
    'user' : os.environ['MYSQL_USER'],
    'passwd': os.environ['MYSQL_PASSWORD']
}
logger = logging.getLogger('tw-svc')
logger.setLevel(logging.DEBUG)
logger.propagete = False
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

app = Bottle()



public_key_file = os.path.join(os.path.dirname(__file__), 'key', 'key.pub')
with open(public_key_file, 'r') as fd:
    public_key = RSA.importKey(fd.read())



@app.post('/tw-svc/encuesta')
def crear_encuesta():
    # Creacion de la cola
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ['RABBITMQ_ENDPOINT']))
    channel = connection.channel()

    logger.info('ENCUESTA ')
    token_type, token = request.headers['Authorization'].split()
    print token
    usr = ""
    try:
        header, claims = jwt.verify_jwt(token, public_key, ['RS256'])
    except jws.exceptions.SignatureError:
        message = "Invalid token"

    usr = claims['userid']
    logger.info('USER : %s ', usr)
    logger.info('Processing create ')
    data = request.json
    cnx = None
    try:
        #variables para el request
        state = "En proceso"
        total = 0
        paramHash = data['hash']
        paramTime = data['time']
        paramSurvey = data['surveyname']


        logger.info('connect : %s', mysql_config)
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()
        insert_test = "INSERT INTO jobs (username, surveyname, hash, tiempo, count,state) VALUES (%s,%s,%s,%s,%s,%s)"
        data = (usr, paramSurvey, paramHash, paramTime, total, state) # tupla s
        cursor.execute(insert_test, data)
        cnx.commit()
        cursor.close()
        ret = {"status": "OK"}
    except pymysql.Error as err:
        logger.info('error : %s', err)
        ret = {"status": "FAIL", "msg": err}
    finally:
        if cnx:
            cnx.close()
    logger.info('---------------ANTES DEL MSG---------------')
    msg = {"user": usr, "paramHash": paramHash, "paramTime": paramTime, "paramSurvey": paramSurvey}
    logger.info('SEND : %s ', msg)
    channel.basic_publish(exchange='', routing_key='newsurvey', body=json.dumps(msg))
    connection.close()
    # ret = {"status": "OK"}
    return ret

@app.put('/tw-svc/update')
def update():
    logger.info('UPDATEEE')
    data = request.body.read()
    json_data = json.loads(str(data))

    logger.info('json recibido : %s', json_data)
    paramUsr = json_data['paramUsr']
    paramHash = json_data['paramHash']
    paramTime = json_data['paramTime']
    paramSurvey = json_data['paramSurvey']
    paramResultado = json_data['paramResultado']
    state = "Finalizo"
    try:
        logger.info(' ----try mysql---- ')
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()
        update = "UPDATE jobs SET state = %s , count = %s  WHERE username = %s AND surveyname = %s"
        data = (state, paramResultado, paramUsr, paramSurvey) # tupla s
        cursor.execute(update, data)
        cnx.commit()
        cursor.close()
        ret = {"status": "OK"}
    except pymysql.Error as err:
        logger.info('error : %s', err)
        ret = {"status": "FAIL", "msg": err}
    finally:
        if cnx:
            cnx.close()
    return ret



@app.get('/tw-svc/all')
def retornar_encuestas():
    token_type, token = request.headers['Authorization'].split()
    ret = {"status":"OK"}
    usr = ""
    try:
        header, claims = jwt.verify_jwt(token, public_key, ['RS256'])
    except jws.exceptions.SignatureError:
        message = "Invalid token"
    usr = claims['userid']

    logger.info('USER : %s', usr)
    print "antes de cnx"
    print usr
    # cnx = None
    print "hago consulta"
    try:
        logger.info('connect : %s', mysql_config)
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()
        select_test = "SELECT * FROM jobs WHERE username = %s"
        logger.info('ahoraHaceElSELECT : %s', select_test)
        data = (claims['userid'])
        cursor.execute(select_test, data)
        results = cursor.fetchall()
        logger.info('results : %s', results)
        ret = {"status":"OK", "table":results}
        cnx.commit()
        cursor.close()
    except pymysql.Error as err:
        logger.info('error : %s', err)
        ret = {"status": "FAIL", "msg": err}
    finally:
        logger.info('FINALLY')
        if cnx:
            cnx.close()
    logger.info('RETURN RET: %s', ret)
    return ret


run(app, host='0.0.0.0', port=8088)
