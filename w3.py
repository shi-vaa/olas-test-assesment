from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()


class W3:
    def __init__(self):

        self.rpc_url = os.getenv("RPC_URL")
        self.erc20_contract_address = os.getenv("CONTRACT_ADDRESS")

        self.from_address = os.getenv("FROM_ADDRESS")
        self.to_address = os.getenv("TO_ADDRESS")

        self.private_key = os.getenv("PRIVATE_KEY")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function",
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"},
                ],
                "name": "transfer",
                "outputs": [{"name": "success", "type": "bool"}],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function",
            },
        ]

        self.erc20_contract = self.w3.eth.contract(
            address=self.erc20_contract_address, abi=self.erc20_abi
        )

    def get_balance(self):
        try:
            balance = self.erc20_contract.functions.balanceOf(self.from_address).call()
            decimals = 18
            formatted_balance = balance / (10**decimals)
            return formatted_balance
        except Exception as e:
            print("Couldnot fetch balance" + str(e))

    def transfer(self):
        try:
            amount = self.w3.to_wei(1, "ether")

            if self.get_balance() >= 1.0:
                transaction = self.erc20_contract.functions.transfer(
                    self.to_address, amount
                ).build_transaction(
                    {
                        "from": self.from_address,
                        "gas": 200000,
                        "gasPrice": self.w3.to_wei("50", "gwei"),
                        "nonce": self.w3.eth.get_transaction_count(self.from_address),
                        "chainId": 97,
                    }
                )

                signed_txn = self.w3.eth.account.sign_transaction(
                    transaction, self.private_key
                )

                txn_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

                # txn_receipt = self.w3.eth.get_transaction_receipt(txn_hash)

                print(
                    f"Transaction sent with hash: {txn_hash.hex()}"
                )
            else:
                print("Not enough funds to transfer")

        except Exception as e:
            print("Exception while transfer" + str(e))
