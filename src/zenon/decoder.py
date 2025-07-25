import base64
import struct
import json
from datetime import datetime
from typing import Dict, Optional
from src.config import TOKEN_DECIMALS, TRANSACTION_TYPES

class TransactionDecoder:
    """Decode Zenon bridge transaction data."""
    
    def __init__(self):
        self.method_signatures = {
            # These are example signatures - need to be updated based on actual bridge contract
            'WrapToken': bytes.fromhex('61d224bc'),
            'UnwrapToken': bytes.fromhex('b60694'),
            'Redeem': bytes.fromhex('d4e06c79'),
            'UpdateWrapRequest': bytes.fromhex('d4bb11c0')
        }
    
    def decode_transaction(self, tx_data: Dict) -> Dict:
        """Decode a transaction and extract relevant information."""
        result = {
            'hash': tx_data.get('hash'),
            'from_addr': tx_data.get('address'),
            'to_addr': tx_data.get('toAddress'),
            'amount': tx_data.get('amount', '0'),
            'token': tx_data.get('tokenStandard'),
            'block_height': tx_data.get('height'),
            'timestamp': self._get_timestamp(tx_data),
            'type': self._determine_tx_type(tx_data),
            'eth_addr': None,
            'raw_data': tx_data.get('data')
        }
        
        # Decode transaction data if present
        if tx_data.get('data'):
            try:
                decoded_data = self._decode_data(tx_data['data'])
                result.update(decoded_data)
            except Exception as e:
                print(f"Error decoding transaction data: {e}")
        
        # Format amount with decimals
        if result['amount'] and result['token']:
            result['formatted_amount'] = self._format_amount(
                result['amount'], 
                result['token']
            )
        
        return result
    
    def _determine_tx_type(self, tx_data: Dict) -> str:
        """Determine transaction type based on various factors."""
        # Check if it's a simple transfer (no data)
        if not tx_data.get('data') or tx_data.get('data') == '':
            if tx_data.get('toAddress') != tx_data.get('address'):
                return TRANSACTION_TYPES['TRANSFER']
        
        # Check block type
        block_type = tx_data.get('blockType')
        if block_type == 4:  # Transfer type
            return TRANSACTION_TYPES['TRANSFER']
        
        # Try to decode data to determine type
        if tx_data.get('data'):
            try:
                data_bytes = base64.b64decode(tx_data['data'])
                if len(data_bytes) >= 4:
                    method_sig = data_bytes[:4]
                    for method, sig in self.method_signatures.items():
                        if method_sig == sig:
                            return TRANSACTION_TYPES.get(method.upper(), 'Unknown')
            except:
                pass
        
        # Check if it's from/to bridge contract
        bridge_addr = 'z1qxemdeddedxdrydgexxxxxxxxxxxxxxxmqgr0d'
        if tx_data.get('toAddress') == bridge_addr:
            # Could be wrap or update request
            if tx_data.get('tokenStandard') in ['zts1znnxxxxxxxxxxxxx9z4ulx', 'zts1qsrxxxxxxxxxxxxxmrhjll']:
                return TRANSACTION_TYPES['WRAP_TOKEN']
        
        return 'Unknown'
    
    def _decode_data(self, data_b64: str) -> Dict:
        """Decode base64 transaction data."""
        try:
            data_bytes = base64.b64decode(data_b64)
            result = {}
            
            # Try to extract ETH address if present
            # Look for 0x prefix in hex
            if b'0x' in data_bytes:
                start = data_bytes.find(b'0x')
                if start != -1 and len(data_bytes) >= start + 42:
                    eth_addr = data_bytes[start:start+42].decode('utf-8', errors='ignore')
                    if self._is_valid_eth_address(eth_addr):
                        result['eth_addr'] = eth_addr
            
            return result
        except Exception as e:
            print(f"Error in _decode_data: {e}")
            return {}
    
    def _is_valid_eth_address(self, address: str) -> bool:
        """Check if string is a valid Ethereum address."""
        if not address.startswith('0x'):
            return False
        if len(address) != 42:
            return False
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
    
    def _format_amount(self, amount: str, token: str) -> str:
        """Format amount with proper decimals."""
        try:
            decimals = TOKEN_DECIMALS.get(token, 8)
            amount_int = int(amount)
            amount_float = amount_int / (10 ** decimals)
            return f"{amount_float:,.2f}"
        except:
            return amount
    
    def _get_timestamp(self, tx_data: Dict) -> Optional[datetime]:
        """Extract timestamp from transaction data."""
        confirmation = tx_data.get('confirmationDetail', {})
        if confirmation and confirmation.get('momentumTimestamp'):
            try:
                return datetime.fromtimestamp(confirmation['momentumTimestamp'])
            except:
                pass
        return None