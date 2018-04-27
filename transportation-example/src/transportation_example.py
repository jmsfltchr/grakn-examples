import grakn

# Examples of an application built on top of TFL transport data

# ./grakn server start
# ./graql console -k transportation_example -f ../grakn-examples/transportation-example/src/schema.gql

q = 1

var_to_find = "res"
if q == 0:
    query = ("match\n"
             "$start isa stop, has name \"Ealing Broadway Underground Station\";\n"
             "$end isa stop, has name \"Epping Underground Station\";\n"
             "(origin: $start, destination: $end, has-route-section: ${}) isa has-stops; get ${};".format(var_to_find,
                                                                                                          var_to_find,
                                                                                                          var_to_find)
             )
#     # "${}(origin: $start, destination: $end) isa has-stops; get ${};".format(var_to_find, var_to_find)

if q == 1:
    query = ("match\n"
             "$start isa stop, has name \"Ealing Broadway Underground Station\";\n"
             "$end isa stop, has name \"Epping Underground Station\";\n"
             "$r has name ${};\n"
             "(origin: $start, destination: $end, has-route-section: $r) isa has-stops; get ${};".format(var_to_find,
                                                                                                         var_to_find)
             )
if q == 2:
    query = ("match\n"
             "$start isa stop, has name \"Ealing Broadway Underground Station\";\n"
             "$end isa stop, has name \"Epping Underground Station\";\n"
             "${}(connected-stop: $start, connected-stop: $end) isa connection; get ${};".format(var_to_find,
                                                                                                 var_to_find)
             )  # This created an intensive task that continued to use 100% CPU even after I ctrl+c'd the process in the terminal

if q == 3:
    query = ("match\n"
             "${} isa stop, has name \"Ealing Broadway Underground Station\"; get;".format(var_to_find))


if q == 4:
    query = ("match" 
             "$x isa stop, has name \"Woolwich Ferry South Pier\";"
             "$y isa stop;"
             "$c ($x, $y) isa connection;"
             "get;")

    "match $x isa stop, has name "Ealing Broadway Underground Station";
$x isa stop;
(connected-from: $x, connected-to: $y) isa connection; get;"



print(query)
client = grakn.Client(uri='http://localhost:4567', keyspace='transportation_example')
result = client.execute(query)
print(result)
print("-------")
print("Type of result:")
print(result[0][var_to_find]['type']['label'])

print("-------")
print("Value of result:")
print(result[0][var_to_find]['value'])
