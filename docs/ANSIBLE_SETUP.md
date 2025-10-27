# Ansible Infrastructure Management

This guide covers the Ansible setup for managing Notarius infrastructure across different environments (local, staging, production).

## Overview

Ansible is used for:
- **Infrastructure provisioning** and configuration
- **Application deployment** across environments
- **Security hardening** and compliance
- **Monitoring setup** and maintenance
- **Backup and recovery** automation

## Architecture

### Inventory Structure

```
ansible/
├── inventory/
│   └── hosts.yml          # Server inventory
├── playbooks/
│   ├── site.yml           # Main deployment playbook
│   ├── deploy-local.yml   # Local environment
│   ├── deploy-staging.yml # Staging environment
│   └── deploy-production.yml # Production environment
└── roles/
    ├── common/            # Common system setup
    ├── docker/            # Docker installation
    ├── security/          # Security hardening
    ├── monitoring/        # Monitoring setup
    ├── backup/            # Backup automation
    └── notarius/          # Application deployment
```

### Environment Configuration

| Environment | Purpose | Servers | Configuration |
|-------------|---------|---------|---------------|
| Local | Development | localhost | Development settings |
| Staging | Testing | staging-server | Production-like setup |
| Production | Live system | Multiple servers | Full production setup |

## Quick Start

### Prerequisites

1. **Install Ansible:**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install ansible

   # macOS
   brew install ansible

   # Python
   pip install ansible
   ```

2. **Configure SSH access:**
   ```bash
   # Generate SSH key
   ssh-keygen -t rsa -b 4096 -C "ansible@notarius"

   # Copy to servers
   ssh-copy-id user@server-ip
   ```

3. **Update inventory:**
   ```bash
   # Edit ansible/inventory/hosts.yml
   # Add your server details
   ```

### Local Deployment

```bash
# Deploy to local environment
make deploy-local

# Or directly
ansible-playbook ansible/playbooks/deploy-local.yml
```

### Staging Deployment

```bash
# Deploy to staging
make deploy-staging

# Or directly
ansible-playbook ansible/playbooks/deploy-staging.yml -i ansible/inventory/hosts.yml
```

### Production Deployment

```bash
# Deploy to production
make deploy-production

# Or directly
ansible-playbook ansible/playbooks/deploy-production.yml -i ansible/inventory/hosts.yml
```

## Inventory Configuration

### Hosts File Structure

```yaml
# ansible/inventory/hosts.yml
all:
  children:
    local:
      hosts:
        localhost:
          ansible_connection: local
          docker_compose_env: development

    staging:
      hosts:
        staging-server:
          ansible_host: staging.notarius.com
          ansible_user: ubuntu
          ansible_ssh_private_key_file: ~/.ssh/notarius-staging.pem
          environment: staging

    production:
      hosts:
        prod-web-1:
          ansible_host: web1.notarius.com
          ansible_user: ubuntu
          role: web
          environment: production
        prod-api-1:
          ansible_host: api1.notarius.com
          ansible_user: ubuntu
          role: api
          environment: production
```

### Group Variables

```yaml
# Common variables for all hosts
all:
  vars:
    project_name: notarius
    project_dir: /opt/notarius
    backup_dir: /opt/backups
    log_dir: /var/log/notarius
