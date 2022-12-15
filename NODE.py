from flask import Flask, jsonify, request
# cors fix
from flask_cors import CORS
# for broadcast and register
import requests
# prepare the node running state
from utility.ip import *
# parse the request and response
import json
#!SECTION prepare the Blockchain
from Wallet import Wallet
from BlockChain import BlockChain
from utility.node_broadcast import node_broadcast
from utility.node_register import register_node
#!SECTION prepare the Blockchain

# NOTE: when running in k8s deployment mode , this port will be stabilized
NODE_MANAGER = "http://localhost:6000"
BROADCAST_MANAGER = "http://localhost:7000"
# NODE_PORT = 5000
NODE_PORT = generate_random_port()
NODE_HOST = get_local_ip_address()
NODE_ID = "{}:{}".format(NODE_HOST, NODE_PORT)
# NOTE: Registering node REST API here
app = Flask(__name__)
CORS(app)
# NOTE: Prepare the this node RSA key pair for node communication
NODE_PRIVATE_KEY, NODE_PUBLIC_KEY = Wallet.generate_wallet()
# NOTE: Prepare the BlockChain
BLOCK_CHAIN = BlockChain(NODE_ID)


@app.route('/alive', methods=["GET", "POST"])
def alive_check():
    # Rule: -
    #  1. BroadCast alive check (POST)
    #  2. Heartbeat alive check (GET)
    if request.method == 'GET':
        return "alive", 200
    post = request.get_json()
    print("Body=>", post)
    return jsonify(post), 200


@app.route('/get-chain', methods=["GET"])
def get_chain():  # REVIEW - PASSED
    # Rule -
    #   1. get the blockchain from this node
    chain_snapshot = BLOCK_CHAIN.chain
    jsonable_chain = [block.__dict__.copy() for block in chain_snapshot]
    for d_block in jsonable_chain:
        d_block["data"] = [tx.__dict__.copy()
                           for tx in d_block["data"]]
    # return jsonify the chain snapshot
    return jsonify(jsonable_chain), 200


@app.route('/create-wallet', methods=["GET"])
def create_wallet():  # REVIEW - PASSED
    # Rule: -
    # 1. create a new wallet to user create wallet to the wallet
    # 2. NOTE: the node will have no memory to remember the wallet address
    new_user_private_key, new_user_public_key = Wallet.generate_wallet()
    api_return = {
        "message": "create new wallet successfully",
        "private_key": new_user_private_key,
        "public_key": new_user_public_key,
    }
    return jsonify(api_return), 200


@app.route("/get-balance", methods=["POST"])
def get_balance():  # REVIEW - PASSED
    """
    #Rule - :
        {
            "wallet_address":"RSA key address"
        }

        #Rule:
            1. should provide a valid wallet public key address
            2. then return the balance
        #NOTE: 1. this function is tightly related the blockchain data structure,
            @related to the get_balance method in blockchain
    """
    try:
        query_address = request.get_json()["wallet_address"]
    except:
        api_return = {
            "message": "invalid  request payload",
        }
        return jsonify(api_return), 400

    if not Wallet.validate_wallet_keys(query_address):
        api_return = {
            "message": "invalid  wallet address ",
        }
        return jsonify(api_return), 400
    if len(query_address) > 1000:
        api_return = {
            "message": "You might use your private key to retrieved balance",
        }
        return jsonify(api_return), 400

    balance = BLOCK_CHAIN.get_balance(query_address)
    if balance == None:
        api_return = {
            "message": "get_balance failed"
        }
        return jsonify(api_return), 500

    api_return = {
        "message": "get_balance successfully",
        "balance": balance
    }
    return jsonify(api_return), 200


@app.route('/get-open_transactions', methods=['GET'])
def get_open_transactions():  # REVIEW - PASSED
    """
    #Rule - :
        #Rule:
            1. should provide current node open transactions
    """
    trans = BLOCK_CHAIN.open_transaction
    jsonable_trans = [tx.__dict__.copy()
                      for tx in trans]
    api_return = {
        "message": "get_open_transactions successfully",
        "open_transactions": jsonable_trans
    }
    return jsonify(api_return), 200


