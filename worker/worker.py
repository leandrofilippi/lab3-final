import tweepy
import pika
import os
import time
import logging
import json
import requests
from cred import cred_consumer_key, cred_consumer_secret, cred_access_token, cred_access_token_secret

time.sleep(10)

logger = logging.getLogger('worker')
logger.setLevel(logging.DEBUG)
logger.propagete = False
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info(' ----------------------------------WORKER---------------------------------- ')

# Authentication details. To  obtain these visit dev.twitter.com
consumer_key =  cred_consumer_key
consumer_secret = cred_consumer_secret
access_token = cred_access_token
access_token_secret = cred_access_token_secret

# CANAL
logger.info(' ----------------------------------WORKER CANAL---------------------------------- ')
connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ['RABBITMQ_ENDPOINT']))  #connectamos al rmq ( una coneccion bloqueante )
channel = connection.channel() #cremmos canal , una vez que tengo la coneccion en el pasoa nterior
channel.queue_declare(queue='newsurvey') # creamos una cola que se llama hellow adentro del canal
# channel.basic_qos(prefetch_count=1)
# channel.basic_consume(callbacknewsurvey, queue='newsurvey', no_ack=True) # 1er param el nombre de la func collback, 2do el nombre de la cola, 3ero el producer nunca se enterara que recibi el mensaje con el parametro no_act=True
#print (' [x] Waiting for messages. To exit press CRTL+C')
channel.start_consuming()

class BreakLoopException(Exception):
    pass

# This is the listener, resposible for receiving data
class MyStreamListener(tweepy.StreamListener):

    def __init__(self,duration):
        tweepy.StreamListener.__init__(self)
        self.stream = None
        self.count = 0
        self.duration = duration
        self.start_time = None
        self.end_time = None
        return


    def on_connect(self):
        logger.debug("\non_connect\n")
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration
        return

    def keep_alive(self):
        logger.debug("\nkeep_alive\n")
        now = time.time()
        if now > self.end_time:
            logger.debug("\nme tengo que ir\n")
            raise BreakLoopException('break the lop!')

    def on_error(self, status):
        print status

    def on_status(self, status):
        logger.debug("\non_status\n")
        now = time.time()
        if now < self.end_time:
            logger.debug("\ncuento el tweet\n")
            self.count = self.count + 1
            print self.count
        else:
            logger.debug('should disconnect')
            return False


def callbacknewsurvey(ch, method, properies, body) : # ESTO SE EJECUTA CUANDO LLEGA UN MENSAJE AL HELLOW
        logger.info('[x] Received ')
        data = json.loads(body)
        logger.info('data json : %s', data )
        paramUsr = data['user']
        paramHash = data['paramHash']
        paramTime = int(data['paramTime'])
        paramSurvey = data['paramSurvey']
        # ENCUESTA DE TW
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        my_stream_listener = MyStreamListener(paramTime) # paramTime es la duracion
        my_stream = tweepy.Stream( auth=auth, listener=my_stream_listener, chunk_size=1 )
        my_stream_listener.stream = my_stream
        try:
            my_stream.filter(track=[paramHash])
        except BreakLoopException:
            pass
        logger.debug('finalizo la cuenta')
        total = my_stream_listener.count
        logger.info('total : %s', total)
        my_stream.disconnect()

        msg = {"paramUsr": paramUsr, "paramHash": paramHash, "paramTime": paramTime, "paramSurvey": paramSurvey, "paramResultado": total}
        logger.info('msg : %s', json.dumps(msg))
        rq = requests.put("http://tw-svc:8088/tw-svc/update", data = json.dumps(msg))
        logger.info('request : %s', rq)
        # ch.basic_ack(delivery_tag=method.delivery_tag)

logger.info(' ----------------------------------WORKER CANAL---------------------------------- ')
connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ['RABBITMQ_ENDPOINT']))  #connectamos al rmq ( una coneccion bloqueante )
channel = connection.channel() #cremmos canal , una vez que tengo la coneccion en el pasoa nterior
channel.queue_declare(queue='newsurvey') # creamos una cola que se llama hellow adentro del canal
channel.basic_qos(prefetch_count=1)

logger.info('-----------------ANTES DEL CHANEL.basic_consume---------------------')
channel.basic_consume(callbacknewsurvey, queue='newsurvey', no_ack=True) # 1er param el nombre de la func collback, 2do el nombre de la cola, 3ero el producer nunca se enterara que recibi el mensaje con el parametro no_act=True
#print (' [x] Waiting for messages. To exit press CRTL+C')
channel.start_consuming()
