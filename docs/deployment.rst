Deploying ExoScope
==================

One-Time Setup
--------------

#. Set up a fresh Linux machine, with a user who can `sudo`, and install `openssh-server`
#. Create a Chef Node configuration for the target machine in the `nodes` directory (e.g. `cp nodes/example.json nodes/192.168.1.15.json`)
#. Bootstrap chef-solo on the server `fix node:192.168.1.15 deploy_chef`

Note: You should also install Chef locally so LittleChef can find the `knife` command.  Instructions can be found at the `OpsCode website`_

.. _OpsCode website: http://wiki.opscode.com/display/chef/Workstation+Setup