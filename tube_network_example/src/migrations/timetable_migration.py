import json
import grakn
import datetime as dt
import os

import tube_network_example.settings as settings
from utils.assertions import check_response_length


def id_generator():
    i = 0
    while 1:
        yield i
        i += 1


def import_query_generator(timetables_dir_path):
    """
    Builds the Grakl statements required to import the transportation data contained in all_routes.json
    :return:
    """

    timetable_paths = os.listdir(timetables_dir_path)
    zone_names = set()
    stop_ids = set()
    line_names = set()
    route_id_gen = id_generator()

    for timetable_path in timetable_paths:
        with open(timetables_dir_path + "/" + timetable_path, 'r') as f:
            data = json.load(f)
            if data['lineName'] not in line_names:
                line_names.add(data['lineName'])
                yield ("insert $line isa line, has name \"{}\";").format(data['lineName'])

            for stop in data["stops"]:
                if stop["id"] not in stop_ids:
                    # Only proceed if we haven't already seen this stop before
                    stop_ids.add(stop["id"])
                    # TODO Check that the stop isn't duplicated, or skip this if instead we only do it once per tube line.
                    # - Actually there willbe duplication doing it per tube, since stations belong to more than one line
                    try:
                        zone_name = stop["zone"]
                    except KeyError:
                        # In the case that there is no zone information
                        zone_name = -1

                    if zone_name not in zone_names:
                        zone_names.add(zone_name)
                        yield ("insert $zone isa zone, has name \"{}\";".format(zone_name))

                    yield ("match\n"
                           "$zone isa zone, has name \"{}\";\n"
                           "insert\n"
                           "$stop isa stop, has naptan-id \"{}\", has name \"{}\", "
                           "has lat {}, has lon {};\n"
                           "(contains-stop: $stop, within: $zone) isa zoning;").format(
                        zone_name,
                        stop["id"],
                        stop["name"],
                        stop["lat"],
                        stop["lon"]
                )

            """
            Get the time between stops
            """
            for routes in data['timetable']["routes"]:

                for station_intervals in routes["stationIntervals"]:
                    last_naptan_id = data['timetable']["departureStopId"]
                    last_time_to_arrival = 0
                    route_id = next(route_id_gen)
                    yield ("match\n"
                           "$line isa line, has name \"{}\";\n"
                           "insert\n"
                           "$route isa route, has identifier {};\n"
                           "(operated-by: $line, operates: $route) isa operation;"
                           ).format(data['lineName'], route_id)

                    for i, interval in enumerate(station_intervals['intervals']):
                        origin_termination_flag = ""
                        if i == 0:
                            origin_termination_flag = ", has is-origin true"
                        elif i == len(station_intervals['intervals']) - 1:
                            origin_termination_flag = ", has is-termination true"
                        yield (
                            "match\n"
                            "$a isa stop, has naptan-id \"{}\";\n"
                            "$b isa stop, has naptan-id \"{}\";\n"
                            "$r isa route, has identifier {};\n"
                            "insert\n"
                            "$rs(goes-from: $a, goes-to: $b, part-of: $r) isa route-section, has duration {}{};").format(
                            last_naptan_id,
                            interval["stopId"],
                            route_id,
                            int(interval["timeToArrival"] - last_time_to_arrival),
                            origin_termination_flag
                        )

                        last_time_to_arrival = interval["timeToArrival"]
                        last_naptan_id = interval["stopId"]


def make_queries(query_generator, timetables_dir_path, keyspace, uri=settings.uri, log_file="logs/graql_output_{}.txt".format(dt.datetime.now())):
    client = grakn.Client(uri=uri, keyspace=keyspace)

    start_time = dt.datetime.now()
    # log_file = "logs/graql_output_{}.txt".format(dt.datetime.now())
    with open(log_file, "w") as graql_output:
        for query in query_generator(timetables_dir_path):
            print(query)
            print("---")
            graql_output.write(query)
            # Feed the queries one at a time
            response = client.execute(query)
            graql_output.write("\n--response:\n" + str(response))
            graql_output.write("\n{} insertions made \n ----- \n".format(len(response)))
            check_response_length(response, min_length=1, max_length=None)

            # TODO how to do complex matches to get the variables of 2 different things without inefficiency
            # TODO Northern Rail takes some time to complete

    end_time = dt.datetime.now()
    time_taken = end_time - start_time
    print("Time taken: {}".format(time_taken))


if __name__ == "__main__":

    go = True

    if go:

        make_queries(import_query_generator, settings.timetables_path, settings.keyspace)
    else:
        for query in import_query_generator(settings.timetables_path):
            print(query)
