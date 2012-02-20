#!/usr/bin/env bash

# This script installs a django application.
#
# NOTES: 
# * see the apache logs for errors: tail /var/log/apache2/${SITE_NAME}_error.log
#
# Author: Shakir James <shak@shakfu.com>
# Based on Cosmin Stejerean talk at PyCon 2011.

SCRIPT_NAME=$0
set -e # die on any error
export DEBIAN_FRONTEND=noninteractive


usage() {
    cat <<EOF
Usage: $SCRIPT_NAME OPTIONS

OPTIONS
    Application:
     -n NAME            application NAME - letters, numbers and underscore
     -g GITREPO         URL of the git repo to clone
     -b BRANCH          git branch name 

    Database:
     -H DB_HOST         database host
     -D DB_NAME         database name: default = \${NAME}
     -U DB_USER         database user: default = \${NAME}
     -P DB_PASS         database password

    Web:
     -w SITE_NAME       SiteName for Apache: default =  \${NAME}.com
     -s STATIC_URL      URL for static assets: default = /static/

    Local:
     -u LOCAL_USER      name of system user to add: defaults to \${NAME}
     -p PROJECT_ROOT    project root: default = /home/\${LOCAL_USER}/\${NAME}
     -f FIXTURE         initial data: default = PROJECT_ROOT/deploy/initial_data.json
EOF
}

die() {
    message=$1
    error_code=$2

    echo "$SCRIPT_NAME: $message" 1>&2
    usage
    exit $error_code
}

check_arg() {
    arg=$1
    if [ -z "${!arg}" ]; then 
        die "$arg is required" 1
    fi
}

getargs() {
    while getopts "hn:g:b:H:D:U:P:w:s:u:p:f:" opt; do
        case "$opt" in
            h) usage; exit 0 ;;
            n) NAME="$OPTARG" ;;
            g) GITREPO="$OPTARG" ;;
            b) BRANCH="$OPTARG" ;;
            H) DB_HOST="$OPTARG" ;;
            D) DB_NAME="$OPTARG" ;;
            U) DB_USER="$OPTARG" ;;
            P) DB_PASS="$OPTARG" ;;
            w) SITE_NAME="$OPTARG" ;;
            s) STATIC_URL="$OPTARG" ;;
            u) LOCAL_USER="$OPTARG" ;;
            p) PROJECT_ROOT="$OPTARG" ;;
            f) FIXTURE="$OPTARG" ;;
            [?]) die "unknown option $opt" 10 ;;
        esac
    done
    # check required args
    check_arg "NAME"
    check_arg "GITREPO"
}

setdefaults() {
    if [ -z "$DB_NAME" ]; then
        DB_NAME="$NAME"
    fi
    if [ -z "$DB_HOST" ]; then
        DB_HOST="localhost"
    fi
    if [ -z "$DB_USER" ]; then
        DB_USER="$NAME"
    fi
    if [ -z "$DB_PASS" ]; then
        DB_PASS=`head -c 100 /dev/urandom | md5sum | awk '{print $1}'`
    fi
    if [ -z "$SITE_NAME" ]; then
        SITE_NAME="${NAME}.com"
    fi
    if [ -z "$STATIC_URL" ]; then
        STATIC_URL="/static/"
    fi
    if [ -z "$ADMIN_EMAIL" ]; then
        ADMIN_EMAIL="alerts@${SITE_NAME}"
    fi
    if [ -z "$LOCAL_USER" ]; then
        LOCAL_USER="$NAME"
    fi
    if [ -z "$PROJECT_ROOT" ]; then
        PROJECT_ROOT="/home/$LOCAL_USER/$NAME" 
    fi
    if [ -z "$BRANCH" ]; then
        BRANCH="master" 
    fi
    if [ -z "$FIXTURE" ]; then
        FIXTURE="$PROJECT_ROOT/deploy/initial_data.json" 
    fi
}

update_system() {
    apt-get update && apt-get upgrade -y
}

install_baseline() {
    apt-get install -y build-essential git-core curl
}

