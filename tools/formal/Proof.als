sig Node {}
run { some Node } for 2
check alwaysMember { all n : Node | n in Node } for 2
