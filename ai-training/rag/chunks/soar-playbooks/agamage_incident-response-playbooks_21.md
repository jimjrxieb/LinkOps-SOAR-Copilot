# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please generate an incident response playbook for ransomware attack in OT environment? [/INST] Sure. Here is the information requested.
Title: : Incident Response Playbook for Ransomware Infection
1. Preparation: : Objective: Establish contacts, define procedures, gather information to save time during an incident.
1.1 Knowledge Requirements
Security Policies: Ensure comprehensive understanding of security policies for operating systems and user profiles.
Network Architecture: Familiarize with architecture, VLAN segmentation, and interconnections to enable isolation of entities, regions, partners, or the Internet.
1.2 Security Product Updates
Regular Updates: Ensure endpoint and perimeter security products (email gateway, proxy caches) are up to date.
1.3 EDR Solution Deployment
Deployment: Implement EDR solutions on endpoints and servers.
Functionality: Use EDR for identification, containment, and remediation. Launch EDR searches and AV scans with IOC rules for progress indicators.
Policies: Set EDR policies to prevent mode.
1.4 IT Support Awareness
Awareness Training: Educate IT support on ransomware threats and detection.
1.5 Block IOCs
IOC Blocking: Block IOCs linked to ransomware activities using Threat Intelligence.
1.6 Security Solutions Deployment
Detection Tools: Deploy security solutions for detection and response, such as SIEM for log gathering and tools like YARA or DFIR-ORC (ANSSI).
1.7 Log Management
Log Retention: Maintain comprehensive log retention and verbosity.
1.8 Posture and Communication
Posture Definition: Define a strict posture against attackers.
Communication Strategy: Prepare internal and external communication plans.
1.9 Communication Protocols
Establish Protocols: Define communication methods for the incident response team, stakeholders, and the public.
1.10 Backups Preparation
Backup Strategy: Ensure exhaustive, recent, and reliable backups of local and network data.
3-2-1 Rule: Maintain three copies in two different formats, with one offsite. Use one backup format stored off the network.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve the appropriate parties.
2.1 General Signs of Ransomware Presence
Indicators:
Monitoring of ransomware IOCs by SOC.
Supervision of EDR alerts.
Odd emails with suspicious attachments.
Ransom messages on desktops.
File availability issues with unusual extensions.
Rapid file modifications on network shares.
Data leak publications by ransomware operators.
Unusual network activity or web browsing.
2.2 Immediate Response
Isolation: Unplug infected machines from the network and keep them on for memory forensics.
2.3 Scoping of the Incident
Scope Determination: Use EDR, YARA, or DFIR-ORC to identify ransomware-infected machines and the attack's initial access point.
2.4 Threat Actor Identification
Threat Actor ID: Identify the threat actor to leverage known TTPs for response planning.
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
3.2 Follow Defined Posture
Posture Adherence: Implement the predefined posture from the preparation phase.
3.3 Security Provider Actions
Sample Submission: Send undetected samples to security providers.
Block Threats: Block C2 traffic, malicious IPs, URLs, and domains.
3.4 Isolation
Network Isolation: Isolate compromised VLANs, entities, and partners. Disable compromised accounts.
Disconnect Devices: Disconnect compromised computers from the network and shared drives.
Monitor for Data Leaks: Keep an eye on ransomware threat actor websites for data leak publications.
3.5 Public Statement
Communication: Issue a public statement based on pre-prepared templates.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
4.1 Remove Threat
Initial Access Removal:
Identify and close any vulnerabilities or security gaps used by attackers to gain initial access.
Patch all affected systems with the latest security updates.
Review and update firewall rules and configurations to prevent unauthorized access.
Binary Removal:
Use EDR tools and antivirus software to scan for and remove malicious binaries and tools used by attackers.
Perform deep scans on all systems to ensure no residual malicious software remains.
Account Management:
Disable and remove any accounts created by the attackers.
Review and remove any unauthorized changes to existing accounts, such as added privileges.
Enforce strong password policies and multi-factor authentication (MFA) for all accounts.
Configuration Reversion:
Revert any unauthorized configuration changes made by attackers.
Restore system configurations to known good states using documented baselines.
System and Network Hardening:
Implement hardening measures across all systems and network devices. This includes disabling unnecessary services and ports, applying security patches, and enforcing least privilege principles.
Ensure proper network segmentation to limit the spread of potential future attacks.
Use network access control (NAC) to enforce security policies on devices trying to access the network.
Third-Party and Vendor Assessment:
Conduct a thorough review of third-party connections and vendor access to the network.
Implement stricter controls and monitoring for third-party access.
Ensure all third-party services and software are up to date and secure.
4.2 Incident-Specific Remediation Actions
Identify and Mitigate Exploited Vulnerabilities:
Use threat intelligence and vulnerability management tools to identify vulnerabilities exploited during the attack.
Prioritize and apply patches to mitigate these vulnerabilities across all systems.
Advanced Threat Detection:
Implement advanced threat detection solutions, such as intrusion detection/prevention systems (IDS/IPS), to monitor for signs of attack techniques used during the incident.
Enhance monitoring and alerting for abnormal activities related to the specific ransomware strain.
4.3 Collaboration and Coordination
Engage with Cybersecurity Experts:
Collaborate with external cybersecurity experts or incident response teams to gain insights and assistance in threat removal and remediation.
Utilize their expertise to conduct thorough forensics and ensure complete eradication of threats.
Share Threat Intelligence:
Share IOCs and attack details with relevant industry groups and threat intelligence communities to aid in broader defense efforts.
Stay updated with threat intelligence feeds to quickly react to new threats and indicators.
4.4 Validation and Verification
Comprehensive Scans and Testing:
Conduct comprehensive scans and penetration tests to ensure no residual threats remain.
Validate that all systems are free from malware and unauthorized modifications.
Verification of System Integrity:
Utilize integrity monitoring tools to verify the integrity of critical system files and configurations.
Regularly compare current system states with known good baselines to detect and remediate unauthorized changes.
4.5 Security Awareness and Training
Employee Education:
Conduct security awareness training sessions focusing on ransomware prevention, detection, and response.
Ensure employees understand the importance of reporting suspicious activities and adhering to security policies.
Regular Drills and Simulations:
Perform regular incident response drills and tabletop exercises to ensure the team is prepared for future incidents.
Simulate ransomware attack scenarios to practice detection, containment, and remediation steps.
4.6 Policy and Procedure Updates
Review and Update Policies:
Review and update security policies and procedures based on lessons learned from the incident.
Ensure policies reflect current best practices and address any gaps identified during the response.
Strengthen Access Controls:
Implement stronger access controls, such as role-based access control (RBAC), to minimize the risk of unauthorized access.
Regularly review and update access permissions to ensure they align with the principle of least privilege.
4.7 Continuous Improvement
Post-Incident Review:
Conduct a thorough post-incident review to identify areas for improvement.
Document lessons learned and incorporate them into the organization's incident response plan.
Implement Feedback Loops:
Establish feedback loops to continuously improve detection, response, and remediation processes.
Regularly review and refine incident response strategies to stay ahead of evolving threats.
5. Recovery: : Objective: Restore the system to normal operations.
5.1 Antivirus and Malicious Binaries
Update AV: Ensure antivirus signatures are updated and malicious binaries are removed.
5.2 Document Restoration
Restore Documents: Restore user documents from clean backups following the DRP.
5.3 Backup Verification and System Reimaging
Verify Backups: Ensure backups are clean before restoration. Reimage systems if necessary.
5.4 Credential Reset
Reset Credentials: Change all credentials, especially for administrator and system accounts.
5.5 Network Monitoring
Monitor Traffic: Continuously monitor network traffic for residual infections and apply geo-filtering.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
6.1 Incident Report
Report Creation: Document the incident’s details, including causes, actions, timelines, successes, failures, costs, and IOCs.
6.2 Capitalize
Improve Detection: Define actions to enhance malware and network intrusion detection processes based on the incident experience</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
