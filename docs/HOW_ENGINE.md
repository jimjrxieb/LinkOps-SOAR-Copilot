# 🔧 HOW Engine - Executable Security Automation

## Vision: From "Do X" to Production-Ready Artifacts

The HOW Engine transforms natural language security requests into **executable, validated, rollback-ready artifacts** that compile and deploy safely.

```
"Enable certificate authority pilot" 
    ↓
PLAN → APPLY → VALIDATE → ROLLBACK
    ↓
├── terraform/ca_pilot.tf
├── k8s/cert-manager.yaml  
├── vault/pki_policy.hcl
└── runbooks/ca_rollback.md
```

## Architecture: LangGraph + Templates + Validators

### Core Components
```
pipelines/how/
├── prompts/
│   ├── planner.yaml        # Break down requests into steps
│   ├── implementer.yaml    # Generate specific artifacts  
│   ├── validator.yaml      # Check artifact quality
│   └── rollback.yaml       # Create rollback procedures
├── templates/
│   ├── terraform/          # IaC templates with placeholders
│   ├── kubernetes/         # Manifests and policies
│   ├── vault/             # Secrets management configs
│   ├── ansible/           # Configuration automation
│   └── runbooks/          # Human-readable procedures
├── validators/
│   ├── terraform_fmt.py   # tf fmt + tf validate
│   ├── kubeconform.py     # Kubernetes schema validation
│   ├── vault_policy.py    # HCL policy syntax checking
│   └── security_rules.py  # Security anti-pattern detection
└── workflows/
    ├── how_engine.py      # Main LangGraph workflow
    ├── artifact_builder.py # Template → concrete artifact
    └── rollback_planner.py # Automatic rollback generation
```

## LangGraph Workflow

### State Management
```python
class HOWState(TypedDict):
    request: str              # Original natural language request
    plan: List[Step]         # Decomposed implementation steps  
    artifacts: List[Artifact] # Generated files and configs
    validations: List[Result] # Validator results
    rollback: RollbackPlan   # Automated rollback procedure
    security_review: SecurityAudit # Anti-pattern detection
```

### Workflow Nodes
```
[REQUEST] → [PLAN] → [IMPLEMENT] → [VALIDATE] → [SECURE] → [ROLLBACK] → [COMPLETE]
     ↓         ↓          ↓           ↓          ↓           ↓
   Parse    Decompose   Generate    Check      Audit      Create
  Intent    into Steps  Artifacts  Syntax   Patterns   Recovery
```

### Node Implementations

#### 🎯 **Planner Node** (`prompts/planner.yaml`)
**Purpose**: Decompose requests into concrete, ordered steps
```yaml
system_prompt: |
  You are a security infrastructure planner. Break down requests into:
  1. Prerequisites (existing resources, permissions)
  2. Implementation steps (ordered, specific)  
  3. Validation criteria (how to verify success)
  4. Rollback triggers (what constitutes failure)
  
  Format as structured YAML with clear dependencies.

few_shot_examples:
  - input: "Enable certificate authority pilot"
    output:
      prerequisites:
        - Vault cluster accessible
        - Kubernetes cluster with cert-manager CRDs
        - Admin permissions on both
      steps:
        - name: "Configure Vault PKI backend"
          type: "vault_config"
          dependencies: []
        - name: "Deploy cert-manager with Vault integration"
          type: "k8s_manifest"  
          dependencies: ["vault_config"]
        - name: "Create Terraform module for CA management"
          type: "terraform"
          dependencies: ["k8s_manifest"]
      validation:
        - "Vault PKI backend healthy"
        - "cert-manager pods running"
        - "Test certificate issued successfully"
      rollback_triggers:
        - "Certificate issuance failure"
        - "Vault backend corruption"
        - "Security policy violation"
```

#### 🏗️ **Implementer Node** (`prompts/implementer.yaml`)
**Purpose**: Generate concrete artifacts from plan steps
```yaml
system_prompt: |
  Generate production-ready artifacts from implementation steps.
  Use templates and fill placeholders with specific values.
  
  Rules:
  - No hardcoded secrets (use ${VAR} placeholders)
  - Follow least-privilege principles  
  - Include monitoring and alerting configs
  - Add comprehensive comments
  
artifact_templates:
  terraform:
    template_dir: "templates/terraform/"
    validators: ["terraform_fmt", "security_rules"]
    
  k8s_manifest:
    template_dir: "templates/kubernetes/"
    validators: ["kubeconform", "security_rules"]
    
  vault_config:
    template_dir: "templates/vault/"  
    validators: ["vault_policy", "security_rules"]
```

