# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please generate a incident response playbook to respond a ransomware attack? [/INST] Sure. Here is the information requested.
Title: : Incident Response Playbook for Ransomware Infection (NIST Compliant)
1. Preparation: : Objective: Establish contacts, define procedures, gather information to save time during an incident. 
1.1 Develop and Maintain Policies:
Ensure all relevant policies are documented and reviewed regularly.
Establish an incident response policy that includes ransomware.
1.2 Identify Critical Assets:
Maintain an updated inventory of critical systems and data.
Prioritize assets based on business impact analysis.
1.3 Conduct Training and Awareness:
Regularly train staff on ransomware threats and incident response procedures.
Conduct phishing simulations and other exercises to prepare users.
1.4 Establish Incident Response Team (IRT):
Define roles and responsibilities within the IRT.
Ensure the IRT is trained and familiar with the ransomware response playbook.
1.5 Deploy and Configure Tools:
Ensure tools for detection, analysis, containment, and eradication are in place and configured.
Regularly update antivirus, EDR, and backup solutions.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve the appropriate parties.
2.1 Determine the type of ransomware
Find any related messages. Check:
Graphical user interfaces (GUIs) for the malware itself.
Text or HTML files, sometimes opened automatically after encryption.
Image files, often as wallpaper on infected systems.
Contact emails in encrypted file extensions.
Pop-ups after trying to open an encrypted file.
Voice messages.
Analyze the messages looking for clues to the ransomware type:
Ransomware name.
Language, structure, phrases, artwork.
Contact email.
Format of the user ID.
Ransom demand specifics.
Payment address in case of digital currency.
Support chat or support page.
Analyze affected and/or new files. Check:
File renaming scheme of encrypted files including extension and base name.
File corruption vs encryption.
Targeted file types and locations.
Owning user/group of affected files.
Icon for encrypted files.
File markers.
Existence of file listings, key files, or other data files.
Analyze affected software or system types.
Upload indicators to automated categorization services like Crypto Sheriff, ID Ransomware, or similar.
2.2 Determine the scope:
Which systems are affected?
Scan for concrete indicators of compromise (IOCs) such as files/hashes, processes, network connections, etc. Use endpoint protection/EDR, endpoint telemetry, system logs, etc.
Check similar systems for infection: check IAM tools, permissions management tools, directory services, etc.
Find external command and control (C2), if present, and find other systems connecting to it: check firewall or IDS logs, system logs/EDR, DNS logs, netflow or router logs, etc.
What data is affected?
Find anomalous changes to file metadata such as mass changes to creation or modification times. Check file metadata search tools.
Find changes to normally-stable or critical data files. Check file integrity monitoring tools.
2.3 Assess the impact to prioritize and motivate resources
Assess functional impact: impact to business or mission.
How much money is lost or at risk?
How many (and which) missions are degraded or at risk?
Assess information impact: impact to confidentiality, integrity, and availability of data.
How critical is the data to the business/mission?
How sensitive is the data?
What is the regulatory status of data?
2.4 Find the infection vector
Check the tactics captured in the Initial Access tactic of MITRE ATT&CK. Common specifics and data sources include:
Email attachment: check email logs, email security appliances and services, e-discovery tools, etc.
Insecure remote desktop protocol (RDP): check vulnerability scanning results, firewall configurations, etc.
Self-propagation (worm or virus) (check host telemetry/EDR, system logs, forensic analysis, etc.)
Infection via removable drives (worm or virus)
Delivered by other malware or attacker tool: expand investigation to include additional attacker tools or malware.
2.5 Communication
Notify senior leadership about the potential ransomware incident.
Provide initial findings and potential impacts.
Ensure all detection and analysis activities are documented.
Record details of the ransomware type, scope of impact, and initial response steps.
Discuss legal implications, compliance requirements, and potential liabilities.
Determine the need for law enforcement involvement.
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
3.1 Immediate Containment:
Disconnect affected systems from the network.
Quarantine impacted user accounts and groups.
Block malicious IPs, domains, and C2 servers.
3.2 Quarantine Steps:
Quarantine infected systems.
Quarantine affected users and groups.
Quarantine file shares and shared databases.
Quarantine backups, if not already secured.
Block command and control domains and addresses.
Remove vector emails from inboxes.
Confirm endpoint protection is up-to-date and enabled on all systems.
Confirm patches are deployed on all systems.
Deploy custom signatures to endpoint protection and network security tools based on discovered IOCs.
Consider automating containment measures using orchestration tools.
3.3 Communication:
Inform affected users about containment actions and expected disruptions.
Provide guidance on steps for users need to take to prevent further spread.
Regularly update stakeholders on containment progress.
Highlight any challenges and additional containment measures being implemented.
Explain why certain systems or services are down.
Provide timelines for restoration and additional containment measures.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
4.1 Remediation Steps:
Plan remediation events where these steps are launched together (or in coordinated fashion), with appropriate teams ready to respond to any disruption.
Consider the timing and tradeoffs of remediation actions: your response has consequences.
Rebuild infected systems from known-good media.
Restore from known-clean backups.
Confirm endpoint protection is up-to-date and enabled on all systems.
Confirm patches are deployed on all systems.
Deploy custom signatures to endpoint protection and network security tools based on discovered IOCs.
Watch for re-infection: consider increased priority for alarms/alerts related to this incident.
Provide updates to users on eradication progress and timelines for system restoration.
5. Recovery: : Objective: Restore the system to normal operations.
5.1 Steps:
Launch business continuity/disaster recovery plan(s): e.g., consider migration to alternate operating locations, fail-over sites, backup systems.
Recover data from known-clean backups to known-clean, patched, monitored systems (post-eradication).
Check backups for indicators of compromise.
Consider partial recovery and backup integrity testing.
Find and try known decryptors for the variant(s) discovered using resources like the No More Ransom! Project's Decryption Tools page.
Consider paying the ransom for irrecoverable critical assets/data, in accordance with policy (e.g., finance, legal, regulatory, insurance). Do not recommend paying the ransom: it does not guarantee a solution to the problem.
Consider ramifications with appropriate stakeholders.
Understand finance implications and budget.
Understand legal, regulatory, and insurance implications.
Understand mechanisms (e.g., technologies, platforms, intermediate vendors/go-betweens).
5.2 Generate required notifications based on applicable regulations:
Prepare notifications for regulators, especially if ransomware constitutes a data breach.
Ensure compliance with notification timelines and content requirements.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
6.1 Lessons Learned:
Conduct a post-incident review to identify gaps and improvements.
Update the incident response playbook based on findings.
6.2 Report and Document:
Compile a detailed incident report.
Ensure all incident documentation is complete and stored securely.
6.3 Improve Defenses:
Implement additional security controls as needed.
Review and enhance backup and recovery procedures.


7. Additional Contents
7.1 Tools and Resources:
Detection Tools: SIEM, EDR, antivirus, and IDS/IPS solutions.
Analysis Tools: Forensic analysis tools, ID Ransomware, Crypto Sheriff.
Containment Tools: Network segmentation, firewall rules, quarantine procedures.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
