#!/usr/bin/env bash

# Copyright (c) 2012 Shakir James and Washington University in St. Louis.
# See LICENSE for details.

# This script transfers bits to the ndn web app.
SCRIPT_NAME=$0

NDNMAP_PATH='bw'

usage() {
    cat <<EOF
Usage: $SCRIPT_NAME OPTIONS

OPTIONS
     -u SITE_URL    Transfer data to SITE_URL
     -n NUM_XFERS   Transfer bits NUM_XFERS time (default=10)
     -i TIME_INT    Wait TIME_INT seconds before sending transfers (default=1)
     -r RX_BITS     Increase rx bits by RX_BITS every NUM_XFERS (default=4000)
     -t TX_BITS     Increase tx bits by TX_BITS every NUM_XFERS (default=2000)
     -l LINKS       Send rx,tx bits updata for LINKS (default="1 2 3") 
     
Example:
    $SCRIPT_NAME -u localhost:8000 -l 1
EOF
}

die() {
    message=$1
    error_code=$2

    echo "$SCRIPT_NAME: $message" 1>&2
    usage
    exit $error_code
}

getargs() {
    while getopts "hu:n:i:t:r:t:l:" opt; do
        case "$opt" in
            u) SITE_URL="$OPTARG" ;;
            n) NUM_XFER="$OPTARG" ;;
            i) TIME_INT="$OPTARG" ;;
            r) RX_BITS="$OPTARG" ;;
            t) TX_BITS="$OPTARG" ;;
            l) LINKS="$OPTARG" ;;
            [?]) die "unknown option $opt" 10 ;;
        esac
    done
    # check required args
    if [ -z "$SITE_URL" ]; then 
        die "SITE_URL is required" 1
    fi 
    if [[ "$SITE_URL" =~ "http://"+ ]] ; then 
        die "Invalid SITE_URL: localhost:8000" 4
    fi

}

setdefaults() {
    if [ -z "$NUM_XFER" ]; then
        NUM_XFER=10
    fi
    if [ -z "$TIME_INT" ]; then
        TIME_INT=.2
    fi
    if [ -z "$RX_BITS" ]; then
        RX_BITS=4000
    fi
    if [ -z "$TX_BITS" ]; then
        TX_BITS=2000
    fi
    if [ -z "$LINKS" ]; then
        LINKS="1 2 3"
    fi
}

http_xfer() {
    for (( n=1; n<=$NUM_XFER; n++ )); do
        t0="$(date +%s)" # NOTE %N not supported on Mac OS X
        for l in $LINKS; do
            #t=$((t0+RANDOM))
            t="$(date +%s)"
            rx=$((n+RX_BITS))
            tx=$((n+TX_BITS))
            # example.com/<link>/<timestamp>/<rx_bits>/<tx_bitd>/            
            set -x
            curl -L http://$SITE_URL/$NDNMAP_PATH/$l/${t}.0/$rx/$tx
            set +x
            t0=$t
        done
        # sleep $TIME_INT
    done
}


getargs "$@"
setdefaults
http_xfer