#### ✅ **Validator Node** (`validators/`)
**Purpose**: Ensure artifacts meet quality and security standards

```python
# validators/terraform_fmt.py
def validate_terraform(artifact: Artifact) -> ValidationResult:
    """Validate Terraform syntax and format"""
    results = []
    
    # Syntax validation
    fmt_result = subprocess.run(['terraform', 'fmt', '-check'], 
                               capture_output=True, text=True)
    if fmt_result.returncode != 0:
        results.append(ValidationError("terraform_format", fmt_result.stderr))
    
    # Validate configuration
    validate_result = subprocess.run(['terraform', 'validate'],
                                   capture_output=True, text=True)  
    if validate_result.returncode != 0:
        results.append(ValidationError("terraform_syntax", validate_result.stderr))
    
    return ValidationResult(artifact.name, results)
```

#### 🛡️ **Security Node** (`validators/security_rules.py`)
**Purpose**: Anti-pattern detection and security review
```python
SECURITY_ANTI_PATTERNS = [
    # Terraform anti-patterns
    r'resource\s+"[^"]*"\s+"[^"]*"\s*\{[^}]*\*[^}]*\}',  # Wildcard permissions
    r'password\s*=\s*"[^"]*"',                            # Hardcoded passwords
    
    # Kubernetes anti-patterns  
    r'privileged:\s*true',                                # Privileged containers
    r'hostNetwork:\s*true',                              # Host networking
    r'runAsUser:\s*0',                                   # Root user
    
    # Vault anti-patterns
    r'policy\s*=\s*"[^"]*\*[^"]*"',                     # Wildcard policies
    r'period\s*=\s*"0s"',                               # No token expiry
]

def scan_security_patterns(artifact: Artifact) -> SecurityAudit:
    """Scan for security anti-patterns"""
    violations = []
    
    for pattern in SECURITY_ANTI_PATTERNS:
        matches = re.findall(pattern, artifact.content, re.IGNORECASE)
        if matches:
            violations.append(SecurityViolation(pattern, matches))
    
    return SecurityAudit(artifact.name, violations)
```

#### 🔄 **Rollback Node** (`prompts/rollback.yaml`)
**Purpose**: Generate automated rollback procedures
```yaml
system_prompt: |
  Create comprehensive rollback procedures for the implementation.
  Include both automated scripts and manual verification steps.
  
  Rollback must be:
  - Idempotent (safe to run multiple times)
  - Verifiable (clear success/failure criteria)
  - Documented (human-readable procedures)
  - Tested (validate rollback before deployment)

rollback_template: |
  # Rollback: {request_summary}
  
  ## Automated Rollback
  ```bash
  # Remove Kubernetes resources
  kubectl delete -f artifacts/k8s/
  
  # Destroy Terraform resources  
  terraform destroy -auto-approve
  
  # Disable Vault PKI backend
  vault auth disable pki/
  ```
  
  ## Verification Steps
  1. [ ] Kubernetes resources removed: `kubectl get all -l app=ca-pilot`
  2. [ ] Terraform state clean: `terraform show`  
  3. [ ] Vault PKI disabled: `vault auth list`
  
  ## Manual Recovery (if automated rollback fails)
  {manual_steps}
```

## Template Library

### 🏗️ **Terraform Templates** (`templates/terraform/`)

#### Certificate Authority Template
```hcl
# templates/terraform/vault_pki.tf
resource "vault_mount" "pki" {
  path                      = "${var.pki_path}"
  type                      = "pki"
  description               = "PKI backend for ${var.environment}"
  default_lease_ttl_seconds = 3600
  max_lease_ttl_seconds     = 86400
  
  # Security: Enable audit logging
  audit_non_hmac_request_keys  = ["common_name"]
  audit_non_hmac_response_keys = ["serial_number"]
}

resource "vault_pki_secret_backend_root_cert" "ca" {
  depends_on = [vault_mount.pki]
  
  backend              = vault_mount.pki.path
  type                 = "internal"
  common_name          = "${var.ca_common_name}"
  ttl                  = "87600h" # 10 years
  format              = "pem"
  private_key_format  = "der"
  key_type            = "rsa"
  key_bits            = 4096
  
  # Security: Restrict key usage
  exclude_cn_from_sans = true
  ou                   = ["Security Operations"]
  organization         = ["${var.organization}"]
}

# Monitoring
resource "vault_audit" "pki_audit" {
  type = "file"
  
  options = {
    file_path = "/vault/audit/pki.log"
    format    = "json"
  }
}
```

