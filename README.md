# packethero-2.0

## Google Cloud Platform Set Up ##

**Step 1: GCP Project Set Up**

Create project
- Click -> project drop down menu (3rd button in header)
- Click -> NEW PROJECT

Open the project and load compute engine
- Click -> Navigation Menu (1st button in header)
- Click -> Compute Engine *
> note: Compute Engine set up automatically starts after clicking on it

Wait for Compute Engine to finish setting up
(To see set up statuses click on 3rd to last button in header)


Step 2: Creating a New VM Instance
Make sure you're still in the project's compute engine
Click -> Create Instance
Instance Values to Change:
Name: packethero
Firewall: Check -> "Allow HTTP traffic" and "Allow HTTPS traffic"
Boot Disk: Debian GNU/Linux 10 (buster)


Step 3: Creating a MySQL Database Instance
Use the search bar in the header and type: Cloud SQL Admin API
Click -> Cloud SQL Admin API
Click -> Enable
Search -> Cloud SQL
Click -> Cloud SQL (THE ONE WITH THE SHOPPING CART NOT THE ONE WITH THE API LOGO)
Click -> GO TO CLOUD SQL
Click -> CREATE INSTANCE
Click -> Choose MySQL
Instance Values to Change:
    
Instance ID: packethero-db
Root password: Click on Generate (copy and save the password somewhere you can access later)

Click -> Create
Wait...
(until green check mark appears next to Instance ID)

Click -> packethero-db
Ctrl + f -> Connect using Cloud Shell
Open up the terminal (5th to last button in header)
Wait...
(until terminal loads, try refreshing page if it takes a while)


# DB Table
Step 4: Creating Database Tables
After your terminal has loaded
Type: gcloud sql connect packethero-db --user=root --quiet
Make sure your database name matches
Hit Enter
Wait...
Enter Password
Copy and Paste the following, hit enter, and then close the terminal
    
CREATE DATABASE packethero;
USE packethero;
CREATE TABLE gamers (
id INT NOT NULL UNIQUE AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(200) NOT NULL,
teamname VARCHAR(200) NOT NULL,
room VARCHAR(200) NOT NULL,
admin INT NOT NULL,
session VARCHAR(200) NOT NULL,
song VARCHAR(200) NOT NULL
);
QUIT;
      

# Packages
Step 5: Installing Packages and Downloading Code
Click -> Navigation Menu (1st button in header)
Click -> Compute Engine
Click -> SSH
(Under the connect column of the table that loaded)
Wait for the terminal to load
Copy Paste the following:

sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y install python3 python3-pip python3-dev nginx git-all ufw
git clone https://github.com/yonJM1267/packethero-2.0.git
sudo pip3 install flask flask_socketio flask_login flask_wtf wtforms eventlet sqlalchemy flask_sqlalchemy pymysql uwsgi

Part 4: DB Connection
Step 6: Configuring Database User Creds
You will continue working in the terminal you opened in Part 3
Enter -> nano packethero-2.0/apps.py
You'll be editing this file later
    
Leave this window open and go back to GCP
Click -> Navigation Menu (1st button in header)
Click -> SQL
Click -> packethero-db
Click -> Users
Click -> Create user account
Variables to Change:
Username: Make one
Password: Make one
Host name: select -> Allow any host (%)
Click -> CREATE
Click -> Connections -> + Add Network
Add the IP of the VM you created in Step 2 and click save
   
Step 7: Configuring Code Variables
Go back to the terminal and edit the following variables
username, passw
Replace their placeholders with the credentials you just created in GCP
Replace the SECRET_KEY placeholder with a random alphanumerical string
(ex: SECRET_KEY='A942AF74DD7FFA84FB96973515BEE')
Ctrl + S -> This command saves the changes

Go back to GCP (still in SQL page)
Click -> Overview
Copy -> Public IP address 
Replace the Host variable's placeholder with this Connection Name and save the file (ctrl + s)
Exit the text editor with Ctrl + x
    
Part 5: Nginx
Step 8: Configuring Nginx
Enter the following commands
sudo ufw allow 'Nginx Full'
sudo mkdir /var/log/nginx/packethero
    
Enter -> sudo nano /etc/nginx/sites-available/packethero
Paste the following and save the file
server {

listen 80;
server_name domain-placeholder.com;

access_log /var/log/nginx/packethero/access.log;
error_log /var/log/nginx/packethero/error.log;

proxy_connect_timeout       605;
proxy_send_timeout          605;
proxy_read_timeout          605;
send_timeout                605;
keepalive_timeout           605;


location / {

proxy_http_version 1.1;

proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
proxy_set_header Host $host;
proxy_set_header X-Real-Ip $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Port $server_port;

proxy_read_timeout 86400s;

proxy_pass http://0.0.0.0:5000;

}

}

IMPORTANT: Replace domain-placeholder.com with your domain
(Example: server_name packethero.baycyber.net;)

Enter the following commands
sudo ln -s /etc/nginx/sites-available/packethero /etc/nginx/sites-enabled/packethero
sudo service nginx configtest
sudo service nginx restart

Part 6: Final Touch ups
Step 9: SSL Cert
Still in the terminal
Run the following commands
sudo apt-get -y install certbot python-certbot-nginx
sudo certbot --nginx
sudo certbot certonly --nginx
(alternative: sudo certbot certonly --nginx --register-unsafely-without-email)
sudo certbot renew --dry-run
  
Step 10: How to run your server
Enter -> sudo python3 packethero-2.0/server.py

Usefull Links:
  SSL Cert: https://certbot.eff.org/lets-encrypt/debianbuster-nginx
  Nginx:
  SQLAlchemy:
  
