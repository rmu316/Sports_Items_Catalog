# Linux Server Configuration - Udacity
### Full Stack Web Development ND
_______________________

## About
This project configures on an Apache web server running Ubuntu hosted by Amazon Lightsail
to host my sports catalog app. Here are the technologies this project showcases:
* Apache HTTP Web server which hosts my web app
* Ubuntu 16.04 OS which the server runs on
* Amazon Lighsail, which provides the physical machines which the OS runs on

## How to log on
* From browser:    home.mysportscatalog.com
* From CLI:        ssh -i graderKey.pem grader@34.221.117.246 -p 2200

## Testing
Following the grading rubric for this project
* You (the grader) can log on as: ssh -i graderKey.pem grader@34.221.117.246 -p 2200
* You CANNOT log in as root remotely: ssh root@34.221.117.246 -p 2200 OR ssh -i graderKey.pem root@34.221.117.246 gives error "Permission denied"
* You (the grader) once logged in an use sudo to run cmds to inspects files only readable as root
* The ONLY ports allow for connections are 2200 (for SSH), 80 (for HTTP), and 123 (for NTP). You can verify this with the "sudo ufw status" command:

$ sudo ufw status
status: active

To                         Action      From
--                         ------      ----
2200/tcp                   ALLOW       Anywhere                  
80/tcp                     ALLOW       Anywhere                  
123/tcp                    ALLOW       Anywhere                  
2200/tcp (v6)              ALLOW       Anywhere (v6)             
80/tcp (v6)                ALLOW       Anywhere (v6)             
123/tcp (v6)               ALLOW       Anywhere (v6) 

* Key-based SSH authentication is enforced
* All system packages have been updated to most recent versions. I recently ran "sudo apt-get install" and "sudo apt-get upgrade"
* SSH is hosted on non-default port. Yes, I changed the port from 22 to 2200
* The web server responds on port 80. Easy test is simply to run home.mysportscatalog.com:80 in a browser
* Database server has been configured to serve data. I'm using PostgreSQL with database and user name "catalog". To see it, run the following:

$ sudo su - postgres
postgres@ip-172-26-12-177:~ $ psql catalog
psql (9.5.14)
Type "help" for help.

catalog=# \ds
List of relations
 Schema |      Name       |   Type   |  Owner  
--------+-----------------+----------+---------
 public | user_id_seq     | sequence | catalog
 public | category_id_seq | sequence | catalog
 public | item_id_seq     | sequence | catalog

 * Web server has been configured to serve the Item Catalog application as a WSGI app. Yes, you can find this in the directory
 /var/www/FlaskApp/flaskapp.wsgi


## IP Address
34.221.117.246

## SSH Port
2200

## URL of my web app
http://home.mysportscatalog.com

## Summary of software installed
* PostgreSQL                   :for storing all the web app data in a SQL database)
* Flask                        :for routing the pages on my web app to the appropriate python responses)
* SSH                          :for accessing the remote server from my terminal window, as well as copying files over
* Amazon Route 53              :the DNS web service that maps my domain name (home.mysportscatalog.com) to the server public IP (34.221.117.246)
* WSGI                         :the kind of application which the Apache server runs to execute my web app (sudo apt-get install libapache2-mod-wsgi-py3)

## List of 3rd party resources used
* SSH
* Flask
* PostgreSQL
* Amazon Lightsail
* Amzon Route 53
* mod_wsgi

