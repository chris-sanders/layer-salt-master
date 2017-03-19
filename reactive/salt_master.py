from charms.reactive import when, when_not, set_state
from charmhelpers.core.hookenv import status_set
from charmhelpers.fetch import apt_install
import subprocess

@when_not('salt-master.installed')
@when('salt-common.installed')
def install_layer_salt_master():
    status_set('maintenance','installing salt-master')
    apt_install('salt-master')
    #subprocess.call(['sudo apt-get install salt-master -y'],shell=True)

    status_set('active','')
    set_state('salt-master.installed')
