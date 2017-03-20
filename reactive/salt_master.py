from charms.reactive import when, when_not, set_state
from charmhelpers.core.hookenv import status_set
from charmhelpers.fetch import apt_install
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from charmhelpers.core import hookenv
import os
import subprocess

@when_not('salt-master.installed')
@when('salt-common.installed')
def install_salt_master():
    status_set('maintenance','installing salt-master')
    apt_install('salt-master')
    status_set('active','')
    set_state('salt-master.installed')

@when_not('ssh-key.generated')
@when('salt-master.installed')
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
    privateKey = keypath+'/id_rsa'
    publicKey = keypath+'/id_rsa.pub'
    try:
        os.mkdir(keypath)
    except OSError as e:
        if e.errno is 17:
          pass
    with open(privateKey,'wb') as file:
        file.write(private_key)
    os.chmod(privateKey,0o600)
    with open(publicKey,'wb') as file:
        file.write(public_key)
    os.chmod(publicKey,0o600)
    print("is_rsa.pub: {}".format(repr(public_key)))
    set_state('ssh-key.generated')

@when('ssh-key.generated')
@when_not('git-cloned')
def pull_repository():
    config = hookenv.config()
    try:
        # TODO: Deal with knownhosts error
        subprocess.call(["ssh-agent bash -c 'ssh-add ./rsa/id_rsa; git clone {} /srv'".format(config['git-repo'])],shell=True)     
    except Exception as e:
        print(e)
    set_state('git-cloned')

