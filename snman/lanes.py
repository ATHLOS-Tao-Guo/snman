import math
import networkx as nx
from .constants import *


def generate_lanes(street_graph):
    """
    Reverse-engineer the lanes of each street edge and store them as a list in the attribute 'ln_desc'
    Naming convention:
    c = cycling,
    m = motorized traffic,
    > = forward,
    < = backward,
    - = both directions

    Parameters
    ----------
    street_graph : nx.MultiGraph
        contains the street network

    Returns
    -------
    None
    """
    for edge in street_graph.edges(data=True, keys=True):
        edge_data = edge[3]
        edge_data['ln_desc'] = _generate_lanes_for_edge(edge_data)


def _generate_lanes_for_edge(edge):
    """
    Reverse-engineer the lanes for one edge

    Parameters
    ----------
    edge : dict
        only edge data

    Returns
    -------
    lane_list : list
        a list of lanes, following the convention described under generate_lanes
    """

    # left/right lanes: cycling lanes that are not included in the osm lanes tag
    left_lanes_list = []
    forward_lanes_list = []
    both_dir_lanes_list = []
    backward_lanes_list = []
    right_lanes_list = []

    # Reverse forward/backward if the edge has been reversed in the conversion into undirected graph
    if edge.get(KEY_REVERSED, False) == True:
        _DIRECTION_FORWARD = DIRECTION_BACKWARD
        _DIRECTION_BACKWARD = DIRECTION_FORWARD
    else:
        _DIRECTION_FORWARD = DIRECTION_FORWARD
        _DIRECTION_BACKWARD = DIRECTION_BACKWARD

    # if no lanes are defined assume one
    n_lanes = int(edge.get('lanes', 1))
    n_lanes_forward = int(edge.get('lanes:forward', 0))
    n_lanes_backward = int(edge.get('lanes:backward', 0))
    n_lanes_both = 0

    n_lanes_motorized = 0
    n_lanes_motorized_forward = 0
    n_lanes_motorized_backward = 0
    n_lanes_motorized_both = 0

    n_lanes_dedicated_pt = 0
    n_lanes_dedicated_pt_forward = 0
    n_lanes_dedicated_pt_backward = 0
    n_lanes_dedicated_pt_both = 0

    # if forward/backward lanes are defined
    if n_lanes_forward + n_lanes_backward == n_lanes:
        pass
    # if more than 1 lane exists but no explicit lane counts forward/backward are defined
    elif n_lanes>1 and edge.get('oneway', False) == False:
        n_lanes_forward = math.floor(n_lanes / 2)
        n_lanes_backward = math.ceil(n_lanes / 2)

    # if exactly one lane exists without oneway tag
    if n_lanes == 1 and edge.get('oneway', False) == False:
        n_lanes_both = 1

    # n lanes with oneway tag
    if n_lanes>0 and edge.get('oneway'):
        n_lanes_forward = n_lanes

    # If the edge is dedicated for public transport
    if (edge.get('highway') == 'service' or edge.get('access') == 'no') and (edge.get('psv') == 'yes' or edge.get('bus') == 'yes'):
        n_lanes_dedicated_pt = max([n_lanes,2])
        n_lanes_dedicated_pt_forward = max([n_lanes_forward,1])
        n_lanes_dedicated_pt_backward = max([n_lanes_backward,1])
        n_lanes_dedicated_pt_both = 0
    else:
        n_lanes_motorized = n_lanes
        n_lanes_motorized_forward = n_lanes_forward
        n_lanes_motorized_backward = n_lanes_backward
        n_lanes_motorized_both = n_lanes_both

    # If the entire edge is only for cycling (+walking)
    if edge.get('highway') in ['footway', 'path', 'track', 'cycleway', 'pedestrian']:
        if edge.get('bicycle') in ['yes', 'designated'] or edge.get('highway') == 'cycleway':
            if edge.get('oneway'):
                forward_lanes_list.extend([LANETYPE_CYCLING_TRACK + _DIRECTION_FORWARD])
            else:
                backward_lanes_list.extend([LANETYPE_CYCLING_TRACK + DIRECTION_BOTH])
        else:
            both_dir_lanes_list.extend([LANETYPE_FOOT + DIRECTION_BOTH])

    # Everything else
    else:
        # Add cycling lane left
        if edge.get('cycleway:left') == 'lane'\
                or edge.get('cycleway:both') == 'lane'\
                or edge.get('cycleway') == 'lane':
            left_lanes_list.extend([LANETYPE_CYCLING_LANE + _DIRECTION_BACKWARD])

        # Add cycling lane right
        if edge.get('cycleway:right') == 'lane'\
                or edge.get('cycleway:both') == 'lane'\
                or edge.get('cycleway') == 'lane':
            right_lanes_list.extend([LANETYPE_CYCLING_LANE + _DIRECTION_FORWARD])

        backward_lanes_list.extend([LANETYPE_MOTORIZED + _DIRECTION_BACKWARD] * n_lanes_motorized_backward)
        backward_lanes_list.extend([LANETYPE_DEDICATED_PT + _DIRECTION_BACKWARD] * n_lanes_dedicated_pt_backward)

        both_dir_lanes_list.extend([LANETYPE_DEDICATED_PT + DIRECTION_BOTH] * n_lanes_dedicated_pt_both)
        both_dir_lanes_list.extend([LANETYPE_MOTORIZED + DIRECTION_BOTH] * n_lanes_motorized_both)

        forward_lanes_list.extend([LANETYPE_DEDICATED_PT + _DIRECTION_FORWARD] * n_lanes_dedicated_pt_forward)
        forward_lanes_list.extend([LANETYPE_MOTORIZED + _DIRECTION_FORWARD] * n_lanes_motorized_forward)

    osm_bus_lanes_forward = edge.get('bus:lanes:forward', '').split('|')
    osm_bus_lanes_backward = edge.get('bus:lanes:backward', '').split('|')
    osm_bus_lanes_backward.reverse()

    for i, lane in enumerate(osm_bus_lanes_forward):
        if lane == 'designated' and i < len(forward_lanes_list):
            forward_lanes_list[i] = LANETYPE_DEDICATED_PT + _DIRECTION_FORWARD

    for i, lane in enumerate(osm_bus_lanes_backward):
        if lane == 'designated' and i < len(backward_lanes_list):
            backward_lanes_list[i] = LANETYPE_DEDICATED_PT + _DIRECTION_BACKWARD

    osm_vehicle_lanes_forward = edge.get('vehicle:lanes:forward', '').split('|')
    osm_vehicle_lanes_backward = edge.get('vehicle:lanes:backward', '').split('|')
    osm_vehicle_lanes_backward.reverse()

    for i, lane in enumerate(osm_vehicle_lanes_forward):
        if lane == 'no' and i < len(forward_lanes_list):
            forward_lanes_list[i] = LANETYPE_DEDICATED_PT + _DIRECTION_FORWARD

    for i, lane in enumerate(osm_vehicle_lanes_backward):
        if lane == 'no' and i < len(backward_lanes_list):
            backward_lanes_list[i] = LANETYPE_DEDICATED_PT + _DIRECTION_BACKWARD

    return left_lanes_list + backward_lanes_list + both_dir_lanes_list + forward_lanes_list + right_lanes_list