```

## Roles Overview

### Common Role

**Purpose:** Basic system setup and configuration

**Tasks:**
- Install essential packages
- Create directories
- Configure timezone and NTP
- Set hostname

**Files:**
```
roles/common/
├── tasks/main.yml
├── handlers/main.yml
└── vars/main.yml
```

### Docker Role

**Purpose:** Docker installation and configuration

**Tasks:**
- Remove old Docker packages
- Add Docker repository
- Install Docker and Docker Compose
- Configure Docker daemon
- Create Docker networks

**Configuration:**
```yaml
# Docker daemon configuration
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true
}
```

### Security Role

**Purpose:** Security hardening and compliance

**Tasks:**
- Configure UFW firewall
- Install and configure fail2ban
- Set up automatic security updates
- Disable root login
- Configure SSH security

**Security Features:**
- Firewall rules for required ports only
- Fail2ban for brute force protection
- Automatic security updates
- SSH hardening
- Non-root user enforcement

### Monitoring Role

**Purpose:** Monitoring and observability setup

**Tasks:**
- Install Prometheus
- Configure Grafana
- Set up Jaeger tracing
- Configure log aggregation
- Set up alerting

**Monitoring Stack:**
- Prometheus for metrics collection
- Grafana for visualization
- Jaeger for distributed tracing
- ELK stack for log aggregation

### Backup Role

**Purpose:** Automated backup and recovery

**Tasks:**
- Set up database backups
- Configure file backups
- Set up backup rotation
- Test backup restoration
- Monitor backup status

**Backup Strategy:**
- Daily database backups
- Weekly full system backups
- 30-day retention policy
- Automated restoration testing

### Notarius Role

**Purpose:** Application deployment and management

**Tasks:**
- Clone application repository
- Build Docker images
- Deploy services
- Run database migrations
- Configure systemd services
- Health checks

**Deployment Process:**
1. Clone/update code
2. Build Docker images
3. Start services
4. Run migrations
5. Health checks
6. Update systemd services

## Playbooks

### Main Playbook (site.yml)

**Purpose:** Complete system deployment

**Execution:**
```bash
ansible-playbook ansible/playbooks/site.yml
```

**Features:**
- Runs all roles
- Environment-specific configuration
- Health checks
- Deployment summary

### Environment-Specific Playbooks

#### Local Deployment

```bash
ansible-playbook ansible/playbooks/deploy-local.yml
```

**Features:**
- Local development setup
- Development tools
- Hot reloading
- Debug configuration

#### Staging Deployment

```bash
ansible-playbook ansible/playbooks/deploy-staging.yml
```

**Features:**
- Production-like environment
- Full monitoring stack
- Security hardening
- Performance testing

#### Production Deployment

```bash
ansible-playbook ansible/playbooks/deploy-production.yml
```

**Features:**
- High availability setup
- Full security hardening
- Monitoring and alerting
- Backup automation
- Health checks and smoke tests

## Configuration Management

### Environment Variables

**Development:**
```bash
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://user:pass@localhost/db
```

**Production:**
```bash
DEBUG=False
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@prod-db/db
```

### Secrets Management

**Using Ansible Vault:**
```bash
# Encrypt sensitive data
ansible-vault encrypt ansible/group_vars/production/secrets.yml

# Edit encrypted file
ansible-vault edit ansible/group_vars/production/secrets.yml

# Run playbook with vault
ansible-playbook playbook.yml --ask-vault-pass
```

**Example secrets file:**
```yaml
# ansible/group_vars/production/secrets.yml
vault_grafana_admin_password: "secure-password"
vault_database_password: "secure-db-password"
vault_openai_api_key: "sk-..."
```

## Security Best Practices

### SSH Configuration

```yaml
# SSH hardening
- name: Disable root login
  lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^#?PermitRootLogin'
    line: 'PermitRootLogin no'

- name: Disable password authentication
  lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^#?PasswordAuthentication'
    line: 'PasswordAuthentication no'
```

### Firewall Configuration

```yaml
# UFW firewall rules
- name: Allow SSH
  ufw:
    rule: allow
    port: "22"
    proto: tcp

- name: Allow HTTP/HTTPS
  ufw:
    rule: allow
    port: "{{ item }}"
    proto: tcp
  loop:
    - "80"
    - "443"
