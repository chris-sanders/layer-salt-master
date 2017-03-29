from charms.reactive import when, when_not, set_state, remove_state
from charmhelpers.fetch import apt_install
from charmhelpers.core import hookenv
from charmhelpers.core.host import chownr
from charmhelpers.core.services.base import service_restart
from charmhelpers.core.hookenv import status_set, resource_get, log, unit_public_ip
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
import os
import subprocess
import shutil
import socket

@when_not('salt-master.installed')
@when('salt-common.installed')
def install_salt_master():
    status_set('maintenance','installing salt-master')
    apt_install('salt-master')
    set_state('salt-master.installed')

@when_not('ssh-key.generated')
@when('salt-master.installed')
def generate_ssh_key(): 
    status_set('maintenance','setting rsa keys')
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
        print("Generated RSA key id_rsa.pub: {}".format(repr(public_key)))
    # Correct permissions
    os.chmod(privateKey,0o600)
    os.chmod(publicKey,0o600)
    # Add to ubuntu user
    shutil.copy(privateKey,'/home/ubuntu/.ssh/id_rsa')
    shutil.chown('/home/ubuntu/.ssh/id_rsa',user='ubuntu',group='ubuntu')
    shutil.copy(publicKey,'/home/ubuntu/.ssh/id_rsa.pub')
    shutil.chown('/home/ubuntu/.ssh/id_rsa.pub',user='ubuntu',group='ubuntu')
    set_state('ssh-key.generated')

@when('ssh-key.generated')
@when_not('git-cloned')
@when_not('git-created')
def setup_repository():
    config = hookenv.config()
    if config['git-repo'] is not "":
      pull_repository()
    else:
      create_repository()
    chownr('/srv',owner='ubuntu',group='ubuntu')
    status_set('active','')

def create_repository():
    status_set('maintenance','creating salt repository')
    os.makedirs('/srv/salt/salt-formulas')
    os.makedirs('/srv/pillar')
    subprocess.check_call(["git init /srv"],shell=True)
    set_state('salt-master.ready')
    set_state('git-created')

def pull_repository():
    status_set('maintenance','pulling salt repository')
    config = hookenv.config()
    try:
        os.environ["GIT_SSH_COMMAND"] = "ssh -i $JUJU_CHARM_DIR/rsa/id_rsa -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
        subprocess.check_call(["git clone --recursive {} /srv".format(config['git-repo'])],shell=True)     
        set_state('git-cloned')
    except Exception as e:
        status_set('maintenance','repository not available')
        shutil.rmtree('/srv')
        log("Unable to pull git repository")

@when('git-cloned')
@when_not('conf.written')
def setup_formulas():
    config = hookenv.config()
    formulas = [name for name in os.listdir(config['formula-path']) if os.path.isdir(os.path.join(config['formula-path'],name))] 
    with open('/etc/salt/master.d/file_roots.conf','w') as conf:
        conf.write('''
file_roots:
  base:
    - /srv/salt\n''')
        for directory in formulas:
            conf.write("    - {}\n".format(os.path.join(config['formula-path'],directory)))
    with open('/etc/salt/master.d/auot_accept.conf','w') as conf:
        conf.write("auto_accept: True")    
    service_restart('salt-master')
    set_state('conf.written')
    set_state('salt-master.ready')

@when('salt-master.ready')
@when('saltinfo.unconfigured')
def configure_interface(saltinfo):
    config = hookenv.config()
    if config['use-dns']:
        address = socket.gethostname()
    else:
        address = unit_public_ip()
    port = None
    saltinfo.configure(address,port)

@when('saltinfo.newminion')
def configure_minion(saltinfo):
    target = saltinfo.minion
    subprocess.check_call(["salt \"{}\" state.apply".format(target)],shell=True)     
    remove_state('saltinfo.newminion')