def _reverse_lanes(lanes):
    """
    Reverse the order and direction of all lanes

    Parameters
    ----------
    lanes : list
        a list of lanes, following the convention described under generate_lanes

    Returns
    -------
    reversed_lanes : list
        lanes, with reversed order and directions
    """
    reversed_lanes = lanes
    # We use >> and << as temporary symbols during the process
    reversed_lanes = [lane.replace(DIRECTION_FORWARD, '>>') for lane in reversed_lanes]
    reversed_lanes = [lane.replace(DIRECTION_BACKWARD, '<<') for lane in reversed_lanes]
    reversed_lanes = [lane.replace('>>', DIRECTION_BACKWARD) for lane in reversed_lanes]
    reversed_lanes = [lane.replace('<<', DIRECTION_FORWARD) for lane in reversed_lanes]
    reversed_lanes.reverse()
    return reversed_lanes


def generate_lane_stats(street_graph):
    """
    Add lane statistics to all edges for the street graph

    Params
    ------
    street_graph : nx.MultiGraph

    Returns
    -------
    None
    """
    for edge in street_graph.edges(data=True, keys=True):
        edge_data = edge[3]
        _generate_lane_stats_for_edge(edge_data)


def _generate_lane_stats_for_edge(edge):
    lanes = edge.get(KEY_LANES_DESCRIPTION, [])

    width_cycling = 0
    width_motorized = 0
    width_total = 0

    for lane in lanes:
        lane_properties = _lane_properties(lane)
        if lane_properties.lanetype == LANETYPE_MOTORIZED:
            width_motorized += lane_properties.width
        if lane_properties.lanetype == LANETYPE_CYCLING_LANE:
            width_cycling += lane_properties.width
        width_total += lane_properties.width

    try:
        proportion_cycling = width_cycling / width_total
    except ZeroDivisionError:
        proportion_cycling = None

    edge['w_cyc_m'] = width_cycling
    edge['w_mot_m'] = width_motorized
    edge['w_tot_m'] = width_total
    edge['prop_cyc'] = proportion_cycling

