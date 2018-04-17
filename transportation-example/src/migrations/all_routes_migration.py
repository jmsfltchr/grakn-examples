import json
import grakn

def routes_generator(routes):
    for route in routes:
        yield route


def route_sections_generator(routes):
    for route in routes_generator(routes):
        for routeSection in route["routeSections"]:
            yield route, routeSection


def symbol_generator():
    i = 0
    while 1:
        yield str(i)
        i += 1


def import_all_routes_graql():
    """
    Builds the Grakl statements required to import the transportation data contained in all_routes.json
    :return:
    """

    s = "../../../datasets/tfl/api_data/all_routes.json"

    with open(s, 'r') as f:
        routes = json.load(f)
        # print(obj)
        # print(routes[0])
        # print(obj[0]['routeSections'])

        # ===== STOPS =====
        stops = dict()  # Create a dict of stops for all modes of transport so that we can't duplicate them, using the
        # stop's naptan Id as the key

        # graql_insert = "insert\n"
        graql_insert = ""

        for route, routeSection in route_sections_generator(routes):

            stops[routeSection['originator']] = routeSection['originationName']
            stops[routeSection['destination']] = routeSection['destinationName']

        stop_vars = dict()  # Store the variables used for each stop for use later on to associate the routes
        for (naptan_id, name), symbol in zip(stops.items(), symbol_generator()):
            stop_var = "$stop" + symbol
            graql_insert += stop_var + " isa stop has naptan-id \"" + naptan_id + "\" has name \"" + name + "\";\n"
            stop_vars[naptan_id] = stop_var

        # ===== MODES OF TRANSPORT =====
        modes_of_transport = set()
        mode_of_transport_vars = dict()
        for route in routes_generator(routes):
            modes_of_transport.add(route["modeName"])

        for mode_name, symbol in zip(modes_of_transport, symbol_generator()):
            mode_of_transport_var = "$mode" + symbol
            mode_of_transport_vars[mode_name] = mode_of_transport_var
            graql_insert += mode_of_transport_var + " isa mode-of-transport has name \"" + mode_name + "\";\n"

        for route, symbol in zip(routes_generator(routes), symbol_generator()):
            route_var = "$route" + symbol
            graql_insert += route_var + " isa route has name \"" + route['name'] + "\";\n"

            # Relate the route to the mode of transport
            mode_of_transport_var = mode_of_transport_vars[route['modeName']]
            graql_insert += "(operated-by: " + mode_of_transport_var + ", operates: " + route_var + ") isa has-operation;\n"

            for routeSection, symbol2 in zip(route["routeSections"], symbol_generator()):
                route_section_var = "$route-section" + symbol + "-" + symbol2
                graql_insert += route_section_var + \
                                " isa route-section has name \"" + routeSection['name'] + \
                                "\" has direction \"" + routeSection['direction'] + \
                                "\" has service-type \"" + routeSection['serviceType'] + \
                                "\" has valid-from \"" + routeSection['validFrom'] + \
                                "\" has valid-to \"" + routeSection['validTo'] + "\";\n"

                # Look up the variable for the origin and destination stops
                origin_stop_var = stop_vars[routeSection['originator']]
                destination_stop_var = stop_vars[routeSection['destination']]
                # Add the relationship
                graql_insert += "(origin: " + origin_stop_var + ", destination: " + destination_stop_var + ", has-route-section: " + route_section_var + ") isa has-stops;\n"

        return graql_insert


graql_insert = import_all_routes_graql()
print(graql_insert)
client = grakn.Client(uri='http://localhost:4567', keyspace='transportation_example')

for line in graql_insert.splitlines():
    # query = "insert " + line + " commit;"  # Commit isn't needed, it seems. Throws an error if it's used.
    query = "insert " + line
    print(query)
    print("---")
    # Feed the insert queries line-by-line
    client.execute(query)
    
