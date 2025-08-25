# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please provide guidelines to respond a ransomware infection or generate an incident response playbook for ransomware attack? [/INST] Sure. Here is the information requested.
Title: : Incident Response Playbook for Ransomware Infection
1. Preparation: : Objective: Establish contacts, define procedures, gather information to save time during an incident.
1.1 Knowledge Requirements
The usual operating systems security policies.
The usual users’ profile policies.
1.2 Architecture, VLAN Segmentation, and Interconnections
Have the capability to isolate entities, regions, partners, or the Internet.
1.3 Security Products
Ensure that endpoint and perimeter (email gateway, proxy caches) security products are up to date.
1.4 Deploy EDR Solution
Deploy an EDR solution on endpoints and servers:
This tool is crucial for incident response in case of ransomware or large-scale compromise, facilitating identification, containment, and remediation phases.
Launch EDR Search and AV scan with IOC explicit rules and get first indicators for remediation progress.
Set the EDR policies in prevent mode.
1.5 IT Support Awareness
Raise the IT support awareness regarding the ransomware threat, as it is often detected by end-users.
1.6 Block IOCs
Block IOCs linked to ransomware activities gathered by Threat Intelligence.
1.7 Security Solutions
Deploy and operate security solutions enabling detection and facilitating response:
Log gathering in a SIEM.
Have the capacity to run tools like YARA or DFIR-ORC (ANSSI).
1.8 Log Management
Have good log retention and verbosity.
1.9 Posture and Communication
Define a strict posture versus the attacker.
Prepare internal and external communication strategy.
Establish communication protocols: Define how the incident response team will communicate with each other, as well as with stakeholders and the public.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve the appropriate parties.
2.1 General Signs of Ransomware Presence
Monitoring of ransomware IOCs by a SOC.
Supervision of EDR alerts.
Odd professional emails containing attachments (often masquerading as invoices).
A ransom message displayed on the user’s desktop.
Complaints about unavailable or corrupted files with unusual extensions.
Numerous files being modified in a very short period on network shares.
Information published on ransomware operator websites or forums.
Check for lateral movement, connections to the AD, and ShareFile server with privileged accounts at abnormal times.
Look for unusual network or web browsing activities; especially connections to Tor I2P IP, Tor gateways (tor2web, etc.), or Bitcoin payment websites.
Look for rare connections.
2.2 Immediate Response
If a machine is identified with ransomware, unplug it from the network and keep it turned on for memory forensics investigation.

2.3 Scoping the Incident
Use EDR or large-scale hunting tools like YARA or DFIR-ORC to scope the ransomware-infected machines.
Identify the initial access and pivot used by the attackers as a priority.
2.4 Threat Actor Identification
Identifying the Threat Actor can help the following phases based on known TTPs.
Ransomware network compromise identification has many similarities with large-scale malware compromise, requiring faster reaction decisions.
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
3.1 Public Communication
Make a public statement based on the communication template prepared in the preparation phase.
3.2 Follow Defined Posture
Follow the posture defined in the preparation phase.
3.3 Endpoint and Perimeter Actions
Send undetected samples to the endpoint security provider and/or private sandboxes.
Send uncategorized malicious URLs, domain names, and IPs to the perimeter security provider.
Block traffic to C2s.
Block any IP detected as used by attackers.
3.4 Isolation
Isolate compromised VLANs, interconnections, entities, regions, partners, or the Internet.
Disable compromised/created accounts by attackers.
Disconnect all detected compromised computers from the network.
You could isolate with EDR and shut down the internet while keeping EDR connections up.
If you cannot isolate computers, disconnect or cancel the shared drives using commands 
Monitor ransomware threat actor websites and the Internet for any data leak publication related to the ransomware compromise.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
4.1 Removal of Threat
Remove the initial access used by the attacker.
Remove binaries used by the attacker to move laterally on the network.
Remove any accounts created by attackers.
Revert configuration changes.
Harden systems and network configuration.
5. Recovery: : Objective: Restore the system to normal operations.
5.1 Update and Verify
Update antivirus signatures for identified malicious binaries to be blocked.
Ensure no malicious binaries are present on the systems before reconnecting them.
Ensure that network traffic is back to normal.
Restore user’s documents from backups.
5.2 Prioritize Recovery
Prioritize the recovery plan based on your DRP (disaster recovery plan).
Verify that backups are not compromised: only restore from a backup if you are very confident that the backup and the device you are connecting it to are clean, or reimage the computer with a clean install.
Reset credentials including passwords, especially for administrator and other system accounts.
Monitor network traffic to identify if any infection remains.
If possible, apply geo-filtering on firewalls to block illegitimate foreign country traffic.
Maintain monitoring ransomware threat actor websites and the Internet for any data leak publication related to the ransomware compromise.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
6.1 Report
An incident report should be written and made available to all stakeholders. The following themes should be described:
Initial cause of the infection.
Actions and timelines of every important event.
What went right.
What went wrong.
Incident cost.
Indicators of compromise.


6.2 Capitalize
Define actions to improve malware and network intrusion detection processes based on this experience.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