class _lane_properties:

    width = None
    lanetype = None
    direction = None
    motorized = None
    private_cars = None
    dedicated_pt = None
    dedicated_cycling = None
    dedicated_cycling_lane = None
    dedicated_cycling_track = None

    def __init__(self, lane_description):

        self.width = DEFAULT_LANE_WIDTHS.get(lane_description, 0)
        self.lanetype = lane_description[0:-1]
        self.direction = lane_description[-1]
        self.motorized = lane_description[0:-1] in [LANETYPE_MOTORIZED, LANETYPE_DEDICATED_PT]
        self.private_cars = lane_description[0:-1] == LANETYPE_MOTORIZED
        self.dedicated_pt = lane_description[0:-1] == LANETYPE_DEDICATED_PT
        self.dedicated_cycling = lane_description[0:-1] in [LANETYPE_CYCLING_TRACK, LANETYPE_CYCLING_LANE]
        self.dedicated_cycling_lane = lane_description[0:-1] == LANETYPE_CYCLING_LANE
        self.dedicated_cycling_track = lane_description[0:-1] == LANETYPE_CYCLING_TRACK

class _lane_stats:

    n_lanes_motorized_forward = 0
    n_lanes_motorized_backward = 0
    n_lanes_motorized_both_ways = 0
    n_lanes_motorized_direction_tbd = 0

    n_lanes_private_cars_forward = 0
    n_lanes_private_cars_backward = 0
    n_lanes_private_cars_both_ways = 0
    n_lanes_private_cars_direction_tbd = 0

    n_lanes_dedicated_pt_forward = 0
    n_lanes_dedicated_pt_backward = 0
    n_lanes_dedicated_pt_both_ways = 0
    n_lanes_dedicated_pt_direction_tbd = 0

    n_lanes_dedicated_cycling_lanes_forward = 0
    n_lanes_dedicated_cycling_lanes_backward = 0
    n_lanes_dedicated_cycling_lanes_both_ways = 0
    n_lanes_dedicated_cycling_lanes_direction_tbd = 0

    n_lanes_dedicated_cycling_tracks_forward = 0
    n_lanes_dedicated_cycling_tracks_backward = 0
    n_lanes_dedicated_cycling_tracks_both_ways = 0
    n_lanes_dedicated_cycling_tracks_direction_tbd = 0

    def __init__(self,lanes_description):
        for lane in lanes_description:
            lane_properties = _lane_properties(lane)
            direction = lane_properties.direction

            # Motorized Lanes
            if lane_properties.motorized:
                if direction == DIRECTION_FORWARD:
                    self.n_lanes_motorized_forward += 1
                elif direction == DIRECTION_BACKWARD:
                    self.n_lanes_motorized_backward += 1
                elif direction == DIRECTION_BOTH:
                    self.n_lanes_motorized_both_ways += 1
                elif direction == DIRECTION_TBD:
                    self.n_lanes_motorized_direction_tbd += 1

            # Private cars
            if lane_properties.private_cars:
                if direction == DIRECTION_FORWARD:
                    self.n_lanes_private_cars_forward += 1
                elif direction == DIRECTION_BACKWARD:
                    self.n_lanes_private_cars_backward += 1
                elif direction == DIRECTION_BOTH:
                    self.n_lanes_private_cars_both_ways += 1
                elif direction == DIRECTION_TBD:
                    self.n_lanes_private_cars_direction_tbd += 1

            # PT lanes
            if lane_properties.dedicated_pt:
                if direction == DIRECTION_FORWARD:
                    self.n_lanes_dedicated_pt_forward += 1
                if direction == DIRECTION_BACKWARD:
                    self.n_lanes_dedicated_pt_backward += 1
                if direction == DIRECTION_BOTH:
                    self.n_lanes_dedicated_pt_both_ways += 1
                if direction == DIRECTION_TBD:
                    self.n_lanes_dedicated_pt_direction_tbd += 1

            # Cycling lanes
            if lane_properties.dedicated_cycling_lane:
                if direction == DIRECTION_FORWARD:
                    self.n_lanes_dedicated_cycling_lanes_forward += 1
                elif direction == DIRECTION_BACKWARD:
                    self.n_lanes_dedicated_cycling_lanes_backward += 1
                elif direction == DIRECTION_BOTH:
                    self.n_lanes_dedicated_cycling_lanes_both_ways += 1
                elif direction == DIRECTION_TBD:
                    self.n_lanes_dedicated_cycling_lanes_direction_tbd += 1

            # Cycling paths
            if lane_properties.dedicated_cycling_track:
                if direction == DIRECTION_FORWARD:
                    self.n_lanes_dedicated_cycling_tracks_forward += 1
                elif direction == DIRECTION_BACKWARD:
                    self.n_lanes_dedicated_cycling_tracks_backward += 1
                elif direction == DIRECTION_BOTH:
                    self.n_lanes_dedicated_cycling_tracks_both_ways += 1
                elif direction == DIRECTION_TBD:
                    self.n_lanes_dedicated_cycling_tracks_direction_tbd += 1


        self.n_lanes_motorized = \
            self.n_lanes_motorized_forward + self.n_lanes_motorized_backward\
            + self.n_lanes_motorized_both_ways + self.n_lanes_motorized_direction_tbd