### ⚓ **Kubernetes Templates** (`templates/kubernetes/`)

#### Cert-Manager with Vault Integration
```yaml
# templates/kubernetes/cert_manager_vault.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: vault-issuer-${environment}
spec:
  vault:
    server: ${vault_url}
    path: ${pki_path}/sign/${role_name}
    auth:
      kubernetes:
        mountPath: /v1/auth/kubernetes
        role: cert-manager
        serviceAccountRef:
          name: cert-manager
          
---
apiVersion: v1  
kind: ServiceAccount
metadata:
  name: cert-manager
  namespace: cert-manager
automountServiceAccountToken: false

---
# Security: Network policy for cert-manager
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cert-manager-netpol
  namespace: cert-manager
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: cert-manager
  policyTypes:
  - Ingress
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 8200  # Vault API
  - to: []  # DNS
    ports:
    - protocol: UDP
      port: 53
```

### 🔐 **Vault Templates** (`templates/vault/`)

#### PKI Role and Policy
```hcl
# templates/vault/pki_policy.hcl
# Policy: PKI Certificate Management
path "${pki_path}/sign/${role_name}" {
  capabilities = ["create", "update"]
}

path "${pki_path}/issue/${role_name}" {
  capabilities = ["create"]
}

# Read-only access for monitoring
path "${pki_path}/cert/ca" {
  capabilities = ["read"]  
}

path "${pki_path}/config/cluster" {
  capabilities = ["read"]
}
```

## CLI Interface

### Core Commands
```bash
# Generate artifacts from natural language
python -m pipelines.how.run \
  --prompt "Enable certificate authority pilot for staging environment" \
  --output artifacts/ca_pilot/ \
  --validate \
  --security-scan

# Validate existing artifacts
python -m pipelines.how.validate \
  --input artifacts/ca_pilot/ \
  --validators terraform,kubeconform,security

# Generate rollback plan
python -m pipelines.how.rollback \
  --artifacts artifacts/ca_pilot/ \
  --output rollback/ca_pilot_rollback.md

# Test artifact deployment (dry-run)
python -m pipelines.how.test \
  --artifacts artifacts/ca_pilot/ \
  --environment staging \
  --dry-run
```

### Example Output Structure
```
artifacts/ca_pilot_2024_02_01/
├── terraform/
│   ├── main.tf
│   ├── variables.tf  
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── kubernetes/
│   ├── cert-manager.yaml
│   ├── network-policy.yaml
│   └── monitoring.yaml
├── vault/
│   ├── pki_policy.hcl
│   ├── role_config.json
│   └── auth_config.sh
├── runbooks/
│   ├── deployment_guide.md
│   ├── troubleshooting.md
│   └── rollback_procedure.md
├── tests/
│   ├── validate_certs.py
│   ├── security_test.py  
│   └── integration_test.sh
└── manifest.json           # Artifact metadata and BOM
```

## Quality Gates & Security

### Validation Pipeline
1. **Syntax Check**: Terraform fmt, YAML lint, HCL validate
2. **Schema Validation**: Kubeconform, JSON schema validation
3. **Security Scan**: Anti-pattern detection, secret scanning  
4. **Logic Check**: Dependency validation, resource conflicts
5. **Integration Test**: Dry-run deployment validation

### Security Standards
- ✅ **No Hardcoded Secrets**: All sensitive values parameterized
- ✅ **Least Privilege**: Minimal required permissions only
- ✅ **Network Isolation**: Default-deny network policies
- ✅ **Audit Logging**: All security-relevant events logged
- ✅ **Rollback Ready**: Automated recovery procedures included

### Quality Metrics
- **Artifact Success Rate**: % artifacts that deploy successfully
- **Rollback Effectiveness**: % rollbacks that restore clean state  
- **Security Compliance**: % artifacts passing security scans
- **Template Coverage**: % requests addressable with existing templates

The HOW Engine bridges the gap between security intent and production implementation, ensuring that "do X" requests result in secure, validated, rollback-ready infrastructure.