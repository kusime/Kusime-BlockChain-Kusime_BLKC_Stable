from time import sleep
from requests import post


def register_node(NODE_MANAGER, node_ip, node_port, node_rsa_pub):
    node_register_info = {
        "ip": node_ip,
        "port": node_port,
        "node_rsa_pub": node_rsa_pub
    }

    MAX_RETRIES = 5
    for retry in range(MAX_RETRIES):
        try:
            # register the node
            response = post(
                f'{NODE_MANAGER}/register-node', json=node_register_info)
            print(response.text)
            if response.status_code == 200:
                # registration successful, return True
                return True

        except:
            # catch exceptions raised by requests library
            print(
                f"NodeManager :{NODE_MANAGER} => Request failed {retry+1}/{MAX_RETRIES}")
            # retry the request after a short delay
            sleep(1)
    else:
        # if we exit the loop without a break, registration failed
        print("Failed to register the node with the Node Manager")
        return False


def notice_death(NODE_MANAGER, NODE_ID, NODE_PRIVATE_KEY, _sign_object):
    try:
        # prepare the death node
        death_payload = {
            "death_node_id": NODE_ID,
            "signature": _sign_object(NODE_PRIVATE_KEY, NODE_ID, False)
        }
        response = post(
            f'{NODE_MANAGER}/death', json=death_payload, timeout=2)
        print(response.text)
    except:
        # catch exceptions raised by requests library
        print("death ok")
