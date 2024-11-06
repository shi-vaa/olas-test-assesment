import os
import logging
import time

from web3 import Web3
from web3.exceptions import (
    ProviderConnectionError,
    Web3RPCError,
    TransactionIndexingInProgress,
    InvalidTransaction,
    TransactionNotFound,
)
from dotenv import load_dotenv

logger = logging.getLogger("App.W3")

load_dotenv()


class W3:
    def __init__(self):

        self.rpc_url = os.getenv("RPC_URL")
        self.erc20_contract_address = os.getenv("CONTRACT_ADDRESS")

        self.from_address = os.getenv("FROM_ADDRESS")
        self.to_address = os.getenv("TO_ADDRESS")

        self.private_key = os.getenv("PRIVATE_KEY")

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
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

            self.erc20_contract = self.w3.eth.contract(
                address=self.erc20_contract_address, abi=self.erc20_abi
            )
        except ProviderConnectionError as e:
            logger.error("Provider connection error" + str(e))
        except Web3RPCError as e:
            logger.error("web3 rpc error" + str(e))
        except Exception as e:
            logger.error("Unknown error" + str(e))

    def get_balance(self,address):
        try:
            balance = self.erc20_contract.functions.balanceOf(address).call()
            decimals = 18
            formatted_balance = balance / (10**decimals)
            return formatted_balance
        except Web3RPCError as e:
            logger.error("web3 rpc error" + str(e))
        except Exception as e:
            logger.error("Couldnot fetch balance" + str(e))

    def transfer(self,from_address,to_address):
        try:
            amount = self.w3.to_wei(1, "ether")

            if self.get_balance(self.from_address) >= 1.0:
                transaction = self.erc20_contract.functions.transfer(
                    to_address, amount
                ).build_transaction(
                    {
                        "from": from_address,
                        "gas": 200000,
                        "gasPrice": self.w3.to_wei("50", "gwei"),
                        "nonce": self.w3.eth.get_transaction_count(self.from_address),
                        "chainId": 80002,
                    }
                )

                signed_txn = self.w3.eth.account.sign_transaction(
                    transaction, self.private_key
                )

                txn_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

                logger.info(f"Transaction sent with hash: {txn_hash.hex()}")
                
                time.sleep(5) # wait for 5 seconds until transaction receipt is generated

                txn_receipt = self.w3.eth.get_transaction_receipt(txn_hash)

                if txn_receipt.status == 1:
                    logger.info(
                        "Funds transfered from"
                        + self.from_address
                        + "to"
                        + self.to_address
                    )
            else:
                logger.info("Not enough funds to transfer from " + self.from_address)
        except InvalidTransaction as e:
            logger.error("Invalid transaction" + str(e))
        except TransactionNotFound as e:
            logger.error("Transaction lookup failed" + str(e))
        except TransactionIndexingInProgress as e:
            logger.error("Transaction submitted but yet to be indexed" + str(e))
        except Exception as e:
            logger.error("Exception while transfer" + str(e))
