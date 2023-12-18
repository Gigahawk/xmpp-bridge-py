import argparse
from subprocess import Popen, PIPE, STDOUT
import os

import xmpp

def _get_credentials():
    jid =  os.environ.get("XMPPBRIDGE_JID")
    peer_jid = os.environ.get("XMPPBRIDGE_PEER_JID")
    password = os.environ.get("XMPPBRIDGE_PASSWORD")
    all_present = True
    if not jid:
        print("FATAL: $XMPPBRIDGE_JID is not set")
        all_present = False
    if not peer_jid:
        print("FATAL: $XMPPBRIDGE_PEER_JID is not set")
        all_present = False
    if not password:
        print("FATAL: $XMPPBRIDGE_PASSWORD is not set")
        all_present = False
    if not all_present:
        exit(1)
    return jid, peer_jid, password

def _parse_args():
    parser = argparse.ArgumentParser(
        prog="xmpp-bridge",
        description="Connect command-line programs to XMPP",
        )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    return args



def main():
    jid, peer_jid, password = _get_credentials()
    args = _parse_args()
    jid = xmpp.protocol.JID(jid)
    connection = xmpp.Client(server=jid.getDomain(), debug=args.debug)
    connection.connect()
    connection.auth(
        user=jid.getNode(), password=password, resource=jid.getResource())
    with Popen(args.cmd, stdout=PIPE, stderr=STDOUT) as proc:
        with proc.stdout:
            for line in iter(proc.stdout.readline, b""):
                line = line.decode(errors="backslashreplace")
                connection.send(
                    xmpp.protocol.Message(to=peer_jid, body=line))

if __name__ == "__main__":
    main()