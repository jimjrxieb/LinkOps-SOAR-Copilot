# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please generate an incident response playbook for ransomware attack? [/INST] Sure. Here is the information requested.
Title: : Incident Response Playbook for Ransomware Infection
1. Preparation: : Objective: Establish contacts, define procedures, gather information to save time during an incident.
1.1 Knowledge Requirements
A good knowledge of:
The usual operating systems security policies is needed.
The usual users’ profile policies is needed.
Architecture, VLAN segmentation, and interconnections:
Have the capability to isolate entities, regions, partners, or the Internet.
1.2 Security Product Updates
Ensure that the endpoint and perimeter (email gateway, proxy caches) security products are up to date.
1.3 EDR Solution Deployment
Deploy an EDR solution on endpoints and servers:
This tool became one of the cornerstones of the incident response in case of ransomware or in large-scale compromise, facilitating identification, containment, and remediation phases.
Launch EDR Search and AV scan with IOC explicit rules and get first indicators for remediation progress following.
Set your EDR policies in prevent mode.
1.4 IT Support Awareness
Since this threat is often detected by end-users, raise your IT support awareness regarding the ransomware threat.
1.5 Block IOCs
Block IOCs linked to ransomware activities gathered by Threat Intelligence.
1.6 Security Solutions Deployment
Deploy and operate security solutions enabling detection and facilitating response:
Log gathering in a SIEM.
Have the capacity to run tools like YARA or DFIR-ORC (ANSSI).
1.7 Log Management
Have good log retention and verbosity.
1.8 Posture and Communication
Define a strict posture versus the attacker.
Prepare internal and external communication strategy.
Establish communication protocols: Define how the incident response team will communicate with each other, as well as with stakeholders and the public. 
1.10 Backups Preparation
Make sure to have exhaustive, recent, and reliable backups of local and network users’ data.
Follow the 3-2-1 backup rules:
At least three copies: three different copies in different places.
In two different formats: e.g., DVD, Hard drive, Cloud services.
One of those copies offsite: ensure one copy is safe offsite.
Try to use one backup format stored out of your network to protect against lateral movement.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve the appropriate parties.
2.1 General Signs of Ransomware Presence
Several leads might hint that the system could be compromised by ransomware:
Monitoring of ransomware IOCs by a SOC.
Supervision of EDR alerts.
Odd professional emails (often masquerading as invoices) containing attachments are being received.
A ransom message explaining that the documents have been encrypted and asking for money is displayed on the user’s desktop.
People are complaining about their files not being available or corrupted on their computers or their network shares with unusual extensions (.abc, .xyz, .aaa, etc.).
Numerous files are being modified in a very short period of time on the network shares.
Publication of information on the ransomware operator websites or forums.
Lateral movement is usually done; check all connections to the AD and ShareFile server with privileged accounts at abnormal times.
Look for unusual network or web browsing activities; especially connections to Tor I2P IP, Tor gateways (tor2web, etc.), or Bitcoin payment websites.
Look for rare connections.
2.2 Immediate Response
If a machine is identified with ransomware, unplug it from the network and keep it turned on for memory forensics investigation.

2.3 Scoping of the Incident
EDR or large-scale hunting tools like YARA or DFIR-ORC allow the scoping of the ransomware-infected machines.
The identification of the initial access and the pivot used by the attackers is the priority, as in large-scale malware compromise. This allows establishing the following phases actions.
2.4 Threat Actor Identification
The identification of the Threat Actor at the origin of the ransomware attack could help the following phases based on known TTPs.
Ransomware network compromise identification has many similarities with large-scale malware compromise. Most of the time, reaction decisions must be taken faster in ransomware cases.
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
3.2 Follow Defined Posture
Follow the posture defined in the preparation phase.
3.3 Security Provider Actions
Send the undetected samples to your endpoint security provider and/or private sandboxes.
Send the uncategorized malicious URLs, domain names, and IPs to your perimeter security provider.
Block traffic to C2s.
Block any IP detected as used by attackers.
3.4 Isolation
Isolate compromised VLANs, interconnections, entities, regions, partners, or the Internet.
Disable accounts compromised/created by attackers.
Disconnect all computers that have been detected as compromised from the network.
You could isolate with EDR and shut down the internet while keeping EDR connections up.
If you cannot isolate computers, disconnect/cancel the shared drives.
(NET USE x: \unc\path\ /DELETE).
Monitor ransomware threat actor websites and the Internet for any data leak publication related to the ransomware compromise.

3.5 Public Statement
Make a public statement as soon as possible based on the communication template elaborated in the preparation phase.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
4.1 Remove Threat
Remove the initial access used by the attacker.
Remove binaries used by the attacker to move laterally on the network.
Remove any accounts created by attackers.
Revert configuration changes.
Operate systems and network configuration hardening.
4.2 Remove Threat Steps
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
5. Recovery: : Objective: Restore the system to normal operations.
5.1 Antivirus and Malicious Binaries
Update antivirus signatures for identified malicious binaries to be blocked.
Ensure that no malicious binaries are present on the systems before reconnecting them.
Ensure that the network traffic is back to normal.
5.2 Document Restoration
Restore user’s documents from backups.
Prioritize your recovery plan based on your DRP (disaster recovery plan).
All of these steps shall be made in a step-by-step manner and with technical monitoring.
5.3 Backup Verification and System Reimaging
Verify that backups are not compromised: only restore from a backup if you are very confident that the backup and the device you are connecting it to are clean.
OR reimage the computer with a clean install.
5.4 Credential Reset
Reset credentials including passwords (especially for administrator and other system accounts).
5.5 Network Monitoring
Monitor network traffic to identify if any infection remains.
If possible, apply geo-filtering on firewalls to block illegitimate foreign country traffic.
Maintain the monitoring ransomware threat actor websites and the Internet to find if there is any data leak publication related to the ransomware compromise.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
6.1 Incident Report
An incident report should be written and made available to all the stakeholders. The following themes should be described:
Initial cause of the infection.
Actions and timelines of every important event.
What went right.
What went wrong.
Incident cost.
Indicators of compromise.
6.2 Capitalize
Actions to improve malware and network intrusion detection processes should be defined to capitalize on this experience.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