```

### Fail2ban Configuration

```yaml
# Fail2ban jail configuration
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
```

## Monitoring and Alerting

### Prometheus Configuration

```yaml
# Prometheus scrape configs
scrape_configs:
  - job_name: 'notarius-api'
    static_configs:
      - targets: ['notarius-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### Grafana Dashboards

**Pre-configured dashboards:**
- Application performance
- Database metrics
- System resources
- Business metrics
- Security events

### Alerting Rules

```yaml
# Prometheus alerting rules
groups:
  - name: notarius
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
```

## Backup and Recovery

### Database Backups

```yaml
# Automated database backup
- name: Create database backup
  postgresql_db:
    name: "{{ item }}"
    state: dump
    target: "{{ backup_dir }}/{{ item }}_{{ ansible_date_time.epoch }}.sql"
  loop:
    - notarius_db
    - lexnode_db
    - vault_db
```

### File Backups

```yaml
# Application file backup
- name: Backup application files
  archive:
    path: "{{ project_dir }}"
    dest: "{{ backup_dir }}/notarius_{{ ansible_date_time.epoch }}.tar.gz"
    format: gz
```

### Backup Rotation

```yaml
# Clean old backups
- name: Remove old backups
  find:
    paths: "{{ backup_dir }}"
    age: "{{ backup_retention_days }}d"
    state: absent
```

## Troubleshooting

### Common Issues

**SSH Connection Issues:**
```bash
# Test SSH connection
ansible all -m ping

# Debug SSH
ansible-playbook playbook.yml -vvv
```

**Permission Issues:**
```bash
# Run with sudo
ansible-playbook playbook.yml --become

# Check user permissions
ansible all -m shell -a "whoami"
```

**Service Issues:**
```bash
# Check service status
ansible all -m systemd -a "name=docker state=started"

# View logs
ansible all -m shell -a "journalctl -u notarius -f"
```

### Debugging

**Verbose Output:**
```bash
# Maximum verbosity
ansible-playbook playbook.yml -vvv

# Check mode (dry run)
ansible-playbook playbook.yml --check

# Limit to specific hosts
ansible-playbook playbook.yml --limit production
```

**Log Analysis:**
```bash
# View Ansible logs
tail -f /var/log/ansible.log

# Check system logs
journalctl -u notarius -f
```

## Best Practices

### Playbook Design

1. **Idempotent tasks** - Can be run multiple times safely
2. **Error handling** - Proper error handling and rollback
3. **Modular design** - Reusable roles and tasks
4. **Documentation** - Clear documentation and comments
5. **Testing** - Test playbooks in staging first

### Security

1. **Use Ansible Vault** for sensitive data
2. **Limit SSH access** to required users only
3. **Regular updates** of system packages
4. **Monitor access** and changes
5. **Backup regularly** and test restoration

### Performance

1. **Parallel execution** where possible
2. **Efficient tasks** - Avoid unnecessary operations
3. **Caching** - Use fact caching for large inventories
4. **Connection pooling** - Reuse SSH connections
5. **Resource monitoring** - Monitor system resources

## Advanced Features

### Dynamic Inventories

```python
# dynamic_inventory.py
import json
import boto3

def get_ec2_instances():
    ec2 = boto3.client('ec2')
    instances = ec2.describe_instances()
    # Process and return inventory
```

### Custom Modules

```python
# custom_module.py
from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present')
        )
    )
    # Custom logic here
```

### Callback Plugins

```python
# callback_plugin.py
from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    def v2_runner_on_ok(self, result):
        # Custom success handling
        pass
```

## Integration with CI/CD

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to production
        run: |
          ansible-playbook ansible/playbooks/deploy-production.yml
        env:
          ANSIBLE_HOST_KEY_CHECKING: False
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Deploy') {
            steps {
                sh 'ansible-playbook ansible/playbooks/deploy-production.yml'
            }
        }
    }
}
```

## Support and Resources

### Documentation

- [Ansible Documentation](https://docs.ansible.com/)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
- [Ansible Galaxy](https://galaxy.ansible.com/)

### Community

- [Ansible Community](https://www.ansible.com/community)
- [GitHub Issues](https://github.com/ansible/ansible/issues)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/ansible)

### Training

- [Ansible Training](https://www.ansible.com/training)
- [Red Hat Training](https://www.redhat.com/en/services/training)
- [Online Courses](https://www.udemy.com/topic/ansible/)

