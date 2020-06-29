\* MasterProblem *\
Minimize
OBJ: 10000000000 artificial_bound_0 + 10000000000 artificial_bound_1 + 30 y1
 + 40 y10 + 30 y11 + 30 y2 + 30 y3 + 30 y4 + 30 y5 + 40 y6 + 40 y7 + 45 y8
 + 20 y9
Subject To
upper_bound_vehicles_0: - artificial_bound_0 + y1 + y10 + y2 + y3 + y4 + y5
 + y6 <= 5
upper_bound_vehicles_1: - artificial_bound_1 + y11 + y7 + y8 + y9 <= 1
visit_node_1: y1 + y7 >= 1
visit_node_2: y10 + y11 + y2 + y7 >= 1
visit_node_3: y10 + y11 + y3 + y7 + y8 >= 1
visit_node_4: y4 + y6 + y8 >= 1
visit_node_5: y5 + y6 + y8 + y9 >= 1
Bounds
y1 <= 1
y2 <= 1
y3 <= 1
y4 <= 1
y5 <= 1
y6 <= 1
y7 <= 1
y8 <= 1
y9 <= 1
Binaries
y10
y11
End
