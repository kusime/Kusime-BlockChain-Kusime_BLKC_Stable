from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
# NOTE:this hashlib is not compatible with Crypto
# from hashlib import sha256
import Crypto.Random
try:
    from .Ku_Binary import *
    from .helper.Ku_Super_OBJ import SuperOBJ
except:
    from Ku_Binary import *
    from helper.Ku_Super_OBJ import SuperOBJ


class Ku_RSA:
    """
        Designed to generate RSA keys, But not care how to them , but just prepare the basic methods for RSA operations. , and also don't care about the what data is , but need to define the general methods to make object to string.
    """

    @staticmethod
    def _generate_RSA_keys():
        """
            Rule:
                return (string, string) 
                    => (private_key,public_key)
        """
        # generate rsa key pair
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        # NOTE : export the key
        private_key = private_key.exportKey(format="DER")
        public_key = public_key.exportKey(format="DER")
        # NOTE : stringify the binary key
        private_key = bin2hex(private_key)
        public_key = bin2hex(public_key)

        return (private_key, public_key)

    @staticmethod
    def _sign_object(private_key: str, SuperOBJ_instance_Or_String, trigger_convert=True) -> str:
        """
            Rule:
                Args:
                    private_key: The private key with string format for signature
                    object: The object to sign, and this object should have the to_string_method
                    to_string_method : The wrapper function to make the object to string
                Return:
                    => signature
        """
        rsa_pri = RSA.import_key(hex2bin(private_key))
        singer = PKCS1_v1_5.new(rsa_pri)
        # prepare the payload
        if trigger_convert:
            object_binary = (
                SuperOBJ_instance_Or_String.to_string()).encode("utf-8")
        else:
            object_binary = (str(SuperOBJ_instance_Or_String)).encode("utf-8")
        object_binary = SHA256.new(object_binary)
        # bin
        signature = singer.sign(object_binary)
        # bin 2 str
        return bin2hex(signature)

    @staticmethod
    def _validate_object(public_key: str, signature: str, SuperOBJ_instance_Or_String, trigger_convert=True):
        """
            Rule:
                Args:
                    public_key: The  public_key with string format for validate_object
                    signature: The signature to check if this signature is singed by this public_key's private key
                    SuperOBJ_instance : The object to validate
                Return:
                    => boolean : True if passed, False otherwise
        """
        rsa_pub = RSA.import_key(hex2bin(public_key))
        validator = PKCS1_v1_5.new(rsa_pub)
        # prepare the payload
        if trigger_convert:
            object_binary = (
                SuperOBJ_instance_Or_String.to_string()).encode("utf-8")
        else:
            object_binary = (str(SuperOBJ_instance_Or_String)).encode("utf-8")
        object_binary = SHA256.new(object_binary)
        # signature should be bin
        # str - > bin -> bool
        return validator.verify(object_binary, hex2bin(signature))

    @staticmethod
    def _validate_is_valid_rsa_key(key: str) -> bool:
        try:
            # Deserialize the public key
            public_key = RSA.importKey(hex2bin(key))
        except ValueError:
            # Return False if the input is not a valid RSA key
            return False

        # Check that the key is an RSA key
        if isinstance(public_key, RSA.RsaKey):
            return True
        else:
            return False


if __name__ == "__main__":

    class Test(SuperOBJ):
        def __init__(self):
            self.payload = 1
            self.payload2 = 2

        def to_json(self):
            # override the to string method
            return str(self.payload) + str(self.payload2)
    private_key, public_key = Ku_RSA._generate_RSA_keys()
    print(private_key, public_key)
    test = Test()
    signature = Ku_RSA._sign_object(private_key, test)
    print(signature)
    test.payload = 3  # modifying
    print(Ku_RSA._validate_object(public_key, signature, test))
    test.payload = 1  # change back
    print(Ku_RSA._validate_object(public_key, signature, test))
    # print(Ku_RSA._validate_is_valid_rsa_key("MAX"))
