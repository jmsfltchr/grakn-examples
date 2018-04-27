
import os
download_dir_name = "data-downloads"
routes_path = "{}/{}/routes/".format(download_dir_name, os.path.dirname(__file__))
timetables_path = "{}/{}/timetables/".format(download_dir_name, os.path.dirname(__file__))

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
keyspace = "tube_example_9"
