import tkinter as tk
import grakn
import tube_network_example.settings as settings
from utils.utils import check_response_length, match_get, insert, match_insert, get_match_id


station_radius = 4

tube_line_colours = {''}


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
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    # root.overrideredirect(1) # Removes the window title bar
    root.geometry("%dx%d+0+0" % (w, h))
    root.focus_set()
    root.bind("<Escape>", lambda e: e.widget.quit())

    # root.configure(background='black')
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

    # min_lat = perform_query(compute_coords_limits.format("min", "lat"))
    # max_lat = perform_query(compute_coords_limits.format("max", "lat"))
    # min_lon = perform_query(compute_coords_limits.format("min", "lon"))
    # max_lon = perform_query(compute_coords_limits.format("max", "lon"))

    min_lat, max_lat, min_lon, max_lon = 51.402142, 51.705208, -0.611247, 0.250882

    # aspect ratio as width over height, which is longitude over latitude
    aspect_ratio = (max_lon - min_lon) / (max_lat - min_lat)
    new_width = w
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
        lat = scale(float(match['lat']['value']), min_lat, max_lat, 0, new_height)
        station_points[naptan_id] = canvas.create_circle(lon, lat, station_radius, fill="black", outline="")
        station_name_labels[naptan_id] = canvas.create_text(lon + station_radius, lat + station_radius, text=name,
                                                            anchor=tk.NW, font=('Johnston', 6, 'bold'), fill="#666")
    canvas.pack()

    zoom_in_scale = 1.1
    zoom_out_scale = 0.9

    def scroll_start(event):
        canvas.scan_mark(event.x, event.y)


    def scroll_move(event):
        canvas.scan_dragto(event.x, event.y, gain=1)

    def wheel(event):
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        canvas.scale('all', x, y, scale, scale)

    def key_handler(event):
        print(event.char)
        if event.char == "+":
            canvas.scale('all', int(w/2), int(h/2), zoom_in_scale, zoom_in_scale)
        if event.char == "_":
            canvas.scale('all', int(w/2), int(h/2), zoom_out_scale, zoom_out_scale)

    canvas.bind("<ButtonPress-1>", scroll_start)
    canvas.bind("<B1-Motion>", scroll_move)
    # canvas.bind_all('<MouseWheel>', wheel)  # with Windows and MacOS, but not Linux
    # canvas.bind_all('<Button-5>', wheel)  # only with Linux, wheel scroll down
    # canvas.bind_all('<Button-4>', wheel)  # only with Linux, wheel scroll up

    root.bind("<Key>", key_handler)

    # root.wm_geometry("794x370")
    # canvas.configure(scrollregion=canvas.bbox("all"))  # Doesn't seem to do anything
    root.title('Map')
    # root.configure(background="#000")  # Seems not to work on Mac
    # root.configure(bg="red")
    # root["bg"] = "black"
    # canvas.scale(1.5, 1.5)
    root.mainloop()
    # while True:
    #     try:
    #         root.mainloop()
    #         break
    #     except UnicodeDecodeError:
    #         pass
