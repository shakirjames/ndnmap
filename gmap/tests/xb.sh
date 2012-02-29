#!/usr/bin/env bash
#
# Copyright (c) 2011 Shakir James and Washington University in St. Louis.
# All rights reserved
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    3. The name of the author or Washington University may not be used 
#       to endorse or promote products derived from this source code 
#       without specific prior written permission.
#    4. Conditions of any other entities that contributed to this are also
#       met. If a copyright notice is present from another entity, it must
#       be maintained in redistributions of the source code.
#
# THIS INTELLECTUAL PROPERTY (WHICH MAY INCLUDE BUT IS NOT LIMITED TO SOFTWARE,
# FIRMWARE, VHDL, etc) IS PROVIDED BY THE AUTHOR AND WASHINGTON UNIVERSITY 
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED 
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR WASHINGTON UNIVERSITY 
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS INTELLECTUAL PROPERTY, EVEN IF 
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

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
}

setdefaults() {
    if [ -z "$NUM_XFER" ]; then
        NUM_XFER=10
    fi
    if [ -z "$TIME_INT" ]; then
        TIME_INT=1
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
        for l in $LINKS; do
            t="$(date +%s)".0 # no %N on Mac OS X
            rx=$((n*RX_BITS))
            tx=$((n*TX_BITS))
            # example.com/<link>/<timestamp>/<rx_bits>/<tx_bitd>/            
            echo http://$SITE_URL/$NDNMAP_PATH/$l/$t/$rx/$tx
            curl -L http://$SITE_URL/$NDNMAP_PATH/$l/$t/$rx/$tx
        done
        sleep $TIME_INT
    done
}


getargs "$@"
setdefaults
http_xfer
