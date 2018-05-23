# Copyright 2018 Grakn Labs Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import grakn
import tube_network_example.settings as settings
from utils.utils import check_response_length, match_get, insert, match_insert, get_match_id

if __name__ == "__main__":

    client = grakn.Client(uri=settings.uri, keyspace=settings.keyspace)

    def perform_query(graql_string):
        # print(graql_string)
        # Send the graql query to the server
        response = client.execute(graql_string)
        # print(response)
        # print("---")
        return response


    # GET ME FROM:
    a_name = "Lancaster Gate Underground Station"
    # TO:
    # b_name = "Edgware Road (Circle Line) Underground Station"
    b_name = "Queensbury Underground Station"
    # b_name = "Upminster Underground Station"  # Tries to return 1048576 paths, which is 2^20, because most stations
    # are connected by 2 tunnels. We need a different return type from compute path before we can practically query for
    # this many paths

    FEWEST_STOPS = 0
    FEWEST_ROUTES = 1
    method = FEWEST_STOPS

    a_id = get_match_id(perform_query(match_get("$s1 isa station, has name \"{}\";".format(a_name))), "s1")
    b_id = get_match_id(perform_query(match_get("$s1 isa station, has name \"{}\";".format(b_name))), "s1")

    if method == FEWEST_STOPS:
        compute_query = "compute path from {}, to {}, in [station, tunnel];".format(a_id, b_id)  # Fewest stops
    elif method == FEWEST_ROUTES:
        compute_query = "compute path from {}, to {}, in [station, route];".format(a_id, b_id)  # Fewest changes
    print("Finding shortest paths...")
    shortest_paths = perform_query(compute_query)
    print("...done")
    # print(shortest_paths)

    # The response contains the different permutations for each path through stations. We are mainly interested in
    # which stations the path passes through
    station_paths = []
    for path in shortest_paths:
        station_ids = []
        for concept in path:
            if concept['type']['label'] == 'station':
                station_id = concept['id']
                station_ids.append(station_id)
        station_paths.append(station_ids)

    # Get the unique paths
    unique_paths = [list(x) for x in set(tuple(x) for x in station_paths)]

    # Get a printout of the names of the stations along the path:
    for i, unique_path in enumerate(unique_paths):
        station_names = []
        print("-- Option {} --".format(i))
        print("Via stations:")
        for station_id in unique_path:
            station_name = perform_query("match $s1 id {}, has name $n; get $n;".format(station_id))[0]['n']['value']
            print("+ " + station_name)
            station_names.append(station_name)