@app.route('/create-transaction', methods=['POST'])
def create_transaction():
    """
    #Rule - :
        {
            "sender_wallet":"RSA key address",
            "recipient_wallet":"RSA key address",
            "amount": 1.3,
            "sender_privatekey":"RSA key address",
        }

        #Rule:
            1. should provide a valid  wallet address
            2. validate self , when self.validate is passed
            3. after successful validate , and passed the transaction validate , this node should broadcast the transaction to other node
        #NOTE: 1. this function will only make a effect to the other node open_transactions record
            @related to the create_transaction ,but use api hit the broadcast_handler method in blockchain
    """
    try:
        transaction_payload = request.get_json()
        sender_wallet = transaction_payload["sender_wallet"]
        recipient_wallet = transaction_payload["recipient_wallet"]
        amount = transaction_payload["amount"]
        sender_privatekey = transaction_payload["sender_privatekey"]
        RSA_Payload = [sender_wallet, recipient_wallet, sender_privatekey]
    except:
        api_return = {
            "message": "invalid  request payload",
        }
        return jsonify(api_return), 400
    # Rule - generic wallet address checking (RSA_Payload validation)
    if not all([Wallet.validate_wallet_keys(wallet_address) for wallet_address in RSA_Payload]):
        api_return = {
            "message": "invalid  RSA_Payload )",
        }
        return jsonify(api_return), 400
    # Rule - public keys checking
        # 1. sender_wallet ,and recipient_wallet should be RSA public keys (less than 1000)
        # 2. sender_privatekey should be RSA private keys (longer than 1000)
    if not all([len(wallet_address) < 1000 for wallet_address in [sender_wallet, recipient_wallet]]):
        api_return = {
            "message": "invalid sender_wallet or recipient_wallet address ",
        }
        return jsonify(api_return), 400
    if not len(sender_privatekey) > 1000:
        api_return = {
            "message": "invalid sender_privatekey , you provide your public key as a private key",
        }
        return jsonify(api_return), 400

    # starting building the new transaction record,by calling the blockchain build-in api,which will performs all necessary check
    created_transaction = BLOCK_CHAIN.create_transaction(
        sender_wallet, recipient_wallet, amount, sender_privatekey)
    if created_transaction == False:
        api_return = {
            "message": "Transaction rejected ...",
        }
        return jsonify(api_return), 500

    api_return = {
        "message": "Transaction add successfully ...",
        "transaction": created_transaction.to_json()

    }
    #!SECTION BroadCast this transaction..
    node_broadcast(BROADCAST_MANAGER, NODE_ID, "transaction",
                   created_transaction.to_json())
    return jsonify(api_return), 200


@app.route('/create-block', methods=["POST"])
def mine():
    """
    #Rule - :
        {
            "miner_wallet":"RSA key address"
        }

        #Rule:
            1. should provide a valid wallet public key address
            2. then return the balance
        #NOTE: 1. this function is tightly related the blockchain data structure,
            @related to the get_balance method in blockchain
    """
    try:
        miner_wallet = request.get_json()["miner_wallet"]
    except:
        api_return = {
            "message": "invalid  request payload",
        }
        return jsonify(api_return), 400

    if not Wallet.validate_wallet_keys(miner_wallet):
        api_return = {
            "message": "invalid  miner_wallet address ",
        }
        return jsonify(api_return), 400
    if len(miner_wallet) > 1000:
        api_return = {
            "message": "You might use your private key to mine ",
        }
        return jsonify(api_return), 400

    mined_block = BLOCK_CHAIN.mine_new_block(miner_wallet)
    if mined_block == False:
        api_return = {
            "message": "Mine rejected ...",
        }
        return jsonify(api_return), 500
    api_return = {
        "message": "New  create successfully ...",
        "block": mined_block.to_json()
    }
    #!SECTION BroadCast this transaction..
    node_broadcast(BROADCAST_MANAGER, NODE_ID, "block",
                   mined_block.to_json())
    return jsonify(api_return), 200


