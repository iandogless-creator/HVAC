from HVAC.hydronics.proportioning.balancing_point_assumption_v1 import (
    get_default_balancing_point_assumption_v1,
)


def main() -> None:
    assumption = get_default_balancing_point_assumption_v1()

    print("SCOPE:", assumption.scope)
    print("APPLICATION POINT:", assumption.application_point)
    print("ADDED RESISTANCE BASIS:", assumption.added_resistance_basis)
    print("ROOM LEVEL:", assumption.room_level_control)
    print("EMITTER LEVEL:", assumption.emitter_level_control)
    print("VALVE SELECTION:", assumption.valve_selection)
    print("STATUS:", assumption.status)

    assert assumption.scope == "route/subleg"
    assert assumption.room_level_control == "not used in v1"
    assert assumption.emitter_level_control == "not used in v1"
    assert assumption.valve_selection == "not selected"


if __name__ == "__main__":
    main()