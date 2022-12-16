from time import sleep
from requests import get


def get_all_other_active_node(NODE_MANAGER, NODE_ID) -> list:
    # Rule: get all available nodes from node manager,and except nodes for all other nodes
    endpoint = f"{NODE_MANAGER}/get-nodes"
    response = get(endpoint)
    if response.status_code == 200:
        nodes = response.json()["nodes"]
        # Rule - remove self node v3 fixed : since we only register after everything is done , so currently , node manager does not have our node information
        # nodes.remove(NODE_ID)
        return nodes
    else:
        raise Exception("Error getting nodes from node manager")


def get_other_nodes_info(OTHER_ACTIVE_NODES, type):
    chain_snapshots = []
    for node in OTHER_ACTIVE_NODES:
        endpoint = f"http://{node}/get-{type}"
        response = get(endpoint)
        if response.status_code == 200:
            chain_snapshots.append(response.json())
    return chain_snapshots


if __name__ == "__main__":
    NODE_MANAGER = "http://192.168.59.100:32576"
    print(type(get_all_other_active_node(NODE_MANAGER, '172.17.0.31:6000')))
    print(get_all_other_active_node(NODE_MANAGER, '172.17.0.31:6000'))
    active_nodes = ["192.168.59.100:30471",
                    "192.168.59.100:30471", "192.168.59.100:30471"]
    other_nodes_chain = get_other_nodes_info(active_nodes, "chain")
    for chain in other_nodes_chain:
        print(chain)
        print(type(chain))
        print(type(chain[0]))
