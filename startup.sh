cd /rDrama
git pull
. /env
gunicorn files.__main__:app load_chat -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 --reload -b 0.0.0.0:5001 --max-requests 30000 --max-requests-jitter 30000 -D
gunicorn files.__main__:app -k gevent -w 3 --reload -b 0.0.0.0:5000 --max-requests 30000 --max-requests-jitter 10000