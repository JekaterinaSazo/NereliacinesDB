import redis
from flask import (Flask, request, jsonify, abort)


def create_app():
    app = Flask(__name__)
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

    def gen_uid():
        return redis_client.incr("user_id")

    def userkey(id):
        return f'client:{id}'

    @app.route('/client', methods=['PUT'])
    def add_client():
        req_body = request.json
        if req_body.get("address") is None or req_body.get("fullName") is None:
            return f'adresas arba vardas nėra duotas', 400
        user_info = str(req_body.get("address")) + ":" + str(req_body.get("fullName"))

        uid = gen_uid()
        redis_client.set(f'client:{uid}', user_info)
        return f'Klientas, {uid}, sėkmingai užregistruotas', 200

    @app.route('/client/<id>', methods=['GET'])
    def get_client(id):
        user = redis_client.get(f"client:{id}")
        if user is None:
            return "Klientas sistemoje nerastas", 404
        else:
            info = user.split(':')
            return {
                "id": int(id),
                "address": info[0],
                "fullName": info[1]
            }


    @app.route('/client/<id>', methods=['DELETE'])
    def delete_client(id):
        result = redis_client.delete(f"client:{id}")
        if result > 0:
            return "Klientas sėkmingai išregistruotas.", 200
        else:
            return f"Klientas sistemoje nerastas", 404

    @app.route('/client/<uid>/meter/<mid>', methods=['GET'])
    def get_meter(uid, mid):
        user = redis_client.get(userkey(uid))
        if user is None:
            return "Klientas sistemoje nerastas", 404
        meter = redis_client.get(f"meter:{uid},{mid}")
        if meter is None:
            return "Skaitiklis sistemoje nerastas", 404
        return meter, 200

    @app.route('/client/<uid>/meter/<mid>', methods=['POST'])
    def add_meter(uid, mid):
        user = redis_client.get(userkey(uid))
        if user is None:
            return "Klientas sistemoje nerastas", 404

        req_body = request.data.decode("utf-8")

        redis_client.set(f"meter:{uid},{mid}", req_body)

        return 'Skaitiklio duomenys atnaujinti', 200

    @app.route('/client/<uid>/meter/<mid>/add', methods=['POST'])
    def add_to_meter(uid, mid):
        user = redis_client.get(userkey(uid))
        if user is None:
            return "Klientas sistemoje nerastas", 404
        meter = redis_client.get(f"meter:{uid},{mid}")
        if meter is None:
            return "Skaitiklis sistemoje nerastas", 404
        req_body = int(request.data.decode("utf-8"))
        if req_body < 0 or not (isinstance(req_body, float) or isinstance(req_body, int)):
            return "Nurodytas kiekis neigiamas arba ne skaičius.", 400
        redis_client.incrbyfloat(f"meter:{uid},{mid}", req_body)
        return redis_client.get(f"meter:{uid},{mid}"), 200

    @app.route('/client/<uid>/meter/', methods=['GET'])
    def get_meters(uid):
        user = redis_client.get(userkey(uid))
        if user is None:
            return "Klientas sistemoje nerastas", 404
        ret = redis_client.scan(0, match=f"meter:{uid},*")[1]
        ret = [item.replace(f"meter:{uid},", "") for item in ret]
        return {"meters": ret}, 200

    @app.route('/flushall', methods=['POST'])
    def flush():
        redis_client.flushall()
        return "", 200

    return app
