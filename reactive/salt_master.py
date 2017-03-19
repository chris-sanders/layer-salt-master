from charms.reactive import when, when_not, set_state
import subprocess

@when_not('salt-master.installed')
@when('salt-common.installed')
def install_layer_salt_master():
    subprocess.call(['sudo','apt install','salt-master'])
    set_state('salt-master.installed')
