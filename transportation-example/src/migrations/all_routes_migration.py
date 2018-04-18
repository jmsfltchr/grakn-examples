import json
import grakn


def routes_generator(routes):
    for route in routes:
        yield route


def route_sections_generator(routes):
    for route in routes_generator(routes):
        for routeSection in route["routeSections"]:
            yield route, routeSection


def import_query_generator():
    """
    Builds the Grakl statements required to import the transportation data contained in all_routes.json
    :return:
    """

    s = "../../datasets/tfl_api/all_routes.json"

    with open(s, 'r') as f:
        routes = json.load(f)

        # ===== STOPS =====
        stops = dict()  # Create a dict of stops for all modes of transport so that we can't duplicate them, using the
        # stop's naptan Id as the key

        for route, routeSection in route_sections_generator(routes):
            stops[routeSection['originator']] = routeSection['originationName']
            stops[routeSection['destination']] = routeSection['destinationName']

        for naptan_id, name in stops.items():
            yield "insert $stop isa stop has naptan-id \"{}\" has name \"{}\";\n".format(naptan_id, name)

        # ===== MODES OF TRANSPORT =====
        modes_of_transport = set()
        for route in routes_generator(routes):
            modes_of_transport.add(route["modeName"])

        for mode_name in modes_of_transport:
            yield "insert $mode isa mode-of-transport has name \"{}\";\n".format(mode_name)

        # ===== ROUTES =====
        for route in routes_generator(routes):

            # Relate the route to the mode of transport
            to_match = "match\n$mode isa mode-of-transport has name \"{}\";\n".format(route['modeName'])
            to_insert = ("insert\n$route isa route has name \"{}\";\n"
                         "(operated-by: $mode, operates: $route) isa operation;\n"
                         ).format(route['name'])
            to_relate = "(composes: $route"

            # ===== ROUTE SECTIONS =====
            for i, routeSection in enumerate(route["routeSections"]):

                to_match += "$origin-{} isa stop has naptan-id \"{}\"; $destination-{} isa stop has naptan-id \"{}\";\n"\
                    .format(i, routeSection['originator'], i, routeSection['destination'])

                to_insert += (
                       "$route-section-{} isa route-section "
                       "has name \"{}\" "
                       "has direction \"{}\" "
                       "has service-type \"{}\" "
                       "has valid-from {} "
                       "has valid-to {};\n"
                       "(origin: $origin-{}, destination: $destination-{}, has-route-section: $route-section-{}) isa "
                       "has-stops;\n"
                       ).format(i,
                                routeSection['name'],
                                routeSection['direction'],
                                routeSection['serviceType'],
                                routeSection['validFrom'][:-1],
                                routeSection['validTo'][:-1],
                                i,
                                i,
                                i)
                to_relate += ", comprises: $route-section-{}".format(i)

            to_relate += ") isa composition;\n"
            yield to_match + to_insert + to_relate


client = grakn.Client(uri='http://localhost:4567', keyspace='transportation_example')

for query in import_query_generator():
    # query = "insert " + line + " commit;"  # Commit isn't needed, it seems. Throws an error if it's used.
    print(query)
    print("---")
    # Feed the insert queries line-by-line
    client.execute(query)
