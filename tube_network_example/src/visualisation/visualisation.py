import tkinter as tk
import grakn
import tube_network_example.settings as settings
from utils.utils import check_response_length, match_get, insert, match_insert, get_match_id




tube_line_colours = {''}


def scale(val, old_min, old_max, new_min, new_max):
    old_range = (old_max - old_min)
    new_range = (new_max - new_min)
    new_val = (((val - old_min) * new_range) / old_range) + new_min
    return new_val


def _create_circle(self, x, y, r, **kwargs):
    return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)


tk.Canvas.create_circle = _create_circle


class TubeGui:
    
    ZOOM_IN_SCALE = 1.1
    ZOOM_OUT_SCALE = 0.9

    STATION_FONT_SIZE = 6
    STATION_CIRCLE_RADIUS = 2
    
    def __init__(self, root):
        self.root = root
        self.w, self.h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.x_pos = int(self.w / 2)
        self.y_pos = int(self.h / 2)
        self.root.geometry("%dx%d+0+0" % (self.w, self.h))
        self.root.focus_set()
        self.root.bind("<Escape>", lambda e: e.widget.quit())
        self.root.bind("<Key>", self.key_handler)
        self.root.title('Map')

        self.canvas = tk.Canvas(self.root)
        self.canvas.bind("<ButtonPress-1>", self.scroll_start)
        self.canvas.bind("<B1-Motion>", self.scroll_move)
        self.canvas.pack(fill=tk.BOTH, expand=1)  # Stretch canvas to root window size.

        def perform_query(graql_string):
            print(graql_string)
            # Send the graql query to the server
            response = client.execute(graql_string)
            return response

        # line = self.canvas.create_line(10, 10, 100, 35, fill="red")

        # We want to scale the longitude and latitude to fit the image
        # To do this we need the minimum and maximum of the longitude and latitude, we can query for this easily!
        compute_coords_limits = "compute {} of {}, in station;"

        # min_lat = perform_query(compute_coords_limits.format("min", "lat"))
        # max_lat = perform_query(compute_coords_limits.format("max", "lat"))
        # min_lon = perform_query(compute_coords_limits.format("min", "lon"))
        # max_lon = perform_query(compute_coords_limits.format("max", "lon"))

        min_lat, max_lat, min_lon, max_lon = 51.402142, 51.705208, -0.611247, 0.250882

        # aspect ratio as width over height, which is longitude over latitude
        aspect_ratio = (max_lon - min_lon) / (max_lat - min_lat)
        new_width = self.w
        new_height = new_width / aspect_ratio

        station_points = dict()
        station_name_labels = dict()
        suffix = " Underground Station"

        station_query = match_get("$s isa station, has name $name, has naptan-id $naptan-id, has lon $lon, has lat $lat;")
        response = perform_query(station_query)
        print("...query complete")
        for i, match in enumerate(response):
            naptan_id = match['naptan-id']['value']
            name = match['name']['value']
            if name.endswith(suffix):
                name = name[:-len(suffix)]

            print("drawing station: {}".format(naptan_id))
            lon = scale(float(match['lon']['value']), min_lon, max_lon, 0, new_width)
            lat = new_height - scale(float(match['lat']['value']), min_lat, max_lat, 0, new_height)
            station_points[naptan_id] = self.canvas.create_circle(lon, lat, self.STATION_CIRCLE_RADIUS,
                                                                  fill="white", outline="black")
            station_name_labels[naptan_id] = self.canvas.create_text(lon + self.STATION_CIRCLE_RADIUS,
                                                                     lat + self.STATION_CIRCLE_RADIUS,
                                                                     text=name, anchor=tk.NW,
                                                                     font=('Johnston', self.STATION_FONT_SIZE, 'bold'),
                                                                     fill="#666")
        self.canvas.pack()

    def scroll_start(self, event):
        self.canvas.scan_mark(event.x, event.y)
        print("scroll_start {}, {}".format(event.x, event.y))

    def scroll_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        # self.x_pos = event.x
        # self.y_pos = event.y
        print("scroll_move {}, {}".format(event.x, event.y))

    def key_handler(self, event):
        print(event.char)
        if event.char == "+" or event.char == "=":
            # self.canvas.scale('all', int(self.x_pos), int(self.y_pos), self.ZOOM_IN_SCALE, self.ZOOM_IN_SCALE)
            self.canvas.scale('all', int(self.w/2), int(self.h/2), self.ZOOM_IN_SCALE, self.ZOOM_IN_SCALE)
        elif event.char == "-" or event.char == "_":
            # self.canvas.scale('all', int(self.x_pos), int(self.y_pos), self.ZOOM_OUT_SCALE, self.ZOOM_OUT_SCALE)
            self.canvas.scale('all', int(self.w/2), int(self.h/2), self.ZOOM_OUT_SCALE, self.ZOOM_OUT_SCALE)


if __name__ == "__main__":

    client = grakn.Client(uri=settings.uri, keyspace=settings.keyspace)
    root = tk.Tk()

    tube_gui = TubeGui(root)
    root.mainloop()
