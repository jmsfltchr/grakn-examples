
import os
download_dir_name = "data-downloads"
routes_path = "{}/{}/routes/".format(os.path.dirname(__file__), download_dir_name)
timetables_path = "{}/{}/timetables/".format(os.path.dirname(__file__), download_dir_name)

lines = ["bakerloo",
         "central",
         "circle",
         "district",
         "hammersmith-city",
         "jubilee",
         "metropolitan",
         "northern",
         "piccadilly",
         "victoria",
         "waterloo-city"]

uri = 'http://localhost:4567'
keyspace = "tube_example_3"