def update_osm_tags(street_graph, lanes_description_key=KEY_LANES_DESCRIPTION):
    for edge in street_graph.edges(data=True, keys=True):
        _update_osm_tags_for_edge(edge, lanes_description_key)

def _update_osm_tags_for_edge(edge, lanes_description_key):

    data = edge[3]
    lane_stats = _lane_stats(data.get(lanes_description_key, []))

    # Clean the tags before updating
    data['lanes'] = None
    data['lanes:forward'] = None
    data['lanes:backward'] = None
    data['lanes:both_ways'] = None

    # Motorized lanes
    if lane_stats.n_lanes_motorized:
        data['lanes'] = lane_stats.n_lanes_motorized
    if lane_stats.n_lanes_motorized_forward:
        data['lanes:forward'] = lane_stats.n_lanes_motorized_forward
    if lane_stats.n_lanes_motorized_backward:
        data['lanes:backward'] = lane_stats.n_lanes_motorized_backward
    if lane_stats.n_lanes_motorized_both_ways > 0:
        data['lanes:both_ways'] = lane_stats.n_lanes_motorized_both_ways

    # Clean the tags before updating
    data['bus:lanes:backward'] = None
    data['bus:lanes:forward'] = None
    data['vehicle:lanes:backward'] = None
    data['vehicle:lanes:forward'] = None

    # PT lanes
    if lane_stats.n_lanes_dedicated_pt_both_ways > 0 or lane_stats.n_lanes_dedicated_pt_backward > 0:
        data['bus:lanes:backward'] = '|'.join(
            ['designated'] * lane_stats.n_lanes_dedicated_pt_both_ways +
            ['designated'] * lane_stats.n_lanes_dedicated_pt_backward +
            ['permissive'] * lane_stats.n_lanes_private_cars_both_ways +
            ['permissive'] * lane_stats.n_lanes_private_cars_backward
        )
        data['vehicle:lanes:backward'] = '|'.join(
            ['no'] * lane_stats.n_lanes_dedicated_pt_both_ways +
            ['no'] * lane_stats.n_lanes_dedicated_pt_backward +
            ['yes'] * lane_stats.n_lanes_private_cars_both_ways +
            ['yes'] * lane_stats.n_lanes_private_cars_backward
        )

    if lane_stats.n_lanes_dedicated_pt_both_ways > 0 or lane_stats.n_lanes_dedicated_pt_forward > 0:
        data['bus:lanes:forward'] = '|'.join(
            ['designated'] * lane_stats.n_lanes_dedicated_pt_both_ways +
            ['designated'] * lane_stats.n_lanes_dedicated_pt_forward +
            ['permissive'] * lane_stats.n_lanes_private_cars_both_ways +
            ['permissive'] * lane_stats.n_lanes_private_cars_forward
        )
        data['vehicle:lanes:forward'] = '|'.join(
            ['no'] * lane_stats.n_lanes_dedicated_pt_both_ways +
            ['no'] * lane_stats.n_lanes_dedicated_pt_forward +
            ['yes'] * lane_stats.n_lanes_private_cars_both_ways +
            ['yes'] * lane_stats.n_lanes_private_cars_forward
        )

    # Clean the tags before updating
    data['cycleway'] = None
    data['cycleway:lane'] = None
    data['cycleway:right'] = None
    data['cycleway:right:lane'] = None
    data['cycleway:left'] = None
    data['cycleway:left:lane'] = None

    # Cycling lanes
    if lane_stats.n_lanes_dedicated_cycling_lanes_both_ways > 0 \
        or (lane_stats.n_lanes_dedicated_cycling_lanes_forward > 0 and lane_stats.n_lanes_dedicated_cycling_lanes_backward > 0):
        # both directions
        data['cycleway'] = 'lane'
        data['cycleway:lane'] = 'advisory'
    elif lane_stats.n_lanes_dedicated_cycling_lanes_forward > 0:
        # only forward
        data['cycleway:right'] = 'lane'
        data['cycleway:right:lane'] = 'advisory'
    elif lane_stats.n_lanes_dedicated_cycling_lanes_backward > 0:
        # only backward
        data['cycleway:left'] = 'lane'
        data['cycleway:left:lane'] = 'advisory'

    # Cycling tracks
    if lane_stats.n_lanes_dedicated_cycling_tracks_both_ways > 0 \
        or (lane_stats.n_lanes_dedicated_cycling_tracks_forward > 0 and lane_stats.n_lanes_dedicated_cycling_tracks_backward > 0):
        # both directions
        data['cycleway'] = 'track'
    elif lane_stats.n_lanes_dedicated_cycling_tracks_forward > 0:
        # only forward
        data['cycleway:right'] = 'track'
    elif lane_stats.n_lanes_dedicated_cycling_tracks_backward > 0:
        # only backward
        data['cycleway:left'] = 'track'


def _order_lanes(lanes):

    pass