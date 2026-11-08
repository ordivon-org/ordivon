---------------- MODULE RuntimeResourceQueueR1 ----------------
EXTENDS Naturals, FiniteSets, TLC
CONSTANT Jobs
VARIABLES state, allocations, dispatches, cancel, gone
vars == <<state, allocations, dispatches, cancel, gone>>
Cpu(j) == IF j = 1 THEN 2 ELSE IF j = 2 THEN 1 ELSE 0
Writes(j) == IF j = 3 THEN {"a"} ELSE {}
Reads(j) == IF j = 2 THEN {"b"} ELSE {"a"}
Conflict(j,k) == (Writes(j) \cap (Reads(k) \cup Writes(k)) # {}) \/ (Writes(k) \cap Reads(j) # {})
CpuUsed(S) == (IF 1 \in S THEN 2 ELSE 0)+(IF 2 \in S THEN 1 ELSE 0)
Init == /\ state = [j \in Jobs |-> "new"] /\ allocations = {} /\ dispatches = [j \in Jobs |-> 0] /\ cancel = {} /\ gone = {}
Admit(j) == /\ state[j] = "new" /\ state' = [state EXCEPT ![j]="pending"] /\ UNCHANGED <<allocations,dispatches,cancel,gone>>
Claim(j) == /\ state[j]="pending" /\ j \notin cancel /\ CpuUsed(allocations)+Cpu(j)<=2 /\ Cardinality(allocations)<2 /\ \A k \in allocations : ~Conflict(j,k)
 /\ allocations'=allocations \cup {j} /\ state'=[state EXCEPT ![j]="allocated"] /\ UNCHANGED <<dispatches,cancel,gone>>
Issue(j) == /\ state[j]="allocated" /\ j \notin cancel /\ state'=[state EXCEPT ![j]="issued"] /\ dispatches'=[dispatches EXCEPT ![j]=@+1] /\ UNCHANGED <<allocations,cancel,gone>>
Cancel(j) == /\ state[j] \in {"pending","allocated","issued"} /\ cancel'=cancel \cup {j} /\ UNCHANGED <<state,allocations,dispatches,gone>>
CancelUnissued(j) == /\ j \in cancel /\ state[j] \in {"pending","allocated"} /\ state'=[state EXCEPT ![j]="done"] /\ allocations'=allocations \ {j} /\ UNCHANGED <<dispatches,cancel,gone>>
KernelExit(j) == /\ state[j]="issued" /\ gone'=gone \cup {j} /\ UNCHANGED <<state,allocations,dispatches,cancel>>
Release(j) == /\ state[j]="issued" /\ j \in gone /\ state'=[state EXCEPT ![j]="done"] /\ allocations'=allocations \ {j} /\ UNCHANGED <<dispatches,cancel,gone>>
Restart == UNCHANGED vars
Next == (\E j \in Jobs : Admit(j) \/ Claim(j) \/ Issue(j) \/ Cancel(j) \/ CancelUnissued(j) \/ KernelExit(j) \/ Release(j)) \/ Restart
Spec == Init /\ [][Next]_vars
Capacity == CpuUsed(allocations)<=2 /\ Cardinality(allocations)<=2
NoDuplicateDispatch == \A j \in Jobs : dispatches[j]<=1
PendingHasNoAllocation == \A j \in Jobs : state[j]="pending" => j \notin allocations
NoConflictingWriters == \A j,k \in allocations : j=k \/ ~Conflict(j,k)
NativeStillOwnsAllocation == \A j \in Jobs : state[j]="issued" => j \in allocations
===============================================================
