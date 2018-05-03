import json
import grakn
import datetime as dt
import os
import tube_network_example.settings as settings
from utils.assertions import check_response_length


def match(graql_body):
    prefix = "match "
    return prefix + graql_body


def match_get(graql_body):
    suffix = " get;"
    return match(graql_body) + suffix


def insert(graql_body):
    prefix = "insert "
    return prefix + graql_body


def match_insert(match_graql_body, insert_graql_body):
    return match(match_graql_body) + "\n" + insert(insert_graql_body)


def get_match_id(match_get_response):
    return match_get_response[0]['id']


def import_query_generator(perform_query, timetables_dir_path):
    """
    Builds the Grakl statements required to import the transportation data contained in all_routes.json
    :return:
    """

    timetable_paths = os.listdir(timetables_dir_path)

    station_query = "$s1 isa station, has naptan-id \"{}\";"

    for timetable_path in timetable_paths:
        with open(timetables_dir_path + "/" + timetable_path, 'r') as f:
            data = json.load(f)

            tube_line_query = "$tl isa tube-line, has name \"{}\";".format(data['lineName'])
            response = perform_query(match_get(tube_line_query))

            if len(response) < 1:
                # In this case we haven't already added this tube-line before
                # We do it this way so that we have explicitly asked the database if the tube-line exists, and if not
                # then we use the same query body but as an insert

                response = perform_query(insert(tube_line_query))
                check_response_length(response, min_length=1, max_length=1) # Exactly one concept should be inserted

            for station in data["stops"]:

                response = perform_query(match_get(station_query.format(station["id"])))

                if len(response) < 1:
                    # Only proceed if there is this station isn't already in the database

                    # Check that the station isn't duplicated, or skip this if instead we only do it once per tube-line.
                    # - Actually there will be duplication doing it per tube, since stations belong to more than one
                    # tube-line
                    try:
                        zone_name = station["zone"]
                    except KeyError:
                        # In the case that there is no zone information
                        zone_name = -1

                    zone_query = "$z isa zone, has name \"{}\";\n".format(zone_name)

                    response = perform_query(match_get(zone_query))

                    if len(response) < 1:
                        # If the zone doesn't already exist then insert it
                        response = perform_query(insert(zone_query))
                        check_response_length(response, min_length=1, max_length=1) # Exactly one concept should be
                        # inserted

                    station_insert_query = (station_query.format(station["id"]) +
                                            "$s1 has name \"{}\", "
                                            "has lat {}, has lon {};\n"
                                            "$z(contained-station: $s1)").format(station["id"],
                                                                                 station["name"],
                                                                                 station["lat"],
                                                                                 station["lon"],
                                                                                 )
                    response = perform_query(match_insert(zone_query, station_insert_query))
                    check_response_length(response, min_length=1, max_length=1)

            """
            Get the time between stops
            """
            for routes in data['timetable']["routes"]:

                for station_intervals in routes["stationIntervals"]:
                    # This actually iterates over the routes, in TFL's infinite wisdom

                    last_naptan_id = data['timetable']["departureStopId"]
                    last_time_to_arrival = 0
                    route_query = "$r(route-operator: $tl) isa route;"

                    response = perform_query(match_insert(tube_line_query, route_query))
                    check_response_length(response, min_length=1, max_length=1)
                    route_id = response[0]['id']
                    # TODO Here we need to execute the query in order to get the ID of the route inserted, since that's
                    # the only way to uniquely identify it for the insertion of the route-sections below

                    for i, interval in enumerate(station_intervals['intervals']):

                        # === TUNNELS ===
                        # Now we need to insert a tunnel that can make the connection if there isn't one, or if there
                        # is one then don't add one and instead use its ID
                        station_pair_query = ("$s1 isa station, has naptan-id \"{}\";\n"
                                              "$s2 isa station, has naptan-id \"{}\";\n"
                                              ).format(last_naptan_id,
                                                       interval["stopId"])

                        tunnel_query = "$t(start: $s1, end: $s2) isa tunnel;"

                        response = perform_query(match_get(station_pair_query + tunnel_query))

                        if len(response) < 1:
                            response = perform_query(match_insert(station_pair_query, tunnel_query))

                        # Get the ID of either the pre-existing tunnel or the one just inserted
                        tunnel_id = get_match_id(response)

                        # === Connect Stations to Routes ===
                        origin_termination_flag = ""
                        if i == 0:
                            # In this case we're at the first route-section of the route, starting at the first station
                            role_played = "origin"

                        elif i == len(station_intervals['intervals']) - 1:
                            # In this case we're at the last route-section of the route, ending at the last station
                            # TODO This doesn't work as it doesn't get the last stop, it gets the one before last
                            # TODO instead this needs to happen as an EXTRA step on the last iteration. In that iteration there are 2 stops to add.
                            # TODO Or this can be changed around to add 2 the first iteration (1 before the loop)
                            role_played = "destination"
                        else:
                            role_played = "stop"

                        match_query = station_query.format(last_naptan_id)
                        insert_query = "$r({}: $s1) isa route id {}".format(role_played, route_id)

                        response = perform_query(match_insert(match_query, insert_query))
                        check_response_length(response, min_length=1, max_length=1)

                        if i == len(station_intervals['intervals']) - 1:

                        response = perform_query((
                            "match\n"
                            "$a isa station, has naptan-id \"{}\";\n"
                            "$b isa station, has naptan-id \"{}\";\n"
                            "$r isa route, id {};\n"
                            "insert\n"
                            "$rs(goes-from: $a, goes-to: $b, part-of: $r) isa route-section, has duration {}{};").format(
                            last_naptan_id,
                            interval["stopId"],
                            route_id,
                            int(interval["timeToArrival"] - last_time_to_arrival),
                            origin_termination_flag
                        ))

                        last_time_to_arrival = interval["timeToArrival"]
                        last_naptan_id = interval["stopId"]


def make_queries(timetables_dir_path, keyspace, uri=settings.uri,
                 log_file="logs/graql_output_{}.txt".format(dt.datetime.now()), send_queries=True):
    client = grakn.Client(uri=uri, keyspace=keyspace)

    start_time = dt.datetime.now()

    with open(log_file, "w") as graql_output:

        def query_function(graql_string):
            print(graql_string)
            print("---")
            graql_output.write(graql_string)
            if send_queries:
                # Send the graql query to the server
                response = client.execute(graql_string)
                graql_output.write("\n--response:\n" + str(response))
                graql_output.write("\n{} insertions made \n ----- \n".format(len(response)))
                return response
            else:
                return ["<DUMMY_RESPONSE>"]

        import_query_generator(query_function, timetables_dir_path)


        end_time = dt.datetime.now()
        time_taken = end_time - start_time
        time_taken_string = "----------\nTime taken: {}".format(time_taken)
        graql_output.write(time_taken_string)
        print(time_taken_string)


if __name__ == "__main__":

    go = False
    make_queries(settings.timetables_path, settings.keyspace, send_queries=go)
