#!/bin/bash

# ============================================================================
# PostgreSQL Remote Access Setup Script for Power BI Connection
# ============================================================================
# Run this on your VPS to enable remote PostgreSQL connections
# Command: sudo bash setup_postgres_remote_access.sh
# ============================================================================

set -e

echo "=========================================="
echo "PostgreSQL Remote Access Setup"
echo "=========================================="

# Configuration paths
PG_CONF="/etc/postgresql/16/main/postgresql.conf"
PG_HBA="/etc/postgresql/16/main/pg_hba.conf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# Step 1: Verify PostgreSQL Installation
# ============================================================================
echo -e "\n${YELLOW}Step 1: Checking PostgreSQL Installation...${NC}"

if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL not installed!${NC}"
    exit 1
fi

PG_VERSION=$(psql --version)
echo -e "${GREEN}✅ PostgreSQL Found: $PG_VERSION${NC}"

# ============================================================================
# Step 2: Backup Configuration Files
# ============================================================================
echo -e "\n${YELLOW}Step 2: Backing up configuration files...${NC}"

if [ ! -f "$PG_CONF.backup" ]; then
    sudo cp "$PG_CONF" "$PG_CONF.backup"
    echo -e "${GREEN}✅ Backed up: $PG_CONF${NC}"
else
    echo -e "${YELLOW}⚠️  Backup already exists${NC}"
fi

if [ ! -f "$PG_HBA.backup" ]; then
    sudo cp "$PG_HBA" "$PG_HBA.backup"
    echo -e "${GREEN}✅ Backed up: $PG_HBA${NC}"
else
    echo -e "${YELLOW}⚠️  Backup already exists${NC}"
fi

# ============================================================================
# Step 3: Update postgresql.conf - Enable Listen on All Addresses
# ============================================================================
echo -e "\n${YELLOW}Step 3: Updating postgresql.conf...${NC}"

# Remove the old line (commented or uncommented)
sudo sed -i "/^#*listen_addresses/d" "$PG_CONF"

# Add the new line
echo "listen_addresses = '*'" | sudo tee -a "$PG_CONF" > /dev/null

echo -e "${GREEN}✅ Updated listen_addresses = '*'${NC}"

# Verify the change
RESULT=$(sudo grep "^listen_addresses" "$PG_CONF")
echo "   Current setting: $RESULT"

# ============================================================================
# Step 4: Update pg_hba.conf - Allow Remote Connections
# ============================================================================
echo -e "\n${YELLOW}Step 4: Updating pg_hba.conf...${NC}"

# Check if remote connection line already exists
if ! sudo grep -q "^host.*all.*all.*0.0.0.0/0" "$PG_HBA"; then
    # Add after the IPv4 localhost line
    sudo sed -i "/^host.*all.*all.*127.0.0.1/a host    all             all             0.0.0.0/0               md5" "$PG_HBA"
    echo -e "${GREEN}✅ Added remote connection rule for 0.0.0.0/0${NC}"
else
    echo -e "${YELLOW}⚠️  Remote connection rule already exists${NC}"
fi

# Verify the change
echo "   Remote access rules:"
sudo grep "0.0.0.0/0" "$PG_HBA" || echo "   No explicit 0.0.0.0 rule found"

# ============================================================================
# Step 5: Restart PostgreSQL
# ============================================================================
echo -e "\n${YELLOW}Step 5: Restarting PostgreSQL...${NC}"

sudo systemctl restart postgresql

sleep 2

# Check status
if sudo systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL restarted successfully${NC}"
else
    echo -e "${RED}❌ PostgreSQL failed to start!${NC}"
    echo "   Check logs: sudo journalctl -u postgresql -n 50"
    exit 1
fi

# ============================================================================
# Step 6: Verify Port Listening
# ============================================================================
echo -e "\n${YELLOW}Step 6: Verifying Port Listening...${NC}"

if sudo netstat -tlnp 2>/dev/null | grep -q "0.0.0.0:5432"; then
    echo -e "${GREEN}✅ PostgreSQL is listening on 0.0.0.0:5432${NC}"
    sudo netstat -tlnp | grep 5432
else
    echo -e "${RED}❌ PostgreSQL is NOT listening on all addresses!${NC}"
    echo "   Current connections:"
    sudo netstat -tlnp | grep 5432
    exit 1
fi

# ============================================================================
# Step 7: Open Firewall Port (if using UFW)
# ============================================================================
echo -e "\n${YELLOW}Step 7: Checking Firewall...${NC}"

if command -v ufw &> /dev/null; then
    if sudo ufw status | grep -q "Status: active"; then
        echo "   Firewall is enabled"
        
        if ! sudo ufw status | grep -q "5432"; then
            echo "   Opening port 5432..."
            sudo ufw allow 5432/tcp
            sudo ufw reload
            echo -e "${GREEN}✅ Port 5432 opened in firewall${NC}"
        else
            echo -e "${GREEN}✅ Port 5432 already open in firewall${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  UFW firewall is not active (no action needed)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  UFW not installed (skipping firewall config)${NC}"
fi

# ============================================================================
# Step 8: Test Connection
# ============================================================================
echo -e "\n${YELLOW}Step 8: Testing Database Connection...${NC}"

if sudo -u postgres psql -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Local connection successful${NC}"
else
    echo -e "${RED}❌ Local connection failed!${NC}"
    exit 1
fi

# ============================================================================
# Final Summary
# ============================================================================
echo -e "\n${GREEN}=========================================="
echo "Setup Complete! ✅"
echo "===========================================${NC}"

echo -e "\n${GREEN}Configuration Summary:${NC}"
echo "  • PostgreSQL Config: $PG_CONF"
echo "    - listen_addresses = '*'"
echo "  • Firewall: Port 5432 open"
echo "  • Remote connections: ENABLED"

echo -e "\n${GREEN}Connection Details:${NC}"
echo "  • Host: 72.61.141.247"
echo "  • Port: 5432"
echo "  • Database: sales_dashboard"
echo "  • Username: postgres"
echo "  • Password: SecurePassword123!"

echo -e "\n${GREEN}Next Steps:${NC}"
echo "  1. From Windows PowerShell, test connection:"
echo "     psql -h 72.61.141.247 -U postgres -d sales_dashboard"
echo ""
echo "  2. In Power BI, use:"
echo "     Server: 72.61.141.247"
echo "     Database: sales_dashboard"
echo "     Username: postgres"
echo "     Password: SecurePassword123!"

echo -e "\n${YELLOW}Configuration Files Backed Up:${NC}"
echo "  • $PG_CONF.backup"
echo "  • $PG_HBA.backup"

echo -e "\n${GREEN}Done!${NC}\n"
