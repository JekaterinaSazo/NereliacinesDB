import neo4j
from flask import Flask, request, jsonify
from neo4j import GraphDatabase

app = Flask(__name__)
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")
driver = GraphDatabase.driver(URI, auth=AUTH)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    driver.close()
    func()
@app.route('/cities',methods=['PUT'])
def register_city():
    # Prideti nauja miesta prie duomenu bazes, 201 pridetas, 400 nepavyko
    # Paduoda name ir country
    req_body = request.get_json()
    if "name" not in req_body or "country" not in req_body:
        return "Bad Request", 400
    result = None
    query = "CREATE (c:City {name: $name, country: $country}) RETURN c"
    with driver.session() as session:
        result = session.run(query, parameters=req_body).single()
    if result is None:
        return "Request failed", 400
    return "City registered successfully", 204
@app.route('/cities',methods=['GET'])
def get_all_cities():
    # Gauti sarasa visu miestu, 200 grazinti miestai
    # Galima filtruoti pagal sali
    query = """
    MATCH (c:City)
    WHERE $country IS NULL OR c.country = $country
    RETURN c
    """
    params = {"country": request.args.get("country")}

    with driver.session() as session:
        result = session.run(query, parameters=params)
        cities = [record['c']._properties for record in result]

    return jsonify(cities), 200
@app.route('/cities/<name>',methods=['GET'])
def get_city(name):
    # Gauti miesta, 200 grazinti miestai, 404 miestas nerastas
    query = "MATCH (c:City) WHERE c.name = $name RETURN c"
    with driver.session() as session:
        result = session.run(query, parameters={"name": name}).single()
    if result is None:
        return "City not found", 404

    return result.data()['c'], 200
@app.route('/cities/<name>/airports', methods=['PUT'])
def register_airport(name):
    # Prideti nauja orouosta prie miesto, 201 pridetas, 400 nepavyko, arba nera miesto kuriame registruojama
    # Paduoda code (3 raides), name, numberOfTerminals, address
    query = """
    MATCH (c:City {name: $city})
    WITH c
    CREATE (a:Airport {code: $code, name: $name, numberOfTerminals: $numberOfTerminals, address: $address, city: $city})
    CREATE (c)-[:HAS_AIRPORT]->(a)
    RETURN c, a
    """
    req_body = request.get_json()
    req_body['city'] = name
    with driver.session() as session:
        result = session.run(query, parameters=req_body).single()
    if result is None:
        return "Request failed, or city does not exist", 400
    return "Airport registered successfully", 204
@app.route('/cities/<name>/airports', methods=['GET'])
def get_all_cities_airports(name):
    query = """
    MATCH (c:City {name: $name}) -[:HAS_AIRPORT]->(a)
    return a
    """
    with driver.session() as session:
        result = session.run(query, parameters={"name": name})
        airports = [record['a']._properties for record in result]

    return jsonify(airports), 200
@app.route('/airports/<code>', methods=['GET'])
def get_airport(code):
    query = """MATCH (a:Airport {code: $code}) RETURN a"""
    with driver.session() as session:
        result = session.run(query, parameters={"code": code}).single()
    if result is None:
        return "Airport not found", 404
    result = result.data()['a']
    return result, 200
@app.route('/flights', methods=['PUT'])
def add_flight():
    # Priregistruoti nauja skrydi is vieno orouosto i kita,
    # Skrydziai vienpusiai,
    # Duoda: number (Skrydzio Nr), fromAirport (Kodas oruosto is kurio skrenda)
    #        toAirport (Kodas orouosto i kuri skrenda), price (kaina)
    #        flightTimeInMinutes (skrydzio laikas minutem), operator (oro linija kuri skraidina)
    # Grazinam, 201 Skrydis sukurtas, 400 skrydis nesukurtas nes truksta duomenu
    req_body = request.get_json()
    query = """
        MATCH (from:Airport {code: $fromAirport}), (to:Airport {code: $toAirport})
        WITH from, to
        CREATE (from)-[f:FLIGHT {
            number: $number,
            fromAirport: $fromAirport,
            fromCity: from.city,
            toAirport: $toAirport,
            toCity: to.city,
            price: $price,
            flightTimeInMinutes: $flightTimeInMinutes,
            operator: $operator
        }]->(to)
        RETURN from, to, f
        """
    with driver.session() as session:
        result = session.run(query, parameters=req_body).single()
    if result is None:
        return "Request failed, or airport/s dont exist", 400
    return "Flight registered successfully", 204
@app.route('/flights/<code>', methods=['GET'])
def get_flight(code):
    # Grazinam skrydi pagal paduota skrydzio koda, 200 radom, 404 nerastas
    query = """
    MATCH (:Airport)-[f:FLIGHT {number: $flight_no}]->(:Airport)
    RETURN f
    """
    with driver.session() as session:
        result = session.run(query, parameters={"flight_no": code}).single()
    if result is None:
        return "Flight not found", 404
    return dict(result['f'].items()), 200
@app.route('/search/flights/<fromCity>/<toCity>', methods=['GET'])
def search_flight(fromCity, toCity):
    # Randame ir graziname skrydziu sarasa is vieno miesto i kita
    # Ieskome su max 3 persedimais
    # Jei miestai turi kelis oruostus, grupuojame pagal oruostus,
    # Ju kaina ir laika
    query = """
    MATCH (start:Airport)<-[:HAS_AIRPORT]-(fromCity:City {name: $fromCity}),
      (end:Airport)<-[:HAS_AIRPORT]-(toCity:City {name: $toCity}),
      path = (start)-[:FLIGHT*0..3]->(end)
    RETURN start, end, [rel IN relationships(path) | {
        fromAirport: rel.fromAirport,
        toAirport: rel.toAirport,
        operator: rel.operator
    }] AS flights, reduce(total = 0, r IN relationships(path) | total + r.price) AS price,
    reduce(total = 0, r IN relationships(path) | total + r.flightTimeInMinutes) AS flightTimeInMinutes,
    [r in relationships(path) | r.number] as numbers
    """
    with driver.session() as session:
        result = session.run(query, fromCity=fromCity, toCity=toCity).values()
    if result is None:
        return "Flight not found", 404
    ret = []
    for res in result:
        flight = {'fromAirport':res[0].get('code'),
                  'toAirport':res[1].get('code'),
                  'flights':res[5],
                  'price':res[3],
                  'flightTimeInMinutes':res[4]}
        ret.append(flight)
    return ret, 200
@app.route('/cleanup', methods=['POST'])
def cleanup():
    query = """MATCH (n)
    DETACH DELETE n"""
    with driver.session() as session:
        result = session.run(query)
    return "Cleanup successful", 200
@app.get('/shutdown')
def shutdown():
    shutdown_server()
    return "Server shutting down...", 200
if __name__ == '__main__':
    app.run()
    driver.close()
