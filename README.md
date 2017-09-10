# Overview

This charm provides [salt-master][salt]. This is server portion of saltstack and is intended to be related to the 
[salt-minion charm][charm-salt-minion] to operate in the Salt Agent configuration.

# Usage

To deploy:

    juju deploy cs:~chris.sanders/salt-master

You can then juju ssh to the unit and configure your pillar and salt formulas in /srv

    juju ssh salt-master/0
    cd /srv

Note the standard ubuntu user will be configured with RSA keys for pushing and pulling your repository. 
Salt requires you run commands as root, when executing be sure to use sudo. Ex:

    sudo salt '*' state.apply

## Scale out Usage

This charm has not been written to setup multiple masters at this time.

## Known Limitations and Issues

 * Adding / configuring salt-formulas after install
 * Apply salt states on demand not just on minion join
 * Support multiple master
 * Agentless configuration

# Configuration

Note you should set the option 'use-dns' to True unless you use the interface and address options to provide a 
static DHCP address.  The address or fqdn will be provided to salt-minions based on this option and does 
not currently update if changed.

During install this charm expects to have access to pull your salt repository. If you are not 
providing RSA keys (see below) a pair will be generated. You can add the public key to your repository 
by checking 'juju debug-log' for the public key or using 'juju ssh' to find the key in the ubuntu user's .ssh folder.

# Resources

By default this charm will setup an empty git repository and generate RSA keys for you to push to a private 
repository. If you want to use an existing repository or keys you can provide resources which this charm will use.

Two resources are available "public-key" and "private-key". Note the charm store ships with blank dummy keys as 
it does not allow optional resources. If not present during install you will need to add them and resolve the install 
error to access your private repository. If you do not provide keys a public and private key will be generated for you. 
An example of adding keys and resolving install errors is below.

    juju attach salt-master private-key=./rsa/id_rsa 
    juju attach salt-master public-key=./rsa/id_rsa.pub
    juju resolved salt-master/0

Starting in juju 2.2.3 resources can be attached in a bundle.
    salt-master:
      resources:
        private-key: "./my-private-key"
        public-key: "./my-public-key"

# Contact Information

## Upstream Project Name

  - https://github.com/chris-sanders/layer-salt-master
  - https://github.com/chris-sanders/layer-salt-master/issues
  - email: sanders.chris@gmail.com

[salt]: https://saltstack.com/salt-open-source/ 
[charm-salt-minion]: https://jujucharms.com/u/chris.sanders/salt-minion
