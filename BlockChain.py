# NOTE: Initialize the Base class for building this blockchain
import functools
from hashlib import sha256
import json
from time import time
from Wallet import Wallet
from Block import Block
from Transaction import Transaction
# NOTE: Initialize the Blockchain Rule
from Ku_Rule import *
# NOTE: Database configuration
from DataBase import *
# GENESIS_BLOCK, this block must have the same number of all field so that the hash check will work
GENESIS_BLOCK = Block("GENESIS_BLOCK", 0, [], 0, 0)


class BlockChain():
    def __init__(self, NODE_ID: str) -> None:
        self.__is_initialized = True
        # NOTE: setting the initialize BlockChain state
        self.chain = [GENESIS_BLOCK]
        self.open_transaction = []
        # NOTE: locking the chain after initialize
        self.__is_initialized = False
        # NOTE - Try Loading the chain
        self.NODE_ID = NODE_ID
        # NOTE: in k8s , there is no need to separate the database base on the node_id
        # self.DB_CHAIN = f'{DATABASE_BLOCKCHAIN}|{self.NODE_ID}'
        # self.DB_TRAN = f'{DATABASE_OPEN_TRANSACTION}|{self.NODE_ID}'
        self.DB_CHAIN = f'{DATABASE_BLOCKCHAIN}'
        self.DB_TRAN = f'{DATABASE_OPEN_TRANSACTION}'

        # EFFECT - No longer loading the blockchain during class initialize , since the source might be different
        # self.load_blockchain()
    # SECTION - Protection of the BlockChain prevent modifications from node directly accessing

    @property
    def chain(self):
        # NOTE: This getter here will get the copy of the block chain
        # but inside the transaction we need to manipulate the actual chain
        # so, we cant change __chain to chain
        return self.__chain[:]

    @chain.setter
    def chain(self, value):
        if self.__is_initialized == True:
            # allow the initializer to set GENESIS_BLOCK
            self.__chain = value
        pass

    @property
    def open_transaction(self):
        # NOTE: This getter here will get the copy of the block chain
        # but inside the transaction we need to manipulate the actual chain
        # so, we cant change __chain to chain
        return self.__open_transactions[:]

    @open_transaction.setter
    def open_transaction(self, value):
        if self.__is_initialized == True:
            # allow the initializer to set GENESIS_BLOCK
            self.__open_transactions = value
        pass

    # SECTION - Database Saver section

    def save_blockchain(self):
        """
            Rule: 
                dumps the blockchain to disk
        """
        try:
            with open(self.DB_CHAIN, "w") as blkc:
                # object to json
                saveable_chain = [block.__dict__.copy()
                                  for block in self.__chain]
                for d_block in saveable_chain:
                    d_block["data"] = [tx.__dict__.copy()
                                       for tx in d_block["data"]]
                blkc.write(json.dumps(saveable_chain))
        except:
            print("Error: Failed to save blockchain")

    def save_open_transaction(self):
        """
            Rule: 
                dumps the blockchain to disk
        """
        try:
            with open(self.DB_TRAN, "w") as blkc:
                # object to json
                saveable_open_transactions = [
                    tx.__dict__ for tx in self.__open_transactions]
                blkc.write(json.dumps(saveable_open_transactions))
        except:
            print("Error: Failed to save open_transaction")
    # SECTION - Database Loader section

    def json_to_CHAIN(self, chain_json):
        """
            Chain: Provide json to load,will performs the validation , but will ignore where the json is coming from.
        """
        try:
            # EFFECT: - Transaction record
            # Rule: - Preprocessing the Database Record
            self.__chain = [Block(block['previous_block_hash'],
                                  block["index"], [Transaction(
                                      tx["sender"], tx["recipient"], tx["amount"], tx["timestamp"],
                                      tx["signature"]) for tx in block['data']], block["proof"], block["timestamp"]) for block in chain_json]
            # NOTE: validate the chain
            # print(self.__chain)
            if not self.validate_chain():
                raise Exception("Invalid Chain")
            print("Parsing chain json successfully")
            return True
        except:
            print("Error loading chain")
            return False

    def json_to_TRANSACTION(self, transaction_json):
        """
            Transaction: Provide json to load,will performs the validation , but will ignore where the json is coming from.
        """
        try:
            # EFFECT: - Transaction record
            self.__open_transactions = [Transaction(
                tx["sender"], tx["recipient"], tx["amount"], tx["timestamp"],
                tx["signature"]) for tx in transaction_json]
            # NOTE: validate the transaction using the self validate
            if not all([tx.validate_self() for tx in self.__open_transactions]):
                raise Exception("Invalid Open_Transaction Record")
            print("Parsing open transaction json successfully")
            return True
        except:
            print("Loading Open_Transaction error ")
            return False

    # SECTION - Getter helper methods

    def get_the_last_block(self):
        if len(self.__chain) == 0:
            return None
        return self.__chain[-1]
    # SECTION - open_transaction operation logic

    def get_balance(self, wallet_address: str):
        # Rule: check if sender_wallet is a valid RSA address
        if not Wallet.validate_wallet_keys(wallet_address):
            print("Invalid wallet address: {}".format(wallet_address))
            return None
        #####!SECTION sender wallet output #################################
        # Rule - get all amount which are send from this account #NOTE - from the blockchain
        tx_out = [[tx.amount for tx in block.data
                   if tx.sender == wallet_address] for block in self.__chain]
        # Rule - get all amount which are send from this account #NOTE - from the open_transaction
        tx_out_open_transaction = [[tx.amount]
                                   for tx in self.__open_transactions if tx.sender == wallet_address]
        # [[],[2],[]] + [[],[1],[]]  => [ [],[2],[],[],[1],[]]
        tx_out += tx_out_open_transaction
        #####!SECTION sender wallet output #################################
        tx_out_amount = functools.reduce(
            lambda sum, curr: sum + curr[0] if curr != [] else sum, tx_out, 0)
        #####!SECTION sender wallet input #################################
        # Rule - get all amount which are send from this account #NOTE - from the blockchain
        tx_in = [[tx.amount for tx in block.data
                  if tx.recipient == wallet_address] for block in self.__chain]
        # Rule - get all amount which are send from this account #NOTE - from the open_transaction
        tx_in_open_transaction = [[tx.amount]
                                  for tx in self.__open_transactions if tx.recipient == wallet_address]
        # [[],[2],[]] + [[],[1],[]]  => [ [],[2],[],[],[1],[]]
        tx_in += tx_in_open_transaction
        # print(tx_in)
        #####!SECTION sender wallet input #################################
        tx_in_amount = functools.reduce(
            lambda sum, curr: sum + curr[0] if curr != [] else sum, tx_in, 0)
        return tx_in_amount - tx_out_amount

    # EFFECT: - Transaction record
    def add_transaction_from_broadcast(self, sender_wallet: str, recipient_wallet: str, amount: float, timestamp: float, signature: str):
        # Rule:
        #      if signature != None means that the transaction likely from broadcast, so we need to performs the signature
        amount = float(amount)
        # Rule - amount should not be negative
        if amount <= 0:
            print("Invalid amount number")
            return False
        # EFFECT: - Transaction record
        broadcast_transaction = Transaction(
            sender_wallet, recipient_wallet, amount, timestamp, signature)

        if not broadcast_transaction.validate_self():
            print("Transaction's signature verification failed")
            return False
        print("BroadCast Transaction signature verified,now checking the balance")

        # we need to performs the transactions amount check
        sender_balance = self.get_balance(sender_wallet)
        if amount > sender_balance:
            print(
                "BroadCast Transaction add failed , since sender does not have enough balance in current blockchain")
            # FIXME - Maybe current blockchain is out date..
            #!SECTION 1. performs the conflict resource
            return False
        # Rule : check if this broadcast transaction is already in our pool
        #EFFECT: - Transaction.__eq__
        if any([tx == broadcast_transaction for tx in self.open_transaction]):
            print(
                "BroadCast Transaction add failed ,this transaction is already in our pool")
            # FIXME - Maybe current blockchain is out date..
            #!SECTION 1. performs the conflict resource
            return False

        print("Add BroadCast  Transaction successfully")
        # NOTE - save the transaction record from the broadcast
        self.__open_transactions.append(broadcast_transaction)
        self.save_open_transaction()
        return broadcast_transaction

    def create_transaction(self, sender_wallet: str, recipient_wallet: str, amount: float, sender_privatekey: str):
        """
            #Rule: -
                sender_wallet : sender wallet address , RSA public key 
                recipient_wallet: recipient wallet address , RSA public key
                amount : amount to send
                # NOTE: provide the sender_privatekey to signature this transaction record
        """
        amount = float(amount)
        # Rule: check out that the transaction is from broadcast or newly create
        #     1. if signature == None means that the transaction is newly create , so we need to user provide

        # Rule - amount should not be negative
        if amount <= 0:
            print("Invalid amount number")
            return False

        # building the transaction
        transaction = Transaction(sender_wallet, recipient_wallet, amount)
        # Rule: check signature state
        if not transaction.sign_self(sender_privatekey):
            print("Error signing transaction error")
            return False
        if not transaction.validate_self():
            print("Error validating transaction")
            return False
        print("Transaction signature verified,now checking the balance")

        # Rule: performs the self check #NOTE - Without balance check
        # we need to performs the transactions amount check
        sender_balance = self.get_balance(sender_wallet)
        if amount > sender_balance:
            print("Transaction add failed , since sender does not have enough balance")
            return False
        # NOTE - save the transaction record from the broadcast
        print("Create new Transaction successfully")
        self.__open_transactions.append(transaction)
        self.save_open_transaction()
        return transaction
    # SECTION - Mining Logic

    # PoW helper
    def validate_proof(self, transactions: list, last_hash: str, proof: int, block_index: int):
        """
            this function is aiming to validate the proof , so this is the judgement of the puzzle,
            Arguments:
                transactions: is just the new block data load
                last_hash: previous block hash
                proof: the proof to iterate to fit the puzzle
                block_index: the index of the future block ,
            # FIXED
                BUG: this proof should containing current block index , so that the index can also be protected 
        """
        guess = (str([tx.to_order() for tx in transactions]) +
                 str(last_hash)+str(proof)+str(block_index)).encode('utf-8')
        # print(guess)
        guess_hash = sha256(guess).hexdigest()
        # print(guess_hash)
        # print("guess_hash>", guess_hash)
        return guess_hash[0:len(HASH_PUZZLE)] == HASH_PUZZLE

    def PoW(self):
        """
            this function is aiming to solve the puzzle , in this case is th hash head is starting with the "4ef" head
            and return the proof , which is the puzzle answer ,
            !NOTE -  this proof is a integer
        """
        last_block = self.get_the_last_block()
        # prepare the previous block dummy hash
        hashed_block = Block.get_block_hash(last_block)
        proof = 0
        # REVIEW : when doing PoW , the open_transactions is not including the reward record
        # Rule:
        #   The Mining reward transaction is only append to __open_transactions after the PoW is finished
        #!SECTION so , we need to notice we actually ignore the reward record when validate the proof
        future_block_index = len(self.__chain)
        while not self.validate_proof(self.__open_transactions, hashed_block, proof, future_block_index):
            proof += 1
        return proof

    #!SECTION Mining Logic IMPORTANT NOTE

    def mine_new_block(self, miner_wallet: str):
        # REVIEW - Exclude the mining when node is not connected to a wallet
        if miner_wallet == None:
            # have no wallet connected
            print("miner_wallet is required to mine coins")
            return False

        # Rule : can not transfer to self !!
        if miner_wallet == MINE_SYSTEM_PUBLIC_KEY:
            # have no wallet connected
            print("miner_wallet is equal to MINE_SYSTEM_PUBLIC_KEY")
            return False

        if not Wallet.validate_wallet_keys(miner_wallet):
            print("miner_wallet is invalid")
            return False
        # FIXME: bad implementation , but it works for checking the input is a RSA public key
        if len(miner_wallet) > 1000:
            print("you might provide more your private key to mine")
            return False

        last_block = self.get_the_last_block()
        # prepare the previous block dummy hash
        last_block_hash = Block.get_block_hash(last_block)
        print("last_block_hash hashed => ", last_block_hash)
        # solve the puzzle
        proof = self.PoW()
        print("proof  => ", proof)
        # Rule: checking all the transaction in open_transactions is valid
        for tx in self.__open_transactions:
            if not tx.validate_self():
                # have invalid transaction
                try:
                    print(
                        "Miner : Invalid transaction found in open_transactions , now try to remove it ", tx)
                    self.__open_transactions.remove(tx)
                    #!SECTION # if Miner Find a transaction which is invalid, it might can be alert to other node
                except:
                    print("Transaction may already be removed")
                    continue
        # NOTE: Starting reward the Miner
        reward_transaction = Transaction(
            MINE_SYSTEM_PUBLIC_KEY, miner_wallet, MINE_REWARD)
        # NOTE: User Miner System private key to signature this RewardTransaction
        reward_transaction.sign_self(MINE_SYSTEM_PRIVATE_KEY)

        self.__open_transactions.append(reward_transaction)
        # prepare the blockchain data structure
        newly_mined_block = Block(last_block_hash, len(
            self.__chain), self.__open_transactions, proof)
        self.__chain.append(newly_mined_block)
        # Rule - clear the open transactions (clear the pending pool)
        self.__open_transactions = []
        self.save_blockchain()
        self.save_open_transaction()
        print("MINE: Your successfully mine a new block")
        return newly_mined_block

    # TODO: Implement the BroadCast RSA checking
    def add_block_from_broadcast(self, previous_block_hash: str, index: int, data_json: list, proof: int, timestamp: float):
        """
            Rule:
                previous_block_hash: The previous block hash which should be our current block hash.
                index: The index of the broadcast's index ,which should be our current blockchain length.
                data: The block payload . the last one should be our miner reward transaction , and except that , the rest or the transaction will be validate the proof of work
                proof: The proof of work answer , which should be ignore the reward transaction
                timestamp: the timestamp should always be lower than the current timestamp
        """

        # Rule: preprocess the parameters
        try:
            # Rule: timestamp checking
            if timestamp > time():
                print("BroadCast Timestamp check failed")
                return False
            index = int(index)
            proof = int(proof)
            # Rule: preprocess the block payload
            #EFFECT: - Transaction
            data_json = [Transaction(
                tx["sender"], tx["recipient"], tx["amount"], tx["timestamp"],
                tx["signature"]) for tx in data_json]
            # Rule: Check All Transaction including the MINE_SYSTEM reward
            if not all([tx.validate_self() for tx in data_json]):
                # Rule: this operation also checks the MINE_SYSTEM signature
                print("This block was containing invalid transaction, rejected")
                return False
        except:
            print("Preprocess failed,add broadcast block failed")
            return False

        broadcast_block = Block(previous_block_hash,
                                index, data_json, proof, timestamp)
        print("Preprocessing block finished,start validating New Block...")
        our_latest_block = self.get_the_last_block()

        # Rule : check if this broadcast block is already add into our block chain
        if our_latest_block.index == broadcast_block.index and our_latest_block.timestamp == broadcast_block.timestamp and our_latest_block.proof == broadcast_block.proof and our_latest_block.data[-1].signature == broadcast_block.data[-1].signature:
            print("New broadcast block might already be added into our block chain,but we don't check the data payload")
            # FIXME: not the best solution, but seems to work
            # at the data field , we check if the miner's signature is the same as the broadcast block, if yes, which means this block is also created by that miner , and already added into our block chain
            # NOTE: and since the miner's reward block will always be the last one
            print("Already added into block chain")
            return False

        # Rule: validate the previous hash
        print("BroadCast Block seems to be new block .. now performing the checking")
        our_latest_block_hash = Block.get_block_hash(our_latest_block)
        if not (our_latest_block_hash == broadcast_block.previous_block_hash):
            print("Hash check failed")
            return False

        # Rule: validate the proof of work
        exclude_the_reward_transactions = broadcast_block.data[:-1]

        if not self.validate_proof(exclude_the_reward_transactions, broadcast_block.previous_block_hash, broadcast_block.proof, broadcast_block.index):
            print("Invalid proof")
            return False

        print("Checking proof passed, Hash check passed , now adding new block in to blockchain")

        self.__chain.append(broadcast_block)
        # Rule - clear the open transactions (clear the pending pool)
        # EFFECT: - since the transaction will be broadcast anyway , so , after one block mime that block ,we should empty our self block chain pending pool
        self.__open_transactions = []
        self.save_blockchain()
        return broadcast_block

    # SECTION - validate the chain logic

    def validate_chain(self):
        for (current_block_index, block) in enumerate(self.__chain):
            # print(current_block_index, block)
            # block[0] is point to the block chain previous hash
            # blockchain[chain_index-1] is point to the current block previous block
            # \                     \           \
            # chain_index -1      block
            if len(self.__chain) == 1:
                print("No other block")
                break
            if current_block_index == 0:
                # skip the first block validate
                continue
            # this check is check the current block previous_block_hash is equal to the previous block hash
            # NOTE - but please note the we are not checking the hash is start with the hash puzzle ,since we add the proof field
            # which means that with the proof field , we can ensure that the hash is must start with the hash puzzle while the proof is failed
            if block.previous_block_hash != Block.get_block_hash(self.__chain[current_block_index-1]):
                print("previous block hash mismatch")
                return False
            # REVIEW - the block is miner minded , so , we have the miner reward transaction in the block["data"] field , but when we calculate the hash puzzle , we are not including the miner reward transaction , so , we need to skip it when we validate the block
            if not self.validate_proof(block.data[:-1], block.previous_block_hash, block.proof, block.index):
                # FIXME: since the proof check will ignore the miner fee transaction,which means that the last block modify cannot be determined
                # which means
                print("Invalid proof in the block")
                return False

            # REVIEW: validate all transactions record in the block payload
            if not all([tx.validate_self() for tx in block.data]):
                print("Invalid transaction record in the block payload")
                return False
        return True


if __name__ == "__main__":
    blck = BlockChain()
    private, public = Wallet.generate_wallet()  # user 1
    private1, public1 = Wallet.generate_wallet()  # user 2
    # # blck.create_transaction(public1, public, 1, private1)
    # tx = Transaction(public, public1, 1)
    # tx.sign_self(private)
    # # blck.add_transaction_from_broadcast(
    # # tx.sender, tx.recipient, tx.amount, tx.signature)

    # NOTE: user try to mine new block
    # blck.mine_new_block(public)
    # blck.add_transaction_from_broadcast(
    #     tx.sender, tx.recipient, tx.amount, tx.signature)  # work
    # print(blck.get_balance(public))
    # NOTE: create a new transaction
    # blck.create_transaction(public, public1, 1, private)
    # blck.mine_new_block(public)
    # print(blck.get_balance(public))
