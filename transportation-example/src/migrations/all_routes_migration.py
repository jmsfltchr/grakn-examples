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


def import_query_generator():
    """
    Builds the Grakl statements required to import the transportation data contained in all_routes.json
    :return:
    """

    s = "../../datasets/tfl_api/all_routes.json"

    with open(s, 'r') as f:
        routes = json.load(f)
        # print(obj)
        # print(routes[0])
        # print(obj[0]['routeSections'])

        # ===== STOPS =====
        stops = dict()  # Create a dict of stops for all modes of transport so that we can't duplicate them, using the
        # stop's naptan Id as the key

        for route, routeSection in route_sections_generator(routes):

            stops[routeSection['originator']] = routeSection['originationName']
            stops[routeSection['destination']] = routeSection['destinationName']

        stop_vars = dict()  # Store the variables used for each stop for use later on to associate the routes
        for (naptan_id, name), symbol in zip(stops.items(), symbol_generator()):
            stop_var = "$stop" + symbol
            yield "insert " + stop_var + " isa stop has naptan-id \"" + naptan_id + "\" has name \"" + name + "\";\n"
            stop_vars[naptan_id] = stop_var

        # ===== MODES OF TRANSPORT =====
        modes_of_transport = set()
        mode_of_transport_vars = dict()
        for route in routes_generator(routes):
            modes_of_transport.add(route["modeName"])

        for mode_name, symbol in zip(modes_of_transport, symbol_generator()):
            mode_of_transport_var = "$mode" + symbol
            mode_of_transport_vars[mode_name] = mode_of_transport_var
            yield "insert " + mode_of_transport_var + " isa mode-of-transport has name \"" + mode_name + "\";\n"

        for route, symbol in zip(routes_generator(routes), symbol_generator()):

            # Relate the route to the mode of transport
            s = ("match $mode isa mode-of-transport has name \"{}\";\n"
                 "insert $route isa route has name \"{}\";\n"
                 "(operated-by: $mode, operates: $route) isa operation;\n"
                 ).format(route['modeName'], route['name'])
            yield s

            for routeSection, symbol2 in zip(route["routeSections"], symbol_generator()):

                s = ("match $origin isa stop has naptan-id \"{}\"; $destination isa stop has naptan-id \"{}\";\n"
                     "insert $route-section isa route-section "
                     "has name \"{}\" "
                     "has direction \"{}\" "
                     "has service-type \"{}\" "
                     "has valid-from {} "
                     "has valid-to {};\n"
                     "(origin: $origin, destination: $destination, has-route-section: $route-section) isa has-stops;\n"
                     ).format(routeSection['originator'],
                              routeSection['destination'],
                              routeSection['name'],
                              routeSection['direction'],
                              routeSection['serviceType'],
                              routeSection['validFrom'][:-1],
                              routeSection['validTo'][:-1])
                yield s


client = grakn.Client(uri='http://localhost:4567', keyspace='transportation_example')

for query in import_query_generator():
    # query = "insert " + line + " commit;"  # Commit isn't needed, it seems. Throws an error if it's used.
    print(query)
    print("---")
    # Feed the insert queries line-by-line
    client.execute(query)
