import hashlib
import json
from datetime import datetime


def canonical_json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Block:
    def __init__(self, index, timestamp, transaction, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transaction = transaction
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def payload(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transaction": self.transaction,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }

    def calculate_hash(self):
        return sha256_text(canonical_json(self.payload()))

    def to_dict(self):
        result = self.payload()
        result["hash"] = self.hash
        return result

    @classmethod
    def from_dict(cls, data):
        block = cls(
            index=data["index"],
            timestamp=data["timestamp"],
            transaction=data["transaction"],
            previous_hash=data["previous_hash"],
            nonce=data.get("nonce", 0),
        )
        block.hash = data.get("hash", "")
        return block


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    @staticmethod
    def create_genesis_block():
        return Block(
            index=0,
            timestamp="Genesis",
            transaction={"type": "GENESIS", "description": "First block"},
            previous_hash="0",
        )

    @property
    def last_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        block = Block(
            index=len(self.chain),
            timestamp=datetime.now().isoformat(timespec="seconds"),
            transaction=transaction,
            previous_hash=self.last_block.hash,
        )
        self.chain.append(block)
        return block

    def is_valid(self):
        if not self.chain:
            return False, "The chain is empty."
        if self.chain[0].index != 0 or self.chain[0].previous_hash != "0":
            return False, "Genesis block structure is invalid."
        for i, block in enumerate(self.chain):
            if block.hash != block.calculate_hash():
                return False, f"Block {i} hash mismatch: data may have changed."
            if i > 0:
                if block.index != self.chain[i - 1].index + 1:
                    return False, f"Block {i} index sequence is invalid."
                if block.previous_hash != self.chain[i - 1].hash:
                    return False, f"Block {i} previous-hash link is invalid."
        return True, "All block hashes and links are valid."

    def to_list(self):
        return [block.to_dict() for block in self.chain]

    @classmethod
    def from_list(cls, records):
        chain = cls()
        if not records:
            return chain
        chain.chain = [Block.from_dict(item) for item in records]
        return chain
