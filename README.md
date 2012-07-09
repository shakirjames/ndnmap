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
    
Clone `ndnmap`.

    git clone https://shakfu@github.com/shakfu/ndnmap.git
    cd ndnmap

Install the packages in ``deploy/requirements.txt``.

  * ``pip`` (and optionally [virtualenv][1]) simplifies the process

        sudo easy_install -U pip # requires setuptools
        pip install -r deploy/requirements.txt
        


Obtain a [key for the Google maps API][2] and enter the API key in
`ndnmap/settings.py`:

    # API key for the Google Maps applications
    GMAP_API_KEY='XXX'

Local Server
----------------

In `ndnmap` dir, run
    
    ./manage.py runserver
    
Open the home page in your browser: http://localhost:8000/


EC2 Deployment
--------------

In the [AWS Management Console][3],
  
  * create a `webserver` EC2 security group that allows HTTP access (port 80).
  * create a S3 bucket, for example `ndnmap-media-<your name>` (for static files).

In `ndnmap/settting.py`, change `AWS_STORAGE_BUCKET_NAME` to your S3 bucket

[Fabric][4] allow us to automate the install of 
a LAMP (Linux Apache MySQL Python) stack on EC2. 

The ndnmap fab file (fabric script) provides a set of admin task.
See the list of admin tasks:

    fab --list 
    
The following assumes you have set up [upload your personal ssh keys to EC2][5].
If you are using  an ssh keypair from amazon, include it as a parameter
    
    fab -i EC2KEYPAIR
    
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
Other relevant but optional settings in `ndnmap/settings.py` follow.

    # Show 0 bandwidth if time since last update > GMAP_LINK_ALIVE_INTERVAL (s)
    GMAP_LINK_ALIVE_INTERVAL = 10 
    
    # Update bandwidth on map every GMAP_BW_UPDATE_INTERVAL (s)
    GMAP_BW_UPDATE_INTERVAL = 0.5
    
    # Store static file in S3 bucket
    AWS_STORAGE_BUCKET_NAME = 'ndnmap-media-<your name>'
    

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

    fab reset

[1]: http://mathematism.com/2009/07/30/presentation-pip-and-virtualenv/
[2]: https://developers.google.com/maps/documentation/javascript/tutorial#api_key
[3]: http://console.aws.amazon.com/
[4]: http://fabfile.org/
[5]: http://alestic.com/2010/10/ec2-ssh-keys