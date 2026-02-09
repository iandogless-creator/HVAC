from HVAC_legacy.heatloss.adapters.simple_heatloss_service_v1 import (
    SimpleHeatLossServiceV1,
)
from HVAC_legacy.heatloss.dto.room_heatloss_row_dto import RoomHeatLossRowDTO


qt = SimpleHeatLossServiceV1.calculate_qt(input_dto)

row = RoomHeatLossRowDTO(
    room_id=input_dto.room_id,
    room_name=input_dto.room_name,
    hl_method="simple",

    qt_calc_w=qt,
    qf_w=qt,
    qv_w=0.0,

    qt_override_w=None,
    notes="",
    is_stale=False,
)

room_store.upsert_row(row)
hl_table_model.refresh_from_store(room_store)
