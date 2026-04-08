import sys
import logging
from subprocess import Popen, PIPE, STDOUT
import os

import xmpp


stdout_handler = logging.StreamHandler(stream=sys.stdout)
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=[stdout_handler]
)


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
    argv = sys.argv[1:]
    if argv[0] == "--debug":
        debug = True
        argv = argv[1:]
    else:
        debug = False
    # HACK: nixos wrappers seem to mess up string parsing,
    # manually rebuild broken strings
    cmd = []
    curr_word = []
    for word in argv:
        curr_word.append(word)
        if not curr_word[0].startswith('"'):
            cmd.append(" ".join(curr_word))
            curr_word = []
            continue
        if curr_word[0].startswith('"') and curr_word[-1].endswith('"'):
            cmd.append(" ".join(curr_word))
            curr_word = []
            continue
    if curr_word:
        print("FATAL: UNCLOSED STRING IN ARGUMENTS")
        print(sys.argv)
        exit(1)
    return debug, cmd

def main():
    jid, peer_jid, password = _get_credentials()
    debug, cmd = _parse_args()
    jid = xmpp.protocol.JID(jid)
    connection = xmpp.Client(server=jid.getDomain(), debug=debug)
    connection.connect()
    connection.auth(
        user=jid.getNode(), password=password, resource=jid.getResource())
    # https://stackoverflow.com/a/12471855
    cmd = ["stdbuf", "-oL"] + cmd
    if debug:
        logging.info(f"Running command {cmd}")
    with Popen(
            cmd, stdout=PIPE, stderr=STDOUT,
            bufsize=1, close_fds=True, text=True,
            ) as proc:
        with proc.stdout:
            for line in iter(proc.stdout.readline, ""):
                if debug:
                    logging.info(line)
                connection.send(
                    xmpp.protocol.Message(to=peer_jid, body=line))

if __name__ == "__main__":
    main()