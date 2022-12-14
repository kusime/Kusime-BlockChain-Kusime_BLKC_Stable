"""
    Make the object printable
"""


class SuperOBJ:
    def __init__(self):
        pass

    def __repr__(self):
        """
            make object printable
        """
        return str(self.__dict__)

    def to_string(self):
        # the OBJ can be stringify
        pass

    def to_order(self):
        # the OBJ can be orderable
        pass
