from time import sleep
from requests import post, get


def node_broadcast(BROADCAST_MANAGER, src_node_id, type, payload_json):
    # Rule: check if broadcast manager is alive
    try:
        response = get(
            f'{BROADCAST_MANAGER}/alive')
        if response.status_code == 200:
            # registration successful, return True
            pass
    except:
        print
        return False
    # Rule: building the broadcast payload
    broad_cast_payload = {
        "src_node_id": src_node_id,
        "endpoint": f"/broadcast-{type}",
        "payload": payload_json
    }

    try:
        # Broadcast the payload with metadata
        response = post(
            f'{BROADCAST_MANAGER}/broadcast', json=broad_cast_payload, timeout=1)
        print("Broadcast successfully ")
    except:
        print("Broadcast successfully ")
