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


def scale_coords(lon, lat, min_lon, max_lon, min_lat, max_lat, new_width, new_height):
    lon = scale(lon, min_lon, max_lon, 0, new_width)
    lat = new_height - scale(lat, min_lat, max_lat, 0, new_height)
    return lon, lat


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

    # Grid coordinates of a path along the centreline of the River Thames
    THAMES_WAYPOINTS = (
                        (51.388592, -0.426814),
                        (51.404487, -0.409858),
                        (51.409538, -0.390457),
                        (51.407749, -0.379153),
                        (51.412011, -0.361944),
                        (51.405223, -0.345663),
                        (51.391487, -0.326768),
                        (51.400803, -0.309137),
                        (51.424900, -0.308209),
                        (51.432526, -0.326262),
                        (51.443253, -0.329383),
                        (51.451718, -0.303738),
                        (51.456028, -0.305088),
                        (51.465068, -0.320778),
                        (51.471164, -0.319176),
                        (51.484088, -0.297243),
                        (51.487082, -0.288217),
                        (51.483983, -0.279444),
                        (51.471742, -0.266622),
                        (51.470839, -0.261951),
                        (51.474607, -0.251973),
                        (51.484884, -0.249098),
                        (51.489681, -0.237854),
                        (51.487997, -0.229271),
                        (51.473779, -0.223284),
                        (51.466401, -0.211568),
                        (51.464329, -0.191527),
                        (51.467697, -0.182686),
                        (51.480180, -0.175627),
                        (51.484764, -0.148011),
                        (51.483788, -0.137282),
                        (51.487129, -0.127519),
                        (51.506112, -0.120438),
                        (51.508943, -0.116210),
                        (51.508916, -0.094474),
                        (51.505297, -0.074797),
                        (51.502198, -0.064648),
                        (51.502131, -0.056944),
                        (51.508155, -0.044370),
                        (51.508035, -0.035337),
                        (51.505244, -0.029843),
                        (51.491952, -0.029285),
                        (51.485566, -0.020659),
                        (51.485272, -0.007892),
                        (51.489935, -0.001047),
                        (51.501490, -0.005360),
                        (51.507260, 0.001378),
                        (51.506526, 0.005648),
                        (51.496922, 0.021677),
                        (51.497620, 0.073815),
                        (51.511549, 0.090750),
                        (51.516348, 0.127855),
                        (51.506580, 0.167984),
                        (51.503888, 0.172763),
                        (51.485042, 0.184526),
                        (51.485852, 0.213678),
                        (51.457240, 0.280714),
                        )

    THAMES_WIDTH = 10

    ZOOM_IN_SCALE = 2
    ZOOM_OUT_SCALE = 1/ZOOM_IN_SCALE

    STATION_FONT_SIZE = 8
    STATION_CIRCLE_RADIUS = 1

    STATION_K_CORE_COLOUR = "#AAF"
    STATION_K_CORE_MAX_RADIUS = 8

    STATION_DEGREE_COLOUR = "#FAA"
    STATION_DEGREE_MAX_RADIUS = 10

    ROUTES_DEGREE_COLOUR = "#AFA"
    ROUTES_DEGREE_MAX_RADIUS = 8

    TUNNEL_SHORTEST_PATH_COLOUR = "#DDD"
    TUNNEL_SHORTEST_PATH_WIDTH = 10

    # Properties of the station connections drawn
    LINE_WIDTH = 2
    LINE_SPACING = 0.5

    def __init__(self, root, grakn_client):
        self.root = root
        self.grakn_client = grakn_client
        self.w, self.h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry("%dx%d+0+0" % (self.w, self.h))
        self.root.focus_set()
        self.root.bind("<Escape>", lambda e: e.widget.quit())
        self.root.bind("<Key>", self.key_handler)
        self.root.title('London Tube Map')

        self.canvas = tk.Canvas(self.root)
        self.canvas.bind("<ButtonPress-1>", self.scan_start)
        self.canvas.bind("<ButtonRelease-1>", self.scan_stop)
        self.canvas.bind("<B1-Motion>", self.scan_move)
        self.canvas.pack(fill=tk.BOTH, expand=1)  # Stretch canvas to root window size.

        # We want to scale the longitude and latitude to fit the image
        # To do this we need the minimum and maximum of the longitude and latitude, we can query for this easily!
        compute_coords_limits = "compute {} of {}, in station;"

        min_lat = self.perform_query(compute_coords_limits.format("min", "lat"))
        max_lat = self.perform_query(compute_coords_limits.format("max", "lat"))
        min_lon = self.perform_query(compute_coords_limits.format("min", "lon"))
        max_lon = self.perform_query(compute_coords_limits.format("max", "lon"))

        # aspect ratio as width over height, which is longitude over latitude
        aspect_ratio = (max_lon - min_lon) / (max_lat - min_lat)
        new_width = self.w
        new_height = new_width / aspect_ratio

        # ===== DRAW RIVER THAMES =====

        scaled_thames_coords = []
        for lat, lon in self.THAMES_WAYPOINTS:
            lon, lat = scale_coords(lon, lat, min_lon, max_lon, min_lat, max_lat, new_width, new_height)
            scaled_thames_coords.append((lon, lat))

        thames_line = self.canvas.create_line(*scaled_thames_coords, width=self.THAMES_WIDTH, fill="#def",
                                              joinstyle=tk.ROUND)

        # ===== DRAW LINES =====
        tunnels = self.perform_query("match\n"
                                "$s1 isa station, has lon $lon1, has lat $lat1;\n"
                                "$s2 isa station, has lon $lon2, has lat $lat2;\n"
                                "$tunnel(beginning: $s1, end: $s2) isa tunnel;\n"
                                "get $tunnel, $lon1, $lat1, $lon2, $lat2;")

        for t, tunnel in enumerate(tunnels):
            # Then, using the tunnel's ID, get the tube-lines that run through the tunnel
            tube_lines = self.perform_query(("match\n"
                                        "$rs isa route-section;\n"
                                        "$tunnel(service: $rs) id {};\n"
                                        "$tube-line isa tube-line, has name $tl-name;\n"
                                        "$route(section: $rs, route-operator: $tube-line) isa route;\n"
                                        "get $tl-name;").format(tunnel["tunnel"]['id']))

            lon1, lat1 = scale_coords(float(tunnel['lon1']['value']), float(tunnel['lat1']['value']),
                                                  min_lon, max_lon, min_lat, max_lat, new_width, new_height)
            lon2, lat2 = scale_coords(float(tunnel['lon2']['value']), float(tunnel['lat2']['value']),
                                                  min_lon, max_lon, min_lat, max_lat, new_width, new_height)

            # Sort the tube lines alphabetically to get a consistent pattern
            tube_line_names = []
            for tube_line in tube_lines:
                tube_line_names.append(tube_line['tl-name']['value'])

            tube_line_names = sorted(tube_line_names)

            for i, tube_line_name in enumerate(tube_line_names):

                # Trigonometry to draw parallel lines with consistent distance between them
                dx = lon2 - lon1
                dy = lat2 - lat1
                dz = self.LINE_SPACING
                grad = dy / dx

                dy2 = ((grad ** 2 + 1) ** -0.5) * dz
                dx2 = grad * dy2

                self.canvas.create_line(lon1 - (i * dx2), lat1 + (i * dy2), lon2 - (i * dx2), lat2 + (i * dy2),
                                        fill=self.TUBE_LINE_COLOURS[tube_line_name],
                                        width=self.LINE_WIDTH)

        # ===== DRAW STATIONS =====

        # We need to associate the id of the station entity in Grakn to the rendered dot on the screen, so that we can
        # find the Grakn id of a station that is clicked on
        self.station_point_ids = dict()
        # Also store the station coords so that we don't have to query Grakn for them again
        self.station_canvas_coords = dict()
        self.station_centrality_points = dict()
        station_name_labels = dict()
        suffix = " Underground Station"

        station_query = match_get("$s isa station, has name $name, has lon $lon, has lat $lat; ($s) isa tunnel;")
        response = self.perform_query(station_query)
        print("...query complete")
        for match in response:
            station_id = match['s']['id']
            name = match['name']['value']
            if name.endswith(suffix):
                name = name[:-len(suffix)]

            print("drawing station: {}".format(station_id))

            lon, lat = scale_coords(float(match['lon']['value']), float(match['lat']['value']),
                                    min_lon, max_lon, min_lat, max_lat, new_width, new_height)

            self.station_canvas_coords[station_id] = (lon, lat)
            station_tag = self.canvas.create_circle(lon, lat, self.STATION_CIRCLE_RADIUS,
                                                                  fill="white", outline="black")
            self.station_point_ids[station_id] = station_tag

            l = lambda event, id=station_id: self.on_station_click(event, id)

            event_sequence = "<Shift-ButtonPress-1>"

            self.canvas.tag_bind(self.station_point_ids[station_id], event_sequence, l)

            station_label_tag = self.canvas.create_text(lon + self.STATION_CIRCLE_RADIUS,
                                                        lat + self.STATION_CIRCLE_RADIUS,
                                                        text=name, anchor=tk.NW,
                                                        font=('Johnston', self.STATION_FONT_SIZE, 'bold'),
                                                        fill="#666")
            station_name_labels[station_id] = station_label_tag
            self.canvas.tag_bind(station_label_tag, event_sequence, l)

        self.canvas.pack()

        # ===== Event state variables =====
        self._displaying_centrality = False
        self._scale = 1
        self._shortest_path_stations = []
        self._shortest_path_elements = []
        self._scan_delta = (0, 0)
        self.x_pos = 0
        self.y_pos = 0
        self._scanning = False

    def perform_query(self, graql_string):
        print(graql_string)
        # Send the graql query to the server
        response = self.grakn_client.execute(graql_string)
        return response

    def scan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self._scan_start_pos = event.x, event.y
        self._scanning = True

    def scan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

        self._scan_delta = event.x - self._scan_start_pos[0], event.y - self._scan_start_pos[1]
        print("scan delta: {}".format(self._scan_delta))

    def scan_stop(self, event):
        self.x_pos += self._scan_delta[0]
        self.y_pos += self._scan_delta[1]
        self._scan_delta = (0, 0)
        self._scanning = False
        print("New pos: {}, {}".format(self.x_pos, self.y_pos))

    def key_handler(self, event):
        print(event.char)
        if event.char == "+" or event.char == "=":
            self.zoom("in")
        elif event.char == "-" or event.char == "_":
            self.zoom("out")
        elif event.char == "z":
            self.show_zones()
        elif event.char == "g":
            query = "compute centrality of station, in [station, tunnel], using degree;"
            self.display_centrality(query, self.STATION_DEGREE_MAX_RADIUS, self.STATION_DEGREE_COLOUR)
        elif event.char == "k":
            query = "compute centrality of station, in [station, tunnel], using k-core;"
            self.display_centrality(query, self.STATION_K_CORE_MAX_RADIUS, self.STATION_K_CORE_COLOUR)
        elif event.char == "r":
            query = "compute centrality of station, in [station, route], using degree;"
            self.display_centrality(query, self.ROUTES_DEGREE_MAX_RADIUS, self.ROUTES_DEGREE_COLOUR)
        elif event.char == "q":
            self.clear_shortest_path()

    def on_station_click(self, event, station_id):
        self._shortest_path_stations.append(station_id)

        x, y = self.get_station_point_coords(station_id)
        r = self.transform_to_current_scale(2 * self.STATION_CIRCLE_RADIUS)
        c = self.canvas.create_circle(x, y, r, fill=self.TUNNEL_SHORTEST_PATH_COLOUR, outline="")
        self.canvas.tag_lower(c, 1)

        self._shortest_path_elements.append(c)

        if len(self._shortest_path_stations) > 1:
            query = "compute path from {}, to {}, in [station, tunnel];".format(self._shortest_path_stations[-2],
                                                                                self._shortest_path_stations[-1])
            shortest_path = self.perform_query(query)
            self.display_shortest_path(shortest_path, self.TUNNEL_SHORTEST_PATH_COLOUR, self.TUNNEL_SHORTEST_PATH_WIDTH)

    def display_shortest_path(self, shortest_path, colour, width):
        # The response contains the different permutations for each path through stations. We are mainly interested in
        # which stations the path passes through
        station_paths = []
        for path in shortest_path:
            station_ids = []
            for concept in path:
                if concept['type']['label'] == 'station':
                    station_id = concept['id']
                    station_ids.append(station_id)
            station_paths.append(station_ids)

        # Get the unique paths
        unique_paths = [list(x) for x in set(tuple(x) for x in station_paths)]

        for unique_path in unique_paths:
            path_points = []
            for station_id in unique_path:
                # TODO Look at uniqueness of these paths
                x0, y0, x1, y1 = self.canvas.coords(self.station_point_ids[station_id])
                point = int((x0 + x1) / 2), int((y0 + y1) / 2)
                path_points.append(point)

            path = self.canvas.create_line(*path_points, width=width, fill=colour, joinstyle=tk.ROUND, dash=(3, 3))
            self._shortest_path_elements.append(path)
            self.canvas.tag_lower(path, 1)

    def get_station_point_coords(self, station_id):
        x0, y0, x1, y1 = self.canvas.coords(self.station_point_ids[station_id])
        point = (x0 + x1) / 2, (y0 + y1) / 2
        return point

    def clear_shortest_path(self):
        self.canvas.delete(*self._shortest_path_elements)
        self._shortest_path_stations = []

    def zoom(self, direction):
        if self._scanning:
            print("Currently scanning. Stop scanning to zoom.")
        else:
            if direction == "in":
                scaling = self.ZOOM_IN_SCALE
            elif direction == "out":
                scaling = self.ZOOM_OUT_SCALE
            else:
                raise ValueError("Call to zoom didn't specify a valid direction")

            # First, scale up the canvas about its origin. Doing this about the canvas origin keeps adding other
            # elements to the canvas simple, because then only scaling needs to be applied
            self.canvas.scale('all', 0, 0, scaling, scaling)

            # Update the persistent scale value
            self._scale *= scaling

            # Find the displacement to shift the canvas by, so that is appears to scale about the centre-point of the
            # window
            dx = -int((1 - scaling) * (self.x_pos - self.w / 2))
            dy = -int((1 - scaling) * (self.y_pos - self.h / 2))

            # Since we're shifting by this amount, also add this displacement to the persistent scan variables
            self.x_pos += dx
            self.y_pos += dy

            # Set an anchor to drag from. I believe this point is arbitrary
            self.canvas.scan_mark(0, 0)

            # The canvas is being scaled about its origin, so we only need to drag the delta to centre the scaling
            self.canvas.scan_dragto(dx, dy, gain=1)

            print("zoom set scan position to {}, {}".format(int(self.x_pos), int(self.y_pos)))

    def transform_to_current_scale(self, val):
        return val * self._scale

    def display_centrality(self, query, upper_radius, colour):
        if not self._displaying_centrality:
            centrality = self.perform_query(query)

            # Find the max centrality value
            max_score = max([int(s) for s in centrality.keys()])

            for score, concept_ids in centrality.items():
                for concept_id in concept_ids:
                    station_element_id = self.station_point_ids[concept_id]
                    lon, lat = self.station_canvas_coords[concept_id]

                    lon = self.transform_to_current_scale(lon)
                    lat = self.transform_to_current_scale(lat)

                    radius = self.transform_to_current_scale((int(score) / max_score) * upper_radius)

                    centrality_element_id = self.canvas.create_circle(lon, lat,
                                                                      radius,
                                                                      fill=colour, outline="")

                    self.station_centrality_points[concept_id] = centrality_element_id
                    self.canvas.tag_lower(centrality_element_id, station_element_id)
        else:
            for concept_id, point_id in self.station_centrality_points.items():
                self.canvas.delete(point_id)

        self._displaying_centrality = not self._displaying_centrality


if __name__ == "__main__":
    grakn_client = grakn.Client(uri=settings.uri, keyspace=settings.keyspace)
    root = tk.Tk()

    tube_gui = TubeGui(root, grakn_client)
    root.mainloop()
