#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    coinrpc
    ~~~~~

    :copyright: (c) 2014 by Halfmoon Labs
    :license: MIT, see LICENSE for more details.
"""

from bitcoinrpc.authproxy import AuthServiceProxy
from commontools import log, error_reply


# ---------------------------------------
class BitcoindClient(object):

    def __init__(self, server, port, user, passwd,
                 use_https=True, passphrase=None):

        self.passphrase = passphrase
        self.server = server

        if use_https:
            http_string = 'https://'
        else:
            http_string = 'http://'

        self.obj = AuthServiceProxy(http_string + user + ':' + passwd +
                                    '@' + server + ':' + str(port))

    def __getattr__(self, name):
        """ changes the behavior of underlying authproxy to return the error
            from bitcoind instead of raising JSONRPCException
        """
        func = getattr(self.__dict__['obj'], name)
        if callable(func):
            def my_wrapper(*args, **kwargs):
                try:
                    ret = func(*args, **kwargs)
                except JSONRPCException as e:
                    return e.error
                else:
                    return ret
            return my_wrapper
        else:
            return func

    # -----------------------------------
    def blocks(self):

        reply = self.obj.getinfo()

        if 'blocks' in reply:
            return reply['blocks']

        return None

    # -----------------------------------
    def unlock_wallet(self, timeout=120):

        try:
            info = self.obj.walletpassphrase(self.passphrase, timeout)

            if info is None:
                return True
        except:
            pass

        return False

    # -----------------------------------
    def sendtoaddress(self, bitcoinaddress, amount):

        self.unlock_wallet()

        try:
            # ISSUE: should not be float, needs fix
            status = self.obj.sendtoaddress(bitcoinaddress, float(amount))
            return status
        except Exception as e:
            return error_reply(str(e))

    # -----------------------------------
    def validateaddress(self, bitcoinaddress):

        try:
            status = self.obj.validateaddress(bitcoinaddress)
            return status
        except Exception as e:
            return error_reply(str(e))

    # -----------------------------------
    def importprivkey(self, bitcoinprivkey, label='import', rescan=False):

        self.unlock_wallet()

        try:
            status = self.obj.importprivkey(bitcoinprivkey, label, rescan)
            return status
        except Exception as e:
            return error_reply(str(e))

    # -----------------------------------
    def sendtousername(self, username, bitcoin_amount):

        # Step 1: get the bitcoin address
        from coinrpc import namecoind
        data = namecoind.get_full_profile('u/' + username)

        try:
            bitcoin_address = data['bitcoin']['address']
        except:
            bitcoin_address = ""

        reply = {}

        # Step 2: send bitcoins to that address
        if bitcoin_address != "":

            if self.unlock_wallet():

                # send the bitcoins
                # ISSUE: should not be float, needs fix
                info = self.sendtoaddress(bitcoin_address,
                                          float(bitcoin_amount))

                if 'status' in info and info['status'] == -1:
                    return error_reply("couldn't send transaction")

                reply['status'] = 200
                reply['tx'] = info
                return reply

        return error_reply("couldn't send BTC")
