class NoSuchTagException(Exception):
    """Raised when a html tag parser is not found in the jump_table"""
    def __init__(self, tag: str):
        super().__init__()
        self.tag = tag