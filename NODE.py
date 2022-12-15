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
from Transaction import Transaction
from Wallet import Wallet
from Block import Block
from BlockChain import BlockChain
from utility.node_register import register_node
#!SECTION prepare the Blockchain

# NOTE: when running in k8s deployment mode , this port will be stabilized
NODE_MANAGER = "http://localhost:6000"
NODE_PORT = 5000
# NODE_PORT = generate_random_port()
NODE_HOST = get_local_ip_address()
# NOTE: Registering node REST API here
app = Flask(__name__)
CORS(app)
# NOTE: Prepare the this node RSA key pair for node communication
NODE_PRIVATE_KEY, NODE_PUBLIC_KEY = Wallet.generate_wallet()
# NOTE: Prepare the BlockChain
BLOCK_CHAIN = BlockChain()


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
    add_status = BLOCK_CHAIN.create_transaction(
        sender_wallet, recipient_wallet, amount, sender_privatekey)
    if add_status != True:
        api_return = {
            "message": "Transaction rejected ...",
        }
        return jsonify(api_return), 500

    api_return = {
        "message": "Transaction add successfully ...",
    }
    #!SECTION BroadCast this transaction..
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
    return jsonify(api_return), 200


if __name__ == '__main__':
    if not register_node(NODE_MANAGER, NODE_HOST, NODE_PORT, NODE_PUBLIC_KEY):  # REVIEW - PASSED
        print("Now shutdown this node ...")
        exit(1)
    print("Registering node successfully , now starting the node...")
    app.run(NODE_HOST, NODE_PORT)
    # Rule: - notice death
    pass
