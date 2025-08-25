# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please generate an incident response playbook for phishing attack. Kindly convert this playbook to NIST incident response framework. [/INST] Sure. Here is the information requested.
Title: : Incident Response Playbook for Phishing Attack
1. Preparation: : Objective: Establish contacts, define procedures, gather information to save time during an incident.
Training and Awareness:
Reinforce training programs regarding suspected phishing attacks. Key suspicious indicators may include:
Misspellings in the message or subject.
Phony-seeming sender names, including mismatches between display name and email address.
Personal email addresses for official business.
Subject lines marked "[EXTERNAL]" on emails that look internal.
Malicious or suspicious links.
Receiving an email or attachment they were not expecting but from someone they know.
Ensure that IT and security staff is up to date on recent phishing techniques.
Resources and Communication:
Reference: User Actions for Suspected Phishing Attack.
Reference: Help Desk Actions for Suspected Phishing Attack.
Reference: Remediation Resources (Specify financial, personnel, and logistical resources to accomplish remediation).
Communicate incident response updates per procedure.
Communicate the impact of the incident and incident response actions.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve the appropriate parties.
Initial Detection:
Usually, you will be notified that a potential phishing attack is underway, either by a user, customer, or partner.
Investigate:
Scope the attack.
Determine the total number of impacted users.
Understand user actions in response to the phishing email.
Find potentially related activity:
Social media.
Suspicious emails.
Emails with links to external and unknown URLs.
Non-returnable or non-deliverable emails.
Notifications of suspicious activity.
Analyze the Message:
Analyze the message using a safe device:
Who received the message.
Who was targeted by the message.
Email address of the sender.
Subject line.
Message body.
Attachments (do not open attachments except according to established procedures).
Links, domains, and hostnames (do not follow links except according to established procedures).
Email metadata including message headers.
Sender information from the 'from' field and the X-authenticated user header.
All client and mail server IP addresses.
Note "quirks" or suspicious features.
Analyze links and attachments:
Use passive collection such as nslookup and whois to find IP addresses and registration information.
Find related domains using OSINT (e.g., reverse whois) on email addresses and other registration data.
Submit links, attachments, and/or hashes to VirusTotal.
Submit links, attachments, and/or hashes to a malware sandbox such as Cuckoo, Hybrid Analysis, Joe Sandbox, or VMray.
Categorize and Determine Severity:
Categorize the type of attack.
Determine the severity by considering:
Public or personal safety risks.
Personal data (or other sensitive data) at risk.
Evidence of who is behind the attack.
Number of affected assets.
Preliminary business impact.
Service impacts.
Control/record critical systems ability.
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
Containment:
Plan remediation events with appropriate teams ready to respond.
Contain affected accounts:
Change login credentials.
Reduce access to critical services, systems, or data.
Reinforce multi-factor authentication (MFA).
Block activity based on discovered indicators of compromise:
Block malicious domains using DNS, firewalls, or proxies.
Block messages with similar senders, message bodies, subjects, links, attachments, etc.
Implement forensic hold or retain forensic copies of messages.
Purge related messages from other user inboxes.
Consider mobile device containment measures such as wiping via mobile device management (MDM).
Increase detection "alert level" with enhanced monitoring.
Confirm relevant software upgrades and anti-malware updates.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.

Eradication:
Confirm and eliminate all traces of the phishing attack.
5. Recovery: : Recovery:
Launch business continuity/disaster recovery plan(s) if the compromise involved business outages.
Determine if any controls have failed and rectify them.
Recover normal operations ensuring no re-entry points remain.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
Documentation and Reporting:
Document the incident per procedure.
Communicate with internal and external legal counsel.
Communicate with users (internal).
Communicate with customers, focusing particularly on those whose data was affected.
Generate required notifications based on applicable regulations.
Contact insurance providers and comply with reporting and claims requirements.
Consider notifying and involving law enforcement.
Communicate with security and IT vendors, managed providers, and incident response consultants.
Post-Incident Review:
Conduct a lessons-learned meeting.
Update incident response plans and training programs based on findings.
Enhance preventive measures to reduce future risk.
Appendix
Help Desk Actions for Suspected Phishing Attack:
Stay calm, document the incident.
Take pictures and notes about the problem(s).
Ask detailed questions about the incident.
Record all information in the ticket.
Quarantine affected users and systems.
Contact the security team.
This structured approach ensures that the response to phishing incidents is comprehensive, systematic, and aligned with industry best practices.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