install_python() {
    apt-get install -y python python-dev python-pip \
    python-setuptools python-mysqldb python-virtualenv
}

install_webserver() {
    # install apache
    apt-get install -y apache2 libapache2-mod-wsgi 
    # configure apache
    APACHE_LOG_DIR=/var/log/apache2 #fix for Ubuntu 10.04 (Lucid) 
    cat <<EOF | sudo tee /etc/apache2/sites-available/$NAME
<VirtualHost *:80>
    ServerName $SITE_NAME
    ServerAdmin $ADMIN_EMAIL
    LogLevel warn
    ErrorLog ${APACHE_LOG_DIR}/${SITE_NAME}_error.log
    CustomLog ${APACHE_LOG_DIR}/${SITE_NAME}_access.log combined

    WSGIDaemonProcess $NAME user=www-data group=www-data maximum-requests=10000 python-path=/home/$LOCAL_USER/env/lib/python2.6/site-packages
    WSGIProcessGroup $NAME

    WSGIScriptAlias / $PROJECT_ROOT/deploy/app.wsgi

    <Directory $PROJECT_ROOT/deploy>
        Order deny,allow
        Allow from all
    </Directory>

</VirtualHost>
EOF

}

activate_webserver() {
    sudo a2dissite default
    sudo a2ensite $NAME
    sudo /etc/init.d/apache2 reload
}

bootstrap_project() {
    pip install virtualenv    
    adduser --system --disabled-password --disabled-login $LOCAL_USER
    sudo -u $LOCAL_USER virtualenv /home/$LOCAL_USER/env
    sudo -u $LOCAL_USER mkdir $PROJECT_ROOT    
}

install_project() {
    # clone from git hub
    # assumes read-only repo
    sudo -u $LOCAL_USER mkdir -p /home/$LOCAL_USER/.ssh    
    sudo -u $LOCAL_USER ssh-keyscan -H github.com | sudo -u $LOCAL_USER tee /home/$LOCAL_USER/.ssh/known_hosts
    sudo -u $LOCAL_USER git clone -b $BRANCH $GITREPO $PROJECT_ROOT
    sudo -u $LOCAL_USER /home/$LOCAL_USER/env/bin/pip install -r $PROJECT_ROOT/deploy/requirements.txt
}

configure_local_settings() {
    local debug="False"
    if [[ "$BRANCH" =~ "develop" ]]; then
       debug="True"
    fi 
    cat <<EOF | sudo -u $LOCAL_USER tee $PROJECT_ROOT/settings_local.py
DEBUG = $debug
TEMPLATE_DEBUG = $debug
SERVE_MEDIA = False

DATABASES = {
    'default': {
       'ENGINE': 'django.db.backends.mysql',
       'NAME': '$DB_NAME',
       'USER': '$DB_USER',
       'PASSWORD': '$DB_PASS',
       'HOST': '$DB_HOST',
    }
}

MEDIA_URL = '$STATIC_URL/'
STATIC_URL = '$STATIC_URL/'
ADMIN_MEDIA_PREFIX = '$STATIC_URL/admin/'
TEMPLATE_DIRS = ('$PROJECT_ROOT/templates', )
EOF
}

django_syncdb() {
    sudo -u $LOCAL_USER /home/$LOCAL_USER/env/bin/python $PROJECT_ROOT/manage.py syncdb --noinput
    if [ -f "$FIXTURE" ]; then
        # load initial data
        sudo -u $LOCAL_USER /home/$LOCAL_USER/env/bin/python $PROJECT_ROOT/manage.py loaddata $FIXTURE
    fi 
}

django_print_info() {
    PUBLIC_DNS=`curl http://169.254.169.254/latest/meta-data/public-hostname 2>/dev/null`
    cat <<EOF
** To view the app you just installed, point your browser to **

http://${PUBLIC_DNS}/

EOF
}


getargs "$@"
setdefaults

update_system
install_baseline
install_python
install_webserver
 
bootstrap_project
install_project
configure_local_settings
activate_webserver

django_syncdb
django_print_info