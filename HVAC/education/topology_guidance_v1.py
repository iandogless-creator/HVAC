"""H-S74-A: programme guidance for the existing Topology Arranger.

Text only. This module never reads ProjectState, validates topology or calculates.
Terms and restrictions follow recursive_subleg_contract_v1, creation/placement
candidates and the arranger adapter. Classical explains the data relationships;
it does not invent hydraulic results from the schematic.
"""

TOPOLOGY_STEPS_V1 = (
    ('start', 'Start', 'Check the heat-source room in Environment and review the existing connections. The schematic shows topology, not measured pipe lengths.'),
    ('legs', 'Legs', 'Select an initial room, then create a leg with its first principal subleg, or add a principal to the selected leg. An allocated room will move.'),
    ('branches', 'Branches', 'Select the parent subleg, the origin room on that parent and a different first branch room. Add Branch makes the change; skip this step if no branch is needed.'),
    ('rooms', 'Rooms', 'Drag rooms between the staging tray and schematic drop positions. Select a route row for the available order/index actions; check the status for editing limits.'),
    ('review', 'Review', 'Check the heat source, connections, room membership, origins and index/terminal markers. Then review return arrangement and downstream evidence in Hydronics. This step does not accept the design.'),
)

# title, programme action, beginner meaning, standard meaning, classical contract,
# frequent mistake. The same topic is used by focus, ? and each wizard step.
_TOPICS = {
    'start': (
        'Topology — Start',
        'Choose the heat-source room in Environment. In the arranger, use View leg and View subleg to inspect the network already present.',
        'Topology records what connects to what. The common main is the shared spine; legs organise sublegs, and rooms belong on sublegs.',
        'A leg groups principal sublegs. A branch subleg takes off from a parent subleg. Review any initial route generated from the room list against the intended installation.',
        'The stored tree is Leg → Principal → Branch, with further Branch children allowed. Identities and parent/origin links define connectivity; screen positions do not define length or pressure.',
        'Do not treat schematic spacing as a measured pipe run or a displayed route as accepted hydraulics.',
    ),
    'legs': (
        'Topology — Legs and principals',
        'Select Initial room. Create New Leg + Principal creates both together; Add Principal uses View leg. Blank labels receive automatic names.',
        'A leg is a grouping, not a room. Its principal sublegs carry ordered rooms. Use a branch for a take-off from a subleg.',
        'The creation controls require a first room. Choosing an already allocated room moves its membership from its previous route; review the creation message and highlighted destination.',
        'Every top-level subleg beneath a leg is principal by position in the tree. The existing candidate/transaction path checks the proposed topology before committing it; labels are not identities.',
        'Creating with an allocated room is a move, not a copy. Back/Next does not create anything.',
    ),
    'branches': (
        'Topology — Branches',
        'Choose Branch parent, Origin on parent and First branch room, optionally name it, then select Add Branch. No branch is required if the existing arrangement is sufficient.',
        'A branch leaves another subleg at a defined room position. A branch can itself have child branches.',
        'The parent may be a principal or an existing branch. The origin stays on the parent route; the first branch room must be different. An allocated first room is transferred.',
        'A nested subleg has a parent_subleg_id and an origin on that parent route. Ancestor paths are inherited up to the take-off; the child owns its own ordered route_room_ids.',
        'Do not put the same room on both parent and child routes, or use the origin as the first branch room.',
    ),
    'origin': (
        'Topology — Branch origin',
        'Choose a room on the selected parent in Origin on parent, then a different First branch room.',
        'The origin marks where the branch takes off. It remains a room on the parent.',
        'The origin is a connectivity reference, not an additional copy of that room or a measured take-off distance. Review it after changing the parent or room order.',
        'The origin identity must belong to the immediate parent route. Recursive ancestry establishes the shared upstream path; separate physical section data supplies lengths later.',
        'An origin reference must not be counted as a second room or heat demand.',
    ),
    'rooms': (
        'Topology — Room placement',
        'Drag a staged room into a schematic insertion position. Drag an assigned room to another position or subleg, or back to the staging tray. Inspect the move message.',
        'Staging contains rooms waiting to be placed. Moving a room changes where it belongs in the network.',
        'Placement uses stable room and subleg identities and the requested order. The existing transaction checks the candidate; an invalid move is blocked rather than silently repaired.',
        'Room membership is unique across assigned routes. A placement changes membership/order, not room heat-loss inputs. The transaction records step-back state and leaves downstream evidence awaiting rebuild where required.',
        'Unplaced rooms are not automatically included in a route. A rejected drop has not completed the move.',
    ),
    'order': (
        'Topology — Room order',
        'Select a row in the route table. Use Move Up or Move Down where enabled, or the schematic placement controls. Check the current subleg and status first.',
        'Order describes the sequence of rooms along that subleg, not their alphabetical order or storey number.',
        'The current order/index buttons are restricted to the adapter-supported legacy subleg. A disabled button does not prove the selected route is correct; other arrangements still need review.',
        'route_room_ids is an ordered identity sequence. Changing it may change branch-origin relationships and downstream evidence. The guide does not extend the existing editing authority.',
        'Do not assume that changing View subleg enables every legacy editing action.',
    ),
    'index': (
        'Topology — Index and terminal',
        'Select the intended room. Set As Index records index intent without moving it; Make Terminal uses the existing index action with a move to the terminal position. These actions are limited to the supported subleg.',
        'Terminal means the end of the route. The index marker records the room used as the design reference; an end room is not automatically a calculated index.',
        'Review both markers before proportioning. The established workflow requires the index room to be terminal. Selecting an index is explicit designer intent, not proof from this schematic of the greatest pressure loss.',
        'Index identity and terminal position are separate facts. The existing index controller synchronises its accepted intent; this help and the wizard do not choose an index or calculate route resistance.',
        'Make Terminal is an engineering action, not merely a display change. Next never performs it.',
    ),
    'review': (
        'Topology — Review and handoff',
        'Inspect the source, each leg/subleg, branch origins, room membership and index/terminal markers. Read any blocker or rebuild message. Continue in Hydronics for return arrangement and hydraulic evidence.',
        'A connected drawing is only the arrangement. Pipe sizes, lengths and losses still need their own inputs and review.',
        'Creation and placement transactions can invalidate downstream evidence. Rebuild/review that evidence through the existing workflow. Return arrangement is handled separately at the supported system/leg/subleg scope, not per room.',
        'Topology validity, hydraulic input readiness and committed engineering acceptance are distinct states. This guide neither evaluates their gates nor promotes a preview into accepted duty or pipework.',
        'Reaching Review is not design completion. This wizard has no Finish/Accept shortcut.',
    ),
}

TOPOLOGY_TOPICS_V1 = frozenset(_TOPICS)
TOPOLOGY_GUIDANCE_V1 = {}
for _topic, (_title, _action, _beginner, _standard, _classical, _mistake) in _TOPICS.items():
    TOPOLOGY_GUIDANCE_V1[_topic] = {}
    for _mode, _detail in (('beginner', _beginner), ('standard', _standard), ('classical', _classical)):
        TOPOLOGY_GUIDANCE_V1[_topic][_mode] = {
            'title': f'{_title} — {_mode.title()}',
            'body': f'{_action}\n\n{_detail}\n\nCheck: {_mistake}',
        }
