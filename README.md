ndnmap web app
==============

This web app displays a geographic map of the NDN testbed with real-time 
bandwidth data.
 

Installation
------------
Install Boto.

    git clone https://github.com/boto/boto.git
    cd boto
    python setup.py install

Set environment variables with your AWS credentials (in `~/.bashrc`).

    export AWS_ACCESS_KEY_ID:  AWS Access Key ID
    export AWS_SECRET_ACCESS_KEY:  AWS Secret Access Key
    # export EC2_KEYPAIR=shak # optional

In the [AWS Management Console](http://console.aws.amazon.com/),
  
  * create a `webserver` EC2 security group that allows HTTP access (port 80).
  * create a S3 bucket name `ndnmap-media` (for static files).
    
Clone `ndnmap`.

    git clone https://shakfu@github.com/shakfu/ndnmap.git
    cd ndnmap



Deployment
----------

Start an EC2 instance

    fab start
    
Install the `ndnmap` Django application on instance.
    
    fab deploy


Shut down the EC2 instances

    fab kill
    

Conventions
-----------

The routers report transmit (tx) and receive (rx) bits via an HTTP request:

    example.com/bw/<link_id>/<time>/<rx_bits>/<tx_bytes>/

Field descriptions

  * `link_id` (integer) link identifier 
  * `time` (interger) timestamp (seconds since the epoch)
  * `rx_bits` (integer) number of bits received (monotonically increasing)
  * `tx_bits` (integer) number of bits transmitted (monotonically increasing)
  
Settings
--------
In the `ndnmap/settings.py`, there are two settings:

    
    # Show 0 bandwidth if time since last update > GMAP_LINK_ALIVE_INTERVAL (s)
    GMAP_LINK_ALIVE_INTERVAL = 10 
    
    # Update bandwidth on map every GMAP_BW_UPDATE_INTERVAL (s)
    GMAP_BW_UPDATE_INTERVAL = 0.5


Testing 
-------

### Unittest

Test the `gmap` application.

    fab test

Generate fake data for visual tests:

  1.  Use the admin site: example.com/admin (`user=demo and pass=demo`)
  2.  Run the `xb.sh` scripts: `ndnmap/gmap/test.xb -h `


### Reset database

Remove all `gmap` records from the database

    fab flush

