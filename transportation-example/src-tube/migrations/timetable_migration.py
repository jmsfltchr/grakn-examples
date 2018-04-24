import json
import grakn
import datetime as dt


def import_query_generator():
    """
    Builds the Grakl statements required to import the transportation data contained in all_routes.json
    :return:
    """

    s = "../../datasets/tfl_api/timetables/940GZZLUEPG_west_ruislip_central_inbound.json"

    with open(s, 'r') as f:
        data = json.load(f)
        # for station in data["stations"]:
        #     print(station["name"])
        #     print("-")
        #     for line in station["lines"]:
        #         print(line["name"])
        #     print("----")

        yield ("insert $service isa service, has name \"{}\";").format(data['lineName'])

        zones = set()
        for stop in data["stops"]:
            try:
                zone = stop["zone"]
            except KeyError:
                # In the case that there is no zone information
                zone = -1

            if zone not in zones:
                zones.add(zone)
                yield ("insert $zone isa zone, has name \"{}\";".format(zone))

            yield ("match\n"
                   "$zone isa zone, has name \"{}\";\n"
                   "insert $stop isa stop, has naptan-id \"{}\", has name \"{}\", "
                   "has lat {}, has lon {};\n"
                   "(contains-stop: $stop, within: $zone) isa zoning;").format(
                zone,
                stop["id"],
                stop["name"],
                stop["lat"],
                stop["lon"]
            )

        # print("Departs at:")
        # for routes in data["timetable"]["routes"]:
        #     # for route in timetable["routes"]:
        #     for schedule in routes["schedules"]:
        #         for known_journey in schedule["knownJourneys"]:
        #             print("{}:{}".format(known_journey["hour"], known_journey["minute"]))
        #             print("intervalId: {}".format(known_journey["intervalId"]))
        #             print("-")
        #         print("End of journey")
        #     print("End of route")


        """
        Get the time between stops
        """
        # print("Departs at:")
        # for timetable in data["timetable"]:
        for routes in data['timetable']["routes"]:

            for station_intervals in routes["stationIntervals"]:
                last_naptan_id = data['timetable']["departureStopId"]
                last_time_to_arrival = 0
                # print("----- id : {} -----".format(station_intervals["id"]))
                yield ("match $service isa service, has name \"{}\";\n"
                       "insert"
                       "$route isa route, has identifier {};\n"
                       "(operated-by: $service, operates: $route) isa operation;"
                       ).format(data['lineName'], station_intervals["id"])

                for interval in station_intervals['intervals']:
                    # print("Arrives at {} after {}".format(interval["stopId"], interval["timeToArrival"]))
                    yield (
                        "match "
                        "$a isa stop, has naptan-id \"{}\";\n"
                        "$b isa stop, has naptan-id \"{}\";\n"
                        "$r isa route, has identifier \"{}\";\n"
                        "insert (goes-from: $a, goes-to: $b, part-of: $r) isa route-section, has duration {};").format(
                        last_naptan_id,
                        interval["stopId"],
                        station_intervals["id"],
                        int(interval["timeToArrival"] - last_time_to_arrival)
                    )

                    last_time_to_arrival = interval["timeToArrival"]
                    last_naptan_id = interval["stopId"]

        # print("End of route")


def make_queries(query_generator, keyspace, uri='http://localhost:4567', log_file="logs/graql_output_{}.txt".format(dt.datetime.now())):
    client = grakn.Client(uri=uri, keyspace=keyspace)

    start_time = dt.datetime.now()
    # log_file = "logs/graql_output_{}.txt".format(dt.datetime.now())
    with open(log_file, "w") as graql_output:
        for query in query_generator():
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


make_queries(import_query_generator, "tube_example")
