# Bridge Bot v2.0 Production Migration Guide

## ⚠️ IMPORTANT: Read Before Deploying

This update includes significant changes to transaction filtering and notifications. **Your existing users and their subscriptions will be preserved**, but some user filter settings need to be cleaned up.

## What Changed

### Transaction Types
- **Before**: 5 transaction types (WrapToken, UnwrapToken, Redeem, Transfer, UpdateWrapRequest)
- **After**: 3 transaction types (WrapToken, UnwrapToken, Redeem only)
- **Impact**: Users with filters for `Transfer` or `UpdateWrapRequest` need cleanup

### Database Schema
- **New**: `transactions` table for statistics
- **Existing**: `subscribers` table unchanged (users preserved)
- **Changed**: Invalid filters automatically cleaned

## Migration Steps

### Step 1: Backup Your Database (CRITICAL!)
```bash
# Backup your production database
cp data/bridge_bot.db data/bridge_bot.db.backup.$(date +%Y%m%d_%H%M%S)
```

### Step 2: Run Migration Script
```bash
# Make sure you're in the bot directory
cd /path/to/your/zenon-bridge-alert

# Run the migration script
python3 migration_script.py
```

**The migration script will:**
- ✅ Preserve all your existing users
- ✅ Clean up invalid filters (Transfer, UpdateWrapRequest)
- ✅ Create new tables for statistics
- ✅ Verify everything worked correctly
- ⚠️ Show you exactly what was changed

### Step 3: Test the Migration
```bash
# Check that users are preserved
sqlite3 data/bridge_bot.db "SELECT COUNT(*) FROM subscribers WHERE active = 1;"

# Check that invalid filters were cleaned
sqlite3 data/bridge_bot.db "SELECT user_id, filters FROM subscribers WHERE filters != '[]';"
```

### Step 4: Deploy New Code
```bash
# Pull latest code
git pull origin main

# Restart your bot service
systemctl restart bridge-bot
# OR
docker-compose restart
```

## What Users Will Experience

### For Users With No Filters
- **No change** - they will continue receiving all bridge notifications

### For Users With Valid Filters (WrapToken/UnwrapToken/Redeem)
- **No change** - their filters remain active

### For Users With Invalid Filters (Transfer/UpdateWrapRequest)
- **Automatic cleanup** - invalid filters are removed
- **Still subscribed** - they won't lose their subscription
- **Notification**: They can use `/filter` to set new preferences

## Verification

After migration, verify everything is working:

1. **Check user count**: Should match pre-migration count
2. **Test /stats command**: Should work (may show "No transactions" initially)
3. **Test /filter command**: Should only show 3 options (WrapToken, UnwrapToken, Redeem)
4. **Monitor logs**: Look for "Cleaned invalid filters for user X" messages

## Rollback Plan (If Needed)

If something goes wrong:

```bash
# Stop the bot
systemctl stop bridge-bot

# Restore the backup
cp data/bridge_bot.db.backup.YYYYMMDD_HHMMSS data/bridge_bot.db

# Deploy old version
git checkout <previous-commit>

# Restart
systemctl start bridge-bot
```

## Safety Features

The new code includes automatic cleanup:
- Invalid filters are removed automatically when users are loaded
- No user subscriptions are lost
- Database schema changes are additive (no data loss)

## Support

If you encounter issues:
1. Check the backup was created successfully
2. Review migration script output for errors
3. Check bot logs for any startup issues
4. Contact support with migration script output

---

**This migration is safe and preserves all user data. The migration script is designed to be run multiple times safely.**