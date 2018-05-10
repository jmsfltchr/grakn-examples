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

    TUBE_LINE_COLOURS = {
        "Bakerloo": "#B36305",
        "Central": "#E32017",
        "Circle": "#FFD300",
        "District": "#00782A",
        "Hammersmith & City": "#F3A9BB",
        "Jubilee": "#A0A5A9",
        "Metropolitan": "#9B0056",
        "Northern": "#000000",
        "Piccadilly": "#003688",
        "Victoria": "#0098D4",
        "Waterloo & City": "#95CDBA",
    }
    
    ZOOM_IN_SCALE = 1.1
    ZOOM_OUT_SCALE = 0.9

    STATION_FONT_SIZE = 6
    STATION_CIRCLE_RADIUS = 2

    LINE_WIDTH = 2
    LINE_SPACING = 0.5

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

        # ===== DRAW STATIONS =====
        station_query = match_get("$s isa station, has name $name, has naptan-id $naptan-id, has lon $lon, has lat $lat;")
        response = perform_query(station_query)
        print("...query complete")
        for match in response:
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

        # ===== DRAW LINES =====
        tunnels = perform_query("match\n"
                                "$s1 isa station, has lon $lon1, has lat $lat1;\n"
                                "$s2 isa station, has lon $lon2, has lat $lat2;\n"
                                "$tunnel(beginning: $s1, end: $s2) isa tunnel;\n"
                                "get $tunnel, $lon1, $lat1, $lon2, $lat2;")

        for t, tunnel in enumerate(tunnels):
            # Then, using the tunnel's ID, get the tube-lines that run through the tunnel
            tube_lines = perform_query(("match\n"
                                        "$rs isa route-section;\n"
                                        "$tunnel(service: $rs) id {};\n"
                                        "$tube-line isa tube-line, has name $tl-name;\n"
                                        "$route(section: $rs, route-operator: $tube-line) isa route;\n"
                                        "get $tl-name;").format(tunnel["tunnel"]['id']))

            lon1 = scale(float(tunnel['lon1']['value']), min_lon, max_lon, 0, new_width)
            lon2 = scale(float(tunnel['lon2']['value']), min_lon, max_lon, 0, new_width)
            lat1 = new_height - scale(float(tunnel['lat1']['value']), min_lat, max_lat, 0, new_height)
            lat2 = new_height - scale(float(tunnel['lat2']['value']), min_lat, max_lat, 0, new_height)

            # print("Tunnel ID: {}".format(tunnel["tunnel"]['id']))
            for i, tube_line in enumerate(tube_lines):
                # print(tube_line['tl-name']['value'])
                # print("----------")

                dx = lon2 - lon1
                dy = lat2 - lat1
                dz = self.LINE_SPACING
                grad = dy / dx

                dy2 = ((grad ** 2 + 1) ** -0.5) * dz
                dx2 = grad * dy2

                self.canvas.create_line(lon1 - i * dx2, lat1 + i * dy2, lon2 - i * dx2, lat2 + i * dy2, arrow=tk.LAST,
                                        fill=self.TUBE_LINE_COLOURS[tube_line['tl-name']['value']],
                                        width=self.LINE_WIDTH)
            if t > 100:
                break

        self.canvas.pack()

    def scroll_start(self, event):
        self.canvas.scan_mark(event.x, event.y)
        # print("scroll_start {}, {}".format(event.x, event.y))

    def scroll_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        # self.x_pos = event.x
        # self.y_pos = event.y
        # print("scroll_move {}, {}".format(event.x, event.y))

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
