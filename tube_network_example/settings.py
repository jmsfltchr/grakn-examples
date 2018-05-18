
import os
download_dir_name = "data-downloads"
routes_path = "{}/{}/routes/".format(os.path.dirname(__file__), download_dir_name)
timetables_path = "{}/{}/timetables/".format(os.path.dirname(__file__), download_dir_name)
migration_logs_path = "{}/src/migrations/logs/".format(os.path.dirname(__file__))

uri = 'http://localhost:4567'
keyspace = "tube_example"
