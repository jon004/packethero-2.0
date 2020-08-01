# packethero-2.0
by Tanisha Babic, Jonathan Muniz-Murguia, Darien Cruz-Nguyen

------------------------------

# Description

In this game, the player must put together a song that is broken down into 10-second clips.
They can listen to the clips as often as they want, but once the game starts, they have 10 seconds
to submit the clips in the correct order. If a clip is submitted out of order or the player fails to 
submit a frame in 10 seconds, they lose and must start over. To start, a player needs a username, 
team name, and room number. They can play alone or as a team. There is a chat provided for players to 
communicate with their team or with the room's admin. To learn more about how to play and about admin 
controls, login and click on the `?`.

------------------------------

# Admin Instructions

To login as admin you input an admin token into the teamname field. 

To get your admin tokens go to file `server.py` line `24`.

The default list of admin tokens should look like: 

- `adminTokens = ['20foUWSN', '9AhXLJJB', 'kXsMmuID', 'iipcCtCw', 'BDqprSyj']`.

CHANGE THESE VALUES BEFORE RUNNING THE SERVER SINCE THIS DOCUMENT IS PUBLIC (only numbers and letters)

You are able to modify this array of tokens without breaking the code.

**IF** the code does break after modifing these values, the following link can help you fix it

- https://www.w3schools.com/python/python_arrays.asp

------------------------------

# Google Cloud Platform Set Up

## VM Setup ##

**Step 1: GCP Project Set Up**

**Before advancing**, be sure to work on an account with adequate credits!

Create project
- Click -> project drop down menu (3rd button in header)
- Click -> NEW PROJECT

Open the project and load compute engine
- Click -> Navigation Menu (1st button in header)
- Click -> Compute Engine *
> *Note: Compute Engine set up automatically starts after clicking on it

Wait for Compute Engine to finish setting up
(To see set up statuses click on 3rd to last button in header)



**Step 2: Creating a New VM Instance**

Make sure you're still in the project's compute engine

- Click -> Create Instance

Instance Values to Change:

    Name: packethero
    Firewall: Check -> "Allow HTTP traffic" and "Allow HTTPS traffic"
    Boot Disk: Debian GNU/Linux 10 (buster)


## DB Table ##

**Step 3: Creating a MySQL Database Instance**

Enable SQL Admin API and create a DB Instance
- Click ->  Cloud SQL Admin API
- Click ->  Enable
- Search -> Cloud SQL
- Click ->  Cloud SQL (THE ONE WITH THE SHOPPING CART NOT THE ONE WITH THE API LOGO)
- Click ->  GO TO CLOUD SQL
- Click ->  CREATE INSTANCE
- Click ->  Choose MySQL

Instance Values to Change:

    Instance ID: packethero-db
    Root password: Click on Generate (copy and save the password somewhere you can access later)

- Click -> Create
- Wait... (When the green check mark appears next to Instance ID)
- Click -> packethero-db
- Ctrl + f -> Connect using Cloud Shell
- Open up the terminal (5th to last button in header)
- Wait... (When the terminal loads, try refreshing page if it takes a while)


**Step 4: Creating Database Tables**

After your terminal has loaded, access your database

You can do this in the terminal with this command
    
    gcloud sql connect packethero-db --user=root --quiet

- Make sure your database name matches
- Hit Enter
- Wait...
- Enter Password

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
      

## Packages ##
**Step 5: Installing Packages and Downloading Code**

Connect to the VM Instance through ssh:
- Click -> Navigation Menu (1st button in header)
- Click -> Compute Engine
- Click -> SSH (Under the connect column of the table that loaded)
- Wait for the terminal to load

Install the following packages, make sure you are in `~/` throught the set up from this point on

Running `cd ~/` gets you here if you're not already there

Run these commands:

    sudo apt-get -y update
    sudo apt-get -y upgrade
    sudo apt-get -y install python3 python3-pip python3-dev nginx git-all ufw
    git clone https://github.com/yonJM1267/packethero-2.0.git
    sudo pip3 install flask flask_socketio flask_login flask_wtf wtforms eventlet sqlalchemy flask_sqlalchemy pymysql uwsgi

## DB Connection ##

**Step 6: Configuring Database User Creds**

You will continue working in the terminal you opened in **Step 5**

Enter `nano ~/packethero-2.0/apps.py` to open the text editor

Leave this window open and go back to GCP and create a user account for your database
- Click -> Navigation Menu (1st button in header)
- Click -> SQL
- Click -> packethero-db
- Click -> Users
- Click -> Create user account

Variables to Change:

    Username: Make one
    Password: Make one
    Host name: select -> Allow any host (%)

Now whitelist your website's IP to give it access to the database
- Click -> CREATE
- Click -> Connections -> + Add Network
- Add the IP of the VM you created in Step 2 and click save
   
**Step 7: Configuring Code Variables**

Go back to the terminal go into `~/packethero-2.0/apps.py` to edit some variables

    nano ~/packethero-2.0/apps.py

Replace the placeholders for `username` and `passw` with the credentials you created in step 6

Replace the `SECRET_KEY` placeholder with a random alphanumerical string

(ex: `SECRET_KEY='A942AF74DD7FFA84FB96973515BEE'`)

Replace the placeholder for `host` with your DB's IP, save the file and exit the editor
- Click (back on GCP) -> Overview
- Copy -> Public IP address of your database
- Ctrl + S -> This command saves the changes
- Exit the text editor with Ctrl + x
    
## Nginx ##

**Step 8: Configuring Nginx**

Enter the following commands

    sudo ufw allow 'Nginx Full'
    sudo mkdir /var/log/nginx/packethero
    sudo mv ~/packethero-2.0/packethero /etc/nginx/sites-available/packethero
    sudo nano /etc/nginx/sites-available/packethero

IMPORTANT: Change the domain name to match yours

Example:

    server {
        ...
        server_name packethero.baycyber.net; # change domain
        ...
    }

- Ctrl + s -> saves file
- Ctrl + x -> exits text editor

Run the following commands

    sudo ln -s /etc/nginx/sites-available/packethero /etc/nginx/sites-enabled/packethero
    sudo service nginx configtest
    sudo service nginx restart

## SSL Cert ##

**Step 9: SSL Cert**

You will have connection errors without SSL Cert 

It's important to do this step before accessing the website

Still in the terminal

Run the following commands:

    sudo apt-get -y install certbot python-certbot-nginx
    sudo certbot --nginx
    or
    sudo certbot --nginx --register-unsafely-without-email

Pick `Redirect` when prompted

## Running your Website ##

**Step 10: How to run your server**

Do once:
    
    sudo chmod +x ~/packethero-2.0/run.sh
    sudo mv ~/packethero-2.0/run.sh ~/run.sh

Next, goto the top of this document and read the Admin Instructions section to learn how get your admin tokens.

After you modify the admin token array, you can start the server by running `./run.sh` when you are on `~/`

You should now be able to access the website

## Helpfull Links ##

SSL Cert: https://certbot.eff.org/lets-encrypt/debianbuster-nginx

Nginx-SocketIO: https://github.com/miguelgrinberg/Flask-SocketIO/issues/826

SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/#connection-uri-forma
