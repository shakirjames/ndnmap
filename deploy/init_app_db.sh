#!/usr/bin/env bash
# This script initializes a MySQL database.
#
# Author: Shakir James <shak@shakfu.com>
# Based on Cosmin Stejerean talk at PyCon 2011.

set -e # die on any error

SCRIPT_NAME=$0

usage() {
    cat <<EOF
Usage: $SCRIPT_NAME OPTIONS

OPTIONS
    Required:
        -d DB_NAME  the database name
    Optional:
        -l URL      url sql dump tarball to load into the database
        -u DB_USER  the database user. Defaults to DB_NAME
        -p DB_PASS  the database password. Defaults to autogenerate.
EOF
}

getargs() {
    while getopts "hd:u:p:l:" op ; do
        case $op in
            h) usage; exit 0 ;; 
            d) DB_NAME="$OPTARG";;
            u) DB_USER="$OPTARG";;
            p) DB_PASS="$OPTARG";;
            l) URL="$OPTARG";;
            *) die "unknown option $opt" 10
        esac
    done
    if [ -z "$DB_NAME" ]; then
        die "DB_NAME is required" 2
    fi
    if [ -z "$DB_USER" ]; then
        DB_USER="$DB_NAME"
    fi
    if [ -z "$DB_PASS" ]; then
        DB_PASS=`head -c 100 /dev/urandom | md5sum | awk '{print substr($1,1,15)}'`
    fi
}

die() {
    message=$1
    error_code=$2

    echo "$SCRIPT_NAME: $message" 1>&2
    usage
    exit $error_code
}


create_mysql_database() {
    cat <<EOF | mysql --user=root
CREATE DATABASE IF NOT EXISTS $DB_NAME;
GRANT ALL PRIVILEGES  on $DB_NAME.* to '$DB_USER'@'%' identified by '$DB_PASS';
EOF
    # create options file
    touch ~/.my.cnf
    chmod 600 ~/.my.cnf
}

open_external_port() {
    cat <<EOF | sudo tee /etc/mysql/conf.d/listen_externally.cnf
[mysqld]
    bind-address = 0.0.0.0
EOF
    sudo /etc/init.d/mysql restart
}

load_sql() {
    if [ -z "$URL" ]; then 
        echo "No url specified. Creating an empty database."
        return 0 
    fi 
    wget $URL -O dump.sql.tgz
    tar zxvf dump.sql.tgz
    mysql --user=$DB_USER --password=$DB_PASS $DB_NAME < dump.sql
}

print_mysql_config() {
    PUBLIC_DNS=`curl http://169.254.169.254/latest/meta-data/public-hostname 2>/dev/null`
    cat <<EOF
Database: $DB_NAME
Username: $DB_USER
Password: $DB_PASS

EOF
}


getargs "$@"
create_mysql_database
load_sql
#open_external_port
print_mysql_config
