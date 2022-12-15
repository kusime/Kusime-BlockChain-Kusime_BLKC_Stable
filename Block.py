from hashlib import sha256
from time import time
from Ku_Crypto.helper.Ku_Super_OBJ import SuperOBJ
from Transaction import Transaction
import json
# NOTE: Initialize the sha256 algorithm to serialize the blockchain: (the calculation of the previous_block_hash)
from hashlib import sha256


class Block(SuperOBJ):
    """
        Rule:
            {
                "previous_block_hash":"ec8s7s6ag28dux9cuf"
                "index": 5
                "data": [transaction_SuperOBJ]
                "proof": 49581
                "timestamp":16998484.39928
            }

        NOTE: Aiming:
            1. genesis_block (initialize of a blockchain)
            2. loading block chain (provide new timestamp)
            3. mining new block  (just use current timestamp)
    """

    def __init__(self, previous_block_hash: str, index: int, data: list, proof: int, timestamp=None):
        self.previous_block_hash = previous_block_hash
        self.index = index
        self.data = data
        self.proof = proof
        # NOTE: if timestamp is None ,which means the block is newly created
        if timestamp != None:
            self.timestamp = timestamp
        else:
            self.timestamp = time()

    @staticmethod
    def get_block_hash(block) -> str:
        """
            Rule:
                get this block's hash, by provide the block object instance , then return the hash of this block
            NOTE: Aiming:
                1. previous_block_hash check mechanism of the blockchain first security layer
                2. validate_proof also needs this function
                3. anyway , this is a import function for validate 
        """
        serializable_block = block.__dict__.copy()
        # the tx is Transaction instance , by calling the to_order method to transforming to the ordered form
        serializable_block["data"] = [tx.to_order()
                                      for tx in serializable_block["data"]]
        return (sha256(json.dumps(serializable_block, sort_keys=True).encode("utf-8"))).hexdigest()

    def to_json(self):
        serializable_block = self.__dict__.copy()
        # the tx is Transaction instance , by calling the to_order method to transforming to the ordered form
        serializable_block["data"] = [tx.__dict__.copy()
                                      for tx in serializable_block["data"]]
        return serializable_block


if __name__ == "__main__":
    tx = Transaction("Alice", "Bob", "100", "abc123")
    blck = Block("hash", 1, [tx, tx, tx], 4425)
    print(blck)
