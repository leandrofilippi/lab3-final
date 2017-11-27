# from  bottle import Bottle, route, run, get, template, post, request
# from cred import cred_consumer_key, cred_consumer_secret, cred_access_token, cred_access_token_secret
# import pymysql
# import time
# import tweepy
# import json
# import os
# import datetime
# import python_jwt as jwt
# import Crypto.PublicKey.RSA as RSA
# import logging
# import jws
#
# mysql_config = {
#     'host' : os.environ['MYSQL_ENDPOINT'],
#     'db' : os.environ['MYSQL_DATABASE'],
#     'user' : os.environ['MYSQL_USER'],
#     'passwd': os.environ['MYSQL_PASSWORD']
# }
# logger = logging.getLogger('tw-svc')
# logger.setLevel(logging.DEBUG)
# logger.propagete = False
# ch = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# ch.setFormatter(formatter)
# logger.addHandler(ch)
#
# app = Bottle()
#
# # Authentication details. To  obtain these visit dev.twitter.com
# consumer_key =  cred_consumer_key
# consumer_secret = cred_consumer_secret
# access_token = cred_access_token
# access_token_secret = cred_access_token_secret
#
# #clave publica para verificar token
# public_key_file = os.path.join(os.path.dirname(__file__), 'key', 'key.pub')
# with open(public_key_file, 'r') as fd:
#     public_key = RSA.importKey(fd.read())
#
# class BreakLoopException(Exception):
#     pass
#
# # This is the listener, resposible for receiving data
# class MyStreamListener(tweepy.StreamListener):
#
#     def __init__(self,duration):
#         tweepy.StreamListener.__init__(self)
#         self.stream = None
#         self.count = 0
#         self.duration = duration
#         self.start_time = None
#         self.end_time = None
#         return
#
#     #def on_data(self, data):
#         #logger.debug("\non_data\n")
#         # Twitter returns data in JSON format - we need to decode it first
#         #decoded = json.loads(data)
#         # Also, we convert UTF-8 to ASCII ignoring all bad characters sent by users
#         #print '@%s: %s' % (decoded['user']['screen_name'], decoded['text'].encode('ascii', 'ignore'))
#         #return True
#
#     def on_connect(self):
#         logger.debug("\non_connect\n")
#         self.start_time = time.time()
#         self.end_time = self.start_time + self.duration
#         return
#
#     def keep_alive(self):
#         logger.debug("\nkeep_alive\n")
#         now = time.time()
#         if now > self.end_time:
#             logger.debug("\nme tengo que ir\n")
#             raise BreakLoopException('break the lop!')
#
#     def on_error(self, status):
#         print status
#
#     def on_status(self, status):
#         logger.debug("\non_status\n")
#         now = time.time()
#         if now < self.end_time:
#             logger.debug("\ncuento el tweet\n")
#             self.count = self.count + 1
#             print self.count
#         else:
#             logger.debug('should disconnect')
#             return False
#
#
# @app.post('/tw-svc/encuesta')
# def crear_encuesta():
#     logger.info('ENCUESTA ')
#     token_type, token = request.headers['Authorization'].split()
#     print token
#     usr = ""
#     try:
#         header, claims = jwt.verify_jwt(token, public_key, ['RS256'])
#     except jws.exceptions.SignatureError:
#         message = "Invalid token"
#
#     usr = claims['userid']
#
#     logger.info('USER : %s ', usr)
#     auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
#     auth.set_access_token(access_token, access_token_secret)
#
#     logger.info('Processing create ')
#     data = request.json
#     paramHash = data['hash']
#     paramTime = data['time']
#     paramSurvey = data['surveyname']
#     logger.info('data : %s', paramHash)
#
#     my_stream_listener = MyStreamListener(10) # paramTime es la duracion
#     my_stream = tweepy.Stream( auth=auth, listener=my_stream_listener, chunk_size=1 )
#
#     my_stream_listener.stream = my_stream
#     try:
#         my_stream.filter(track=[paramHash])
#     except BreakLoopException:
#         pass
#     logger.debug('finalizo la cuenta')
#     total = my_stream_listener.count
#     logger.info('total : %s', total)
#     my_stream.disconnect()
#     # logger.info()
#     cnx = None
#     try:
#         logger.info('connect : %s', mysql_config)
#         cnx = pymysql.connect(**mysql_config)
#         cursor = cnx.cursor()
#         insert_test = "INSERT INTO jobs (username, surveyname, hash, tiempo, count) VALUES (%s, %s,%s, %s, %s)"
#         data = (usr, paramSurvey, paramHash, paramTime, total) # tupla s
#         cursor.execute(insert_test, data)
#         cnx.commit()
#         cursor.close()
#         ret = {"status": "OK"}
#     except pymysql.Error as err:
#         logger.info('error : %s', err)
#         ret = {"status": "FAIL", "msg": err}
#     finally:
#         if cnx:
#             cnx.close()
#     return ret
#
# @app.get('/tw-svc/all')
# def retornar_encuestas():
#     token_type, token = request.headers['Authorization'].split()
#     ret = {"status":"OK"}
#     usr = ""
#     try:
#         header, claims = jwt.verify_jwt(token, public_key, ['RS256'])
#     except jws.exceptions.SignatureError:
#         message = "Invalid token"
#     usr = claims['userid']
#
#     logger.info('USER : %s', usr)
#     print "antes de cnx"
#     print usr
#     # cnx = None
#     print "hago consulta"
#     try:
#         logger.info('connect : %s', mysql_config)
#         cnx = pymysql.connect(**mysql_config)
#         cursor = cnx.cursor()
#         select_test = "SELECT * FROM jobs WHERE username = %s"
#         logger.info('ahoraHaceElSELECT : %s', select_test)
#         data = (claims['userid'])
#         cursor.execute(select_test, data)
#         results = cursor.fetchall()
#         logger.info('results : %s', results)
#         ret = {"status":"OK", "table":results}
#         cnx.commit()
#         cursor.close()
#     except pymysql.Error as err:
#         logger.info('error : %s', err)
#         ret = {"status": "FAIL", "msg": err}
#     finally:
#         logger.info('FINALLY')
#         if cnx:
#             cnx.close()
#     logger.info('RETURN RET: %s', ret)
#     return ret
#
# @app.route('/jobs', method='GET')
# def get_jobs():
#     logger.info('Processing GET /jobs')
#     token_type, token = request.headers['Authorization'].split()
#     logger.debug('token_type: {}, token: '.format(token_type, token))
#
#     try:
#         header, claims = jwt.verify_jwt(token, public_key, ['RS256'])
#     except jws.exceptions.SignatureError:
#         logger.warn('invalid token signature!')
#         message = "invalid token"
#         response.status = 400
#         ret_data = {
#             "message": message
#         }
#
#     results = db_get_jobs(claims['userId'])
#
#     if results.ok:
#         ret_data = {
#             'jobs' : []
#         }
#     return ret_data
#
# run(app, host='0.0.0.0', port=8088)
