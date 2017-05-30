# Satellite-Monitoring
Satellite-monitoring contains simple Ansible playbooks that can be used to perform following tasks:
### Monitor Satellite & Capsule Details
       *System Resources*
            - cpu, Memory, Disk, Network, Turbostat, Numa, IRQ, Load time
       *Satellite processes Memory, cpu, pagefaults, IOPS, IO throuhput*
            - Dynflow, Forman-smartproxy, Mongodb, Passenger, Postgres, Pulp, Puppet-agent, Qpidd, Qpid Dispatch Router, Tomcat,  
       * Satellite Database Operations*
            - Foreman, Candlepin

## Getting Started
Ideally, you need Three hosts to run this project:

1. Ansible Control node (referred to as `Control node` in the rest of this document) is the host from which satellite-monitoring ansible playbooks are run. Could be user laptop
2. Destination node - Ansible playbooks install collectd on below nodes 
    - A Satellite server
    - Capsule servers
3. Monitoring server - Ansible playbooks install below services 
    - Grafana
    - Graphite
    - Carbon 

*Note*

1. You can get away with using one host by optionally choosing to use `Destination node` as the `Control node`.
2. Make sure that the `Control node` can connect to the `Destination node` & `Monitirng Server` via paswordless ssh.

#### On the Control node:

*Supported versions*
- RHEL 6
- RHEL 7

1. git clone this project.

   ```console
     # git clone https://github.com/redhat-performance/satellite-monitoring.git
   ```
   NOTE: Optionally you may utilize the script [control_node_setup.sh] (adhoc-scripts/control_node_setup.sh) to perform step 2 below.  The instructions to use this script are documented in the script itself.
2. Install `ansible` package on the Control node. For RHEL boxes, [access to EPEL] (https://access.redhat.com/solutions/3358) is required.

   ```console
     # yum install -y ansible
   ```
3. Create an inventory file named `inventory` (by copying `ansible/inventory.sample`) and update satellite, capsule, grafana, graphite it as necessary:

  ```console
    # cp conf/hosts.ini.sample conf/hosts.ini
  ```

# To run with raw ansible-playbook commands on commandline

###  To install Collectd on satellite & capsules:

```
$ ansible-playbook --private-key conf/id_rsa -i conf/hosts.ini ansible/collectd-generic.yaml --tags "satellite6"
```

```
$ ansible-playbook --private-key conf/id_rsa -i conf/hosts.ini ansible/collectd-generic.yaml --tags "capsules"
```

### To install graphite server, grafana on Monitoring server:

```
$ ansible-playbook --private-key conf/id_rsa -i conf/hosts.ini ansible/grafana.yaml --tags "grafana"
```

```
$ ansible-playbook --private-key conf/id_rsa -i conf/hosts.ini ansible/graphite.yaml --tags "graphite"
```


### To build graphite dashboards:

```
$ ansible-playbook --private-key conf/id_rsa -i conf/hosts.ini ansible/dashboard-generic.yaml
```

#### If collectd fails to send metrics to your grafana instance

You might wanna check the selinux policies. Try one of the following to counter "Permission Denied" log statement:

```
# setsebool -P collectd_tcp_network_connect 1
```

OR

```
# audit2allow -a
# audit2allow -a -M collectd_t
# semodule -i collectd_t.pp
```

OR

```
# semanage permissive -a httpd_t
```

..or all.

