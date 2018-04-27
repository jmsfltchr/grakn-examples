from tube_network_example.settings

"""
Get the routes and their origination and termination stations
"""
q = ("match $r isa route; $o isa stop; $orig(originates-at: $o, has-route:$r) isa origination; "
     "$t isa stop; $term(terminates-at: $t, has-route:$r) isa termination; "
     "get $r, $o, $orig, $t, $term;")

"""
Get the names of all origin stations
"""
q = ("match $rs isa route-section, has is-origin true; $rs(goes-from: $o); "
     "$o isa stop; $o has name $name; get $name;")

#Get from a to b passing through the fewest stops:
"""compute path from "V262368" to "V86160" in stop, route-section;"""






"""
===== DEMO =====

match
$s1 isa stop has name "Lancaster Gate Underground Station";
$s2 isa stop has name "Edgware Road (Circle Line) Underground Station"; offset 0; limit 999; get;

compute path from "V86160" to "V262368" in stop, route-section;
compute path from "V86160" to "V262368" in stop, route-section, route;

=== ZONES ===
match $s isa stop;
$z isa zone;
($s, $z) isa zoning; get;
compute path from "V1880232" to "V1044704" in stop, route-section, route;

=== LINES PASSING THROUGH STOP ===
To be run in the dashboard console
match 
$s isa stop has name "Green Park Underground Station";
$r isa route;
$rs($r, $s) isa route-section;
$l isa line, has name $line-name;
($l, $r) isa operation;
get $line-name;


=== CONNECTEDNESS ===
match
$s1 isa stop;
$s2 isa stop;
$l isa line;
$c($s1, $s2, $l) isa connection;
get $s1, $s2, $c; 


"""

"""
on-line sub rule,
    when {

    }
"""



"""
>>> compute path from "V2355368" to "V86160" in stop, route-section;
Exception in thread "main" io.grpc.StatusRuntimeException: UNKNOWN
        at io.grpc.Status.asRuntimeException(Status.java:526)
        at io.grpc.stub.ClientCalls$StreamObserverToCallListenerAdapter.onClose(ClientCalls.java:418)
        at io.grpc.ForwardingClientCallListener.onClose(ForwardingClientCallListener.java:41)
        at io.grpc.internal.CensusStatsModule$StatsClientInterceptor$1$1.onClose(CensusStatsModule.java:663)
        at io.grpc.ForwardingClientCallListener.onClose(ForwardingClientCallListener.java:41)
        at io.grpc.internal.CensusTracingModule$TracingClientInterceptor$1$1.onClose(CensusTracingModule.java:392)
        at io.grpc.internal.ClientCallImpl.closeObserver(ClientCallImpl.java:443)
        at io.grpc.internal.ClientCallImpl.access$300(ClientCallImpl.java:63)
        at io.grpc.internal.ClientCallImpl$ClientStreamListenerImpl.close(ClientCallImpl.java:525)
        at io.grpc.internal.ClientCallImpl$ClientStreamListenerImpl.access$600(ClientCallImpl.java:446)
        at io.grpc.internal.ClientCallImpl$ClientStreamListenerImpl$1StreamClosed.runInContext(ClientCallImpl.java:557)
        at io.grpc.internal.ContextRunnable.run(ContextRunnable.java:37)
        at io.grpc.internal.SerializingExecutor.run(SerializingExecutor.java:123)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
        at java.lang.Thread.run(Thread.java:748)
"""


"""
# Get from a to b using with the fewest changes:
"compute path from "V262368" to "V86160" in stop, route-section, route;"


Then get the lines of the routes
match $line isa line; 
$route isa route, has identifier 4;
($route, $line) isa operation;
get;
"""

"""
Get all stops, routes and route-sections on the Central line

match $l isa line, has name "Central";
$r isa route;
($r, $l) isa operation;
$s1 isa stop;
$s2 isa stop;
$rs($r, $s1, $s2) isa $route-section;
get $s1, $s2, $rs;
"""

"""
Questions to ask of the dataset:

Do all trains take the same amount of time to travel between 2 stations?
How does the schedules time compare with the actual time taken?
What speed do the trains travel at?
What's the velocity profile of the trains?
How long do trains stop for?
What's the longest stop on the network?
What's the shortest stop on the network?
What's the average stop duration on the network?

Can we find the mean and std dev of the stop durations on a per-line basis to determine the "fastest" tube line? Could 
also factor in the distance between the stops to actually do the same process but for velocity rather than stop duration 

Journey planner: 
from a to b, how to choose a path: shortest in time, number of changes, distance, monetary cost, or a cost function 
between these

Determine: 
-the duration of the journey
-the stops passed through
-the lines used, and where to change
-how much that will cost also, depending on the fare between the zone of the origin and the destination
-the length in km of the route

We can also determine the distance as-the-crow flies from the latitude and longitude of the start and end stations


Can we use oyster card journey card data combined with ML to predict actual journey times? We can build a dataset 
based on the number of changes, the lines involved, the time of day of the journey etc
"""

"""===== ===== ===== ===== ANSWERS ===== ===== ===== ===== ====="""

"""
Do all trains take the same amount of time to travel between 2 stations?

match
$s1 isa stop;
$s2 isa stop;
$rs1($s1, $s2) isa route-section has duration $d1;
$rs2($s1, $s2) isa route-section has duration $d2;
$d1 != $d2;
get $s1, $s2, $d1, $d2, $rs1, $rs2;

This returns some results, but not that many compared to the full number of route-sections in the graph

compute count 
"""

"""
What's the longest stop on the network?

compute max of duration in route-section;

Instead get all the statistics you want in one go:
match $rs isa route-section, has duration $d; aggregate (min $d as minDuration, max $d as maxDuration);

"""