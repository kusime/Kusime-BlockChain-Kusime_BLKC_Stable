from Ku_Crypto.Ku_RSA import Ku_RSA

# NOTE: inherit from the Ku_RSA class to make the wallet have their fo


class Wallet():
    @staticmethod
    def generate_wallet():
        """
            Returns:
                Generated key pair
                (wallet_private , wallet_public)
        """
        # NOTE: this function will generate a RSA key pair for the wallet, but this will not store to the ,

        return Ku_RSA._generate_RSA_keys()

    @staticmethod
    def sign_transaction(wallet_private: str, transaction_SuperOBJ):
        """
            Rule:
                wallet_private: wallet_private key to sign transaction
                transaction_SuperOBJ : transaction object to validate
            Returns:
                transaction signature (string)
        """

        return Ku_RSA._sign_object(wallet_private, transaction_SuperOBJ)

    @staticmethod
    def validate_wallet_keys(wallet_address: str):
        """
            Rule:
                wallet_address : validate wallet address (is RSA key pair , or not a random address that passed in...)
            Returns:
                boolean : True if address is valid
        """
        return Ku_RSA._validate_is_valid_rsa_key(wallet_address)

    @staticmethod
    def validate_transaction(wallet_public, transaction_signature, transaction_SuperOBJ):
        """
            Rule:
                wallet_public: wallet_private key to sign transaction
                transaction_signature : signature of transaction
                transaction_SuperOBJ : transaction object to validate
            Returns:
                transaction signature (string)
        """

        return Ku_RSA._validate_object(wallet_public, transaction_signature, transaction_SuperOBJ)


if __name__ == "__main__":
    from Transaction import Transaction
    tx = Transaction("Alice", "Bob", "100", "abc123")
    private, public = Wallet.generate_wallet()
    tx_signature = Wallet.sign_transaction(private, tx)
    print(tx_signature)
    # tx.amount = 400
    tx_validate = Wallet.validate_transaction(public, tx_signature, tx)
    print(tx_validate)
