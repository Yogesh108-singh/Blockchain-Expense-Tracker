import unittest
from blockchain_core import Blockchain


class BlockchainTests(unittest.TestCase):
    def test_new_chain_is_valid(self):
        chain = Blockchain()
        self.assertTrue(chain.is_valid()[0])

    def test_added_block_is_valid(self):
        chain = Blockchain()
        chain.add_transaction({
            "type": "EXPENSE", "amount": "10.00", "category": "Food",
            "description": "Test", "transaction_date": "2026-10-25"
        })
        self.assertTrue(chain.is_valid()[0])

    def test_tampering_is_detected(self):
        chain = Blockchain()
        chain.add_transaction({
            "type": "EXPENSE", "amount": "10.00", "category": "Food",
            "description": "Test", "transaction_date": "2026-10-25"
        })
        chain.chain[1].transaction["amount"] = "999.00"
        self.assertFalse(chain.is_valid()[0])


if __name__ == "__main__":
    unittest.main()
