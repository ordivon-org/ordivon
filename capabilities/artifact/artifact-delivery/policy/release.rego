package artifact.release

default ready := false

every_required_verified if {
	every gate in input.verification.required_gates {
		gate in input.verification.passed_gates
	}
}

every_required_assembled if {
	every gate in input.assembly.required_gates {
		gate in input.assembly.satisfied_gates
	}
}

ready if {
	input.package_status == "PASS"
	input.local_unsigned == false
	input.trust_standing == "CRYPTOGRAPHICALLY_VERIFIED"
	every_required_verified
	every_required_assembled
}
