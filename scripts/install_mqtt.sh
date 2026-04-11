#!/bin/bash

# Install Mosquitto MQTT Broker and Client
echo "Updating package list..."
sudo apt-get update

echo "Installing Mosquitto and Mosquitto Client..."
sudo apt-get install -y mosquitto mosquitto-clients

echo "Enabling Mosquitto service..."
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Configure Mosquitto to allow remote access (anonymous for now, or use password file)
# By default, recent Mosquitto versions bind only to localhost and require auth.
# We will enable anonymous access for this private network setup, or user can configure auth.

CONFIG_FILE="/etc/mosquitto/conf.d/sentinelpi.conf"

echo "Configuring Mosquitto listener on port 1883..."
sudo bash -c "cat > $CONFIG_FILE" <<EOF
listener 1883
allow_anonymous true
EOF

echo "Restarting Mosquitto..."
sudo systemctl restart mosquitto

echo "Mosquitto installation complete."
echo "Status:"
sudo systemctl status mosquitto --no-pager
