import asyncio
import json
import websockets
import logging
from typing import Callable, Optional
from datetime import datetime
from pathlib import Path
from src.config import ZENON_WSS_URL, BRIDGE_ADDRESS
from src.zenon.decoder import TransactionDecoder

logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(exist_ok=True)

class ZenonWebSocket:
    """Manage WebSocket connection to Zenon node."""
    
    def __init__(self, on_transaction: Callable):
        self.url = ZENON_WSS_URL
        self.bridge_address = BRIDGE_ADDRESS
        self.on_transaction = on_transaction
        self.decoder = TransactionDecoder()
        self.ws = None
        self.subscription_id = None
        self.reconnect_delay = 5
        self.max_reconnect_delay = 300
        self._running = False
    
    async def start(self):
        """Start the WebSocket connection with auto-reconnect."""
        self._running = True
        while self._running:
            try:
                await self._connect()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
    
    async def stop(self):
        """Stop the WebSocket connection."""
        self._running = False
        if self.ws:
            await self._unsubscribe()
            await self.ws.close()
    
    async def _connect(self):
        """Connect to WebSocket and subscribe to bridge address."""
        logger.info(f"Connecting to {self.url}")
        
        async with websockets.connect(self.url) as ws:
            self.ws = ws
            self.reconnect_delay = 5  # Reset delay on successful connection
            
            # Subscribe to bridge address
            await self._subscribe()
            
            # Listen for messages
            async for message in ws:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
    
    async def _subscribe(self):
        """Subscribe to all account blocks and filter for bridge transactions."""
        subscribe_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "ledger.subscribe",
            "params": ["allAccountBlocks"]
        }
        
        await self.ws.send(json.dumps(subscribe_msg))
        
        # Wait for subscription confirmation
        response = await self.ws.recv()
        data = json.loads(response)
        
        if 'result' in data:
            self.subscription_id = data['result']
            logger.info(f"Subscribed to all account blocks with ID: {self.subscription_id}")
        else:
            raise Exception(f"Failed to subscribe: {data}")
    
    async def _unsubscribe(self):
        """Unsubscribe from notifications."""
        if self.subscription_id:
            unsubscribe_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "ledger.unsubscribe",
                "params": [self.subscription_id]
            }
            await self.ws.send(json.dumps(unsubscribe_msg))
    
    async def _handle_message(self, data: dict):
        """Handle incoming WebSocket messages."""
        # Log all raw messages to file for debugging
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save raw message to logs
        with open(LOGS_DIR / f'ws_raw_{timestamp}.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        # Check if it's a notification
        if data.get('method') == 'ledger.subscription':
            params = data.get('params', {})
            if params.get('subscription') == self.subscription_id:
                # Extract account block data
                result = params.get('result')
                if result:
                    logger.info(f"Received WebSocket notification with {len(result) if isinstance(result, list) else 1} blocks")
                    await self._process_account_block(result)
            else:
                logger.warning(f"Received notification for unknown subscription: {params.get('subscription')}")
    
    async def _process_account_block(self, block_data):
        """Process an account block and trigger callback if it's a bridge transaction."""
        try:
            # Define addresses to filter
            BURN_ADDRESS = 'z1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqsggv2f'
            
            # Save block data for debugging
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            
            # Handle both single blocks and arrays
            blocks = block_data if isinstance(block_data, list) else [block_data]
            
            for i, block in enumerate(blocks):
                to_addr = block.get('toAddress', '')
                from_addr = block.get('address', '')
                
                # Skip burn address transactions
                if to_addr == BURN_ADDRESS:
                    logger.debug(f"Skipping burn address transaction: {block.get('hash', 'unknown')[:16]}")
                    continue
                
                # Process transactions FROM bridge (unwrap/redeem)
                if from_addr == self.bridge_address:
                    logger.info(f"Found block FROM bridge: {block.get('hash')}")
                    
                    # Validate it's a real transaction
                    tx_info = self.decoder.decode_transaction(block)
                    if self._is_valid_bridge_transaction(tx_info):
                        logger.info(f"Valid bridge transaction (from bridge): Type={tx_info['type']}, Hash={tx_info['hash']}")
                        
                        # Save decoded transaction
                        with open(LOGS_DIR / f'tx_from_bridge_{timestamp}_{i}.json', 'w') as f:
                            json.dump(tx_info, f, indent=2)
                        
                        await self.on_transaction(tx_info)
                
                # Process transactions TO bridge (wrap/update)
                if to_addr == self.bridge_address:
                    logger.info(f"Found block TO bridge: {block.get('hash')}")
                    
                    tx_info = self.decoder.decode_transaction(block)
                    if self._is_valid_bridge_transaction(tx_info):
                        logger.info(f"Valid bridge transaction (to bridge): Type={tx_info['type']}, Hash={tx_info['hash']}")
                        
                        # Save decoded transaction
                        with open(LOGS_DIR / f'tx_to_bridge_{timestamp}_{i}.json', 'w') as f:
                            json.dump(tx_info, f, indent=2)
                        
                        await self.on_transaction(tx_info)
                
                # Also check paired account block if exists
                paired_block = block.get('pairedAccountBlock')
                if paired_block and paired_block.get('toAddress') != BURN_ADDRESS:
                    paired_to = paired_block.get('toAddress', '')
                    paired_from = paired_block.get('address', '')
                    
                    if paired_to == self.bridge_address or paired_from == self.bridge_address:
                        logger.debug(f"Processing paired block: {paired_block.get('hash', 'unknown')[:16]}")
                        tx_info = self.decoder.decode_transaction(paired_block)
                        if self._is_valid_bridge_transaction(tx_info):
                            logger.info(f"Valid paired bridge transaction: Type={tx_info['type']}, Hash={tx_info['hash']}")
                            await self.on_transaction(tx_info)
            
        except Exception as e:
            logger.error(f"Error processing account block: {e}", exc_info=True)
            # Save error block for debugging
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            with open(LOGS_DIR / f'ws_error_{timestamp}.json', 'w') as f:
                json.dump({'error': str(e), 'block_data': block_data}, f, indent=2)
    
    def _is_valid_bridge_transaction(self, tx_info: dict) -> bool:
        """Check if transaction is a valid bridge operation."""
        # Valid transaction types for bridge
        valid_types = ['WrapToken', 'UnwrapToken', 'Redeem', 'UpdateWrapRequest']
        
        # Check transaction type
        if tx_info.get('type') not in valid_types:
            logger.debug(f"Skipping transaction with type: {tx_info.get('type')}")
            return False
        
        # Check token is ZNN or QSR
        token = tx_info.get('token', '')
        valid_tokens = ['zts1znnxxxxxxxxxxxxx9z4ulx', 'zts1qsrxxxxxxxxxxxxxmrhjll']
        
        # For wrap/unwrap, must have valid token and non-zero amount
        if tx_info['type'] in ['WrapToken', 'UnwrapToken']:
            if token not in valid_tokens:
                logger.debug(f"Skipping {tx_info['type']} with invalid token: {token}")
                return False
            
            # Must have non-zero amount for wrap/unwrap
            amount = tx_info.get('amount', '0')
            if amount == '0' or amount == 0:
                logger.debug(f"Skipping {tx_info['type']} with zero amount")
                return False
        
        # UpdateWrapRequest and Redeem can have zero amounts (they're contract calls)
        # but should still be valid tokens if specified
        if tx_info['type'] in ['UpdateWrapRequest', 'Redeem']:
            if token and token not in valid_tokens and token != 'zts1qqqqqqqqqqqqqqqqtq587y':
                # Allow empty token or system token for these operations
                logger.debug(f"Allowing {tx_info['type']} with token: {token}")
        
        return True