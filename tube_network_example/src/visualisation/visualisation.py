import tkinter as tk
import grakn
import tube_network_example.settings as settings
from utils.utils import check_response_length, match_get, insert, match_insert, get_match_id


station_radius = 4


def scale(val, old_min, old_max, new_min, new_max):
    old_range = (old_max - old_min)
    new_range = (new_max - new_min)
    new_val = (((val - old_min) * new_range) / old_range) + new_min
    return new_val


def _create_circle(self, x, y, r, **kwargs):
    return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)


tk.Canvas.create_circle = _create_circle


if __name__ == "__main__":

    client = grakn.Client(uri=settings.uri, keyspace=settings.keyspace)
    root = tk.Tk()
    # frame = tk.Frame(root, width=1000, height=200)
    canvas = tk.Canvas(root)
    # background_image=tk.PhotoImage(file="map.png")
    canvas.pack(fill=tk.BOTH, expand=1) # Stretch canvas to root window size.
    # image = canvas.create_image(0, 0, anchor=tk.NW, image=background_image)

    def perform_query(graql_string):
        print(graql_string)
        # Send the graql query to the server
        response = client.execute(graql_string)
        return response


    # line = canvas.create_line(10, 10, 100, 35, fill="red")

    # We want to scale the longitude and latitude to fit the image
    # To do this we need the minimum and maximum of the longitude and latitude, we can query for this easily!
    compute_coords_limits = "compute {} of {}, in station;"

    min_lat = perform_query(compute_coords_limits.format("min", "lat"))
    max_lat = perform_query(compute_coords_limits.format("max", "lat"))
    min_lon = perform_query(compute_coords_limits.format("min", "lon"))
    max_lon = perform_query(compute_coords_limits.format("max", "lon"))

    # aspect ratio as width over height, which is longitude over latitude
    aspect_ratio = (max_lon - min_lon) / (max_lat - min_lat)
    new_width = 1000
    new_height = new_width / aspect_ratio

    station_points = dict()

    station_query = match_get("$s isa station, has naptan-id $naptan-id, has lon $lon, has lat $lat;")
    response = perform_query(station_query)
    print("...query complete")
    for i, match in enumerate(response):
        naptan_id = match['naptan-id']['value']
        print("drawing station: {}".format(naptan_id))
        lon = scale(float(match['lon']['value']), min_lon, max_lon, 0, new_width)
        lat = scale(float(match['lat']['value']), min_lat, max_lat, 0, new_height)
        station_points[naptan_id] = canvas.create_circle(lon, lat, station_radius, fill="blue", outline="")

    # root.wm_geometry("794x370")
    canvas.configure(scrollregion=canvas.bbox("all"))  # Doesn't seem to do anything
    root.title('Map')
    root.mainloop()