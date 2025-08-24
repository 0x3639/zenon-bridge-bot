import base64
import struct
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
from src.config import TOKEN_DECIMALS, TRANSACTION_TYPES

logger = logging.getLogger(__name__)

class TransactionDecoder:
    """Decode Zenon bridge transaction data."""
    
    def __init__(self):
        self.method_signatures = {
            # Method signatures from actual bridge contract
            'WRAP_TOKEN': bytes.fromhex('61d224bc'),  # WrapToken method signature
            'UNWRAP_TOKEN': bytes.fromhex('52298858'),  # UnwrapToken method  
            'REDEEM': bytes.fromhex('1e83409a'),  # Redeem method
            'UPDATE_WRAP_REQUEST': bytes.fromhex('d4bb11c0')  # UpdateWrapRequest method (corrected)
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
        """Determine transaction type based on method signature and context."""
        logger.debug(f"Determining transaction type for: {tx_data.get('hash', 'unknown')}")
        
        bridge_addr = 'z1qxemdeddedxdrydgexxxxxxxxxxxxxxxmqgr0d'
        to_addr = tx_data.get('toAddress', '')
        from_addr = tx_data.get('address', '')
        
        # First, try to decode method signature from data field
        if tx_data.get('data') and tx_data['data'] != '':
            try:
                data_bytes = base64.b64decode(tx_data['data'])
                logger.debug(f"Data decoded: {len(data_bytes)} bytes")
                
                if len(data_bytes) >= 4:
                    method_sig = data_bytes[:4]
                    method_sig_hex = method_sig.hex()
                    logger.info(f"Method signature: 0x{method_sig_hex}")
                    
                    # Check against known bridge method signatures
                    for method, sig in self.method_signatures.items():
                        if method_sig == sig:
                            logger.info(f"Found matching signature: {method}")
                            return TRANSACTION_TYPES.get(method, 'Unknown')
                    
                    # If has data but no matching signature, it's not a bridge operation
                    logger.debug(f"Unknown method signature: 0x{method_sig_hex}")
                    return 'Unknown'
                    
            except Exception as e:
                logger.error(f"Error decoding data: {e}")
        
        # For transactions TO bridge without explicit method signature
        if to_addr == bridge_addr:
            token_std = tx_data.get('tokenStandard', '')
            amount = tx_data.get('amount', '0')
            
            # If it's sending ZNN/QSR to bridge with amount > 0, likely a wrap
            if token_std in ['zts1znnxxxxxxxxxxxxx9z4ulx', 'zts1qsrxxxxxxxxxxxxxmrhjll']:
                if amount != '0' and amount != 0:
                    logger.info("Identified as WRAP_TOKEN based on context (token to bridge)")
                    return TRANSACTION_TYPES['WRAP_TOKEN']
        
        # For transactions FROM bridge
        if from_addr == bridge_addr:
            token_std = tx_data.get('tokenStandard', '')
            amount = tx_data.get('amount', '0')
            
            # If it's sending tokens from bridge, could be unwrap or redeem
            if token_std and amount != '0' and amount != 0:
                # Without explicit method signature, assume unwrap for now
                logger.info("Identified as UNWRAP_TOKEN based on context (from bridge)")
                return TRANSACTION_TYPES['UNWRAP_TOKEN']
        
        # Simple transfers not involving bridge
        if not tx_data.get('data') or tx_data.get('data') == '':
            if to_addr != from_addr and to_addr != bridge_addr and from_addr != bridge_addr:
                logger.debug("Identified as TRANSFER (not bridge-related)")
                return TRANSACTION_TYPES['TRANSFER']
        
        logger.warning(f"Could not determine transaction type for {tx_data.get('hash', 'unknown')}")
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