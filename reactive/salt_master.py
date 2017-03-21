from charms.reactive import when, when_not, set_state
from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import status_set, resource_get
from charmhelpers.fetch import apt_install
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
import os
import subprocess
import shutil

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
    keypath = './rsa'
    privateKey = keypath+'/id_rsa'
    publicKey = keypath+'/id_rsa.pub'
    # Create rsa folder
    try:
        os.mkdir(keypath)
    except OSError as e:
        if e.errno is 17:
          pass

    # Get or generate keys
    private_path = resource_get('private-key')
    public_path = resource_get('public-key')
    if private_path and public_path:
        shutil.copy(private_path,privateKey)
        shutil.copy(public_path,publicKey)
    else:
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
        with open(privateKey,'wb') as file:
            file.write(private_key)
        with open(publicKey,'wb') as file:
            file.write(public_key)
        print("is_rsa.pub: {}".format(repr(public_key)))
    os.chmod(privateKey,0o600)
    os.chmod(publicKey,0o600)
    set_state('ssh-key.generated')

@when('ssh-key.generated')
@when_not('git-cloned')
def pull_repository():
    config = hookenv.config()
    try:
        os.environ["GIT_SSH_COMMAND"] = "ssh -i $JUJU_CHARM_DIR/rsa/id_rsa -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
        subprocess.call(["git clone {} /srv".format(config['git-repo'])],shell=True)     
    except Exception as e:
        print(e)
    set_state('git-cloned')

