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

        yield ("insert $service isa service, has name \"{}\"").format(data['lineName'])

        for stop in data["stops"]:
            try:
                zone = stop["zone"]
            except KeyError:
                # In the case that there is no zone information
                zone = -1

            yield ("insert $s isa stop, has naptan-id \"{}\", has name \"{}\", "
                   "has lat {}, has lon {}, has zone {};").format(
                stop["id"],
                stop["name"],
                stop["lat"],
                stop["lon"],
                zone
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
                yield ("match $service isa service, has name {};\n"
                       "insert"
                       "$route isa route, has identifier {};\n"
                       "(operated-by: $service, operates: $route)"
                       ).format(data['lineName'], station_intervals["id"])

                for interval in station_intervals['intervals']:
                    # print("Arrives at {} after {}".format(interval["stopId"], interval["timeToArrival"]))
                    yield (
                        "match "
                        "$a isa stop, has naptan-id \"{}\";\n"
                        "$b isa stop, has naptan-id \"{}\";\n"
                        "$r isa route, has identifier \"{}\";\n"
                        "insert (from: $a, to: $b, belongs-to: $r) isa route-section, has duration {};").format(
                        last_naptan_id,
                        interval["stopId"],
                        station_intervals["id"],
                        int(interval["timeToArrival"] - last_time_to_arrival)
                    )

                    last_time_to_arrival = interval["timeToArrival"]
                    last_naptan_id = interval["stopId"]

        # print("End of route")


for query in import_query_generator():
    print(query)
