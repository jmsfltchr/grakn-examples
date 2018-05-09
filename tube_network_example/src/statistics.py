import grakn
import tube_network_example.settings as settings
from utils.utils import check_response_length, match_get, insert, match_insert, get_match_id

if __name__ == "__main__":

    client = grakn.Client(uri=settings.uri, keyspace=settings.keyspace)

    def perform_query(graql_string):
        print(graql_string)
        # Send the graql query to the server
        response = client.execute(graql_string)
        return response

    def perform_analytics(op, concepts, attribute=""):
        if attribute != "":
            attribute = "of {}, ".format(attribute)

        query = "compute {} {}in {};".format(op, attribute, concepts)
        response = perform_query(query)
        print("{} of {}s: {}".format(op, concepts, response))
        return response

    # count
    # Find the number of stations, routes, tube lines, zones, etc.
    v = "station"
    op = "count"
    perform_analytics(op, v)
    print("-----")

    # max
    v = "route-section"
    op = "max"
    perform_analytics(op, v, "duration")
    print("-----")

    # min
    v = "route-section"
    op = "min"
    min_duration = perform_analytics(op, v, "duration")
    # Now we have the minimum duration we can query to find where in the graph this occurs
    match_query = ("match\n"
                   "$s1 isa station, has name $s1-name;\n"
                   "$s2 isa station, has name $s2-name;\n"
                   "$o isa station, has name $o-name;\n"
                   "$d isa station, has name $d-name;\n"
                   "$rs isa route-section, has duration {};\n"
                   "$t(beginning: $s1, end: $s2, service: $rs) isa tunnel;\n"
                   "$tl isa tube-line, has name $tl-name;"
                   "$r(section: $rs, origin: $o, destination: $d, route-operator: $tl) isa route;\n"
                   "get $s1-name, $s2-name, $o-name, $d-name, $tl-name;").format(min_duration)
    response = perform_query(match_query)

    for m in response:
        print("Tunnel from {} to {}, via {} line, on the route going from {} to {}".format(
            m['s1-name']['value'], m['s2-name']['value'], m['tl-name']['value'], m['o-name']['value'],
            m['d-name']['value']))
    print("-----")
    # mean
    # median
    # std
    # sum