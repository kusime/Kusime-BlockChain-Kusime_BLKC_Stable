from collections import OrderedDict
from Ku_Crypto.helper.Ku_Super_OBJ import SuperOBJ
from Wallet import Wallet
# NOTE: Initialize the Blockchain Rule
from Ku_Rule import *
"""
    NOTE: Aiming:
        1. load the block chain transaction record
            all the information can be retrieved from the database
        2. load the open_transaction record
            all the information can be retrieved from the database
        3. add new transaction record
        4. performing the reward transaction

    #NOTE -  this call will not care about if this transaction is valid or not , but have a organization of a transaction record
"""


class Transaction(SuperOBJ):
    """
    Rule:
        Transaction:
            sender : sender wallet address
            recipient : recipient wallet address
            amount : amount of this transaction
            # NOTE: since signature generation is only can be generate form the private key, we cannot generate that signature during create transaction object
            signature : the signature of this transaction
    """

    def __init__(self, sender: str, recipient: str, amount: str, signature: str = None):
        self.sender = sender
        self.recipient = recipient
        # NOTE : the outside should not be take care of the amount type but the Inner initialize will take care of it
        self.amount = float(amount)
        # TODO - 1. add timestamp to indicate the transaction created time
        self.signature = signature

    def to_json(self):
        return self.__dict__.copy()

    def to_string(self):
        """
            NOTE : this function will use to the 
                1. generate the signature
                2. validate the signature
        """
        return str(self.sender) + str(self.recipient) + str(self.amount)

    def to_order(self):
        """
            NOTE : this function will use to the 
                1. to serialize the Transaction , since the block needs to be hash , and in block "data" field will have the instance of Transaction
                    and we need to make sure the order of the transaction cannot change
        """
        return OrderedDict(
            [("sender", self.sender), ("recipient", self.recipient), ("amount", self.amount)])

    def sign_self(self, wallet_private_key: str):
        """
            NOTE : this function will use to the ,this function will not care about what the transaction data looks like ,but only make sure 
                1. signature this transaction with given private key
        """

        # if self.sender == MINE_SYSTEM_PRIVATE_KEY:
        #     print("Please do not use the MINE_SYSTEM_PRIVATE_KEY as sender")
        #     return False

        # performing key checking
        if not all([Wallet.validate_wallet_keys(self.sender), Wallet.validate_wallet_keys(self.recipient)]):
            # Rule: - cannot send to invalid wallet address ( this can also check random transaction, since the wallet address is hard to guess)
            print("Invalid wallet address")
            return False
        if not Wallet.validate_wallet_keys(wallet_private_key):
            print("This private key is not valid")
            return False
        if self.signature != None:
            # Rule: -  this transaction is already be signed
            return False
        try:
            self.signature = Wallet.sign_transaction(wallet_private_key, self)
            return True
        except Exception as e:
            print(e)
            return False

    def validate_self(self) -> bool:
        """
        #REVIEW - This function will not care about the data !
            1. which means this method will only validate the basic data of this transaction record
                1.1 sender and recipient should be RSA keys
                1.2 sender and recipient should be not same
                1.3 extra check logic for the MINE_SYSTEM
                1.4 check the signature should not be None !

            NOTE: This function will performing self checking , instating making checking at out side , by calling this method can easily validate this transaction record is a valid one
                Rule:
                    return True if the transaction record is valid
        """
        if self.signature == None:
            # Rule - No signature is provided , reject the transaction record
            print("# Rule - No signature is provided , reject the transaction record")
            return False
        # performing self to self checking
        if self.sender == self.recipient:
            print("# Rule : cannot send transaction to self")
            return False

        # performing key checking
        if not all([Wallet.validate_wallet_keys(self.sender), Wallet.validate_wallet_keys(self.recipient)]):
            # Rule: - cannot send to invalid wallet address ( this can also check random transaction, since the wallet address is hard to guess)
            print("Invalid wallet address (RSA check fails")
            return False

        # FIXME: this is might not be a good solution
        # check if user is using his private key to committed this transaction
        if len(self.sender) > 1000 or len(self.recipient) > 1000:
            print(
                "Invalid public key check , Maybe you are using your own private key to commit this transaction")
            return False

        # Rule: check signature is matches the sender_wallet
        if not Wallet.validate_transaction(self.sender, self.signature, self):
            print("That private key does not match the sender_wallet")
            return False

        # Rule: maybe we should have a special rule to check the MINE_SYSTEM
        if self.sender == MINE_SYSTEM_PUBLIC_KEY:
            # Rule - this transaction might be committed by the MINE_SYSTEM
            # print("Transaction committed by MINE_SYSTEM")
            if self.amount != MINE_REWARD:
                # Rule - this MINE_REWARD is being modified , reject this transaction
                print("Transaction rejected by MINE_REWARD check failed")
                return False

        if self.sender == MINE_SYSTEM_PRIVATE_KEY:
            print("Please not using the MINE_SYSTEM_PRIVATE_KEY to send this transaction")
            return False

        if self.recipient == MINE_SYSTEM_PRIVATE_KEY:
            print(
                "Please not using the MINE_SYSTEM_PRIVATE_KEY to receive this transaction")
            return False
        if self.recipient == MINE_SYSTEM_PUBLIC_KEY:
            print(
                "Please not using the MINE_SYSTEM_PUBLIC_KEY to receive this transaction")
            return False

        # Rule: - performing the signature validate
        if not Wallet.validate_transaction(self.sender, self.signature, self):
            # Rule: signature verification failed
            print("Signature verification failed")
            return False
        return True


if __name__ == "__main__":
    private, public = Wallet.generate_wallet()
    private1, public1 = Wallet.generate_wallet()
    tx = Transaction(public1,
                     public, MINE_REWARD)
    print(tx.sign_self(private1))

    print(tx.validate_self())
