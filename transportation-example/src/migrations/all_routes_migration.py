import json
import grakn
import datetime as dt
import os


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
            yield to_match + to_insert + to_relate + "\n"

if __name__ == "__main__":

    download_dir_name = "data-downloads"
    routes_path = "{}/{}/routes/".format(download_dir_name, os.path.dirname(__file__))
    timetables_path = "{}/{}/timetables/".format(download_dir_name, os.path.dirname(__file__))


    client = grakn.Client(uri='http://localhost:4567', keyspace='insert_bug_1')

    start_time = dt.datetime.now()
    log_file = "logs/graql_output_{}.txt".format(dt.datetime.now())
    with open(log_file, "w") as graql_output:
        for i, query in enumerate(import_query_generator()):
            print(query)
            print("---")
            graql_output.write(query)
            # graql_output.write("---")
            # Feed the queries one at a time
            response = client.execute(query)
            graql_output.write(str(response))
            graql_output.write("\n{} insertions made \n ----- \n".format(len(response)))
            if len(response) == 0:
                raise RuntimeError("Tried to make an insertion, but no concepts could be inserted. Check entities in \""
                                   "match\" clause")

            # TODO how to do complex matches to get the variables of 2 different things without inefficiency
            # TODO Northern Rail takes some time to complete

    end_time = dt.datetime.now()
    time_taken = end_time - start_time
    print("Time taken: {}".format(time_taken))