@app.route("/broadcast-transaction", methods=["POST"])
def broadcast_transaction_handler():
    """
    #Rule - :
        {
            "sender":"RSA key address",
            "recipient":"RSA key address",
            "amount": 1.3,
            "signature":"sender_wallet's signature"
        }

        #Rule:
            1. all check will be delegated to add_transaction_from_broadcast
        #FIXME - 
            1. this will be failed when our block chain is outdated, which means we should have a logic to handle the data conflict
            2. this should also handle the RSA verification
    """
    try:
        transaction_payload = request.get_json()["payload"]
        #EFFECT: - Transaction record
        sender_wallet = transaction_payload["sender"]
        recipient_wallet = transaction_payload["recipient"]
        amount = float(transaction_payload["amount"])
        timestamp = float(transaction_payload["timestamp"])
        signature = transaction_payload["signature"]
    except:
        api_return = {
            "message": "invalid  request payload",
        }
        return jsonify(api_return), 400

    # REVIEW - check if already have this transaction in our open_transactions pool

    # Rule - balance checking
    # FIXME - our blockchain might be out of sync with other blockchain
    # EFFECT: - Transaction record
    broadcast_transaction_status = BLOCK_CHAIN.add_transaction_from_broadcast(
        sender_wallet, recipient_wallet, amount, timestamp, signature)

    if broadcast_transaction_status == False:
        api_return = {
            "message": "Broadcast Transaction rejected ... ( This also possible because of current node is out of sync with in-coming node )",
        }
        return jsonify(api_return), 500

    api_return = {
        "message": "Broadcast Transaction added successfully ...",
        "added_transactions": broadcast_transaction_status.to_json()
    }

    return jsonify(api_return), 200


@app.route("/broadcast-block", methods=["POST"])
def broadcast_block_handler():
    """
    #Rule - :
    {
        "data": [
            {
                "amount": 10.0,
                "recipient": "30819f300d06092a864886f70d010101050003818d0030818902818100a535ee8b2e63677271fee7cca8206fce04588677f21b86b5302a6e0526430540bcf0c7488d7e88a66a6dc8feb9226985089d641d8dd1e000b4f4175350b462138c3fef5bffc0840bda87130e544d56307712a8b30fdeb27f7ebe093e37fcd68007849df9f0b82454f75dfb958726708de32ac503183604d020cf8548d4b05cbf0203010001",
                "sender": "30819f300d06092a864886f70d010101050003818d0030818902818100c8501b7d73404a8f101cf011827d261662ee9b17195f0b297da79604114c48fa3f161cb13d8e039ceefdfb03cb559bcef332c6a3713d74d04b948e363019b1472265ef92efeb3ea6ee91ad585369fdf8e155582756e93ccf8bef9ef8062ed2535d52af1e6f11cd03e1a34e98436b278afab544c3cf28c0aa8e27af2ddd8b19030203010001",
                "signature": "0df22f492457d5444dc78236a0eaa34d34c938596ca8c23107f7626620d776e957b9831fd4a457a2f74e9023ff3dc8d4b2667ff0336a552099adaeaca41af313edcafd961ff3d56f243adb0c60e92f8076406d1250dbe53e09794254766c14142a46362900b773ee9fac2b820d6a1c26eed62ba14fcc82040a2240de0a850b07"
            }
        ],
        "index": 2,
        "previous_block_hash": "d5e6a130a61f8cd82591102dff7c08b4fb03f5bd45c7341338c9dd25f0b4503e",
        "proof": 103,
        "timestamp": 1671089939.4542882
    }

        #Rule:
            1. all check will be delegated to add_block_from_broadcast
        #FIXME - 
            1. this will be failed when our block chain already contains this block
            2. this should also handle the NODE RSA verification
    """
    try:
        block_payload = request.get_json()["payload"]
        data_json = list(block_payload["data"])
        index = int(block_payload["index"])
        previous_block_hash = block_payload["previous_block_hash"]
        proof = int(block_payload["proof"])
        timestamp = float(block_payload["timestamp"])
    except:
        api_return = {
            "message": "invalid  request payload",
        }
        return jsonify(api_return), 400

    # Rule - balance checking
    # FIXME - our blockchain might be out of sync with other blockchain
    broadcast_block_status = BLOCK_CHAIN.add_block_from_broadcast(
        previous_block_hash, index, data_json, proof, timestamp)

    if broadcast_block_status == False:
        api_return = {
            "message": "Broadcast Block rejected ... ( This also possible because of that is block is already added)",
        }
        return jsonify(api_return), 500

    api_return = {
        "message": "Broadcast Block added successfully ...",
        "added_block": broadcast_block_status.to_json()
    }
    #!SECTION BroadCast this transaction..
    return jsonify(api_return), 200


if __name__ == '__main__':
    if not register_node(NODE_MANAGER, NODE_HOST, NODE_PORT, NODE_PUBLIC_KEY):  # REVIEW - PASSED
        print("Now shutdown this node ...")
        exit(1)
    print("Registering node successfully , now starting the node...")
    app.run(NODE_HOST, NODE_PORT)
    # Rule: - notice death
    pass
