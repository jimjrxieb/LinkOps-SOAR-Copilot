# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please generate an incident response playbook for Locker Ransomware in an OT Environment? [/INST] Sure. Here is the information requested.
Title: : Incident Response Playbook: Locker Ransomware in an OT Environment (NIST Compliant)
1. Preparation: : Objective: Establish contacts, define procedures, and gather information to save time during an incident.
1.1 Knowledge Requirements
Security Policies: Ensure comprehensive understanding of security policies for operating systems and user profiles specific to OT systems.
Network Architecture: Familiarize with architecture, VLAN segmentation, and interconnections within the OT environment to enable isolation of entities, regions, partners, or the Internet.
1.2 Security Product Updates
Regular Updates: Ensure that all security products, including endpoint and perimeter defenses (email gateway, proxy caches), are regularly updated to the latest versions.
1.3 Endpoint Protection Deployment
Deployment: Implement endpoint protection solutions on all endpoints and servers within the OT environment.
Functionality: Use these solutions for identifying, containing, and remediating ransomware attacks. Configure policies to block identified threats.
1.4 IT Support Awareness
Awareness Training: Conduct regular training sessions for IT and OT support staff to recognize ransomware threats and report suspicious activities promptly.
1.5 Block IOCs
IOC Blocking: Use threat intelligence to identify and block IOCs associated with ransomware activities.
1.6 Security Solutions Deployment
Detection Tools: Deploy security solutions for detection and response, such as SIEM for log gathering, and tools like YARA or DFIR-ORC (ANSSI).
1.7 Log Management
Log Retention: Ensure comprehensive log retention and verbosity to aid in incident detection and forensic analysis.
1.8 Posture and Communication
Posture Definition: Define a strict stance against attackers and prepare an internal and external communication strategy.
1.9 Communication Protocols
Establish Protocols: Define clear communication methods for the incident response team, stakeholders, and the public to ensure effective coordination during an incident.
1.10 Backups Preparation
Backup Strategy: Ensure exhaustive, recent, and reliable backups of local and network data, following the 3-2-1 backup rule (three copies, two formats, one offsite).
Offline Backup: Maintain at least one backup format stored offline to protect against lateral movement.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve the appropriate parties.
2.1 General Signs of Locker Ransomware Presence
Indicators:
User reports of being locked out of their systems.
Displayed ransom messages on locked screens demanding payment for unlocking.
Inability to access critical OT systems or control interfaces.
Reports of unusual system behavior or changes in system functionality.
2.2 Immediate Response
Isolation: Physically isolate the affected machines from the network to prevent further spread.
Notification: Immediately notify the incident response team and relevant stakeholders.
Documentation: Document the symptoms and any ransom messages for further analysis.
2.3 Scoping of the Incident
Scope Determination: Use endpoint protection and monitoring tools to identify all affected systems.
Asset Inventory: Identify and prioritize critical OT systems affected by the ransomware.
2.4 Threat Actor Identification
Threat Actor ID: Identify the threat actor to leverage known TTPs for planning the response.
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
3.1 Public Statement
Communication: Issue a public statement based on pre-prepared templates to inform stakeholders and the public about the incident.
3.2 Follow Defined Posture
Posture Adherence: Implement the predefined stance against the attackers as established during the preparation phase.
3.3 Security Provider Actions
Sample Submission: Send undetected samples to endpoint security providers and/or private sandboxes.
Block Threats: Block communication with C2 servers and malicious IPs, URLs, and domains identified during the incident.
3.4 Isolation
Network Isolation: Isolate compromised VLANs, entities, and regions to prevent the spread of ransomware.
Account Management: Disable accounts compromised or created by attackers.
Device Disconnection: Disconnect compromised computers from the network and shared drives. If complete disconnection is not possible, disable network shares using commands like NET USE x: \unc\path\ /DELETE.
Monitor Data Leaks: Monitor ransomware threat actor websites for data leak publications.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
4.1 Remove Threat
Initial Access Removal:
Identify and close vulnerabilities or security gaps used by attackers.
Apply the latest security patches to affected systems.
Review and update firewall rules and configurations.
Binary Removal:
Use endpoint protection tools and antivirus software to scan for and remove malicious binaries.
Perform deep scans to ensure no residual malware remains.
Account Management:
Disable and remove accounts created by attackers.
Revert unauthorized changes to existing accounts.
Enforce strong password policies and multi-factor authentication (MFA).
Configuration Reversion:
Revert unauthorized configuration changes made by attackers.
Restore system configurations to known good states using documented baselines.
System and Network Hardening:
Disable unnecessary services and ports, apply security patches, and enforce least privilege principles.
Ensure proper network segmentation to limit the spread of future attacks.
Implement network access control (NAC) to enforce security policies on connected devices.
Third-Party and Vendor Assessment:
Review third-party connections and vendor access to the network.
Implement stricter controls and monitoring for third-party access.
Ensure third-party services and software are up to date and secure.
4.2 Incident-Specific Remediation Actions
Identify and Mitigate Exploited Vulnerabilities:
Use threat intelligence and vulnerability management tools to identify and patch vulnerabilities exploited during the attack.
Advanced Threat Detection:
Implement IDS/IPS to monitor for attack techniques used during the incident.
Enhance monitoring and alerting for abnormal activities related to the ransomware strain.
4.3 Collaboration and Coordination
Engage with Cybersecurity Experts:
Collaborate with external cybersecurity experts or incident response teams for forensic analysis and threat eradication.
Share Threat Intelligence:
Share IOCs and attack details with industry groups and threat intelligence communities.
4.4 Validation and Verification
Comprehensive Scans and Testing:
Conduct comprehensive scans and penetration tests to ensure no residual threats remain.
Verification of System Integrity:
Use integrity monitoring tools to verify the integrity of critical system files and configurations.
4.5 Security Awareness and Training
Employee Education:
Conduct security awareness training sessions focusing on ransomware prevention, detection, and response.
Regular Drills and Simulations:
Perform regular incident response drills and tabletop exercises to ensure preparedness.
4.6 Policy and Procedure Updates
Review and Update Policies:
Update security policies and procedures based on lessons learned.
Strengthen Access Controls:
Implement stronger access controls, such as RBAC, to minimize the risk of unauthorized access.
4.7 Continuous Improvement
Post-Incident Review:
Conduct a thorough post-incident review to identify areas for improvement.
Document lessons learned and update the incident response plan.
Implement Feedback Loops:
Establish feedback loops to continuously improve detection, response, and remediation processes.
5. Recovery: : Objective: Restore the system to normal operations.
5.1 System Unlock and Restoration
Unlock Systems: Use decryption keys if available or collaborate with security experts to unlock systems without paying the ransom.
Malicious Binary Removal: Ensure all ransomware-related binaries are removed before system restoration.
5.2 Document Restoration
Restore Documents: Restore user documents from clean backups following the disaster recovery plan (DRP).
Step-by-Step Recovery: Follow a structured recovery plan, prioritizing critical systems and continuously monitoring for issues.
5.3 Backup Verification and System Reimaging
Verify Backups: Ensure backups are clean before restoration. Reimage systems if necessary.
5.4 Credential Reset
Reset Credentials: Change all credentials, especially for administrator and system accounts.
5.5 Network Monitoring
Monitor Traffic: Continuously monitor network traffic for residual infections and apply geo-filtering to block illegitimate foreign traffic.
Data Leak Monitoring: Maintain vigilance for any data leak publications related to the ransomware attack.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
6.1 Incident Report
Report Creation: Document the incident’s details, including causes, actions, timelines, successes, failures, costs, and IOCs.
6.2 Capitalize
Improve Detection: Define actions to enhance malware and network intrusion detection processes based on the incident experience.
Update Training: Integrate lessons learned into ongoing security training and awareness programs for staff.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
