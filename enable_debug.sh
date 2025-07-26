#!/bin/bash
# Enable debug logging to capture all WebSocket data

echo "Enabling debug mode..."

# Update .env file to set debug logging
if grep -q "LOG_LEVEL" .env; then
    sed -i.bak 's/LOG_LEVEL=.*/LOG_LEVEL=DEBUG/' .env
else
    echo "LOG_LEVEL=DEBUG" >> .env
fi

echo "✅ Debug mode enabled!"
echo "Now restart the bot to see detailed logs:"
echo ""
echo "Docker:"
echo "  sudo docker compose down"
echo "  sudo docker compose up -d --build"
echo "  sudo docker compose logs -f"
echo ""
echo "Local:"
echo "  python3 -m src.bot"
echo ""
echo "Logs will be saved to:"
echo "  logs/bot.log - General bot logs"
echo "  logs/ws_*.json - Raw WebSocket messages"
echo "  logs/tx_*.json - Decoded transactions"