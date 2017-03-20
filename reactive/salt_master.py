from charms.reactive import when, when_not, set_state
from charmhelpers.core.hookenv import status_set
from charmhelpers.fetch import apt_install
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
import os

@when_not('salt-master.installed')
@when('salt-common.installed')
def install_salt_master():
    status_set('maintenance','installing salt-master')
    apt_install('salt-master')
    status_set('active','')
    set_state('salt-master.installed')

@when_not('ssh-key.generated')
def generate_ssh_key(): 
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=4096)
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption())
    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH)
    keypath = './rsa'
    try:
        os.mkdir(keypath)
    except OSError as e:
        if e.errno is 17:
          pass
    with open(keypath+'/id_rsa','wb') as file:
        file.write(private_key)
    with open(keypath+'/id_rsa.pub','wb') as file:
        file.write(public_key)
    print("is_rsa.pub: {}".format(repr(public_key)))
    set_state('ssh-key.generated')

