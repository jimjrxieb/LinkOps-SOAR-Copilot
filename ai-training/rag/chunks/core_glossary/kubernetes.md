# Kubernetes Security

**Kubernetes (K8s)** is an open-source container orchestration platform that automates the deployment, scaling, and management of containerized applications across clusters of machines.

## Core Components

- **Control Plane**: API server, scheduler, controller manager, and etcd datastore
- **Worker Nodes**: kubelet, kube-proxy, and container runtime
- **Pods**: Smallest deployable units containing one or more containers
- **Services**: Network abstractions for pod communication

## Security Concerns

**RBAC Misconfigurations**: Overprivileged service accounts and users can escalate privileges
- Monitor for `system:masters` group membership
- Audit service account token usage patterns

**Pod Security**: Containers running with excessive privileges
- Enable Pod Security Standards (restricted, baseline, privileged)
- Scan images for vulnerabilities before deployment

**Secrets Management**: Hardcoded credentials and exposed secrets
- Use external secret management (HashiCorp Vault, AWS Secrets Manager)
- Enable encryption at rest for etcd

**Network Policies**: Unrestricted pod-to-pod communication
- Implement default-deny network policies
- Segment workloads by namespace and labels

**Supply Chain Attacks**: Malicious or vulnerable container images
- Use admission controllers (OPA Gatekeeper, Falco)
- Implement image signing and verification

## Monitoring & Detection

Monitor Kubernetes audit logs for:
- Unusual API server requests
- Privilege escalation attempts  
- Persistent volume access patterns
- Service account token abuse

**Your Environment**: K8s clusters monitored via Falco + CloudTrail integration with automated threat detection rules.

## Response Actions

- **Isolate**: Apply network policies to quarantine compromised pods
- **Contain**: Scale suspicious deployments to zero replicas
- **Investigate**: Export pod logs and filesystem artifacts
- **Recover**: Redeploy from known-good images and configurations